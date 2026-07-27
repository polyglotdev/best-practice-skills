"""Chapters 27-41 for best-practice-python (async, FastAPI, tooling)."""

from __future__ import annotations

from scripts.python_skill._render import Rule, write_chapter


def _r(*rules: Rule) -> list[Rule]:
  assert len(rules) >= 12
  return list(rules)


def build() -> None:
  _async()
  _fastapi()
  _tooling()


def _async() -> None:
  write_chapter(
    '27-asyncio-fundamentals.md',
    'Asyncio Fundamentals',
    """Asyncio is the concurrency model for FastAPI. Know the event loop,
`async def`, awaitables, and when not to use async at all.""",
    'Async rules are **Suggestion** under the shipped select (no `ASYNC`).',
    _r(
      Rule('Only use `async def` when the function awaits something (or is a required framework signature).', 'Async without awaits is overhead and lies.', 'Suggestion', None, """# bad\nasync def add(a: int, b: int) -> int:\n  return a + b\n\n# good\ndef add(a: int, b: int) -> int:\n  return a + b"""),
      Rule('Await every coroutine you create; do not fire-and-forget without an owned task.', 'Unawaited coroutines warn and drop work.', 'Suggestion', None, """# bad\nasync def handle():\n  send_email(user)  # forgot await\n\n# good\nasync def handle():\n  await send_email(user)"""),
      Rule('Do not call `asyncio.run` from inside a running loop.', 'Nested run breaks servers/tests.', 'Suggestion', None, """# bad  -  asyncio.run inside FastAPI handler\n# good  -  await directly"""),
      Rule('Prefer `asyncio.TaskGroup` (3.11+) over ad-hoc `gather` for sibling tasks.', 'See chapter 28.', 'Suggestion', None, """# bad  -  create_task without supervision\n# good  -  TaskGroup"""),
      Rule('Keep CPU-bound work off the loop (`asyncio.to_thread` / process pool).', 'CPU loops starve IO.', 'Suggestion', None, """# bad\nasync def handler():\n  return crunch(data)\n\n# good\nasync def handler():\n  return await asyncio.to_thread(crunch, data)"""),
      Rule('Use timeout APIs deliberately (`asyncio.timeout`).', 'Hung awaits need bounds.', 'Suggestion', None, """# bad  -  await forever\n# good\nasync with asyncio.timeout(2):\n  await upstream()"""),
      Rule('Do not mix blocking clients (`requests`) into async handlers.', 'Use httpx/async SDK or to_thread.', 'Suggestion', None, """# bad\nasync def get():\n  return requests.get(url).json()\n\n# good\nasync def get(client: httpx.AsyncClient):\n  response = await client.get(url)\n  return response.json()"""),
      Rule('Cancel scopes intentionally; do not ignore `CancelledError`/`BaseException`.', 'See chapter 29.', 'Suggestion', None, """# bad\nexcept Exception:\n  pass\n\n# good  -  let cancellation propagate"""),
      Rule('Create one shared `httpx.AsyncClient` / DB pool per app, not per request.', 'Connection storms follow per-request clients.', 'Suggestion', None, """# bad  -  AsyncClient() inside every handler\n# good  -  lifespan-managed client on app.state"""),
      Rule('Annotate async functions with the real return type, not `Coroutine[...]` at user APIs.', 'Callers await and get T.', 'Suggestion', None, """# bad\nasync def load() -> Coroutine[Any, Any, User]:\n  ...\n\n# good\nasync def load() -> User:\n  ..."""),
      Rule('Prefer async libraries end-to-end once a path is async.', 'Sync islands need explicit bridges.', 'Suggestion', None, """# bad  -  async route calling sync ORM without to_thread\n# good  -  async ORM or to_thread boundary"""),
      Rule('Write deterministic async tests with pytest-asyncio (chapter 38).', 'Real sleeps make flakes.', 'Suggestion', None, """# bad  -  time.sleep in async test\n# good  -  await asyncio.sleep(0) / fake clock"""),
    ),
  )

  write_chapter(
    '28-structured-concurrency.md',
    'Structured Concurrency',
    """`asyncio.TaskGroup` (Python 3.11+) is the default way to run sibling
tasks with proper lifetimes and error propagation.""",
    'Structured concurrency guidance is **Suggestion**.',
    _r(
      Rule('Prefer `TaskGroup` over bare `create_task` for request-scoped fan-out.', 'Owned lifetimes cancel cleanly.', 'Suggestion', None, """# bad\nasyncio.create_task(fetch_a())\nasyncio.create_task(fetch_b())\n\n# good\nasync with asyncio.TaskGroup() as group:\n  a = group.create_task(fetch_a())\n  b = group.create_task(fetch_b())"""),
      Rule('Let TaskGroup cancel siblings when one fails; do not swallow the first error.', 'Half-success states are worse.', 'Suggestion', None, """# bad  -  gather(return_exceptions=True) then ignore\n# good  -  TaskGroup default failure propagation"""),
      Rule('Do not use `asyncio.gather` with `return_exceptions=True` as a silent best-effort default.', 'Make partial failure explicit.', 'Suggestion', None, """# bad\nresults = await asyncio.gather(*tasks, return_exceptions=True)\n\n# good  -  TaskGroup or explicit per-task error policy"""),
      Rule('Keep task bodies small and named; avoid giant closures capturing mutable state.', 'Hard to debug races.', 'Suggestion', None, """# bad  -  closure mutates shared list without sync\n# good  -  return values from tasks and merge"""),
      Rule('Bound fan-out size; do not create unbounded tasks per request.', 'Task storms kill the loop.', 'Suggestion', None, """# bad  -  one task per row in unbounded query\n# good  -  chunk / semaphore"""),
      Rule('Use semaphores for concurrency limits against upstreams.', 'Respect neighbor services.', 'Suggestion', None, """# bad  -  10k concurrent upstream calls\n# good  -  asyncio.Semaphore(n)"""),
      Rule('Do not store tasks on globals without ownership.', 'Orphans outlive requests.', 'Suggestion', None, """# bad  -  module-level set of tasks\n# good  -  app.state workers managed by lifespan"""),
      Rule('Propagate request context (ids) into tasks explicitly.', 'Contextvars may need copying.', 'Suggestion', None, """# bad  -  child task loses request_id\n# good  -  pass request_id into task args"""),
      Rule('Prefer returning values from tasks over mutating shared structures.', 'Join by results.', 'Suggestion', None, """# bad  -  tasks append to shared list\n# good  -  results = [t.result() for t in tasks]"""),
      Rule('Cancel owned tasks on request timeout/cancellation.', 'Chapter 29.', 'Suggestion', None, """# bad  -  background work continues after client disconnect with no policy\n# good  -  document and enforce cancellation policy"""),
      Rule('Use `asyncio.Barrier`/`Event` sparingly; prefer dataflow via results.', 'Coordination primitives hide design issues.', 'Suggestion', None, """# bad  -  complex event choreography\n# good  -  TaskGroup results"""),
      Rule('Test failure injection: one sibling raises and others cancel.', 'Prove structure works.', 'Suggestion', None, """# bad  -  only happy-path gather tests\n# good  -  unit test TaskGroup cancellation behavior"""),
    ),
  )

  write_chapter(
    '29-cancellation-and-timeouts.md',
    'Cancellation & Timeouts',
    """Cancellation is normal in asyncio. Treat `CancelledError` as control
flow, not as a generic failure to log-and-swallow.""",
    'Cancellation guidance is **Suggestion**.',
    _r(
      Rule('Do not catch broad `Exception` around awaits without re-raising cancellation.', 'Swallowing cancel breaks shutdown.', 'Suggestion', None, """# bad\ntry:\n  await work()\nexcept Exception:\n  return None\n\n# good\ntry:\n  await work()\nexcept asyncio.CancelledError:\n  raise\nexcept ValueError:\n  return None"""),
      Rule('Use `asyncio.timeout` (3.11+) instead of `wait_for` in new code.', 'Timeout contexts compose better.', 'Suggestion', None, """# bad\nawait asyncio.wait_for(work(), timeout=2)\n\n# good\nasync with asyncio.timeout(2):\n  await work()"""),
      Rule('Keep cleanup in `finally` / async context managers so cancel still releases resources.', 'Locks and sockets must free.', 'Suggestion', None, """# bad  -  no finally around lock\n# good  -  async with lock:"""),
      Rule('Shield only the tiny critical sections that must complete; never shield whole requests.', 'Over-shielding ignores client disconnects.', 'Suggestion', None, """# bad  -  await asyncio.shield(entire_handler())\n# good  -  shield only commit()"""),
      Rule('Document timeout budgets end-to-end (client, gateway, handler, upstream).', 'Nested 30s timeouts become minutes.', 'Suggestion', None, """# bad  -  every layer waits 30s\n# good  -  budgeted deadlines"""),
      Rule('On timeout, fail clearly to clients (504/408) with correlation ids.', 'Silent hangs are worst.', 'Suggestion', None, """# bad  -  request hangs until worker recycle\n# good  -  timeout -> HTTP 504"""),
      Rule('Do not replace cancellation with infinite retries.', 'Retries need budgets/jitter.', 'Suggestion', None, """# bad  -  while True: await call()\n# good  -  bounded retry with timeout"""),
      Rule('Ensure ORM transactions do not stay open across long awaits without a strategy.', 'Idle-in-transaction kills pools.', 'Suggestion', None, """# bad  -  await external HTTP inside open transaction\n# good  -  commit/close before slow IO"""),
      Rule('Test cancellation paths, not only happy paths.', 'Most production bugs are shutdown bugs.', 'Suggestion', None, """# bad  -  no cancel tests\n# good  -  cancel task mid-await and assert cleanup"""),
      Rule('Prefer cooperative checkpoints in long CPU loops (`await asyncio.sleep(0)`).', 'Otherwise cancel cannot land.', 'Suggestion', None, """# bad  -  tight CPU loop in async def\n# good  -  to_thread or periodic await sleep(0)"""),
      Rule('Do not log CancelledError as error at request boundaries unless unexpected.', 'Noise trains people to ignore logs.', 'Suggestion', None, """# bad  -  logger.exception on every disconnect cancel\n# good  -  debug/info or silent propagate"""),
      Rule('When using TaskGroup, understand that one failure cancels peers  -  design idempotency accordingly.', 'Partial side effects need compensation.', 'Suggestion', None, """# bad  -  non-idempotent side effects in siblings\n# good  -  idempotent ops / outbox"""),
    ),
  )

  write_chapter(
    '30-async-context-and-iteration.md',
    'Async Context Managers & Iteration',
    """`async with` and `async for` are the resource and streaming primitives
for asyncio code.""",
    'Async context/iteration guidance is **Suggestion**.',
    _r(
      Rule('Use `async with` for async resources (DB sessions, HTTP clients, locks).', 'Manual close races cancel.', 'Suggestion', None, """# bad\nsession = await open_session()\n...\nawait session.close()\n\n# good\nasync with open_session() as session:\n  ..."""),
      Rule('Implement `__aenter__`/`__aexit__` or `@asynccontextmanager` for custom resources.', 'Sync context managers are not enough.', 'Suggestion', None, """# bad  -  sync __enter__ around async client\n# good  -  @asynccontextmanager async def client():"""),
      Rule('Use FastAPI lifespan (`asynccontextmanager`) for app startup/shutdown.', 'Deprecated `@app.on_event` is legacy.', 'Suggestion', None, """# bad\n@app.on_event('startup')\nasync def start():\n  ...\n\n# good  -  lifespan context manager"""),
      Rule('Prefer `async for` when iterating async streams / cursors.', 'Materializing loses streaming benefits.', 'Suggestion', None, """# bad\nrows = [row async for row in cursor]\n\n# good\nasync for row in cursor:\n  await handle(row)"""),
      Rule('Do not hold app-global async generators open across requests.', 'Generators carry connection state.', 'Suggestion', None, """# bad  -  module-level async gen reused\n# good  -  per-request iteration"""),
      Rule('Close async generators with `aclose()` when abandoning early.', 'Otherwise cleanup stalls.', 'Suggestion', None, """# bad  -  break out and drop gen\n# good  -  aclose in finally"""),
      Rule('Keep async context manager enter/exit fast; do heavy work in explicit methods.', 'Enter should not hide latency.', 'Suggestion', None, """# bad  -  __aenter__ downloads 100MB\n# good  -  async with client; await client.download()"""),
      Rule('Nest async with carefully; prefer AsyncExitStack for dynamic sets.', 'Variable depth needs a stack.', 'Suggestion', None, """# bad  -  manually nested N clients\n# good  -  AsyncExitStack"""),
      Rule('Do not mix sync `with` around blocking close methods on the event loop thread.', 'Use async close or to_thread.', 'Suggestion', None, """# bad  -  with blocking_lock inside async def\n# good  -  asyncio.Lock"""),
      Rule('Annotate async iterators as `AsyncIterator[T]`.', 'Types document streaming contracts.', 'Suggestion', None, """# bad\nasync def stream(events):\n  ...\n\n# good\nasync def stream(events: AsyncIterable[Event]) -> AsyncIterator[Event]:\n  async for event in events:\n    yield event"""),
      Rule('For SSE/streaming responses, ensure cancellation closes upstream iterators.', 'Client disconnect must free servers.', 'Suggestion', None, """# bad  -  ignore disconnect\n# good  -  finally/aclose on disconnect"""),
      Rule('Test lifespan startup failure (DB down) fails fast.', 'Half-booted apps are dangerous.', 'Suggestion', None, """# bad  -  swallow startup errors\n# good  -  let lifespan raise"""),
    ),
  )

  write_chapter(
    '31-blocking-call-trap.md',
    'The Blocking-Call Trap',
    """The most common FastAPI performance bug: calling blocking IO or CPU
work directly inside `async def` handlers, stalling the event loop.
Normative treatment is the
[Async Routes](https://github.com/zhanymkanov/fastapi-best-practices#async-routes)
section of fastapi-best-practices: async routes must stay non-blocking;
sync routes run in a threadpool; CPU work needs processes/queues.""",
    'Blocking-call guidance is **Suggestion** (enable `ASYNC` later to catch more).',
    _r(
      Rule('Never call blocking IO in `async def` without a bridge.', 'One slow `time.sleep` stalls all requests on the worker.', 'Suggestion', None, """# bad\nasync def handle():\n  time.sleep(1)\n\n# good\nasync def handle():\n  await asyncio.sleep(1)"""),
      Rule('Wrap known-blocking stdlib calls with `asyncio.to_thread`.', 'Files, subprocess, zipfile often block.', 'Suggestion', None, """# bad\nasync def read():\n  return Path('x').read_text()\n\n# good\nasync def read():\n  return await asyncio.to_thread(Path('x').read_text)"""),
      Rule('Do not use sync `requests` in async routes; use `httpx.AsyncClient`.', 'requests blocks.', 'Suggestion', None, """# bad\nrequests.get(url)\n\n# good\nawait client.get(url)"""),
      Rule('Watch ORMs: sync SQLAlchemy in async routes needs `to_thread` or migrate to async Session.', 'DB drivers are classic stalls.', 'Suggestion', None, """# bad  -  session.execute in async def\n# good  -  AsyncSession or to_thread"""),
      Rule('Profile with blocking detectors in staging (`blockbuster`, custom middlewares).', 'Guessing is insufficient.', 'Suggestion', None, """# bad  -  assume nothing blocks\n# good  -  enable a blocker detector in staging"""),
      Rule('Keep CPU-bound cryptography/image work off the loop.', 'Use to_thread/process pool.', 'Suggestion', None, """# bad  -  PIL process in async handler\n# good  -  await asyncio.to_thread(process, image)"""),
      Rule('Avoid sync locks (`threading.Lock`) inside async code; use `asyncio.Lock`.', 'Sync locks block the loop thread.', 'Suggestion', None, """# bad\nlock = threading.Lock()\nasync def handle():\n  with lock:\n    ...\n\n# good\nlock = asyncio.Lock()\nasync def handle():\n  async with lock:\n    ..."""),
      Rule('Treat `run_until_complete` / nested loops as a smell in libraries.', 'Callers own the loop.', 'Suggestion', None, """# bad  -  library calls asyncio.run\n# good  -  expose async API; let app await"""),
      Rule('Document sync parts of hybrid codebases clearly.', 'Surprises cause stalls.', 'Suggestion', None, """# bad  -  async facade over sync-only client undocumented\n# good  -  docstring: blocking; use to_thread"""),
      Rule('Prefer async SDKs when available rather than wrapping everything.', 'Wrappers still occupy threads.', 'Suggestion', None, """# bad  -  to_thread every AWS call forever\n# good  -  aiobotocore/async SDK where viable"""),
      Rule('Load-test event-loop lag, not only RPS.', 'Healthy RPS can hide 95p stalls.', 'Suggestion', None, """# bad  -  only measure throughput\n# good  -  track event loop delay metrics"""),
      Rule('In reviews, treat new sync IO in `async def` as a defect until proven bridged.', 'Default deny.', 'Suggestion', None, """# bad  -  'we'll optimize later'\n# good  -  bridge or make sync def route deliberately"""),
    ),
  )


