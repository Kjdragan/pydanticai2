## Context caching

In a typical AI workflow, you might pass the same input tokens over and over to a model. Using the Gemini API context caching feature, you can pass some content to the model once, cache the input tokens, and then refer to the cached tokens for subsequent requests. At certain volumes, using cached tokens is lower cost than passing in the same corpus of tokens repeatedly.

When you cache a set of tokens, you can choose how long you want the cache to exist before the tokens are automatically deleted. This caching duration is called the _time to live_ (TTL). If not set, the TTL defaults to 1 hour. The cost for caching depends on the input token size and how long you want the tokens to persist.

Context caching supports both Gemini 1.5 Pro and Gemini 1.5 Flash.

**Note:** Context caching is only available for stable models with fixed versions (for example, `gemini-1.5-pro-001`). You must include the version postfix (for example, the `-001` in `gemini-1.5-pro-001`).

## When to use context caching

Context caching is particularly well suited to scenarios where a substantial initial context is referenced repeatedly by shorter requests. Consider using context caching for use cases such as:

- Chatbots with extensive [system instructions](/gemini-api/docs/system-instructions)
- Repetitive analysis of lengthy video files
- Recurring queries against large document sets
- Frequent code repository analysis or bug fixing

## How caching reduces costs

Context caching is a paid feature designed to reduce overall operational costs. Billing is based on the following factors:

1. **Cache token count:** The number of input tokens cached, billed at a reduced rate when included in subsequent prompts.
2. **Storage duration:** The amount of time cached tokens are stored (TTL), billed based on the TTL duration of cached token count. There are no minimum or maximum bounds on the TTL.
3. **Other factors:** Other charges apply, such as for non-cached input tokens and output tokens.

For up-to-date pricing details, refer to the Gemini API [pricing page](/pricing). To learn how to count tokens, see the [Token guide](/gemini-api/docs/tokens).

## How to use context caching

This section assumes that you've installed a Gemini SDK (or have curl installed) and that you've configured an API key, as shown in the [quickstart](/gemini-api/docs/quickstart).

### Generate content using a cache

The following example shows how to generate content using a cached system instruction and video file.

```python
import os
import google.generativeai as genai
from google.generativeai import caching
import datetime
import time
# Get your API key from https://aistudio.google.com/app/apikey
# and access your API key as an environment variable.
# To authenticate from a Colab, see
# https://github.com/google-gemini/cookbook/blob/main/quickstarts/Authentication.ipynb
genai.configure(api_key=os.environ['API_KEY'])
# Download video file
# curl -O https://storage.googleapis.com/generativeai-downloads/data/Sherlock_Jr_FullMovie.mp4
path_to_video_file = 'Sherlock_Jr_FullMovie.mp4'
# Upload the video using the Files API
video_file = genai.upload_file(path=path_to_video_file)
# Wait for the file to finish processing
while video_file.state.name == 'PROCESSING':
    print('Waiting for video to be processed.')
    time.sleep(2)
    video_file = genai.get_file(video_file.name)
print(f'Video processing complete: {video_file.uri}')
# Create a cache with a 5 minute TTL
cache = caching.CachedContent.create(
    model='models/gemini-1.5-flash-001',
    display_name='sherlock jr movie', # used to identify the cache
    system_instruction=(
        'You are an expert video analyzer, and your job is to answer '
        'the user\'s query based on the video file you have access to.'
    ),
    contents=[video_file],
    ttl=datetime.timedelta(minutes=5),
)
# Construct a GenerativeModel which uses the created cache.
model = genai.GenerativeModel.from_cached_content(cached_content=cache)
# Query the model
response = model.generate_content([(
    'Introduce different characters in the movie by describing '
    'their personality, looks, and names. Also list the timestamps '
    'they were introduced for the first time.')])
print(response.usage_metadata)
# The output should look something like this:
#
# prompt_token_count: 696219
# cached_content_token_count: 696190
# candidates_token_count: 214
# total_token_count: 696433
print(response.text)
```

### List caches

It's not possible to retrieve or view cached content, but you can retrieve cache metadata (`name`, `model`, `display_name`, `usage_metadata`, `create_time`, `update_time`, and `expire_time`).

To list metadata for all uploaded caches, use `CachedContent.list()`:

```python
for c in caching.CachedContent.list():
    print(c)
```

### Update a cache

You can set a new `ttl` or `expire_time` for a cache. Changing anything else about the cache isn't supported.

The following example shows how to update the `ttl` of a cache using `CachedContent.update()`.

```python
import datetime
cache.update(ttl=datetime.timedelta(hours=2))
```

### Delete a cache

The caching service provides a delete operation for manually removing content from the cache. The following example shows how to delete a cache using `CachedContent.delete()`.

```python
cache.delete()
```

## Additional considerations

Keep the following considerations in mind when using context caching:

- The _minimum_ input token count for context caching is 32,768, and the _maximum_ is the same as the maximum for the given model. (For more on counting tokens, see the [Token guide](/gemini-api/docs/tokens)).
- The model doesn't make any distinction between cached tokens and regular input tokens. Cached content is simply a prefix to the prompt.
- There are no special rate or usage limits on context caching; the standard rate limits for `GenerateContent` apply, and token limits include cached tokens.
- The number of cached tokens is returned in the `usage_metadata` from the create, get, and list operations of the cache service, and also in `GenerateContent` when using the cache.