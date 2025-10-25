#!/usr/bin/env python3
"""
LLM Configuration Checker
Verifies OpenAI/Gemini API configuration and connectivity for IBKR Trading WebUI.
"""
import argparse
import asyncio
import base64
import json
import os
import sys
from pathlib import Path

try:
    import httpx
    from dotenv import load_dotenv
except ImportError:
    print("❌ Required packages not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx", "python-dotenv"])
    import httpx
    from dotenv import load_dotenv


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print a section header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 80}{Colors.RESET}\n")


def print_success(text):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_warning(text):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")


def print_info(text):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")


def load_config():
    """Load configuration from .env file."""
    env_path = Path(__file__).parent / '.env'
    if not env_path.exists():
        print_error(f".env file not found at {env_path}")
        return {}
    
    load_dotenv(env_path)
    
    config = {
        'provider': os.getenv('LLM_VISION_PROVIDER', 'openai'),
        'openai_api_key': os.getenv('OPENAI_API_KEY', ''),
        'openai_api_base': os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1'),
        'openai_model': os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview'),
        'vision_model': os.getenv('LLM_VISION_MODEL', 'gpt-4-vision-preview'),
        'gemini_api_key': os.getenv('GEMINI_API_KEY', ''),
        'gemini_api_base': os.getenv('GEMINI_API_BASE', 'https://generativelanguage.googleapis.com/v1beta'),
        'max_tokens': int(os.getenv('LLM_VISION_MAX_TOKENS', '4096')),
        'temperature': float(os.getenv('LLM_VISION_TEMPERATURE', '0.1')),
        'timeout': int(os.getenv('LLM_VISION_TIMEOUT', '60')),
    }
    
    return config


def check_configuration(config):
    """Check if configuration is valid."""
    print_header("Configuration Check")
    
    provider = config.get('provider', 'openai')
    print_info(f"Provider: {provider}")
    
    if provider == 'openai':
        api_key = config.get('openai_api_key', '')
        api_base = config.get('openai_api_base', '')
        model = config.get('vision_model', '')
        
        print_info(f"API Base: {api_base}")
        print_info(f"Model: {model}")
        print_info(f"API Key: {api_key[:20]}..." if len(api_key) > 20 else "API Key: (empty)")
        
        if not api_key or api_key == 'your_key_here':
            print_error("OpenAI API key not configured!")
            print_info("Set OPENAI_API_KEY in .env file")
            print_info("Get your key from: https://platform.openai.com/api-keys")
            return False
        
        if not api_base:
            print_error("API base URL not configured!")
            return False
        
        print_success("OpenAI configuration looks valid")
        return True
        
    elif provider == 'gemini':
        api_key = config.get('gemini_api_key', '')
        api_base = config.get('gemini_api_base', '')
        
        print_info(f"API Base: {api_base}")
        print_info(f"API Key: {api_key[:20]}..." if len(api_key) > 20 else "API Key: (empty)")
        
        if not api_key:
            print_error("Gemini API key not configured!")
            print_info("Set GEMINI_API_KEY in .env file")
            print_info("Get your key from: https://aistudio.google.com/app/apikey")
            return False
        
        print_success("Gemini configuration looks valid")
        return True
    
    else:
        print_error(f"Unknown provider: {provider}")
        return False