def _fastapi() -> None:
  write_chapter(
    '32-fastapi-app-structure.md',
    'FastAPI App Structure',
    """Structure FastAPI apps for testability and scale. The normative FastAPI
architecture source for this skill is
[zhanymkanov/fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices)
(domain packages under `src/`, thin routers, service layer, Pydantic schemas
separate from DB models). Pair that with an app factory, lifespan-managed
resources, and the house Ruff style (2-space indent, single quotes).""",
    'Structure guidance is **Suggestion**.',
    _r(
      Rule('Organize by domain package under `src/`, not by file type across the whole app.', 'Layer-by-type trees (all routers/, all models/) do not scale; each domain owns router/schemas/models/service/dependencies.', 'Suggestion', None, """# bad - global routers/, models/, crud/ piles\n# good - src/orders/{router,schemas,models,service,dependencies}.py"""),
      Rule('Keep `router.py` thin: HTTP in, call `service.py`, return schema out.', 'SQL and business rules in routes resists testing and reuse.', 'Suggestion', None, """# bad\n@router.post('/orders')\nasync def create(order: OrderCreate, db: Session):\n  db.add(Order(**order.model_dump()))\n  db.commit()\n\n# good\n@router.post('/orders', response_model=OrderResponse)\nasync def create_order(\n  order: OrderCreate,\n  service: Annotated[OrderService, Depends(get_order_service)],\n) -> OrderResponse:\n  return await service.create(order)"""),
      Rule('Separate Pydantic schemas from DB models (`schemas.py` vs `models.py`).', 'Transport and persistence change for different reasons.', 'Suggestion', None, """# bad - ORM entity used as request body\n# good - OrderCreate / OrderResponse in schemas.py; Order in models.py"""),
      Rule('Put domain exceptions in `exceptions.py` and map them at the app edge.', 'HTTP status codes do not belong in repositories.', 'Suggestion', None, """# bad - HTTPException inside service SQL helper\n# good - OrderNotFoundError in exceptions.py; handler maps to 404"""),
      Rule('Expose an app factory or a thin `src/main.py` that includes domain routers explicitly.', 'Import side-effect registration hides the graph.', 'Suggestion', None, """# bad\nimport src.orders.router  # magic registration\n\n# good\ndef create_app() -> FastAPI:\n  app = FastAPI(lifespan=lifespan)\n  app.include_router(orders.router)\n  return app"""),
      Rule('Use `APIRouter(prefix=..., tags=[...])` per domain package.', 'OpenAPI stays navigable.', 'Suggestion', None, """# bad - prefix duplicated on every decorator\n# good\nrouter = APIRouter(prefix='/orders', tags=['orders'])"""),
      Rule('Prefer lifespan over deprecated startup/shutdown events.', 'One async context owns pools and clients.', 'Suggestion', None, """# bad\n@app.on_event('startup')\nasync def start() -> None:\n  ...\n\n# good - @asynccontextmanager lifespan attached to FastAPI()"""),
      Rule('Import cross-domain collaborators with explicit module aliases.', 'Matches the fastapi-best-practices import style and avoids name clashes.', 'Suggestion', None, """# bad\nfrom src.auth.constants import ErrorCode\nfrom src.posts.constants import ErrorCode  # clash\n\n# good\nfrom src.auth import constants as auth_constants\nfrom src.posts.constants import ErrorCode as PostsErrorCode"""),
      Rule('Follow REST for public HTTP shapes; keep RPC-style only behind clear non-REST paths.', 'Consistent resources beat verb-in-path chaos.', 'Suggestion', None, """# bad - POST /createOrder /getOrder\n# good - POST /orders , GET /orders/{order_id}"""),
      Rule('Wire global config in `src/config.py`; keep domain `config.py` for domain-only settings.', 'Decouple BaseSettings per the FastAPI guide.', 'Suggestion', None, """# bad - os.getenv sprinkled in routers\n# good - Settings in src/config.py; domain overrides in src/orders/config.py"""),
      Rule('Mirror domain packages under `tests/` (`tests/orders/...`).', 'Tests navigate the same way as production code.', 'Suggestion', None, """# bad - tests/test_all_routes.py god file\n# good - tests/orders/test_create_order.py"""),
      Rule('Document local run with `uv run uvicorn src.main:app` without starting servers from agent sessions.', 'Checks and tests only in automation.', 'Suggestion', None, """# bad - python nested server in scripts during CI/agent runs\n# good - uv run pytest && uv run ruff check ."""),
    ),
  )

  write_chapter(
    '33-fastapi-dependency-injection.md',
    'FastAPI Dependency Injection',
    """Dependencies are FastAPI's DI system and, per
[fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices),
also the place for request validation that needs the DB or other services.
Prefer `Annotated[T, Depends(...)]`, chain small deps, prefer `async`
dependencies, and rely on per-request caching of dependency results.""",
    'DI guidance is **Suggestion**.',
    _r(
      Rule('Use `Annotated` for dependencies and path/query/body params.', 'Keeps defaults from colliding with Depends.', 'Suggestion', None, """# bad\nasync def get(user: User = Depends(get_user)):\n  ...\n\n# good\nasync def get(user: Annotated[User, Depends(get_user)]):\n  ..."""),
      Rule('Depend on Protocols/interfaces, not concrete infrastructure types, at service boundaries.', 'Tests swap fakes.', 'Suggestion', None, """# bad  -  Depends(SqlAlchemyOrderRepo)\n# good  -  Depends(get_orders_repo) -> OrdersRepo protocol"""),
      Rule('Use `dependency_overrides` in tests rather than patching internals.', 'Official escape hatch.', 'Suggestion', None, """# bad  -  monkeypatch private imports\n# good  -  app.dependency_overrides[get_repo] = fake"""),
      Rule('Keep dependencies small and reusable; avoid hidden mega-dependencies.', 'A Depends that does five things is middleware.', 'Suggestion', None, """# bad  -  get_context loads user+flags+db+redis+audit\n# good  -  split dependencies"""),
      Rule('Yield dependencies for resources that need teardown (sessions).', 'Ensures close even on errors.', 'Suggestion', None, """# bad  -  request-scoped session never closed\n# good\ndef get_session():\n  session = Session()\n  try:\n    yield session\n  finally:\n    session.close()"""),
      Rule('Do not perform authorization only inside nested helpers; put `require_permission` in the signature.', 'Visible security beats hidden checks.', 'Suggestion', None, """# bad  -  check buried in service\n# good  -  user: Annotated[User, Depends(require_permission(...))]"""),
      Rule('Cache expensive pure deps with `lru_cache` only when settings-safe.', 'Do not cache request-scoped state.', 'Suggestion', None, """# bad  -  lru_cache on get_current_user\n# good  -  lru_cache on get_settings"""),
      Rule('Prefer shared deps modules (`deps.py`) per package over circular imports across routers.', 'Import cycles follow messy deps.', 'Suggestion', None, """# bad  -  routers import each other's deps\n# good  -  package deps.py"""),
      Rule('Keep side-effecting deps obvious (names like `require_`, `get_db`).', 'Readers scan signatures for security/IO.', 'Suggestion', None, """# bad  -  Depends(load)\n# good  -  Depends(require_admin)"""),
      Rule('Avoid Depends on concrete FastAPI Request unless necessary.', 'Couples logic to transport.', 'Suggestion', None, """# bad  -  every service takes Request\n# good  -  extract headers in deps; pass values"""),
      Rule('For multi-tenant apps, resolve tenant in a dependency and thread it explicitly.', 'Globals will leak across awaits.', 'Suggestion', None, """# bad  -  global context tenant\n# good  -  tenant: Annotated[Tenant, Depends(get_tenant)]"""),
      Rule('Document override points for tests in README/dev docs.', 'Unknown seams slow everyone.', 'Suggestion', None, """# bad  -  tribal knowledge overrides\n# good  -  list overridable deps"""),
    ),
  )

  write_chapter(
    '34-fastapi-request-response-models.md',
    'Request & Response Models',
    """Pydantic v2 models define the HTTP contract. The FastAPI guide's
[Pydantic](https://github.com/zhanymkanov/fastapi-best-practices#pydantic)
section is normative here: use Pydantic heavily, prefer a custom base model
when you need shared serialization rules, and keep schemas out of ORM
entities.""",
    'Model guidance is **Suggestion**.',
    _r(
      Rule('Declare `response_model` (or return annotated models) for every public route.', 'OpenAPI and filtering depend on it.', 'Suggestion', None, """# bad\n@router.get('/orders/{order_id}')\nasync def get_order(...):\n  return orm_order\n\n# good\n@router.get('/orders/{order_id}', response_model=OrderResponse)\nasync def get_order(...) -> OrderResponse:\n  ..."""),
      Rule('Never return SQLAlchemy/ORM entities directly.', 'Lazy loads and private fields leak.', 'Suggestion', None, """# bad  -  return User ORM\n# good  -  UserResponse.model_validate(user)"""),
      Rule('Separate create/update/response models when fields differ.', 'One mega-model invites mass-assignment bugs.', 'Suggestion', None, """# bad  -  same model for input/output with id/password\n# good  -  UserCreate / UserUpdate / UserResponse"""),
      Rule("Use `model_config = ConfigDict(extra='forbid')` for request bodies you control.", 'Unknown fields should fail fast.', 'Suggestion', None, """# bad - silently ignore unknown fields\n# good - extra='forbid' on request models"""),
      Rule('Prefer field constraints (`Field(ge=0)`) over ad-hoc validation in routes.', 'Keep invariants in the model.', 'Suggestion', None, """# bad  -  if qty < 0 in route\n# good  -  qty: int = Field(ge=0)"""),
      Rule('Use `EmailStr` / constrained types for common formats.', 'Do not regex casually.', 'Suggestion', None, """# bad  -  email: str\n# good  -  email: EmailStr"""),
      Rule('Alias wire names intentionally (`alias` / `serialization_alias`) rather than renaming ad hoc in routes.', 'Keep one mapping place.', 'Suggestion', None, """# bad  -  payload['userId'] mapped manually\n# good  -  Field(validation_alias='userId')"""),
      Rule('Keep response models stable; add fields carefully and avoid renames without versioning.', 'Clients break quietly.', 'Suggestion', None, """# bad  -  rename fields casually\n# good  -  additive changes / versioning"""),
      Rule('Do not put methods with IO on response models.', 'Models are data.', 'Suggestion', None, """# bad  -  response.model.save()\n# good  -  service.save()"""),
      Rule('Use `TypedDict` only for internal shaping; external HTTP uses BaseModel.', 'BaseModel gives validation/OpenAPI.', 'Suggestion', None, """# bad  -  TypedDict as response_model\n# good  -  BaseModel response"""),
      Rule('Prefer explicit status codes with `status_code=` / `Response` when not 200/201 defaults.', 'Be intentional.', 'Suggestion', None, """# bad  -  create returns 200 by accident\n# good  -  status_code=201"""),
      Rule('Document examples sparingly via `json_schema_extra` when they help clients.', 'Do not invent fantasy payloads.', 'Suggestion', None, """# bad  -  misleading examples\n# good  -  realistic examples"""),
    ),
  )

  write_chapter(
    '35-pydantic-validation-and-settings.md',
    'Pydantic Validation & Settings',
    """Pydantic v2 validation and `pydantic-settings` are the configuration
and boundary-validation stack. Follow
[Decouple Pydantic BaseSettings](https://github.com/zhanymkanov/fastapi-best-practices#decouple-pydantic-basesettings):
global settings in `src/config.py`, domain settings beside the domain.""",
    'Validation/settings guidance is **Suggestion**.',
    _r(
      Rule('Use `pydantic_settings.BaseSettings` for configuration, not scattered `os.environ`.', 'One typed object beats stringly config.', 'Suggestion', None, """# bad\nDEBUG = os.getenv('DEBUG') == 'true'\n\n# good\nclass Settings(BaseSettings):\n  debug: bool = False\n  model_config = SettingsConfigDict(env_file='.env')"""),
      Rule('Prefer immutable settings (`frozen=True`) loaded once.', 'Mutable global settings race.', 'Suggestion', None, """# bad  -  mutate settings mid-request\n# good  -  frozen Settings dependency"""),
      Rule('Use `@field_validator` / `@model_validator` for cross-field rules.', 'Keep them pure and fast.', 'Suggestion', None, """# bad  -  validate in route after parse\n# good  -  model_validator(mode='after')"""),
      Rule('Do not call networks inside validators.', 'Validators run often and surprisingly.', 'Suggestion', None, """# bad  -  validator hits DNS/HTTP\n# good  -  validate shape; resolve remotely in service"""),
      Rule('Use `SecretStr` for secrets in settings/models.', 'Prevents accidental log/repr leaks.', 'Suggestion', None, """# bad\napi_key: str\n\n# good\napi_key: SecretStr"""),
      Rule('Prefer `ValidationError` details at boundaries; translate to problem+json for clients.', 'Chapter 36.', 'Suggestion', None, """# bad  -  str(err) dump\n# good  -  structured 422"""),
      Rule('Pin pydantic v2 APIs (`model_validate`, `model_dump`)  -  do not use v1 `.parse_obj` / `.dict`.', 'v1 methods are legacy.', 'Suggestion', None, """# bad\nUser.parse_obj(data)\n\n# good\nUser.model_validate(data)"""),
      Rule('Keep settings env names explicit when clarity needs it (`validation_alias`).', 'Silent env mismatches waste hours.', 'Suggestion', None, """# bad  -  unclear env key\n# good  -  Field(validation_alias='ORDERS_DB_URL')"""),
      Rule('Provide safe defaults only when they are safe in production.', 'Default open CORS is not safe.', 'Suggestion', None, """# bad  -  allow_origins=['*'] default in prod settings\n# good  -  fail if unset in prod profile"""),
      Rule('Test settings loading with env overrides in unit tests.', 'Config bugs are prod bugs.', 'Suggestion', None, """# bad  -  only test happy defaults\n# good  -  monkeyset env and validate"""),
      Rule('Avoid catching `ValidationError` and rebuilding ad-hoc dicts; fix the model.', 'Translation layers drift.', 'Suggestion', None, """# bad  -  manually revalidate dict\n# good  -  tighten Field constraints"""),
      Rule('Keep domain invariants in domain types; keep transport constraints in schemas.', 'Do not double-encode poorly.', 'Suggestion', None, """# bad  -  same regex in 4 models\n# good  -  shared annotated types"""),
    ),
  )

  write_chapter(
    '36-fastapi-error-handling.md',
    'FastAPI Error Handling',
    """Map domain errors to HTTP at the edge. Prefer consistent error
payloads over ad-hoc `HTTPException` strings everywhere.""",
    'Error-handling guidance is **Suggestion**.',
    _r(
      Rule('Raise domain exceptions in services/repos; convert in exception handlers.', 'HTTP concerns stay at the edge.', 'Suggestion', None, """# bad  -  HTTPException in repository\n# good  -  OrderNotFoundError -> 404 handler"""),
      Rule('Use `HTTPException` for transport-level failures when no domain type exists.', 'Do not invent 20 wrappers for one-offs.', 'Suggestion', None, """# bad  -  DomainHttpError soup\n# good  -  HTTPException(status_code=400, detail='...') for simple cases"""),
      Rule('Return stable error shapes (problem+json or a single ErrorResponse model).', 'Clients parse one schema.', 'Suggestion', None, """# bad  -  sometimes str, sometimes dict\n# good  -  ErrorResponse everywhere"""),
      Rule('Do not leak internal exception messages to clients.', 'Log internally; return safe detail.', 'Suggestion', None, """# bad  -  detail=str(err)\n# good  -  detail='order not found'; log exception"""),
      Rule('Preserve 422 validation errors from FastAPI/Pydantic; do not replace with opaque 400s without cause.', 'Field errors help clients.', 'Suggestion', None, """# bad  -  catch ValidationError -> 400 blank\n# good  -  default 422 or shaped translation"""),
      Rule('Log 5xx with stack traces; log 4xx at info/warning without stacks by default.', 'Noise vs signal.', 'Suggestion', None, """# bad  -  exception stack on every 404\n# good  -  info for 404, exception for 500"""),
      Rule('Map auth failures to 401/403 correctly; do not use 404 to hide existence unless that is a deliberate anti-enumeration policy.', 'Be consistent.', 'Suggestion', None, """# bad  -  random status codes\n# good  -  documented auth error policy"""),
      Rule('Include correlation/request ids in error responses when you have them.', 'Support needs handles.', 'Suggestion', None, """# bad  -  uncorrelated errors\n# good  -  error.request_id"""),
      Rule('Write handlers for your top domain errors; avoid one mega handler for Exception that returns 400.', 'Catch-all 400 hides outages.', 'Suggestion', None, """# bad  -  except Exception: 400\n# good  -  specific handlers + 500 fallback"""),
      Rule('Do not use assertions for request validation.', 'Use Pydantic / HTTPException.', 'Suggestion', None, """# bad  -  assert body.n > 0\n# good  -  Field(gt=0)"""),
      Rule('Ensure background tasks have their own error logging; failures will not reach the client.', 'Chapter 37.', 'Suggestion', None, """# bad  -  assume client sees background failure\n# good  -  log/metrics in task"""),
      Rule('Add tests for each mapped domain error status code.', 'Prevent regressions in handlers.', 'Suggestion', None, """# bad  -  no tests for 404 mapping\n# good  -  assert response.status_code == 404"""),
    ),
  )

  write_chapter(
    '37-fastapi-background-tasks.md',
    'Background Tasks',
    """FastAPI `BackgroundTasks` are for short after-response work on the
same worker. Per
[BackgroundTasks vs a real task queue](https://github.com/zhanymkanov/fastapi-best-practices#backgroundtasks-vs-a-real-task-queue),
they are not durable job infrastructure.""",
    'Background-task guidance is **Suggestion**.',
    _r(
      Rule('Use BackgroundTasks for short, reliable, in-process work only.', 'Email to a flaky SMTP may need a queue.', 'Suggestion', None, """# bad  -  video encoding in BackgroundTasks\n# good  -  enqueue to worker"""),
      Rule('Do not pass ORM attached instances into background tasks.', 'Sessions close before tasks run.', 'Suggestion', None, """# bad  -  tasks.add_task(send, user_orm)\n# good  -  tasks.add_task(send, user_id)"""),
      Rule('Prefer explicit job queues (RQ/Celery/Arq/NATS) for retries and durability.', 'Process death drops BackgroundTasks.', 'Suggestion', None, """# bad  -  payment capture in BackgroundTasks\n# good  -  durable outbox/queue"""),
      Rule('Log start/finish/failure inside background callables.', 'Otherwise silent loss.', 'Suggestion', None, """# bad  -  task without logging\n# good  -  try/except logger.exception"""),
      Rule('Keep task functions sync or async deliberately; know FastAPI scheduling rules.', 'Blocking tasks stall workers.', 'Suggestion', None, """# bad  -  blocking heavy work in sync background task\n# good  -  queue or async+to_thread"""),
      Rule('Do not rely on BackgroundTasks for work that must complete before responding.', 'It runs after the response.', 'Suggestion', None, """# bad  -  audit write needed for compliance after response with no durability\n# good  -  await audit or durable outbox"""),
      Rule('Pass settings/deps explicitly into tasks; do not assume request-scoped context remains.', 'Contextvars may be gone.', 'Suggestion', None, """# bad  -  task reads request contextvar\n# good  -  pass request_id arg"""),
      Rule('Bound fan-out of tasks per request.', 'Easy DoS against yourself.', 'Suggestion', None, """# bad  -  1000 background tasks per request\n# good  -  one enqueue batch job"""),
      Rule('Document the durability story for each background call site.', 'Reviewers need to know loss tolerance.', 'Suggestion', None, """# bad  -  unexplained add_task\n# good  -  comment: best-effort metrics only"""),
      Rule('Test background work by invoking the callable directly; do not only assert 200.', 'Response success != task success.', 'Suggestion', None, """# bad  -  only assert status 200\n# good  -  assert task side effect / call args"""),
      Rule('Avoid capturing `Request` in tasks.', 'Lifecycle ends.', 'Suggestion', None, """# bad  -  add_task(fn, request)\n# good  -  extract needed values first"""),
      Rule('Consider `after_response` patterns via ASGI middleware carefully; prefer obvious BackgroundTasks or queues.', 'Cleverness ages poorly.', 'Suggestion', None, """# bad  -  hidden middleware side effects\n# good  -  explicit tasks/queue"""),
    ),
  )

  write_chapter(
    '38-fastapi-testing.md',
    'FastAPI Testing',
    """Test FastAPI with httpx ASGI transport / `AsyncClient` from day zero
([fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices#set-tests-client-async-from-day-0)),
plus dependency overrides and deterministic fakes.""",
    'FastAPI testing guidance is **Suggestion**.',
    _r(
      Rule('Prefer app-factory + fresh app per test module when overrides are needed.', 'Shared global app state leaks.', 'Suggestion', None, """# bad  -  mutate global app in tests\n# good  -  create_app() per test"""),
      Rule('Use `dependency_overrides` for DB/auth/clock seams.', 'Patching internals is brittle.', 'Suggestion', None, """# bad  -  mock.patch path strings\n# good  -  app.dependency_overrides[get_db] = fake_db"""),
      Rule('Use `httpx.AsyncClient(transport=ASGITransport(app=app))` for async tests.', 'Real network optional.', 'Suggestion', None, """# bad  -  live server required for unit tests\n# good  -  ASGI transport in-process"""),
      Rule('Clear `dependency_overrides` after tests.', 'Order-dependent suites follow.', 'Suggestion', None, """# bad  -  leave overrides set\n# good  -  fixture finalizer clears"""),
      Rule('Assert status code and payload shape; do not only assert 200.', 'Wrong body still 200s.', 'Suggestion', None, """# bad\nassert response.status_code == 200\n\n# good\nassert response.status_code == 200\nassert response.json()['id'] == order_id"""),
      Rule('Test authz negative cases (401/403) for every protected route class.', 'Happy path is not security.', 'Suggestion', None, """# bad  -  only authorized tests\n# good  -  anonymous/forbidden cases"""),
      Rule('Keep DB integration tests transactional/isolated.', 'Shared DB state flakes.', 'Suggestion', None, """# bad  -  leftover rows\n# good  -  transaction rollback fixture"""),
      Rule('Do not start uvicorn in tests.', 'In-process ASGI is enough.', 'Suggestion', None, """# bad  -  subprocess uvicorn\n# good  -  TestClient/AsyncClient"""),
      Rule('Freeze time for expiring tokens/signatures.', 'Sleep-based tests flake.', 'Suggestion', None, """# bad  -  sleep until expiry\n# good  -  clock dependency override"""),
      Rule('Contract-test OpenAPI for intentional breaks when external clients exist.', 'Silent schema drift hurts.', 'Suggestion', None, """# bad  -  ignore schema diffs\n# good  -  snapshot or schemathesis selectively"""),
      Rule('Prefer factory helpers for JSON payloads over giant literals everywhere.', 'Literals rot.', 'Suggestion', None, """# bad  -  40-line JSON dict duplicated\n# good  -  make_order_payload(**overrides)"""),
      Rule('Run unit tests by default; mark and separate e2e.', 'Default suite must be fast.', 'Suggestion', None, """# bad  -  e2e in unmarked default\n# good  -  -m 'not e2e' default"""),
    ),
  )


