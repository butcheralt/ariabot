#!/usr/bin/env python3
"""
Portable AI Chatbot - Main application
A configurable chatbot that works with multiple AI providers.
"""

import os
import sys
import json
from datetime import datetime
from typing import List, Dict
from config_manager import Config
from ai_providers import ProviderFactory

# Try to import colorama for colored output
try:
    from colorama import init, Fore, Style
    init()
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False
    # Define dummy color constants
    class Fore:
        CYAN = YELLOW = GREEN = RED = MAGENTA = ""
    class Style:
        BRIGHT = RESET_ALL = ""

class ChatBot:
    """Main chatbot class."""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize the chatbot."""
        self.config = Config(config_path)
        self.provider = None
        self.conversation_history = []
        self.setup_provider()
    
    def setup_provider(self):
        """Set up the AI provider."""
        try:
            self.provider = ProviderFactory.create_provider(self.config)
            
            # Validate configuration
            issues = self.config.validate() + self.provider.validate_config()
            if issues:
                print(f"{Fore.RED}Configuration issues found:{Style.RESET_ALL}")
                for issue in issues:
                    print(f"  • {issue}")
                print(f"\nPlease fix these issues and try again.")
                sys.exit(1)
                
        except Exception as e:
            print(f"{Fore.RED}Error setting up AI provider: {e}{Style.RESET_ALL}")
            print("Please check your configuration and try again.")
            sys.exit(1)
    
    def print_welcome(self):
        """Print welcome message."""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"  {Style.BRIGHT}{self.config.bot_name} - Portable AI Chatbot")
        print(f"{Style.RESET_ALL}{Fore.CYAN}{'='*60}")
        print(f"Provider: {Fore.YELLOW}{self.config.api_provider}{Style.RESET_ALL}")
        print(f"Model: {Fore.YELLOW}{self.config.model}{Style.RESET_ALL}")
        print(f"Temperature: {Fore.YELLOW}{self.config.temperature}{Style.RESET_ALL}")
        print(f"\n{Fore.GREEN}Type 'quit', 'exit', or 'bye' to end the conversation.")
        print(f"Type 'clear' to clear conversation history.")
        print(f"Type 'help' for more commands.{Style.RESET_ALL}\n")
    
    def print_help(self):
        """Print help information."""
        print(f"\n{Fore.MAGENTA}Available commands:")
        print("  quit, exit, bye - End the conversation")
        print("  clear - Clear conversation history")
        print("  help - Show this help message")
        print("  config - Show current configuration")
        print("  history - Show conversation history")
        print(f"  save - Save conversation to file{Style.RESET_ALL}\n")
    
    def print_config(self):
        """Print current configuration."""
        print(f"\n{Fore.CYAN}Current Configuration:")
        print(f"  Bot Name: {self.config.bot_name}")
        print(f"  Provider: {self.config.api_provider}")
        print(f"  Model: {self.config.model}")
        print(f"  Temperature: {self.config.temperature}")
        print(f"  Max Tokens: {self.config.max_tokens}")
        print(f"  Instructions: {self.config.bot_instructions[:100]}...")
        print(f"{Style.RESET_ALL}")
    
    def save_conversation(self):
        """Save conversation to file."""
        if not self.conversation_history:
            print(f"{Fore.YELLOW}No conversation to save.{Style.RESET_ALL}")
            return
        
        filename = self.config.get('settings.conversation_file', 'chat_history.txt')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            with open(filename, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"Conversation saved on {timestamp}\n")
                f.write(f"Bot: {self.config.bot_name} ({self.config.api_provider}/{self.config.model})\n")
                f.write(f"{'='*60}\n")
                
                for msg in self.conversation_history:
                    role = msg['role'].title()
                    content = msg['content']
                    f.write(f"{role}: {content}\n")
                
                f.write(f"{'='*60}\n\n")
            
            print(f"{Fore.GREEN}Conversation saved to {filename}{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}Error saving conversation: {e}{Style.RESET_ALL}")
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
        print(f"{Fore.GREEN}Conversation history cleared.{Style.RESET_ALL}")
    
    def show_history(self):
        """Show conversation history."""
        if not self.conversation_history:
            print(f"{Fore.YELLOW}No conversation history.{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.MAGENTA}Conversation History:")
        for i, msg in enumerate(self.conversation_history, 1):
            role = msg['role'].title()
            content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
            print(f"{i}. {role}: {content}")
        print(f"{Style.RESET_ALL}")
    
    def get_messages_for_api(self) -> List[Dict[str, str]]:
        """Get formatted messages for API call."""
        messages = []
        
        # Add system message with bot instructions
        if self.config.bot_instructions:
            messages.append({
                "role": "system",
                "content": self.config.bot_instructions
            })
        
        # Add conversation history
        messages.extend(self.conversation_history)
        
        return messages
    
    def handle_user_input(self, user_input: str) -> bool:
        """Handle user input and return True to continue, False to quit."""
        user_input = user_input.strip()
        
        # Handle commands
        if user_input.lower() in ['quit', 'exit', 'bye']:
            if self.config.get('settings.save_conversation', True) and self.conversation_history:
                self.save_conversation()
            print(f"\n{Fore.GREEN}Goodbye! Thanks for chatting with {self.config.bot_name}!{Style.RESET_ALL}")
            return False
        
        elif user_input.lower() == 'clear':
            self.clear_history()
            return True
        
        elif user_input.lower() == 'help':
            self.print_help()
            return True
        
        elif user_input.lower() == 'config':
            self.print_config()
            return True
        
        elif user_input.lower() == 'history':
            self.show_history()
            return True
        
        elif user_input.lower() == 'save':
            self.save_conversation()
            return True
        
        elif not user_input:
            return True
        
        # Process as chat message
        return self.process_chat_message(user_input)
    
    def process_chat_message(self, user_input: str) -> bool:
        """Process a chat message and return response."""
        try:
            # Add user message to history
            self.conversation_history.append({
                "role": "user",
                "content": user_input
            })
            
            # Get messages for API
            messages = self.get_messages_for_api()
            
            # Get response from AI provider
            print(f"{Fore.YELLOW}Thinking...{Style.RESET_ALL}", end="", flush=True)
            response = self.provider.chat(messages)
            print(f"\r{' ' * 20}\r", end="")  # Clear "Thinking..." message
            
            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            
            # Print response
            print(f"{Fore.GREEN}{self.config.bot_name}:{Style.RESET_ALL} {response}\n")
            
            # Show token usage if enabled
            if self.config.get('settings.show_token_usage', False):
                total_chars = sum(len(msg['content']) for msg in messages)
                print(f"{Fore.CYAN}(Estimated tokens used: ~{total_chars // 4}){Style.RESET_ALL}")
            
            return True
            
        except Exception as e:
            print(f"\r{Fore.RED}Error: {e}{Style.RESET_ALL}")
            print("Please try again or check your configuration.")
            return True
    
    def run(self):
        """Run the main chat loop."""
        self.print_welcome()
        
        try:
            while True:
                # Get user input
                user_input = input(f"{Fore.CYAN}You:{Style.RESET_ALL} ")
                
                # Handle input and check if should continue
                if not self.handle_user_input(user_input):
                    break
                    
        except KeyboardInterrupt:
            print(f"\n\n{Fore.YELLOW}Chat interrupted. Goodbye!{Style.RESET_ALL}")
            if self.config.get('settings.save_conversation', True) and self.conversation_history:
                self.save_conversation()
        except EOFError:
            print(f"\n\n{Fore.YELLOW}End of input. Goodbye!{Style.RESET_ALL}")
            if self.config.get('settings.save_conversation', True) and self.conversation_history:
                self.save_conversation()

def main():
    """Main function."""
    # Check if config exists
    if not os.path.exists("config.json"):
        print(f"{Fore.RED}Configuration file 'config.json' not found.")
        print(f"Please run 'python setup.py' first to configure your chatbot.{Style.RESET_ALL}")
        sys.exit(1)
    
    # Create and run chatbot
    try:
        bot = ChatBot()
        bot.run()
    except Exception as e:
        print(f"{Fore.RED}Error starting chatbot: {e}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()