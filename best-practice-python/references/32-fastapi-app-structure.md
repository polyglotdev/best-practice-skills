<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 32. FastAPI App Structure

Structure FastAPI apps for testability and scale. The normative FastAPI
architecture source for this skill is
[zhanymkanov/fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices)
(domain packages under `src/`, thin routers, service layer, Pydantic schemas
separate from DB models). Pair that with an app factory, lifespan-managed
resources, and the house Ruff style (2-space indent, single quotes).

**Tool alignment:** Structure guidance is **Suggestion**.

## 32.1 Organize by domain package under `src/`, not by file type across the whole app.

> Why? Layer-by-type trees (all routers/, all models/) do not scale; each domain owns router/schemas/models/service/dependencies.
> **Suggestion.**

```python
# bad - global routers/, models/, crud/ piles
# good - src/orders/{router,schemas,models,service,dependencies}.py
```

## 32.2 Keep `router.py` thin: HTTP in, call `service.py`, return schema out.

> Why? SQL and business rules in routes resists testing and reuse.
> **Suggestion.**

```python
# bad
@router.post('/orders')
async def create(order: OrderCreate, db: Session):
  db.add(Order(**order.model_dump()))
  db.commit()

# good
@router.post('/orders', response_model=OrderResponse)
async def create_order(
  order: OrderCreate,
  service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderResponse:
  return await service.create(order)
```

## 32.3 Separate Pydantic schemas from DB models (`schemas.py` vs `models.py`).

> Why? Transport and persistence change for different reasons.
> **Suggestion.**

```python
# bad - ORM entity used as request body
# good - OrderCreate / OrderResponse in schemas.py; Order in models.py
```

## 32.4 Put domain exceptions in `exceptions.py` and map them at the app edge.

> Why? HTTP status codes do not belong in repositories.
> **Suggestion.**

```python
# bad - HTTPException inside service SQL helper
# good - OrderNotFoundError in exceptions.py; handler maps to 404
```

## 32.5 Expose an app factory or a thin `src/main.py` that includes domain routers explicitly.

> Why? Import side-effect registration hides the graph.
> **Suggestion.**

```python
# bad
import src.orders.router  # magic registration

# good
def create_app() -> FastAPI:
  app = FastAPI(lifespan=lifespan)
  app.include_router(orders.router)
  return app
```

## 32.6 Use `APIRouter(prefix=..., tags=[...])` per domain package.

> Why? OpenAPI stays navigable.
> **Suggestion.**

```python
# bad - prefix duplicated on every decorator
# good
router = APIRouter(prefix='/orders', tags=['orders'])
```

## 32.7 Prefer lifespan over deprecated startup/shutdown events.

> Why? One async context owns pools and clients.
> **Suggestion.**

```python
# bad
@app.on_event('startup')
async def start() -> None:
  ...

# good - @asynccontextmanager lifespan attached to FastAPI()
```

## 32.8 Import cross-domain collaborators with explicit module aliases.

> Why? Matches the fastapi-best-practices import style and avoids name clashes.
> **Suggestion.**

```python
# bad
from src.auth.constants import ErrorCode
from src.posts.constants import ErrorCode  # clash

# good
from src.auth import constants as auth_constants
from src.posts.constants import ErrorCode as PostsErrorCode
```

## 32.9 Follow REST for public HTTP shapes; keep RPC-style only behind clear non-REST paths.

> Why? Consistent resources beat verb-in-path chaos.
> **Suggestion.**

```python
# bad - POST /createOrder /getOrder
# good - POST /orders , GET /orders/{order_id}
```

## 32.10 Wire global config in `src/config.py`; keep domain `config.py` for domain-only settings.

> Why? Decouple BaseSettings per the FastAPI guide.
> **Suggestion.**

```python
# bad - os.getenv sprinkled in routers
# good - Settings in src/config.py; domain overrides in src/orders/config.py
```

## 32.11 Mirror domain packages under `tests/` (`tests/orders/...`).

> Why? Tests navigate the same way as production code.
> **Suggestion.**

```python
# bad - tests/test_all_routes.py god file
# good - tests/orders/test_create_order.py
```

## 32.12 Document local run with `uv run uvicorn src.main:app` without starting servers from agent sessions.

> Why? Checks and tests only in automation.
> **Suggestion.**

```python
# bad - python nested server in scripts during CI/agent runs
# good - uv run pytest && uv run ruff check .
```
