# Gemini 2.0 Flash Thinking Mode

Gemini 2.0 Flash Thinking Mode is an experimental model that's trained to generate the "thinking process" the model goes through as part of its response. As a result, Thinking Mode is capable of stronger reasoning capabilities in its responses than the Gemini 2.0 Flash Experimental model.

## Using Thinking Models

Thinking models are available in [Google AI Studio](https://aistudio.google.com/prompts/new_chat?model=gemini-2.0-flash-thinking-exp-1219), and through the Gemini API. One of the main considerations when using a model that returns the thinking process is how much information you want to expose to end users, as the thinking process can be quite verbose.

**Note:** We have setup `gemini-2.0-flash-thinking-exp` as an alias to the latest thinking model. Use this alias to get the latest Flash thinking model, or specify the full model name.

### Sending a basic request

### Python

This example uses the new [Google Genai SDK](/docs/sdks#python-quickstart) which is useful in this context for parsing out "thoughts" programmatically.

```python
from google import genai
client = genai.Client(api_key='GEMINI_API_KEY', http_options={'api_version':'v1alpha'})
response = client.models.generate_content(
  model='gemini-2.0-flash-thinking-exp', contents='Explain how RLHF works in simple terms.'
)
# Usually the first part is the thinking process, but it's not guaranteed
print(response.candidates[0].content.parts[0].text)
print(response.candidates[0].content.parts[1].text)
```

### Working with thoughts

On a standard request, the model responds with two parts, the thoughts and the model response. You can check programmatically if a part is a thought or not by seeing if the `part.thought` field is set to `True`.

### Python

To use the new `thought` parameter, you need to use the `v1alpha` version of the Gemini API along with the new [Google Genai SDK](/docs/sdks#python-quickstart).

```python
from google import genai
client = genai.Client(api_key='GEMINI_API_KEY', http_options={'api_version':'v1alpha'})
response = client.models.generate_content(
  model='gemini-2.0-flash-thinking-exp', contents='Explain how RLHF works in simple terms.'
)
for part in response.candidates[0].content.parts:
  if part.thought == True:
    print(f"Model Thought:\n{part.text}\n")
  else:
    print(f"\nModel Response:\n{part.text}\n")
```

### Streaming model thinking

Thinking models generally take longer to respond than standard models. To stream the model thinking, you can use the `generate_content_stream` method.

### Python

To use the new `thought` parameter, you need to use the `v1alpha` version of the Gemini API along with the new [Google Genai SDK](/docs/sdks#python-quickstart).

```python
from google import genai
client = genai.Client(api_key='GEMINI_API_KEY', http_options={'api_version':'v1alpha'})
for chunk in client.models.generate_content_stream(
  model='gemini-2.0-flash-thinking-exp', contents='What is your name?'
):
  for part in chunk.candidates[0].content.parts:
    if part.thought == True:
      print(f"Model Thought Chunk:\n{part.text}\n")
    else:
      print(f"\nModel Response:\n{part.text}\n")
```

### Multi-turn thinking conversations

During multi-turn conversations, the model will by default not pass the thoughts from the previous turn to the next turn, but you can still see the thoughts on the most recent turn.

### Python

The new [Google Genai SDK](/docs/sdks#python-quickstart) provides the ability to create a multi-turn chat session which is helpful to manage the state of a conversation.

```python
import asyncio
from google import genai
client = genai.Client(api_key='GEMINI_API_KEY', http_options={'api_version':'v1alpha'})
async def main():
  chat = client.aio.chats.create(model='gemini-2.0-flash-thinking-exp')
  response = await chat.send_message('What is your name?')
  print(response.text)
  response = await chat.send_message('What did you just say before this?')
  print(response.text)
asyncio.run(main())
```

## Limitations

Thinking Mode is an experimental model and has the following limitations:

- 32k token input limit
- Text and image input only
- 8k token output limit
- Text only output
- No built-in tool usage like Search or code execution

## What's next?

Try Thinking Mode for yourself with our [Colab notebook](https://github.com/google-gemini/cookbook/blob/main/gemini-2/thinking.ipynb), or open [Google AI Studio](https://aistudio.google.com/prompts/new_chat?model=gemini-2.0-flash-thinking-exp-1219) and try prompting the model for yourself.