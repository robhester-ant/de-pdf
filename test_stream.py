import anthropic

client = anthropic.Anthropic(api_key="test-key")

# Check if streaming is supported
print("Checking streaming support...")
try:
    response = client.completions.create(
        model="claude-2.1",
        prompt=f"{anthropic.HUMAN_PROMPT} Hello {anthropic.AI_PROMPT}",
        max_tokens_to_sample=10,
        temperature=0,
        stream=True
    )
    print(f"Response type: {type(response)}")
    print(f"Is iterator: {hasattr(response, '__iter__')}")
    if hasattr(response, '__iter__'):
        for chunk in response:
            print(f"Chunk: {chunk}")
            break
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()