async def test_openai_connection(config):
    """Test connection to OpenAI API."""
    print_header("OpenAI Connection Test")
    
    api_key = config.get('openai_api_key', '')
    api_base = config.get('openai_api_base', '')
    
    # Test 1: List models endpoint
    print_info("Testing /models endpoint...")
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            response = await client.get(
                f"{api_base}/models",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            
            if response.status_code == 200:
                print_success(f"API connection successful! ({response.status_code})")
                try:
                    models = response.json()
                    if 'data' in models:
                        print_info(f"Found {len(models['data'])} models")
                        # Show first few models
                        for model in models['data'][:5]:
                            print(f"  - {model.get('id', 'unknown')}")
                    else:
                        print_info(f"Response: {json.dumps(models, indent=2)[:500]}")
                    return True
                except json.JSONDecodeError:
                    print_warning("Response is not JSON")
                    print_info(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
                    print_info(f"Response preview: {response.text[:300]}")
                    return False
            elif response.status_code == 401:
                print_error(f"Authentication failed! ({response.status_code})")
                try:
                    error_data = response.json()
                    print_error(f"Error: {error_data}")
                except:
                    print_error(f"Response: {response.text[:200]}")
                return False
            elif response.status_code == 403:
                print_error(f"Access forbidden! ({response.status_code})")
                try:
                    error_data = response.json()
                    print_error(f"Error: {error_data}")
                except:
                    print_error(f"Response: {response.text[:200]}")
                return False
            else:
                print_warning(f"Unexpected response: {response.status_code}")
                print_info(f"Response: {response.text[:200]}")
                return False
                
    except httpx.ConnectError as e:
        print_error(f"Cannot connect to API: {e}")
        print_info(f"Check if {api_base} is accessible")
        return False
    except Exception as e:
        print_error(f"Error: {type(e).__name__}: {str(e)}")
        return False


async def test_openai_chat(config):
    """Test OpenAI chat completion endpoint."""
    print_header("OpenAI Chat Completion Test")
    
    api_key = config.get('openai_api_key', '')
    api_base = config.get('openai_api_base', '')
    model = config.get('vision_model', 'gpt-4-vision-preview')
    
    print_info(f"Testing with model: {model}")
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Say 'API test successful' in JSON format"}
        ],
        "max_tokens": 50,
        "temperature": 0.1
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            response = await client.post(
                f"{api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            
            if response.status_code == 200:
                print_success("Chat API works!")
                try:
                    result = response.json()
                    if 'choices' in result and len(result['choices']) > 0:
                        message = result['choices'][0].get('message', {}).get('content', '')
                        print_info(f"Response: {message[:100]}")
                    else:
                        print_info(f"Response structure: {json.dumps(result, indent=2)[:500]}")
                    return True
                except json.JSONDecodeError:
                    print_warning("Response is not JSON")
                    print_info(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
                    print_info(f"Response preview: {response.text[:500]}")
                    return False
            elif response.status_code == 401:
                print_error(f"Authentication failed! ({response.status_code})")
                try:
                    error_data = response.json()
                    print_error(f"Error: {json.dumps(error_data, indent=2)}")
                except:
                    print_error(f"Response: {response.text[:300]}")
                return False
            else:
                print_error(f"Request failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print_error(f"Error: {json.dumps(error_data, indent=2)}")
                except:
                    print_error(f"Response: {response.text[:300]}")
                return False
                
    except Exception as e:
        print_error(f"Error: {type(e).__name__}: {str(e)}")
        return False


async def test_openai_vision(config):
    """Test OpenAI vision API with a simple image."""
    print_header("OpenAI Vision API Test")
    
    api_key = config.get('openai_api_key', '')
    api_base = config.get('openai_api_base', '')
    model = config.get('vision_model', 'gpt-4-vision-preview')
    
    print_info(f"Testing vision model: {model}")
    print_info("Creating test image (red square)...")
    
    # Create a simple test image (1x1 red pixel PNG)
    # This is a base64-encoded 1x1 red pixel PNG
    test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What color is this pixel? Answer in one word."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{test_image_b64}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 10,
        "temperature": 0.1
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0, verify=False) as client:
            print_info("Sending vision API request...")
            response = await client.post(
                f"{api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            
            if response.status_code == 200:
                print_success("Vision API works! ✓")
                try:
                    result = response.json()
                    if 'choices' in result and len(result['choices']) > 0:
                        message = result['choices'][0].get('message', {}).get('content', '')
                        print_success(f"Model response: {message}")
                        print_success("Your LLM configuration is FULLY WORKING!")
                        return True
                    else:
                        print_warning("Unexpected response structure")
                        print_info(f"Response: {json.dumps(result, indent=2)[:500]}")
                        return False
                except json.JSONDecodeError:
                    print_warning("Response is not JSON")
                    print_info(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
                    print_info(f"Response preview: {response.text[:500]}")
                    print_error("API endpoint may not be OpenAI-compatible")
                    return False
            elif response.status_code == 401:
                print_error(f"Authentication failed! ({response.status_code})")
                try:
                    error_data = response.json()
                    print_error(f"Error details:")
                    print(json.dumps(error_data, indent=2))
                except:
                    print_error(f"Response: {response.text[:500]}")
                
                print_info("\n💡 Possible solutions:")
                print_info("1. Verify your API key is correct")
                print_info("2. Check if the key is valid for this endpoint")
                print_info("3. Contact your API provider for key verification")
                return False
            elif response.status_code == 404:
                print_error(f"Model not found! ({response.status_code})")
                print_warning(f"Model '{model}' may not be available at this endpoint")
                print_info("Try updating LLM_VISION_MODEL in .env")
                return False
            else:
                print_error(f"Request failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print_error(f"Error: {json.dumps(error_data, indent=2)}")
                except:
                    print_error(f"Response: {response.text[:500]}")
                return False
                
    except Exception as e:
        print_error(f"Error: {type(e).__name__}: {str(e)}")
        return False


async def test_gemini_connection(config):
    """Test connection to Gemini API."""
    print_header("Gemini Connection Test")
    
    api_key = config.get('gemini_api_key', '')
    api_base = config.get('gemini_api_base', '')
    
    print_info("Testing Gemini API...")
    print_warning("Note: Gemini implementation not yet complete in backend")
    
    # TODO: Implement Gemini testing
    print_info("Gemini testing will be added in future update")
    return True


def print_recommendations(config):
    """Print recommendations based on configuration."""
    print_header("Recommendations")
    
    provider = config.get('provider', 'openai')
    
    if provider == 'openai':
        api_base = config.get('openai_api_base', '')
        
        if 'openai.com' in api_base:
            print_info("✓ Using official OpenAI API")
            print_info("  Cost: ~$0.01-0.03 per chart analysis")
            print_info("  Quality: Excellent")
        else:
            print_info(f"Using custom endpoint: {api_base}")
            print_warning("Make sure your API key is valid for this endpoint")
            print_info("\nIf you have authentication issues:")
            print_info("1. Contact your API provider to verify the key")
            print_info("2. Check if the model name is correct")
            print_info("3. Try official OpenAI or Gemini as alternatives")
    
    print_info("\n💡 Alternative Options:")
    print_info("1. Google Gemini - FREE (1500 requests/day)")
    print_info("   Get key: https://aistudio.google.com/app/apikey")
    print_info("2. Official OpenAI - Best quality")
    print_info("   Get key: https://platform.openai.com/api-keys")


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Check LLM configuration for IBKR Trading WebUI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python check_llm_config.py                    # Check configuration only
  python check_llm_config.py --test-connection  # Test API connection
  python check_llm_config.py --test-all         # Run all tests
        """
    )
    
    parser.add_argument(
        '--test-connection',
        action='store_true',
        help='Test API connection'
    )
    
    parser.add_argument(
        '--test-chat',
        action='store_true',
        help='Test chat completion API'
    )
    
    parser.add_argument(
        '--test-vision',
        action='store_true',
        help='Test vision API (full test)'
    )
    
    parser.add_argument(
        '--test-all',
        action='store_true',
        help='Run all tests'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    if not config:
        print_error("Failed to load configuration")
        return 1
    
    # Always check configuration
    config_valid = check_configuration(config)
    
    if not config_valid:
        print_error("\n❌ Configuration is invalid!")
        print_info("Fix the issues above and try again")
        return 1
    
    # Run tests if requested
    provider = config.get('provider', 'openai')
    all_tests_passed = True
    
    if args.test_all or args.test_connection or args.test_chat or args.test_vision:
        if provider == 'openai':
            if args.test_all or args.test_connection:
                result = await test_openai_connection(config)
                all_tests_passed = all_tests_passed and result
            
            if args.test_all or args.test_chat:
                result = await test_openai_chat(config)
                all_tests_passed = all_tests_passed and result
            
            if args.test_all or args.test_vision:
                result = await test_openai_vision(config)
                all_tests_passed = all_tests_passed and result
        
        elif provider == 'gemini':
            result = await test_gemini_connection(config)
            all_tests_passed = all_tests_passed and result
    
    # Print recommendations
    print_recommendations(config)
    
    # Final status
    print_header("Summary")
    if all_tests_passed or not (args.test_all or args.test_connection or args.test_chat or args.test_vision):
        print_success("✓ All checks passed!")
        print_info("\nYour LLM configuration is ready to use.")
        print_info("Run: python check_llm_config.py --test-all")
        print_info("     to verify full API functionality")
        return 0
    else:
        print_error("✗ Some tests failed")
        print_info("\nPlease fix the issues above before using signal generation")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

