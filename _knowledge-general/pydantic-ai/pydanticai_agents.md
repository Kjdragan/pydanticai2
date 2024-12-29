# Agents

## Introduction

Agents are PydanticAI's primary interface for interacting with LLMs.

In some use cases a single Agent will control an entire application or component, but multiple agents can also interact to embody more complex workflows.

The `Agent` class has full API documentation, but conceptually you can think of an agent as a container for:

| **Component** | **Description** |
| --- | --- |
| [System prompt(s)](#system-prompts) | A set of instructions for the LLM written by the developer. |
| [Function tool(s)](../tools/) | Functions that the LLM may call to get information while generating a response. |
| [Structured result type](../results/) | The structured datatype the LLM must return at the end of a run, if specified. |
| [Dependency type constraint](../dependencies/) | System prompt functions, tools, and result validators may all use dependencies when they're run. |
| [LLM model](../api/models/base/) | Optional default LLM model associated with the agent. Can also be specified when running the agent. |
| [Model Settings](#additional-configuration) | Optional default model settings to help fine tune requests. Can also be specified when running the agent. |

In typing terms, agents are generic in their dependency and result types, e.g., an agent which required dependencies of type `Foobar` and returned results of type `list[str]` would have type `Agent[Foobar, list[str]]`. In practice, you shouldn't need to care about this, it should just mean your IDE can tell you when you have the right type, and if you choose to use [static type checking](#static-type-checking) it should work well with PydanticAI.

Here's a toy example of an agent that simulates a roulette wheel:

```python
from pydantic_ai import Agent, RunContext

roulette_agent = Agent(
    'openai:gpt-4o',
    deps_type=int,
    result_type=bool,
    system_prompt=(
        'Use the `roulette_wheel` function to see if the '
        'customer has won based on the number they provide.'
    ),
)

@roulette_agent.tool
async def roulette_wheel(ctx: RunContext[int], square: int) -> str:
    """check if the square is a winner"""
    return 'winner' if square == ctx.deps else 'loser'

# Run the agent
success_number = 18
result = roulette_agent.run_sync('Put my money on square eighteen', deps=success_number)
print(result.data)  #> True
result = roulette_agent.run_sync('I bet five is the winner', deps=success_number)
print(result.data)  #> False
```

Agents are designed for reuse, like FastAPI Apps.

Agents are intended to be instantiated once (frequently as module globals) and reused throughout your application, similar to a small [FastAPI](https://fastapi.tiangolo.com/reference/fastapi/#fastapi.FastAPI) app or an [APIRouter](https://fastapi.tiangolo.com/reference/apirouter/#fastapi.APIRouter).

## Running Agents

There are three ways to run an agent:

1. `agent.run()` — a coroutine which returns a `RunResult` containing a completed response
2. `agent.run_sync()` — a plain, synchronous function which returns a `RunResult` containing a completed response (internally, this just calls `loop.run_until_complete(self.run())`)
3. `agent.run_stream()` — a coroutine which returns a `StreamedRunResult`, which contains methods to stream a response as an async iterable

Here's a simple example demonstrating all three:

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-4o')
result_sync = agent.run_sync('What is the capital of Italy?')
print(result_sync.data)  #> Rome

async def main():
    result = await agent.run('What is the capital of France?')
    print(result.data)  #> Paris
    async with agent.run_stream('What is the capital of the UK?') as response:
        print(await response.get_data())  #> London
```

_(This example is complete, it can be run "as is")_

You can also pass messages from previous runs to continue a conversation or provide context, as described in [Messages and Chat History](../message-history/).

### Additional Configuration

#### Usage Limits

PydanticAI offers a `settings.UsageLimits` structure to help you limit your usage (tokens and/or requests) on model runs.

You can apply these settings by passing the `usage_limits` argument to the `run{_sync,_stream}` functions.

Consider the following example, where we limit the number of response tokens:

```python
from pydantic_ai import Agent
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.settings import UsageLimits

agent = Agent('claude-3-5-sonnet-latest')
result_sync = agent.run_sync(
    'What is the capital of Italy? Answer with just the city.',
    usage_limits=UsageLimits(response_tokens_limit=10),
)
print(result_sync.data)  #> Rome
print(result_sync.usage())
# Usage(requests=1, request_tokens=62, response_tokens=1, total_tokens=63, details=None)
try:
    result_sync = agent.run_sync(
        'What is the capital of Italy? Answer with a paragraph.',
        usage_limits=UsageLimits(response_tokens_limit=10),
    )
except UsageLimitExceeded as e:
    print(e)  #> Exceeded the response_tokens_limit of 10 (response_tokens=32)
```

Restricting the number of requests can be useful in preventing infinite loops or excessive tool calling:

```python
from typing_extensions import TypedDict
from pydantic_ai import Agent, ModelRetry
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.settings import UsageLimits

class NeverResultType(TypedDict):
    """
    Never ever coerce data to this type.
    """
    never_use_this: str

agent = Agent(
    'claude-3-5-sonnet-latest',
    result_type=NeverResultType,
    system_prompt='Any time you get a response, call the `infinite_retry_tool` to produce another response.',
)

@agent.tool_plain(retries=5)
def infinite_retry_tool() -> int:
    raise ModelRetry('Please try again.')

try:
    result_sync = agent.run_sync(
        'Begin infinite retry loop!', usage_limits=UsageLimits(request_limit=3)
    )
except UsageLimitExceeded as e:
    print(e)  #> The next request would exceed the request_limit of 3
```

#### Model (Run) Settings

PydanticAI offers a `settings.ModelSettings` structure to help you fine tune your requests. This structure allows you to configure common parameters that influence the model's behavior, such as `temperature`, `max_tokens`, `timeout`, and more.

There are two ways to apply these settings: 1. Passing to `run{_sync,_stream}` functions via the `model_settings` argument. This allows for fine-tuning on a per-request basis. 2. Setting during `Agent` initialization via the `model_settings` argument. These settings will be applied by default to all subsequent run calls using said agent. However, `model_settings` provided during a specific run call will override the agent's default settings.

For example, if you'd like to set the `temperature` setting to `0.0` to ensure less random behavior, you can do the following:

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-4o')
result_sync = agent.run_sync(
    'What is the capital of Italy?', model_settings={'temperature': 0.0}
)
print(result_sync.data)  #> Rome
```

## Runs vs. Conversations

An agent **run** might represent an entire conversation — there's no limit to how many messages can be exchanged in a single run. However, a **conversation** might also be composed of multiple runs, especially if you need to maintain state between separate interactions or API calls.

Here's an example of a conversation comprised of multiple runs:

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-4o')
# First run
result1 = agent.run_sync('Who was Albert Einstein?')
print(result1.data)  #> Albert Einstein was a German-born theoretical physicist.
# Second run, passing previous messages
result2 = agent.run_sync(
    'What was his most famous equation?',
    message_history=result1.new_messages(),
)
print(result2.data)  #> Albert Einstein's most famous equation is (E = mc^2).
```

_(This example is complete, it can be run "as is")_

## Type safe by design

PydanticAI is designed to work well with static type checkers, like mypy and pyright.

Typing is (somewhat) optional.

PydanticAI is designed to make type checking as useful as possible for you if you choose to use it, but you don't have to use types everywhere all the time.

That said, because PydanticAI uses Pydantic, and Pydantic uses type hints as the definition for schema and validation, some types (specifically type hints on parameters to tools, and the `result_type` arguments to `Agent`) are used at runtime.

We (the library developers) have messed up if type hints are confusing you more than helping you, if you find this, please create an issue explaining what's annoying you!

In particular, agents are generic in both the type of their dependencies and the type of results they return, so you can use the type hints to ensure you're using the right types.

Consider the following script with type mistakes:

```python
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext

@dataclass
class User:
    name: str

agent = Agent(
    'test',
    deps_type=User,
    result_type=bool,
)

@agent.system_prompt
def add_user_name(ctx: RunContext[str]) -> str:
    return f"The user's name is {ctx.deps}."


def foobar(x: bytes) -> None:
    pass

result = agent.run_sync('Does their name start with "A"?', deps=User('Anne'))
foobar(result.data)
```

Running `mypy` on this will give the following output:

```
➤ uvrun mypy type_mistakes.py

type_mistakes.py:18:error: Argument 1 to "system_prompt" of "Agent" has incompatible type "Callable[[RunContext[str]], str]"; expected "Callable[[RunContext[User]], str]" [arg-type]
type_mistakes.py:28:error: Argument 1 to "foobar" has incompatible type "bool"; expected "bytes" [arg-type]
Found 2 errors in 1 file (checked 1 source file)
```

Running `pyright` would identify the same issues.

## System Prompts

System prompts might seem simple at first glance since they're just strings (or sequences of strings that are concatenated), but crafting the right system prompt is key to getting the model to behave as you want.

Generally, system prompts fall into two categories:

1. **Static system prompts** : These are known when writing the code and can be defined via the `system_prompt` parameter of the `Agent` constructor.
2. **Dynamic system prompts** : These depend in some way on context that isn't known until runtime, and should be defined via functions decorated with `@agent.system_prompt`.

You can add both to a single agent; they're appended in the order they're defined at runtime.

Here's an example using both types of system prompts:

```python
from datetime import date
from pydantic_ai import Agent, RunContext

agent = Agent(
    'openai:gpt-4o',
    deps_type=str,
    system_prompt="Use the customer's name while replying to them.",
)

@agent.system_prompt
def add_the_users_name(ctx: RunContext[str]) -> str:
    return f"The user's name is {ctx.deps}."

@agent.system_prompt
def add_the_date() -> str:
    return f'The date is {date.today()}.'

result = agent.run_sync('What is the date?', deps='Frank')
print(result.data)  #> Hello Frank, the date today is 2032-01-02.
```

_(This example is complete, it can be run "as is")_

## Reflection and self-correction

Validation errors from both function tool parameter validation and structured result validation can be passed back to the model with a request to retry.

You can also raise `ModelRetry` from within a tool or result validator function to tell the model it should retry generating a response.

- The default retry count is **1** but can be altered for the entire agent, a specific tool, or a result validator.
- You can access the current retry count from within a tool or result validator via `ctx.retry`.

Here's an example:

```python
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext, ModelRetry
from fake_database import DatabaseConn

class ChatResult(BaseModel):
    user_id: int
    message: str

agent = Agent(
    'openai:gpt-4o',
    deps_type=DatabaseConn,
    result_type=ChatResult,
)

@agent.tool(retries=2)
def get_user_by_name(ctx: RunContext[DatabaseConn], name: str) -> int:
    """Get a user's ID from their full name."""
    print(name)  #> John
    user_id = ctx.deps.users.get(name=name)
    if user_id is None:
        raise ModelRetry(
            f'No user found with name {name!r}, remember to provide their full name'
        )
    return user_id

result = agent.run_sync(
    'Send a message to John Doe asking for coffee next week', deps=DatabaseConn()
)
print(result.data)
# user_id=123 message='Hello John, would you be free for coffee sometime next week? Let me know what works for you!'
```

## Model errors

If models behave unexpectedly (e.g., the retry limit is exceeded, or their API returns `503`), agent runs will raise `UnexpectedModelBehavior`.

In these cases, `capture_run_messages` can be used to access the messages exchanged during the run to help diagnose the issue.

```python
from pydantic_ai import Agent, ModelRetry, UnexpectedModelBehavior, capture_run_messages

agent = Agent('openai:gpt-4o')

@agent.tool_plain
def calc_volume(size: int) -> int:
    if size == 42:
        return size**3
    else:
        raise ModelRetry('Please try again.')

with capture_run_messages() as messages:
    try:
        result = agent.run_sync('Please get me the volume of a box with size 6.')
    except UnexpectedModelBehavior as e:
        print('An error occurred:', e)
        print('cause:', repr(e.__cause__))
        print('messages:', messages)
    else:
        print(result.data)
```

_(This example is complete, it can be run "as is")_

Note: You may not call `run`, `run_sync`, or `run_stream` more than once within a single `capture_run_messages` context. If you try to do so, a `UserError` will be raised.