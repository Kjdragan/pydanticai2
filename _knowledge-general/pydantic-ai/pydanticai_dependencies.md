# Dependencies

PydanticAI uses a dependency injection system to provide data and services to your agent's [system prompts](../agents/#system-prompts), [tools](../tools/) and [result validators](../results/#result-validators-functions).

Matching PydanticAI's design philosophy, our dependency system tries to use existing best practice in Python development rather than inventing esoteric "magic", this should make dependencies type-safe, understandable easier to test and ultimately easier to deploy in production.

## Defining Dependencies

Dependencies can be any python type. While in simple cases you might be able to pass a single object as a dependency (e.g. an HTTP connection), [dataclasses](https://docs.python.org/3/library/dataclasses.html#module-dataclasses) are generally a convenient container when your dependencies included multiple objects.

Here's an example of defining an agent that requires dependencies.

```python
from dataclasses import dataclass
import httpx
from pydantic_ai import Agent

dataclass
class MyDeps:
  api_key: str
  http_client: httpx.AsyncClient

agent = Agent(
  'openai:gpt-4o',
  deps_type=MyDeps,
)

async def main():
  async with httpx.AsyncClient() as client:
    deps = MyDeps('foobar', client)
    result = await agent.run(
      'Tell me a joke.',
      deps=deps,
    )
    print(result.data)
    #> Did you hear about the toothpaste scandal? They called it Colgate.
```

_(This example is complete, it can be run "as is")_

## Accessing Dependencies

Dependencies are accessed through the `RunContext` type, this should be the first parameter of system prompt functions etc.

```python
from dataclasses import dataclass
import httpx
from pydantic_ai import Agent, RunContext

dataclass
class MyDeps:
  api_key: str
  http_client: httpx.AsyncClient

agent = Agent(
  'openai:gpt-4o',
  deps_type=MyDeps,
)

@agent.system_prompt
async def get_system_prompt(ctx: RunContext[MyDeps]) -> str:
  response = await ctx.deps.http_client.get(
    'https://example.com',
    headers={'Authorization': f'Bearer {ctx.deps.api_key}'},
  )
  response.raise_for_status()
  return f'Prompt: {response.text}'

async def main():
  async with httpx.AsyncClient() as client:
    deps = MyDeps('foobar', client)
    result = await agent.run('Tell me a joke.', deps=deps)
    print(result.data)
    #> Did you hear about the toothpaste scandal? They called it Colgate.
```

_(This example is complete, it can be run "as is")_

### Asynchronous vs. Synchronous dependencies

[System prompt functions](../agents/#system-prompts), [function tools](../tools/) and [result validators](../results/#result-validators-functions) are all run in the async context of an agent run.

If these functions are not coroutines (e.g. `async def`) they are called with `run_in_executor` in a thread pool, it's therefore marginally preferable to use `async` methods where dependencies perform IO, although synchronous dependencies should work fine too.

Whether you use synchronous or asynchronous dependencies, is completely independent of whether you use `run` or `run_sync` — `run_sync` is just a wrapper around `run` and agents are always run in an async context.

Here's the same example as above, but with a synchronous dependency:

```python
from dataclasses import dataclass
import httpx
from pydantic_ai import Agent, RunContext

dataclass
class MyDeps:
  api_key: str
  http_client: httpx.Client

agent = Agent(
  'openai:gpt-4o',
  deps_type=MyDeps,
)

@agent.system_prompt
def get_system_prompt(ctx: RunContext[MyDeps]) -> str:
  response = ctx.deps.http_client.get(
    'https://example.com', headers={'Authorization': f'Bearer {ctx.deps.api_key}'}
  )
  response.raise_for_status()
  return f'Prompt: {response.text}'

async def main():
  deps = MyDeps('foobar', httpx.Client())
  result = await agent.run(
    'Tell me a joke.',
    deps=deps,
  )
  print(result.data)
  #> Did you hear about the toothpaste scandal? They called it Colgate.
```

_(This example is complete, it can be run "as is")_

## Full Example

As well as system prompts, dependencies can be used in [tools](../tools/) and [result validators](../results/#result-validators-functions).

```python
from dataclasses import dataclass
import httpx
from pydantic_ai import Agent, ModelRetry, RunContext

dataclass
class MyDeps:
  api_key: str
  http_client: httpx.AsyncClient

agent = Agent(
  'openai:gpt-4o',
  deps_type=MyDeps,
)

@agent.system_prompt
async def get_system_prompt(ctx: RunContext[MyDeps]) -> str:
  response = await ctx.deps.http_client.get('https://example.com')
  response.raise_for_status()
  return f'Prompt: {response.text}'

@agent.tool
async def get_joke_material(ctx: RunContext[MyDeps], subject: str) -> str:
  response = await ctx.deps.http_client.get(
    'https://example.com#jokes',
    params={'subject': subject},
    headers={'Authorization': f'Bearer {ctx.deps.api_key}'},
  )
  response.raise_for_status()
  return response.text

@agent.result_validator
async def validate_result(ctx: RunContext[MyDeps], final_response: str) -> str:
  response = await ctx.deps.http_client.post(
    'https://example.com#validate',
    headers={'Authorization': f'Bearer {ctx.deps.api_key}'},
    params={'query': final_response},
  )
  if response.status_code == 400:
    raise ModelRetry(f'invalid response: {response.text}')
  response.raise_for_status()
  return final_response

async def main():
  async with httpx.AsyncClient() as client:
    deps = MyDeps('foobar', client)
    result = await agent.run('Tell me a joke.', deps=deps)
    print(result.data)
    #> Did you hear about the toothpaste scandal? They called it Colgate.
```

_(This example is complete, it can be run "as is")_

## Overriding Dependencies

When testing agents, it's useful to be able to customise dependencies.

While this can sometimes be done by calling the agent directly within unit tests, we can also override dependencies while calling application code which in turn calls the agent.

This is done via the `override` method on the agent.

```python
from dataclasses import dataclass
import httpx
from pydantic_ai import Agent, RunContext

dataclass
class MyDeps:
  api_key: str
  http_client: httpx.AsyncClient
  async def system_prompt_factory(self) -> str:
    response = await self.http_client.get('https://example.com')
    response.raise_for_status()
    return f'Prompt: {response.text}'

joke_agent = Agent('openai:gpt-4o', deps_type=MyDeps)

@joke_agent.system_prompt
async def get_system_prompt(ctx: RunContext[MyDeps]) -> str:
  return await ctx.deps.system_prompt_factory()

async def application_code(prompt: str) -> str:
  ...
  ...
  # now deep within application code we call our agent
  async with httpx.AsyncClient() as client:
    app_deps = MyDeps('foobar', client)
    result = await joke_agent.run(prompt, deps=app_deps)
  return result.data
```

```python
from joke_app import MyDeps, application_code, joke_agent

class TestMyDeps(MyDeps):
  async def system_prompt_factory(self) -> str:
    return 'test prompt'

async def test_application_code():
  test_deps = TestMyDeps('test_key', None)
  with joke_agent.override(deps=test_deps):
    joke = await application_code('Tell me a joke.')
  assert joke.startswith('Did you hear about the toothpaste scandal?')
```

## Agents as dependencies of other Agents

Since dependencies can be any python type, and agents are just python objects, agents can be dependencies of other agents.

```python
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext

dataclass
class MyDeps:
  factory_agent: Agent[None, list[str]]

joke_agent = Agent(
  'openai:gpt-4o',
  deps_type=MyDeps,
  system_prompt=(
    'Use the "joke_factory" to generate some jokes, then choose the best. '
    'You must return just a single joke.'
  ),
)
factory_agent = Agent('gemini-1.5-pro', result_type=list[str])

@joke_agent.tool
async def joke_factory(ctx: RunContext[MyDeps], count: int) -> str:
  r = await ctx.deps.factory_agent.run(f'Please generate {count} jokes.')
  return '\n'.join(r.data)

result = joke_agent.run_sync('Tell me a joke.', deps=MyDeps(factory_agent))
print(result.data)
#> Did you hear about the toothpaste scandal? They called it Colgate.
```

## Examples

The following examples demonstrate how to use dependencies in PydanticAI:

  * [Weather Agent](../examples/weather-agent/)
  * [SQL Generation](../examples/sql-gen/)
  * [RAG](../examples/rag/)