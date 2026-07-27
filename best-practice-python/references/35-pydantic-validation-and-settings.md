<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 35. Pydantic Validation & Settings

Pydantic v2 validation and `pydantic-settings` are the configuration
and boundary-validation stack. Follow
[Decouple Pydantic BaseSettings](https://github.com/zhanymkanov/fastapi-best-practices#decouple-pydantic-basesettings):
global settings in `src/config.py`, domain settings beside the domain.

**Tool alignment:** Validation/settings guidance is **Suggestion**.

## 35.1 Use `pydantic_settings.BaseSettings` for configuration, not scattered `os.environ`.

> Why? One typed object beats stringly config.
> **Suggestion.**

```python
# bad
DEBUG = os.getenv('DEBUG') == 'true'

# good
class Settings(BaseSettings):
  debug: bool = False
  model_config = SettingsConfigDict(env_file='.env')
```

## 35.2 Prefer immutable settings (`frozen=True`) loaded once.

> Why? Mutable global settings race.
> **Suggestion.**

```python
# bad - mutate settings mid-request
# good - frozen Settings dependency
```

## 35.3 Use `@field_validator` / `@model_validator` for cross-field rules.

> Why? Keep them pure and fast.
> **Suggestion.**

```python
# bad - validate in route after parse
# good - model_validator(mode='after')
```

## 35.4 Do not call networks inside validators.

> Why? Validators run often and surprisingly.
> **Suggestion.**

```python
# bad - validator hits DNS/HTTP
# good - validate shape; resolve remotely in service
```

## 35.5 Use `SecretStr` for secrets in settings/models.

> Why? Prevents accidental log/repr leaks.
> **Suggestion.**

```python
# bad
api_key: str

# good
api_key: SecretStr
```

## 35.6 Prefer `ValidationError` details at boundaries; translate to problem+json for clients.

> Why? Chapter 36.
> **Suggestion.**

```python
# bad - str(err) dump
# good - structured 422
```

## 35.7 Pin pydantic v2 APIs (`model_validate`, `model_dump`) - do not use v1 `.parse_obj` / `.dict`.

> Why? v1 methods are legacy.
> **Suggestion.**

```python
# bad
User.parse_obj(data)

# good
User.model_validate(data)
```

## 35.8 Keep settings env names explicit when clarity needs it (`validation_alias`).

> Why? Silent env mismatches waste hours.
> **Suggestion.**

```python
# bad - unclear env key
# good - Field(validation_alias='ORDERS_DB_URL')
```

## 35.9 Provide safe defaults only when they are safe in production.

> Why? Default open CORS is not safe.
> **Suggestion.**

```python
# bad - allow_origins=['*'] default in prod settings
# good - fail if unset in prod profile
```

## 35.10 Test settings loading with env overrides in unit tests.

> Why? Config bugs are prod bugs.
> **Suggestion.**

```python
# bad - only test happy defaults
# good - monkeyset env and validate
```

## 35.11 Avoid catching `ValidationError` and rebuilding ad-hoc dicts; fix the model.

> Why? Translation layers drift.
> **Suggestion.**

```python
# bad - manually revalidate dict
# good - tighten Field constraints
```

## 35.12 Keep domain invariants in domain types; keep transport constraints in schemas.

> Why? Do not double-encode poorly.
> **Suggestion.**

```python
# bad - same regex in 4 models
# good - shared annotated types
```
