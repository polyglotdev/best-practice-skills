<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 22. Properties & Descriptors

[pyguide §2.13](https://google.github.io/styleguide/pyguide.html#s2.13-properties) defines when properties are
appropriate. Descriptors are rare outside frameworks.

**Tool alignment:** Property guidance is **Suggestion**.

## 22.1 Use `@property` for cheap derived values.

> Why? Hidden IO in properties surprises.
> **Suggestion.**

```python
# bad
@property
def users(self) -> list[User]:
  return self._db.fetch_users()

# good
def load_users(self) -> list[User]:
  return self._db.fetch_users()
```

## 22.2 Prefer methods when computation is non-trivial or cached state is involved.

> Why? Caches need explicit invalidation APIs.
> **Suggestion.**

```python
# bad - property with LRU side effects
# good - get_report() method
```

## 22.3 Do not invent setters that silently coerce invalid data.

> Why? Raise instead.
> **Suggestion.**

```python
# bad
@email.setter
def email(self, value: str) -> None:
  self._email = value or 'unknown'

# good - validate and raise
```

## 22.4 Keep descriptors for framework/library authors, not app business logic.

> Why? Descriptors are hard to reason about in apps.
> **Suggestion.**

```python
# bad - custom descriptor for order total
# good - function or property
```

## 22.5 Document property side effects if any exist (they usually should not).

> Why? Surprises belong in method names.
> **Suggestion.**

```python
# bad - silent lazy remote fetch
# good - method named fetch_
```

## 22.6 Prefer dataclass fields / Pydantic fields over hand-rolled descriptor validation in apps.

> Why? Ecosystem tools already solve this.
> **Suggestion.**

```python
# bad - FieldDescriptor for every attribute
# good - pydantic BaseModel
```

## 22.7 Avoid properties that mutate other properties as a chain reaction.

> Why? Setter cascades are debugging traps.
> **Suggestion.**

```python
# bad - setting width mutates height mutates area mutates width
# good - explicit recompute method
```

## 22.8 Expose read-only attributes with `@property` (no setter) instead of public fields you hope nobody writes.

> Why? Makes intent clear.
> **Suggestion.**

```python
# bad
self.id = value  # public

# good
@property
def id(self) -> str:
  return self._id
```

## 22.9 Do not use properties to paper over poor naming of methods.

> Why? Verbs should be methods.
> **Suggestion.**

```python
# bad
@property
def save(self):
  ...

# good
def save(self) -> None:
  ...
```

## 22.10 Cache with `functools.cached_property` only for immutable instances.

> Why? Mutable objects + cached_property stale easily.
> **Suggestion.**

```python
# bad - cached_property on mutable entity
# good - cached_property on frozen/dataclass(frozen=True)
```

## 22.11 Keep property implementations short enough to read inline.

> Why? Long properties should be methods.
> **Suggestion.**

```python
# bad - 40-line property
# good - method
```

## 22.12 For FastAPI response models, expose data as fields, not as properties that hit the DB during serialization.

> Why? Serialization-time IO is a footgun.
> **Suggestion.**

```python
# bad - @property on model triggers lazy load during response
# good - eager load / compute before returning
```