def _tooling() -> None:
  write_chapter(
    '39-ruff-configuration.md',
    'Ruff Configuration',
    """This skill ships `ruff.toml` at the repo root. Formatting is delegated
to `ruff format`; lint uses the minimal enabled set `E4`/`E7`/`E9`/`F`.
Expanding `select` is a deliberate product decision because it will surface
findings in existing code.""",
    'Config rules that restate the shipped file are **Violation** where they '
    'map to enabled checks; expansion guidance is **Suggestion**.',
    _r(
      Rule('Keep `target-version = \'py312\'` aligned with the language floor.', 'A 3.11 target disables 3.12-aware fixes.', 'Suggestion', None, """# bad\ntarget-version = 'py311'\n\n# good\ntarget-version = 'py312'"""),
      Rule('Keep `indent-width = 2` and `quote-style = \'single\'` as house law.', 'Do not locally reintroduce 4-space/double-quote Python.', 'Violation', 'ruff format', """# bad  -  editor inserts 4 spaces\n# good  -  editorconfig + ruff format"""),
      Rule('Do not claim a Ruff rule is enforced unless it is in the effective select set.', 'Reconciliation rule from the handoff.', 'Suggestion', None, """# bad  -  Enforced by: D100 when D is not selected\n# good  -  Suggestion until select expands"""),
      Rule('Run `ruff format` and `ruff check` in CI.', 'Format drift is a CI failure.', 'Violation', 'ruff format', """# bad  -  format only on laptops\n# good  -  CI runs both"""),
      Rule('Prefer scoped `# noqa: CODE` with reasons; ban file-wide ignores without review.', 'Unscoped noqa grows forever.', 'Suggestion', None, """# bad\n# ruff: noqa\n\n# good\nimport x  # noqa: F401  # re-export"""),
      Rule('When expanding select, add families deliberately (`I`, `UP`, `B`, `ASYNC`, `PT`).', 'Big-bang enablements stall teams.', 'Suggestion', None, """# bad  -  select = ['ALL'] overnight\n# good  -  phased enablement"""),
      Rule('Keep exclude lists for virtualenvs/build dirs; do not exclude `src`/`tests`.', 'Excluding tests hides violations.', 'Suggestion', None, """# bad  -  exclude = ['tests']\n# good  -  exclude only caches/build"""),
      Rule('Treat `.mypy_cache` (correct spelling) as excluded; never `.mymy_cache`.', 'Typo creates useless exclude noise.', 'Suggestion', None, """# bad\n'.mymy_cache'\n\n# good\n'.mypy_cache'"""),
      Rule('Pin Ruff in project tooling (`uv add --dev ruff`) and invoke via `uv run`.', 'Global Ruff drifts (local 0.9 vs latest 0.16).', 'Suggestion', None, """# bad  -  random global ruff\n# good  -  uv run ruff check ."""),
      Rule('Do not enable detekt-style semantic families in prose without enabling them in config.', 'Honesty over aspirational badges.', 'Suggestion', None, """# bad  -  claim ASYNC001 enforced\n# good  -  Suggestion until ASYNC selected"""),
      Rule('Keep `line-length = 88` unless the whole org moves together.', 'Mixed lengths cause churn.', 'Violation', 'ruff format', """# bad  -  80 in one package, 120 in another\n# good  -  88 everywhere"""),
      Rule('Document any future select expansions in README-python.md.', 'Skilled agents need the effective set.', 'Suggestion', None, """# bad  -  silent select change\n# good  -  changelog note + callout reconciliation"""),
    ),
  )

  write_chapter(
    '40-type-checking.md',
    'Type Checking',
    """Ruff is not a type checker. Use Pyright or mypy for static types.
This skill assumes a strict checker is available in CI even though types
are Suggestions under Ruff's minimal select.""",
    'Type-checker setup is **Suggestion**.',
    _r(
      Rule('Run a type checker in CI (pyright or mypy) on application packages.', 'Ruff F rules are not enough.', 'Suggestion', None, """# bad  -  only ruff check\n# good  -  ruff + pyright"""),
      Rule('Prefer pyright/`basedpyright` for FastAPI+Pydantic v2 projects unless the team is already on mypy.', 'Pydantic plugins differ; pick one.', 'Suggestion', None, """# bad  -  neither checker configured\n# good  -  pyrightconfig.json / [tool.pyright]"""),
      Rule('Keep `strict` (or gradually strict) mode; do not celebrate `Any` silence.', 'Loose mode hides the bugs you wanted.', 'Suggestion', None, """# bad  -  type checker optional locally\n# good  -  strict on app packages"""),
      Rule('Do not `# type: ignore` without an error code.', 'Same discipline as Ruff noqa.', 'Suggestion', None, """# bad\nvalue = legacy()  # type: ignore\n\n# good\nvalue = legacy()  # type: ignore[no-untyped-call]"""),
      Rule('Commit stubs only when upstream lacks them; prefer upstream typing.', 'Local stubs rot.', 'Suggestion', None, """# bad  -  sprawling custom stubs\n# good  -  typeshed/upstream first"""),
      Rule('Type FastAPI deps and handlers fully; OpenAPI will not save your internals.', 'Handlers are code.', 'Suggestion', None, """# bad  -  untyped **kwargs handler\n# good  -  Annotated models throughout"""),
      Rule('Avoid `cast` as a habit; narrow with isinstance/TypeGuards.', 'cast is an unchecked assertion.', 'Suggestion', None, """# bad  -  cast(User, data)\n# good  -  User.model_validate(data)"""),
      Rule('Keep third-party untyped libs behind typed adapters.', 'Contain the fire.', 'Suggestion', None, """# bad  -  Any spreads from vendor SDK\n# good  -  adapter returns domain types"""),
      Rule('Ensure `target-version`/pyright pythonVersion match 3.12.', 'Mismatch causes false diagnostics.', 'Suggestion', None, """# bad  -  pyright pythonVersion 3.10\n# good  -  3.12"""),
      Rule('Type test helpers enough to catch broken fakes.', 'Untyped fakes diverge.', 'Suggestion', None, """# bad  -  fake repo returns Any\n# good  -  FakeOrdersRepo implements Protocol"""),
      Rule('Do not disable the checker on whole packages to ship.', 'Fix or quarantine with a plan.', 'Suggestion', None, """# bad  -  exclude src/legacy forever\n# good  -  tracked quarantine list"""),
      Rule('Reconcile type-ignore counts in CI budgets.', 'Unbounded ignores become culture.', 'Suggestion', None, """# bad  -  ignore count climbs unnoticed\n# good  -  budget gate"""),
    ),
  )

  write_chapter(
    '41-project-layout-and-uv.md',
    'Project Layout & uv',
    """`uv` is the package/environment manager for this skill. Prefer
`src/` layouts, locked deps, and `uv run` for every tool invocation.""",
    'Layout/tooling guidance is **Suggestion**.',
    _r(
      Rule('Manage environments with `uv`; do not hand-maintain ad-hoc venvs as the primary workflow.', 'Reproducibility matters.', 'Suggestion', None, """# bad  -  pip install -r requirements.txt on system Python\n# good  -  uv sync && uv run pytest"""),
      Rule('Use a `src/<package>/` layout for libraries and services.', 'Avoids accidental imports from CWD.', 'Suggestion', None, """# bad  -  package at repo root mixed with tests\n# good  -  src/orders + tests/"""),
      Rule('Commit the lockfile (`uv.lock`) for applications.', 'Unpinned builds drift.', 'Suggestion', None, """# bad  -  floating deps only\n# good  -  uv.lock committed"""),
      Rule('Declare Python requires as `>=3.12` (and not older) for new projects following this skill.', 'Floor is 3.12.', 'Suggestion', None, """# bad  -  requires-python = '>=3.9'\n# good  -  requires-python = '>=3.12'"""),
      Rule('Put Ruff config at project root (`ruff.toml` or `[tool.ruff]`) and keep it authoritative.', 'Per-package drift hurts.', 'Suggestion', None, """# bad  -  each package different quotes\n# good  -  root ruff.toml"""),
      Rule('Invoke tools via `uv run` (ruff, pytest, pyright).', 'PATH pollution disappears.', 'Suggestion', None, """# bad  -  globally installed pytest\n# good  -  uv run pytest"""),
      Rule('Keep secrets out of the repo; use env / secret managers.', '`.env` is local-only.', 'Suggestion', None, """# bad  -  commit .env with keys\n# good  -  .env.example without secrets"""),
      Rule('Separate optional deps (`dev`, `test`) from runtime deps.', 'Prod images stay lean.', 'Suggestion', None, """# bad  -  pytest in main deps\n# good  -  dependency-groups / optional-deps"""),
      Rule('Do not start long-lived web servers from agent automation sessions.', 'Policy: run checks, not servers.', 'Suggestion', None, """# bad  -  uvicorn in background during skill authoring\n# good  -  pytest + ruff only"""),
      Rule('Document the exact bootstrap commands in README.', 'New contributors should not guess.', 'Suggestion', None, """# bad  -  undocumented poetry leftovers\n# good  -  uv sync / uv run pytest"""),
      Rule('Keep scripts under `scripts/` and make them `uv run`-able.', 'Random bash with system python fails.', 'Suggestion', None, """# bad  -  #!/usr/bin/env python relying on system 3.9\n# good  -  uv run scripts/build_python_skill.py"""),
      Rule('Align CI with local: same uv version policy, same ruff/pytest commands.', 'Works-on-my-machine dies here.', 'Suggestion', None, """# bad  -  CI pip, laptop uv\n# good  -  uv in both"""),
    ),
  )
