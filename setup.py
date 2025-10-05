#!/usr/bin/env python3
"""
Interactive setup wizard for the Portable AI Chatbot.
Guides users through configuration of their chatbot.
"""

import json
import os
import getpass
from typing import Dict, Any, List

# Try to import colorama for colored output
try:
    from colorama import init, Fore, Style
    init()
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False
    # Define dummy color constants
    class Fore:
        CYAN = YELLOW = GREEN = RED = MAGENTA = WHITE = ""
    class Style:
        BRIGHT = RESET_ALL = ""

class SetupWizard:
    """Interactive setup wizard for chatbot configuration."""
    
    def __init__(self):
        self.config = {}
        self.providers_info = {
            'openai': {
                'name': 'OpenAI',
                'models': ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo-preview', 'gpt-3.5-turbo-16k'],
                'default_model': 'gpt-3.5-turbo',
                'api_key_help': 'Get your API key from: https://platform.openai.com/api-keys'
            },
            'anthropic': {
                'name': 'Anthropic (Claude)',
                'models': ['claude-3-sonnet-20240229', 'claude-3-opus-20240229', 'claude-3-haiku-20240307'],
                'default_model': 'claude-3-sonnet-20240229',
                'api_key_help': 'Get your API key from: https://console.anthropic.com/'
            },
            'cohere': {
                'name': 'Cohere',
                'models': ['command', 'command-light', 'command-nightly'],
                'default_model': 'command',
                'api_key_help': 'Get your API key from: https://dashboard.cohere.ai/api-keys'
            },
            'groq': {
                'name': 'Groq (Ultra-Fast)',
                'models': [
                    'groq/compound',              # Best: No rate limit
                    'groq/compound-mini',         # Fast: No rate limit  
                    'llama-3.3-70b-versatile',   # LLaMA 3.3 70B
                    'llama-3.1-8b-instant',      # Fastest LLaMA
                    'gemma2-9b-it',              # Google Gemma2
                    'deepseek-r1-distill-llama-70b',  # Reasoning model
                    'openai/gpt-oss-120b',       # GPT OSS 120B
                    'custom'
                ],
                'default_model': 'groq/compound',
                'api_key_help': 'Get your API key from: https://console.groq.com/keys'
            },
            'ollama': {
                'name': 'Ollama (Local)',
                'models': ['llama2', 'codellama', 'mistral', 'custom'],
                'default_model': 'llama2',
                'api_key_help': 'No API key needed for local Ollama installation'
            }
        }
    
    def print_header(self):
        """Print setup wizard header."""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"  {Style.BRIGHT}Portable AI Chatbot - Setup Wizard")
        print(f"{Style.RESET_ALL}{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"\nWelcome! This wizard will help you configure your chatbot.")
        print("Press Enter to use default values shown in [brackets].")
        print(f"{Fore.YELLOW}Type 'back' to go to previous step, 'exit' to quit.{Style.RESET_ALL}\n")
    
    def get_input(self, prompt: str, default: str = "", password: bool = False, allow_back: bool = True) -> str:
        """Get user input with optional default value."""
        if default:
            full_prompt = f"{prompt} [{default}]: "
        else:
            full_prompt = f"{prompt}: "
        
        if password:
            value = getpass.getpass(full_prompt)
        else:
            value = input(full_prompt).strip()
        
        # Handle special commands
        if allow_back and value.lower() in ['back', 'exit', 'quit']:
            return value.lower()
        
        return value if value else default
    
    def get_choice(self, prompt: str, choices: List[str], default: str = "", allow_custom: bool = False) -> str:
        """Get user choice from a list of options."""
        print(f"\n{prompt}")
        for i, choice in enumerate(choices, 1):
            marker = " (default)" if choice == default else ""
            print(f"  {i}. {choice}{marker}")
        
        if allow_custom:
            print(f"  {Fore.CYAN}Or type a custom value{Style.RESET_ALL}")
        
        while True:
            choice_input = input(f"\nEnter choice [1-{len(choices)}] (or 'back'/'exit'): ").strip()
            
            # Handle navigation commands
            if choice_input.lower() in ['back', 'exit', 'quit']:
                return choice_input.lower()
            
            if not choice_input and default:
                return default
            
            # Try to parse as number
            try:
                choice_num = int(choice_input)
                if 1 <= choice_num <= len(choices):
                    return choices[choice_num - 1]
                else:
                    print(f"{Fore.RED}Please enter a number between 1 and {len(choices)}{Style.RESET_ALL}")
            except ValueError:
                # If allow_custom, treat as custom input
                if allow_custom and choice_input:
                    return choice_input
                else:
                    print(f"{Fore.RED}Please enter a valid number{Style.RESET_ALL}")
    
    def setup_basic_info(self):
        """Setup basic bot information."""
        print(f"{Fore.YELLOW}Step 1: Basic Bot Information{Style.RESET_ALL}")
        
        bot_name = self.get_input(
            "What should your bot be called?",
            "Assistant"
        )
        
        if bot_name in ['exit', 'quit']:
            return 'exit'
        if bot_name == 'back':
            return 'back'
        
        self.config['bot_name'] = bot_name
        
        print(f"\n{Fore.GREEN}Great! Now let's define your bot's personality and behavior.{Style.RESET_ALL}")
        print("This is the system prompt that tells your bot how to behave.")
        
        # Provide some preset options
        preset_instructions = {
            "1": "You are a helpful assistant. Be concise and friendly in your responses.",
            "2": "You are a coding assistant. Help users with programming questions and provide clear code examples.",
            "3": "You are a creative writing assistant. Help users brainstorm ideas and improve their writing.",
            "4": "You are a customer service bot. Be polite, helpful, and professional in all interactions.",
            "5": "Custom (enter your own instructions)"
        }
        
        print(f"\nChoose a personality preset:")
        for key, value in preset_instructions.items():
            print(f"  {key}. {value}")
        
        while True:
            choice = input(f"\nEnter choice [1-5] (or 'back'/'exit'): ").strip()
            
            if choice.lower() in ['exit', 'quit']:
                return 'exit'
            if choice.lower() == 'back':
                return 'back'
            
            if choice == "5":
                print(f"\n{Fore.CYAN}Enter your custom instructions (press Enter twice when done):{Style.RESET_ALL}")
                lines = []
                empty_count = 0
                while empty_count < 2:
                    line = input()
                    if line == "":
                        empty_count += 1
                    else:
                        empty_count = 0
                        lines.append(line)
                self.config['bot_instructions'] = "\n".join(lines) if lines else preset_instructions["1"]
                break
            elif choice in preset_instructions:
                self.config['bot_instructions'] = preset_instructions[choice]
                break
            else:
                print(f"{Fore.RED}Please enter a number between 1 and 5{Style.RESET_ALL}")
        
        return 'next'
    
    def setup_provider(self):
        """Setup AI provider configuration."""
        print(f"\n{Fore.YELLOW}Step 2: AI Provider Configuration{Style.RESET_ALL}")
        
        # Show available providers
        provider_list = []
        print(f"\nAvailable AI providers:")
        for key, info in self.providers_info.items():
            provider_list.append(key)
            print(f"  {len(provider_list)}. {info['name']}")
        
        # Get provider choice
        choice = self.get_choice(
            "Choose your AI provider:",
            provider_list,
            "groq"  # Changed default to Groq since user uses it
        )
        
        if choice in ['exit', 'quit', 'back']:
            return choice
        
        self.config['api_provider'] = choice
        provider_info = self.providers_info[choice]
        
        # Get model choice with custom option
        print(f"\n{Fore.GREEN}Available models for {provider_info['name']}:{Style.RESET_ALL}")
        
        # Add custom option to models list
        model_options = provider_info['models'] + ['custom']
        
        model_choice = self.get_choice(
            f"Choose a model (or type your own custom model name):",
            model_options,
            provider_info['default_model'],
            allow_custom=True
        )
        
        if model_choice in ['exit', 'quit']:
            return 'exit'
        if model_choice == 'back':
            return 'back'
        
        # Handle custom model input
        if model_choice == 'custom':
            custom_model = self.get_input(
                f"Enter custom model name",
                provider_info['default_model']
            )
            if custom_model in ['exit', 'quit']:
                return 'exit'
            if custom_model == 'back':
                return self.setup_provider()  # Restart provider setup
            model_choice = custom_model
        
        self.config['model'] = model_choice
        print(f"{Fore.GREEN}✓ Model set to: {model_choice}{Style.RESET_ALL}")
        
        # Get API key (except for Ollama)
        if choice != 'ollama':
            print(f"\n{Fore.CYAN}{provider_info['api_key_help']}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Tip: You can paste your API key here (Ctrl+V or right-click){Style.RESET_ALL}")
            api_key = self.get_input(
                f"Enter your {provider_info['name']} API key (or press Enter to set later)",
                password=False,  # Changed to False to allow pasting
                allow_back=False  # Don't allow back during API key entry
            )
            self.config['api_key'] = api_key
        else:
            self.config['api_key'] = ""
            ollama_url = self.get_input(
                "Ollama server URL",
                "http://localhost:11434"
            )
            if ollama_url in ['exit', 'quit']:
                return 'exit'
            if ollama_url == 'back':
                return 'back'
            self.config['ollama_url'] = ollama_url
        
        return 'next'
    
    def setup_advanced_settings(self):
        """Setup advanced configuration."""
        print(f"\n{Fore.YELLOW}Step 3: Advanced Settings (Optional){Style.RESET_ALL}")
        
        # Temperature setting
        temp_input = self.get_input(
            "Temperature (0.0-2.0, higher = more creative)",
            "0.7"
        )
        
        if temp_input in ['exit', 'quit']:
            return 'exit'
        if temp_input == 'back':
            return 'back'
        
        try:
            self.config['temperature'] = float(temp_input)
        except ValueError:
            self.config['temperature'] = 0.7
        
        # Max tokens
        tokens_input = self.get_input(
            "Maximum response length (tokens)",
            "150"
        )
        
        if tokens_input in ['exit', 'quit']:
            return 'exit'
        if tokens_input == 'back':
            return 'back'
        
        try:
            self.config['max_tokens'] = int(tokens_input)
        except ValueError:
            self.config['max_tokens'] = 150
        
        # Additional settings
        settings = {}
        
        save_conv = self.get_input(
            "Save conversations to file? (y/n)",
            "y"
        )
        
        if save_conv in ['exit', 'quit']:
            return 'exit'
        if save_conv == 'back':
            return 'back'
        
        settings['save_conversation'] = save_conv.lower().startswith('y')
        
        if settings['save_conversation']:
            conv_file = self.get_input(
                "Conversation file name",
                "chat_history.txt"
            )
            if conv_file in ['exit', 'quit']:
                return 'exit'
            if conv_file == 'back':
                return 'back'
            settings['conversation_file'] = conv_file
        
        show_tokens = self.get_input(
            "Show token usage info? (y/n)",
            "n"
        )
        
        if show_tokens in ['exit', 'quit']:
            return 'exit'
        if show_tokens == 'back':
            return 'back'
        
        settings['show_token_usage'] = show_tokens.lower().startswith('y')
        
        self.config['settings'] = settings
        return 'next'
    
    def save_config(self):
        """Save configuration to file."""
        try:
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            print(f"\n{Fore.GREEN}✓ Configuration saved to config.json{Style.RESET_ALL}")
            return True
        except Exception as e:
            print(f"\n{Fore.RED}Error saving configuration: {e}{Style.RESET_ALL}")
            return False
    
    def show_summary(self):
        """Show configuration summary."""
        print(f"\n{Fore.MAGENTA}Configuration Summary:{Style.RESET_ALL}")
        print(f"  Bot Name: {self.config['bot_name']}")
        print(f"  Provider: {self.config['api_provider']}")
        print(f"  Model: {self.config['model']}")
        print(f"  Temperature: {self.config['temperature']}")
        print(f"  Max Tokens: {self.config['max_tokens']}")
        print(f"  Instructions: {self.config['bot_instructions'][:60]}...")
    
    def run(self):
        """Run the setup wizard with navigation support."""
        self.print_header()
        
        try:
            # Check if config already exists
            if os.path.exists('config.json'):
                overwrite = self.get_input(
                    f"{Fore.YELLOW}config.json already exists. Overwrite? (y/n){Style.RESET_ALL}",
                    "n",
                    allow_back=False
                )
                if overwrite in ['exit', 'quit']:
                    print(f"{Fore.YELLOW}Setup cancelled.{Style.RESET_ALL}")
                    return
                if not overwrite.lower().startswith('y'):
                    print("Setup cancelled.")
                    return
            
            # Setup flow with navigation
            steps = [
                ('basic_info', self.setup_basic_info),
                ('provider', self.setup_provider),
                ('advanced', self.setup_advanced_settings)
            ]
            
            current_step = 0
            
            while current_step < len(steps):
                step_name, step_func = steps[current_step]
                result = step_func()
                
                if result == 'exit':
                    print(f"\n{Fore.YELLOW}Setup cancelled.{Style.RESET_ALL}")
                    return
                elif result == 'back':
                    if current_step > 0:
                        current_step -= 1
                        print(f"\n{Fore.CYAN}Going back to previous step...{Style.RESET_ALL}")
                    else:
                        print(f"\n{Fore.YELLOW}Already at first step.{Style.RESET_ALL}")
                else:  # result == 'next' or completed successfully
                    current_step += 1
            
            # Show summary and confirm
            self.show_summary()
            
            confirm = self.get_input(
                f"\n{Fore.WHITE}Save this configuration? (y/n){Style.RESET_ALL}",
                "y",
                allow_back=False
            )
            
            if confirm in ['exit', 'quit']:
                print(f"{Fore.YELLOW}Setup cancelled.{Style.RESET_ALL}")
                return
            
            if confirm.lower().startswith('y'):
                if self.save_config():
                    print(f"\n{Fore.GREEN}{'='*60}")
                    print(f"  🎉 Setup Complete!")
                    print(f"{'='*60}{Style.RESET_ALL}")
                    
                    # Offer to install dependencies
                    install_deps = self.get_input(
                        f"\nInstall required Python packages? (y/n)",
                        "y",
                        allow_back=False
                    )
                    
                    if install_deps.lower().startswith('y'):
                        print(f"\n{Fore.CYAN}Installing dependencies...{Style.RESET_ALL}")
                        os.system("pip install -r requirements.txt")
                        print(f"\n{Fore.GREEN}✓ Dependencies installed!{Style.RESET_ALL}")
                    
                    # Show clear next steps
                    print(f"\n{Fore.CYAN}{'='*60}")
                    print(f"  {Style.BRIGHT}🚀 Ready to Start!{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
                    print(f"\n{Fore.GREEN}To start chatting, run:{Style.RESET_ALL}")
                    print(f"  {Fore.YELLOW}python chatbot.py{Style.RESET_ALL}")
                    print(f"\n{Fore.GREEN}Or use the quick launcher:{Style.RESET_ALL}")
                    print(f"  {Fore.YELLOW}.\\start_chatbot.bat{Style.RESET_ALL}")
                    print(f"\n{Fore.CYAN}Enjoy your AI chatbot! 🤖{Style.RESET_ALL}\n")
                else:
                    print(f"\n{Fore.RED}Setup failed. Please try again.{Style.RESET_ALL}")
            else:
                print("Setup cancelled.")
                
        except KeyboardInterrupt:
            print(f"\n\n{Fore.YELLOW}Setup cancelled.{Style.RESET_ALL}")
        except Exception as e:
            print(f"\n{Fore.RED}Setup error: {e}{Style.RESET_ALL}")

def main():
    """Main function."""
    wizard = SetupWizard()
    wizard.run()

if __name__ == "__main__":
    main()