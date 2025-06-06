import anthropic
import sys

print(f"Anthropic version: {anthropic.__version__}")
print(f"Python version: {sys.version}")

try:
    # Test initialization
    client = anthropic.Anthropic(api_key="test-key")
    print("Success: anthropic.Anthropic(api_key='test-key') works")
except Exception as e:
    print(f"Error with anthropic.Anthropic(api_key='test-key'): {e}")

try:
    # Test alternative initialization
    client = anthropic.Client("test-key")
    print("Success: anthropic.Client('test-key') works")
except Exception as e:
    print(f"Error with anthropic.Client('test-key'): {e}")

# Print available attributes
print("\nAvailable in anthropic module:")
for attr in dir(anthropic):
    if not attr.startswith('_'):
        print(f"  - {attr}")