import anthropic

client = anthropic.Anthropic(api_key="test-key")
print("Available attributes on client:")
for attr in dir(client):
    if not attr.startswith('_'):
        print(f"  - {attr}")

print("\nChecking for completion methods:")
if hasattr(client, 'completions'):
    print("Has completions attribute")
if hasattr(client, 'messages'):
    print("Has messages attribute")
if hasattr(client, 'complete'):
    print("Has complete method")