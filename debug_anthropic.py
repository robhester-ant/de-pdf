import sys
import traceback

try:
    import anthropic
    print(f"Anthropic version: {anthropic.__version__}")
    
    # Try to understand the issue
    print("\nTrying to initialize client...")
    client = anthropic.Anthropic(api_key="test-key")
    print("Success!")
except Exception as e:
    print(f"Error: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    
    # Let's see what's happening in the stack
    print("\n\nChecking anthropic module internals...")
    print(f"anthropic.Anthropic class: {anthropic.Anthropic}")
    print(f"anthropic.Anthropic.__module__: {anthropic.Anthropic.__module__}")
    
    # Try to understand the initialization
    import inspect
    print(f"\nAnthropic.__init__ signature: {inspect.signature(anthropic.Anthropic.__init__)}")