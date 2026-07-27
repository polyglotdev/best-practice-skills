<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 34. Request & Response Models

Pydantic v2 models define the HTTP contract. The FastAPI guide's
[Pydantic](https://github.com/zhanymkanov/fastapi-best-practices#pydantic)
section is normative here: use Pydantic heavily, prefer a custom base model
when you need shared serialization rules, and keep schemas out of ORM
entities.

**Tool alignment:** Model guidance is **Suggestion**.

## 34.1 Declare `response_model` (or return annotated models) for every public route.

> Why? OpenAPI and filtering depend on it.
> **Suggestion.**

```python
# bad
@router.get('/orders/{order_id}')
async def get_order(...):
  return orm_order

# good
@router.get('/orders/{order_id}', response_model=OrderResponse)
async def get_order(...) -> OrderResponse:
  ...
```

## 34.2 Never return SQLAlchemy/ORM entities directly.

> Why? Lazy loads and private fields leak.
> **Suggestion.**

```python
# bad - return User ORM
# good - UserResponse.model_validate(user)
```

## 34.3 Separate create/update/response models when fields differ.

> Why? One mega-model invites mass-assignment bugs.
> **Suggestion.**

```python
# bad - same model for input/output with id/password
# good - UserCreate / UserUpdate / UserResponse
```

## 34.4 Use `model_config = ConfigDict(extra='forbid')` for request bodies you control.

> Why? Unknown fields should fail fast.
> **Suggestion.**

```python
# bad - silently ignore unknown fields
# good - extra='forbid' on request models
```

## 34.5 Prefer field constraints (`Field(ge=0)`) over ad-hoc validation in routes.

> Why? Keep invariants in the model.
> **Suggestion.**

```python
# bad - if qty < 0 in route
# good - qty: int = Field(ge=0)
```

## 34.6 Use `EmailStr` / constrained types for common formats.

> Why? Do not regex casually.
> **Suggestion.**

```python
# bad - email: str
# good - email: EmailStr
```

## 34.7 Alias wire names intentionally (`alias` / `serialization_alias`) rather than renaming ad hoc in routes.

> Why? Keep one mapping place.
> **Suggestion.**

```python
# bad - payload['userId'] mapped manually
# good - Field(validation_alias='userId')
```

## 34.8 Keep response models stable; add fields carefully and avoid renames without versioning.

> Why? Clients break quietly.
> **Suggestion.**

```python
# bad - rename fields casually
# good - additive changes / versioning
```

## 34.9 Do not put methods with IO on response models.

> Why? Models are data.
> **Suggestion.**

```python
# bad - response.model.save()
# good - service.save()
```

## 34.10 Use `TypedDict` only for internal shaping; external HTTP uses BaseModel.

> Why? BaseModel gives validation/OpenAPI.
> **Suggestion.**

```python
# bad - TypedDict as response_model
# good - BaseModel response
```

## 34.11 Prefer explicit status codes with `status_code=` / `Response` when not 200/201 defaults.

> Why? Be intentional.
> **Suggestion.**

```python
# bad - create returns 200 by accident
# good - status_code=201
```

## 34.12 Document examples sparingly via `json_schema_extra` when they help clients.

> Why? Do not invent fantasy payloads.
> **Suggestion.**

```python
# bad - misleading examples
# good - realistic examples
```
