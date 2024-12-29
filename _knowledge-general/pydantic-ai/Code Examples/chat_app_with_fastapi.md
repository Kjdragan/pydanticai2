# Chat App with FastAPI

Simple chat app example built with FastAPI.

Demonstrates:

- [reusing chat history](../../message-history/)
- [serializing messages](../../message-history/#accessing-messages-from-results)
- [streaming responses](../../results/#streamed-results)

This demonstrates storing chat history between requests and using it to give the model context for new responses.

Most of the complex logic here is between `chat_app.py` which streams the response to the browser, and `chat_app.ts` which renders messages in the browser.

## Running the Example

With [dependencies installed and environment variables set](../#usage), run:

```
python -m pydantic_ai_examples.chat_app
```

```
uvicorn -m pydantic_ai_examples.chat_app
```

Then open the app at [localhost:8000](http://localhost:8000).

## Example Code

Python code that runs the chat app:

```python
from __future__ import annotations as _annotations
import asyncio
import json
import sqlite3
from collections.abc import AsyncIterator
from concurrent.futures.thread import ThreadPoolExecutor
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import partial
from pathlib import Path
from typing import Annotated, Any, Callable, Literal, TypeVar
import fastapi
import logfire
from fastapi import Depends, Request
from fastapi.responses import FileResponse, Response, StreamingResponse
from typing_extensions import LiteralString, ParamSpec, TypedDict
from pydantic_ai import Agent
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.messages import (
  ModelMessage,
  ModelMessagesTypeAdapter,
  ModelRequest,
  ModelResponse,
  TextPart,
  UserPromptPart,
)

logfire.configure(send_to_logfire='if-token-present')
agent = Agent('openai:gpt-4o')
THIS_DIR = Path(__file__).parent

@asynccontextmanager
async def lifespan(_app: fastapi.FastAPI):
  async with Database.connect() as db:
    yield {'db': db}

app = fastapi.FastAPI(lifespan=lifespan)
logfire.instrument_fastapi(app)

@app.get('/')
async def index() -> FileResponse:
  return FileResponse((THIS_DIR / 'chat_app.html'), media_type='text/html')

@app.get('/chat_app.ts')
async def main_ts() -> FileResponse:
  return FileResponse((THIS_DIR / 'chat_app.ts'), media_type='text/plain')

async def get_db(request: Request) -> Database:
  return request.state.db

@app.get('/chat/')
async def get_chat(database: Database = Depends(get_db)) -> Response:
  msgs = await database.get_messages()
  return Response(
    b'\n'.join(json.dumps(to_chat_message(m)).encode('utf-8') for m in msgs),
    media_type='text/plain',
  )

class ChatMessage(TypedDict):
  role: Literal['user', 'model']
  timestamp: str
  content: str

def to_chat_message(m: ModelMessage) -> ChatMessage:
  first_part = m.parts[0]
  if isinstance(m, ModelRequest):
    if isinstance(first_part, UserPromptPart):
      return {
        'role': 'user',
        'timestamp': first_part.timestamp.isoformat(),
        'content': first_part.content,
      }
  elif isinstance(m, ModelResponse):
    if isinstance(first_part, TextPart):
      return {
        'role': 'model',
        'timestamp': m.timestamp.isoformat(),
        'content': first_part.content,
      }
  raise UnexpectedModelBehavior(f'Unexpected message type for chat app: {m}')

@app.post('/chat/')
async def post_chat(
  prompt: Annotated[str, fastapi.Form()], database: Database = Depends(get_db)
) -> StreamingResponse:
  async def stream_messages():
    yield (
      json.dumps(
        {
          'role': 'user',
          'timestamp': datetime.now(tz=timezone.utc).isoformat(),
          'content': prompt,
        }
      ).encode('utf-8')
      + b'\n'
    )
    messages = await database.get_messages()
    async with agent.run_stream(prompt, message_history=messages) as result:
      async for text in result.stream(debounce_by=0.01):
        m = ModelResponse.from_text(content=text, timestamp=result.timestamp())
        yield json.dumps(to_chat_message(m)).encode('utf-8') + b'\n'
    await database.add_messages(result.new_messages_json())
  return StreamingResponse(stream_messages(), media_type='text/plain')

P = ParamSpec('P')
R = TypeVar('R')

@dataclass
class Database:
  con: sqlite3.Connection
  _loop: asyncio.AbstractEventLoop
  _executor: ThreadPoolExecutor
  @classmethod
  @asynccontextmanager
  async def connect(
    cls, file: Path = THIS_DIR / '.chat_app_messages.sqlite'
  ) -> AsyncIterator[Database]:
    loop = asyncio.get_event_loop()
    executor = ThreadPoolExecutor(max_workers=1)
    con = await loop.run_in_executor(executor, cls._connect, file)
    slf = cls(con, loop, executor)
    try:
      yield slf
    finally:
      await slf._asyncify(con.close)
  @staticmethod
  def _connect(file: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(file))
    cur = con.cursor()
    cur.execute(
      'CREATE TABLE IF NOT EXISTS messages (id INT PRIMARY KEY, message_list TEXT);'
    )
    con.commit()
    return con
  async def add_messages(self, messages: bytes):
    await self._asyncify(
      self._execute,
      'INSERT INTO messages (message_list) VALUES (?);',
      messages,
      commit=True,
    )
    await self._asyncify(self.con.commit)
  async def get_messages(self) -> list[ModelMessage]:
    c = await self._asyncify(
      self._execute, 'SELECT message_list FROM messages order by id desc'
    )
    rows = await self._asyncify(c.fetchall)
    messages: list[ModelMessage] = []
    for row in rows:
      messages.extend(ModelMessagesTypeAdapter.validate_json(row[0]))
    return messages
  def _execute(
    self, sql: LiteralString, *args: Any, commit: bool = False
  ) -> sqlite3.Cursor:
    cur = self.con.cursor()
    cur.execute(sql, args)
    if commit:
      self.con.commit()
    return cur
  async def _asyncify(
    self, func: Callable[P, R], *args: P.args, **kwargs: P.kwargs
  ) -> R:
    return await self._loop.run_in_executor(
      self._executor,
      partial(func, **kwargs),
      *args,
    )

if __name__ == '__main__':
  import uvicorn
  uvicorn.run(
    'pydantic_ai_examples.chat_app:app', reload=True, reload_dirs=[str(THIS_DIR)]
  )
```

Simple HTML page to render the app:

```html
<!DOCTYPE html>
<html lang="en">
<head>
 <meta charset="UTF-8">
 <meta name="viewport" content="width=device-width, initial-scale=1.0">
 <title>Chat App</title>
 <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
 <style>
main{
max-width:700px;
}
#conversation.user::before{
content:'You asked: ';
font-weight:bold;
display:block;
}
#conversation.model::before{
content:'AI Response: ';
font-weight:bold;
display:block;
}
#spinner{
opacity:0;
transition:opacity 500ms ease-in;
width:30px;
height:30px;
border:3px solid #222;
border-bottom-color:transparent;
border-radius:50%;
animation:rotation 1s linear infinite;
}
@keyframes rotation {
0%{transform:rotate(0deg);}
100%{transform:rotate(360deg);}
}
#spinner.active{
opacity:1;
}
</style>
</head>
<body>
 <main class="border rounded mx-auto my-5 p-4">
  <h1>Chat App</h1>
  <p>Ask me anything...</p>
  <div id="conversation" class="px-2"></div>
  <div class="d-flex justify-content-center mb-3">
   <div id="spinner"></div>
  </div>
  <form method="post">
   <input id="prompt-input" name="prompt" class="form-control"/>
   <div class="d-flex justify-content-end">
    <button class="btn btn-primary mt-2">Send</button>
   </div>
  </form>
  <div id="error" class="d-none text-danger">
   Error occurred, check the browser developer console for more information.
  </div>
 </main>
</body>
</html>
<script src="https://cdnjs.cloudflare.com/ajax/libs/typescript/5.6.3/typescript.min.js" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
<script type="module">
async function loadTs() {
const response = await fetch('/chat_app.ts');
const tsCode = await response.text();
const jsCode = window.ts.transpile(tsCode, { target: "es2015" });
let script = document.createElement('script');
script.type = 'module';
script.text = jsCode;
document.body.appendChild(script);
}
loadTs().catch((e) => {
console.error(e);
document.getElementById('error').classList.remove('d-none');
document.getElementById('spinner').classList.remove('active');
});
</script>
```

TypeScript to handle rendering the messages:

```typescript
// BIG FAT WARNING: to avoid the complexity of npm, this typescript is compiled in the browser
// there's currently no static type checking
import { marked } from 'https://cdnjs.cloudflare.com/ajax/libs/marked/15.0.0/lib/marked.esm.js';
const convElement = document.getElementById('conversation');
const promptInput = document.getElementById('prompt-input') as HTMLInputElement;
const spinner = document.getElementById('spinner');

async function onFetchResponse(response: Response): Promise<void> {
let text = '';
let decoder = new TextDecoder();
if (response.ok) {
const reader = response.body.getReader();
while (true) {
const { done, value } = await reader.read();
if (done) {
break;
}
text += decoder.decode(value);
addMessages(text);
spinner.classList.remove('active');
}
addMessages(text);
promptInput.disabled = false;
promptInput.focus();
} else {
const text = await response.text();
console.error(`Unexpected response: ${response.status}`, { response, text });
throw new Error(`Unexpected response: ${response.status}`);
}
}

interface Message {
role: string;
content: string;
timestamp: string;
}

function addMessages(responseText: string) {
const lines = responseText.split('\n');
const messages: Message[] = lines.filter(line => line.length > 1).map(j => JSON.parse(j));
for (const message of messages) {
const { timestamp, role, content } = message;
const id = `msg-${timestamp}`;
let msgDiv = document.getElementById(id);
if (!msgDiv) {
msgDiv = document.createElement('div');
msgDiv.id = id;
msgDiv.title = `${role} at ${timestamp}`;
msgDiv.classList.add('border-top', 'pt-2', role);
convElement.appendChild(msgDiv);
}
msgDiv.innerHTML = marked.parse(content);
}
window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
}

async function onSubmit(e: SubmitEvent): Promise<void> {
e.preventDefault();
spinner.classList.add('active');
const body = new FormData(e.target as HTMLFormElement);
promptInput.value = '';
promptInput.disabled = true;
const response = await fetch('/chat/', { method: 'POST', body });
await onFetchResponse(response);
}
document.querySelector('form').addEventListener('submit', (e) => onSubmit(e).catch(onError));
fetch('/chat/').then(onFetchResponse).catch(onError);
```