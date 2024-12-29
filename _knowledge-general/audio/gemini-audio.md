# Explore audio capabilities with the Gemini API

Gemini can respond to prompts about audio. For example, Gemini can:

- Describe, summarize, or answer questions about audio content.
- Provide a transcription of the audio.
- Provide answers or a transcription about a specific segment of the audio.

**Note:** You can't generate audio _output_ with the Gemini API.

This guide demonstrates different ways to interact with audio files and audio content using the Gemini API.

## Supported audio formats

Gemini supports the following audio format MIME types:

- WAV - `audio/wav`
- MP3 - `audio/mp3`
- AIFF - `audio/aiff`
- AAC - `audio/aac`
- OGG Vorbis - `audio/ogg`
- FLAC - `audio/flac`

### Technical details about audio

Gemini imposes the following rules on audio:

- Gemini represents each second of audio as 25 tokens; for example, one minute of audio is represented as 1,500 tokens.
- Gemini can only infer responses to English-language speech.
- Gemini can "understand" non-speech components, such as birdsong or sirens.
- The maximum supported length of audio data in a single prompt is 9.5 hours. Gemini doesn't limit the _number_ of audio files in a single prompt; however, the total combined length of all audio files in a single prompt cannot exceed 9.5 hours.
- Gemini downsamples audio files to a 16 Kbps data resolution.
- If the audio source contains multiple channels, Gemini combines those channels down to a single channel.

## Before you begin: Set up your project and API key

Before calling the Gemini API, you need to set up your project and configure your API key.

**Tip:** For complete setup instructions, see the [Gemini API quickstart](/gemini-api/docs/quickstart).

### Get and secure your API key

You need an API key to call the Gemini API. If you don't already have one, create a key in Google AI Studio.

[Get an API key ](https://aistudio.google.com/app/apikey)

It's strongly recommended that you do _not_ check an API key into your version control system.

You should store your API key in a secrets store such as Google Cloud [Secret Manager](https://cloud.google.com/secret-manager/docs).

This tutorial assumes that you're accessing your API key as an environment variable.

### Install the SDK package and configure your API key

**Note:** This section shows setup steps for a local Python environment. To install dependencies and configure your API key for Colab, see the [Authentication quickstart notebook](https://github.com/google-gemini/cookbook/blob/main/quickstarts/Authentication.ipynb)

The Python SDK for the Gemini API is contained in the `google-generativeai` package.

1. Install the dependency using pip:

   ```
   pip install -U google-generativeai
   ```

2. Import the package and configure the service with your API key:

   ```
   import os
   import google.generativeai as genai
   genai.configure(api_key=os.environ['API_KEY'])
   ```

## Make an audio file available to Gemini

You can make an audio file available to Gemini in either of the following ways:

- [Upload](#upload-audio) the audio file _prior_ to making the prompt request.
- Provide the audio file as [inline data](#inline-data) to the prompt request.

## Upload an audio file and generate content

You can use the File API to upload an audio file of any size. Always use the File API when the total request size (including the files, text prompt, system instructions, etc.) is larger than 20 MB.

**Note:** The File API lets you store up to 20 GB of files per project, with a per-file maximum size of 2 GB. Files are stored for 48 hours. They can be accessed in that period with your API key, but cannot be downloaded from the API. The File API is available at no cost in all regions where the Gemini API is available.

Call `media.upload` to upload a file using the File API. The following code uploads an audio file and then uses the file in a call to `models.generateContent`.

```python
import google.generativeai as genai
myfile = genai.upload_file(media / "sample.mp3")
print(f"{myfile=}")
model = genai.GenerativeModel("gemini-1.5-flash")
result = model.generate_content([myfile, "Describe this audio clip"])
print(f"{result.text=}")
```

## Get metadata for a file

You can verify the API successfully stored the uploaded file and get its metadata by calling `files.get`.

```python
import google.generativeai as genai
myfile = genai.upload_file(media / "poem.txt")
file_name = myfile.name
print(file_name) # "files/*"
myfile = genai.get_file(file_name)
print(myfile)
```

## List uploaded files

You can upload multiple audio files (and other kinds of files). The following code generates a list of all the files uploaded:

```python
import google.generativeai as genai
print("My files:")
for f in genai.list_files():
  print(" ", f.name)
```

## Delete uploaded files

Files are automatically deleted after 48 hours. Optionally, you can manually delete an uploaded file. For example:

```python
import google.generativeai as genai
myfile = genai.upload_file(media / "poem.txt")
myfile.delete()
try:
  # Error.
  model = genai.GenerativeModel("gemini-1.5-flash")
  result = model.generate_content([myfile, "Describe this file."])
except google.api_core.exceptions.PermissionDenied:
  pass
```

## Provide the audio file as inline data in the request

Instead of uploading an audio file, you can pass audio data in the same call that contains the prompt.

Then, pass that downloaded small audio file along with the prompt to Gemini:

```python
# Initialize a Gemini model appropriate for your use case.
model = genai.GenerativeModel('models/gemini-1.5-flash')
# Create the prompt.
prompt = "Please summarize the audio."
# Load the samplesmall.mp3 file into a Python Blob object containing the audio
# file's bytes and then pass the prompt and the audio to Gemini.
response = model.generate_content([
  prompt,
  {
    "mime_type": "audio/mp3",
    "data": pathlib.Path('samplesmall.mp3').read_bytes()
  }
])
# Output Gemini's response to the prompt and the inline audio.
print(response.text)
```

Note the following about providing audio as inline data:

- The maximum request size is 20 MB, which includes text prompts, system instructions, and files provided inline. If your file's size will make the _total request size_ exceed 20 MB, then [use the File API](#upload-audio) to upload files for use in requests.
- If you're using an audio sample multiple times, it is more efficient to [use the File API](#upload-audio).

## More ways to work with audio

This section provides a few additional ways to get more from audio.

### Get a transcript of the audio file

To get a transcript, just ask for it in the prompt. For example:

```python
# Initialize a Gemini model appropriate for your use case.
model = genai.GenerativeModel(model_name="gemini-1.5-flash")
# Create the prompt.
prompt = "Generate a transcript of the speech."
# Pass the prompt and the audio file to Gemini.
response = model.generate_content([prompt, audio_file])
# Print the transcript.
print(response.text)
```

### Refer to timestamps in the audio file

A prompt can specify timestamps of the form `MM:SS` to refer to particular sections in an audio file. For example, the following prompt requests a transcript that:

- Starts at 2 minutes 30 seconds from the beginning of the file.
- Ends at 3 minutes 29 seconds from the beginning of the file.

```python
# Create a prompt containing timestamps.
prompt = "Provide a transcript of the speech from 02:30 to 03:29."
```

### Count tokens

Call the `countTokens` method to get a count of the number of tokens in the audio file. For example:

```python
model.count_tokens([audio_file])
```

## What's next

This guide shows how to upload audio files using the File API and then generate text outputs from audio inputs. To learn more, see the following resources:

- [File prompting strategies](/gemini-api/docs/file-prompting-strategies): The Gemini API supports prompting with text, image, audio, and video data, also known as multimodal prompting.
- [System instructions](/gemini-api/docs/system-instructions): System instructions let you steer the behavior of the model based on your specific needs and use cases.
- [Safety guidance](/gemini-api/docs/safety-guidance): Sometimes generative AI models produce unexpected outputs, such as outputs that are inaccurate, biased, or offensive. Post-processing and human evaluation are essential to limit the risk of harm from such outputs.