#!/usr/bin/env python3
"""
Telegram Bot integration for the Portable AI Chatbot.
Connects your AI chatbot to Telegram messaging platform.
"""

import logging
import sys
from typing import Dict
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config_manager import Config
from ai_providers import ProviderFactory

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Store conversation history per user
user_conversations: Dict[int, list] = {}

class TelegramChatBot:
    """Telegram bot wrapper for AI chatbot."""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize the Telegram bot."""
        self.config = Config(config_path)
        
        # Validate Telegram token
        if not self.config.get('telegram_bot_token'):
            raise ValueError("Telegram bot token not found in config.json. Add 'telegram_bot_token' field.")
        
        # Initialize AI provider
        try:
            self.provider = ProviderFactory.create_provider(self.config)
            logger.info(f"Initialized {self.config.api_provider} provider with model {self.config.model}")
        except Exception as e:
            logger.error(f"Failed to initialize AI provider: {e}")
            raise
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name
        
        # Initialize conversation history for new user
        if user_id not in user_conversations:
            user_conversations[user_id] = []
        
        welcome_message = (
            f"👋 Hello {user_name}! I'm {self.config.bot_name}.\n\n"
            f"💬 Just send me a message and I'll respond!\n\n"
            f"Commands:\n"
            f"/start - Show this welcome message\n"
            f"/clear - Clear conversation history\n"
            f"/help - Show help information\n"
            f"/info - Show bot configuration"
        )
        
        await update.message.reply_text(welcome_message)
        logger.info(f"User {user_id} ({user_name}) started the bot")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_message = (
            f"🤖 {self.config.bot_name} - Help\n\n"
            f"📝 How to use:\n"
            f"• Simply send me any message and I'll respond\n"
            f"• I maintain conversation context\n"
            f"• Use /clear to start fresh\n\n"
            f"⚙️ Commands:\n"
            f"/start - Restart and show welcome\n"
            f"/clear - Clear your chat history\n"
            f"/help - Show this help\n"
            f"/info - Bot configuration details\n\n"
            f"💡 Tips:\n"
            f"• I remember our conversation\n"
            f"• Be specific for better responses\n"
            f"• Clear history if context gets confusing"
        )
        
        await update.message.reply_text(help_message)
    
    async def info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /info command."""
        user_id = update.effective_user.id
        msg_count = len(user_conversations.get(user_id, []))
        
        info_message = (
            f"ℹ️ Bot Information\n\n"
            f"🤖 Name: {self.config.bot_name}\n"
            f"🌐 Provider: {self.config.api_provider.title()}\n"
            f"🧠 Model: {self.config.model}\n"
            f"🌡️ Temperature: {self.config.temperature}\n"
            f"📊 Max Tokens: {self.config.max_tokens}\n"
            f"💬 Messages in History: {msg_count}\n\n"
            f"📋 Instructions:\n{self.config.bot_instructions[:150]}..."
        )
        
        await update.message.reply_text(info_message)
    
    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clear command."""
        user_id = update.effective_user.id
        
        if user_id in user_conversations:
            user_conversations[user_id] = []
        
        await update.message.reply_text(
            "✅ Conversation history cleared! Starting fresh. 🆕"
        )
        logger.info(f"User {user_id} cleared their conversation history")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages."""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name
        user_message = update.message.text
        
        # Initialize conversation history if needed
        if user_id not in user_conversations:
            user_conversations[user_id] = []
        
        logger.info(f"User {user_id} ({user_name}): {user_message[:50]}...")
        
        try:
            # Show typing indicator
            await update.message.chat.send_action("typing")
            
            # Add user message to history
            user_conversations[user_id].append({
                "role": "user",
                "content": user_message
            })
            
            # Build messages for API
            messages = []
            
            # Add system message with bot instructions
            if self.config.bot_instructions:
                messages.append({
                    "role": "system",
                    "content": self.config.bot_instructions
                })
            
            # Add conversation history
            messages.extend(user_conversations[user_id])
            
            # Get AI response
            response = self.provider.chat(messages)
            
            # Add assistant response to history
            user_conversations[user_id].append({
                "role": "assistant",
                "content": response
            })
            
            # Send response to user
            await update.message.reply_text(response)
            
            logger.info(f"Responded to user {user_id}: {response[:50]}...")
            
        except Exception as e:
            logger.error(f"Error processing message from user {user_id}: {e}")
            await update.message.reply_text(
                "❌ Sorry, I encountered an error. Please try again or use /clear to reset."
            )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors."""
        logger.error(f"Update {update} caused error {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ An error occurred. Please try again later."
            )
    
    def run(self):
        """Run the Telegram bot."""
        try:
            # Create application
            app = Application.builder().token(self.config.get('telegram_bot_token')).build()
            
            # Add command handlers
            app.add_handler(CommandHandler("start", self.start_command))
            app.add_handler(CommandHandler("help", self.help_command))
            app.add_handler(CommandHandler("info", self.info_command))
            app.add_handler(CommandHandler("clear", self.clear_command))
            
            # Add message handler
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
            
            # Add error handler
            app.add_error_handler(self.error_handler)
            
            # Start the bot
            logger.info(f"Starting Telegram bot: {self.config.bot_name}")
            logger.info(f"Using {self.config.api_provider} with model {self.config.model}")
            print(f"\n{'='*60}")
            print(f"  🚀 {self.config.bot_name} - Telegram Bot Started!")
            print(f"{'='*60}")
            print(f"Provider: {self.config.api_provider}")
            print(f"Model: {self.config.model}")
            print(f"\n✅ Bot is running! Go to Telegram and start chatting.")
            print(f"Press Ctrl+C to stop.\n")
            
            # Run the bot
            app.run_polling(allowed_updates=Update.ALL_TYPES)
            
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            print(f"\n❌ Error: {e}")
            print("\nMake sure:")
            print("1. Your Telegram bot token is correct in config.json")
            print("2. You have installed: pip install python-telegram-bot")
            print("3. Your AI API key is valid")
            sys.exit(1)

def main():
    """Main function."""
    try:
        bot = TelegramChatBot()
        bot.run()
    except KeyboardInterrupt:
        print("\n\n👋 Bot stopped. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()