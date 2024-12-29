# Models

PydanticAI is Model-agnostic and has built in support for the following model providers:

- [OpenAI](#openai)
- [Anthropic](#anthropic)
- Gemini via two different APIs: [Generative Language API](#gemini) and [VertexAI API](#gemini-via-vertexai)
- [Ollama](#ollama)
- [Groq](#groq)
- [Mistral](#mistral)

You can also [add support for other models](#implementing-custom-models).

PydanticAI also comes with `TestModel` and `FunctionModel` for testing and development.

To use each model provider, you need to configure your local environment and make sure you have the right packages installed.

## OpenAI

### Install

To use OpenAI models, you need to either install `pydantic-ai`, or install `pydantic-ai-slim` with the `openai` optional group:

```bash
pip install 'pydantic-ai-slim[openai]'
```

### Configuration

To use `OpenAIModel` through their main API, go to [platform.openai.com](https://platform.openai.com/) and follow your nose until you find the place to generate an API key.

### Environment variable

Once you have the API key, you can set it as an environment variable:

```bash
export OPENAI_API_KEY='your-api-key'
```

You can then use `OpenAIModel` by name:

```python
from pydantic_ai import Agent
agent = Agent('openai:gpt-4o')
```

Or initialise the model directly with just the model name:

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
model = OpenAIModel('gpt-4o')
agent = Agent(model)
```

### `api_key` argument

If you don't want to or can't set the environment variable, you can pass it at runtime via the `api_key` argument:

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
model = OpenAIModel('gpt-4o', api_key='your-api-key')
agent = Agent(model)
```

### `base_url` argument

To use another OpenAI-compatible API, such as [OpenRouter](https://openrouter.ai), you can make use of the `base_url` argument:

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
model = OpenAIModel(
  'anthropic/claude-3.5-sonnet',
  base_url='https://openrouter.ai/api/v1',
  api_key='your-api-key',
)
agent = Agent(model)
```

### Custom OpenAI Client

`OpenAIModel` also accepts a custom `AsyncOpenAI` client via the `openai_client` parameter, so you can customise the `organization`, `project`, `base_url` etc. as defined in the [OpenAI API docs](https://platform.openai.com/docs/api-reference).

```python
from openai import AsyncAzureOpenAI
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
client = AsyncAzureOpenAI(
  azure_endpoint='...',
  api_version='2024-07-01-preview',
  api_key='your-api-key',
)
model = OpenAIModel('gpt-4o', openai_client=client)
agent = Agent(model)
```

## Anthropic

### Install

To use `AnthropicModel` models, you need to either install `pydantic-ai`, or install `pydantic-ai-slim` with the `anthropic` optional group:

```bash
pip install 'pydantic-ai-slim[anthropic]'
```

### Configuration

To use [Anthropic](https://anthropic.com) through their API, go to [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys) to generate an API key.

### Environment variable

Once you have the API key, you can set it as an environment variable:

```bash
export ANTHROPIC_API_KEY='your-api-key'
```

You can then use `AnthropicModel` by name:

```python
from pydantic_ai import Agent
agent = Agent('claude-3-5-sonnet-latest')
```

Or initialise the model directly with just the model name:

```python
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
model = AnthropicModel('claude-3-5-sonnet-latest')
agent = Agent(model)
```

### `api_key` argument

If you don't want to or can't set the environment variable, you can pass it at runtime via the `api_key` argument:

```python
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
model = AnthropicModel('claude-3-5-sonnet-latest', api_key='your-api-key')
agent = Agent(model)
```

## Gemini

For prototyping only

Google themselves refer to this API as the "hobby" API, I've received 503 responses from it a number of times. The API is easy to use and useful for prototyping and simple demos, but I would not rely on it in production.

### Install

To use `GeminiModel` models, you just need to install `pydantic-ai` or `pydantic-ai-slim`, no extra dependencies are required.

### Configuration

`GeminiModel` lets you use the Google's Gemini models through their [Generative Language API](https://ai.google.dev/api/all-methods), `generativelanguage.googleapis.com`.

To use `GeminiModel`, go to [aistudio.google.com](https://aistudio.google.com/) and follow your nose until you find the place to generate an API key.

### Environment variable

Once you have the API key, you can set it as an environment variable:

```bash
export GEMINI_API_KEY='your-api-key'
```

You can then use `GeminiModel` by name:

```python
from pydantic_ai import Agent
agent = Agent('gemini-1.5-flash')
```

Or initialise the model directly with just the model name:

```python
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
model = GeminiModel('gemini-1.5-flash')
agent = Agent(model)
```

### `api_key` argument

If you don't want to or can't set the environment variable, you can pass it at runtime via the `api_key` argument:

```python
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
model = GeminiModel('gemini-1.5-flash', api_key='your-api-key')
agent = Agent(model)
```

## Gemini via VertexAI

To run Google's Gemini models in production, you should use `VertexAIModel` which uses the `*-aiplatform.googleapis.com` API.

### Install

To use `VertexAIModel`, you need to either install `pydantic-ai`, or install `pydantic-ai-slim` with the `vertexai` optional group:

```bash
pip install 'pydantic-ai-slim[vertexai]'
```

### Configuration

This interface has a number of advantages over `generativelanguage.googleapis.com` documented above:

1. The VertexAI API is more reliably and marginally lower latency in our experience.
2. You can [purchase provisioned throughput](https://cloud.google.com/vertex-ai/generative-ai/docs/provisioned-throughput#purchase-provisioned-throughput) with VertexAI to guarantee capacity.
3. If you're running PydanticAI inside GCP, you don't need to set up authentication, it should "just work".
4. You can decide which region to use, which might be important from a regulatory perspective, and might improve latency.

### Application default credentials

Luckily if you're running PydanticAI inside GCP, or you have the `gcloud` CLI installed and configured, you should be able to use `VertexAIModel` without any additional setup.

To use `VertexAIModel`, with [application default credentials](https://cloud.google.com/docs/authentication/application-default-credentials) configured (e.g. with `gcloud`), you can simply use:

```python
from pydantic_ai import Agent
from pydantic_ai.models.vertexai import VertexAIModel
model = VertexAIModel('gemini-1.5-flash')
agent = Agent(model)
```

### Service account

If instead of application default credentials, you want to authenticate with a service account, you'll need to create a service account, add it to your GCP project, give that service account the "Vertex AI Service Agent" role, and download the service account JSON file.

Once you have the JSON file, you can use it thus:

```python
from pydantic_ai import Agent
from pydantic_ai.models.vertexai import VertexAIModel
model = VertexAIModel(
  'gemini-1.5-flash',
  service_account_file='path/to/service-account.json',
)
agent = Agent(model)
```

### Customising region

Whichever way you authenticate, you can specify which region requests will be sent to via the `region` argument.

```python
from pydantic_ai import Agent
from pydantic_ai.models.vertexai import VertexAIModel
model = VertexAIModel('gemini-1.5-flash', region='asia-east1')
agent = Agent(model)
```

## Ollama

### Install

To use `OllamaModel`, you need to either install `pydantic-ai`, or install `pydantic-ai-slim` with the `openai` optional group:

```bash
pip install 'pydantic-ai-slim[openai]'
```

### Configuration

To use [Ollama](https://ollama.com/), you must first download the Ollama client, and then download a model using the [Ollama model library](https://ollama.com/library).

You must also ensure the Ollama server is running when trying to make requests to it. For more information, please see the [Ollama documentation](https://github.com/ollama/ollama/tree/main/docs).

## Groq

### Install

To use `GroqModel`, you need to either install `pydantic-ai`, or install `pydantic-ai-slim` with the `groq` optional group:

```bash
pip install 'pydantic-ai-slim[groq]'
```

### Configuration

To use [Groq](https://groq.com/) through their API, go to [console.groq.com/keys](https://console.groq.com/keys) and follow your nose until you find the place to generate an API key.

### Environment variable

Once you have the API key, you can set it as an environment variable:

```bash
export GROQ_API_KEY='your-api-key'
```

You can then use `GroqModel` by name:

```python
from pydantic_ai import Agent
agent = Agent('groq:llama-3.1-70b-versatile')
```

Or initialise the model directly with just the model name:

```python
from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel
model = GroqModel('llama-3.1-70b-versatile')
agent = Agent(model)
```

### `api_key` argument

If you don't want to or can't set the environment variable, you can pass it at runtime via the `api_key` argument:

```python
from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel
model = GroqModel('llama-3.1-70b-versatile', api_key='your-api-key')
agent = Agent(model)
```

## Mistral

### Install

To use `MistralModel`, you need to either install `pydantic-ai`, or install `pydantic-ai-slim` with the `mistral` optional group:

```bash
pip install 'pydantic-ai-slim[mistral]'
```

### Configuration

To use [Mistral](https://mistral.ai) through their API, go to [console.mistral.ai/api-keys/](https://console.mistral.ai/api-keys/) and follow your nose until you find the place to generate an API key.

### Environment variable

Once you have the API key, you can set it as an environment variable:

```bash
export MISTRAL_API_KEY='your-api-key'
```

You can then use `MistralModel` by name:

```python
from pydantic_ai import Agent
agent = Agent('mistral:mistral-large-latest')
```

Or initialise the model directly with just the model name:

```python
from pydantic_ai import Agent
from pydantic_ai.models.mistral import MistralModel
model = MistralModel('mistral-small-latest')
agent = Agent(model)
```

### `api_key` argument

If you don't want to or can't set the environment variable, you can pass it at runtime via the `api_key` argument:

```python
from pydantic_ai import Agent
from pydantic_ai.models.mistral import MistralModel
model = MistralModel('mistral-small-latest', api_key='your-api-key')
agent = Agent(model)
```

## Implementing Custom Models

To implement support for models not already supported, you will need to subclass the `Model` abstract base class.

This in turn will require you to implement the following other abstract base classes:

- `AgentModel`
- `StreamTextResponse`
- `StreamStructuredResponse`

The best place to start is to review the source code for existing implementations, e.g. `OpenAIModel`.

For details on when we'll accept contributions adding new models to PydanticAI, see the [contributing guidelines](../contributing/#new-model-rules).