<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 18. Pattern Matching

`match` / `case` (PEP 634+) is the structured alternative to long
`if/elif` type trees. Use it for closed shapes; do not use it as a fancy
switch for booleans.

**Tool alignment:** Pattern-matching style is **Suggestion**.

## 18.1 Use `match` for structured destructuring of tagged shapes, not for simple equality chains of primitives unless clarity wins.

> Why? Overusing match for booleans hurts.
> **Suggestion.**

```python
# bad
match ready:
  case True:
    start()
  case False:
    stop()

# good
if ready:
  start()
else:
  stop()
```

## 18.2 Prefer sealed-like unions (`A | B`) with match over `isinstance` ladders when you control the types.

> Why? Exhaustiveness is easier to see.
> **Suggestion.**

```python
# bad - long isinstance chain
# good - match event with case Created()/case Updated()
```

## 18.3 Use capture names carefully; avoid bare names that always match.

> Why? A single bare name case is a catch-all.
> **Suggestion.**

```python
# bad
match value:
  case x:
    return x

# good
match value:
  case int() as n:
    return n
  case _:
    raise TypeError(type(value))
```

## 18.4 Put `|` or-patterns for shared handling; duplicate case bodies are a smell.

> Why? Or-patterns keep handling unified.
> **Suggestion.**

```python
# bad - duplicated bodies
# good
case 401 | 403:
  raise AuthError()
```

## 18.5 Use guards (`case x if ...`) sparingly; complex guards belong in helpers.

> Why? Guards can hide the shape being matched.
> **Suggestion.**

```python
# bad - giant guard expression
# good - case User() as user if is_billable(user):
```

## 18.6 Prefer matching mapping keys explicitly over matching entire dicts loosely.

> Why? Precise keys document required payload shape.
> **Suggestion.**

```python
# bad
case {'type': t, **rest}:
  ...

# good
case {'type': 'order', 'id': str() as order_id}:
  ...
```

## 18.7 Keep match statements exhaustive for domain unions; include `case _` only at boundaries.

> Why? Silent `_` swallows new variants.
> **Suggestion.**

```python
# bad - case _ everywhere in core logic
# good - case _ at the HTTP edge with logging
```

## 18.8 Do not match on Pydantic models as if they were dicts unless you convert deliberately.

> Why? Model instances use class patterns.
> **Suggestion.**

```python
# bad - case {'id': ...} on a BaseModel instance
# good - case Order(id=order_id):
```

## 18.9 Avoid deeply nested matches; extract functions per variant.

> Why? Nested matches recreate callback hell.
> **Suggestion.**

```python
# bad - match inside match inside match
# good - dispatch to handle_created/handle_updated
```

## 18.10 Use class patterns with keyword attributes for dataclasses and similar.

> Why? Positional class patterns are brittle under field reordering.
> **Suggestion.**

```python
# bad
case Point(x, y):
  ...

# good
case Point(x=x, y=y):
  ...
```

## 18.11 Do not use match to reinvent polymorphism when a method on the type is clearer.

> Why? OOP dispatch still wins for open sets.
> **Suggestion.**

```python
# bad - match on type to call methods
# good - animal.speak()
```

## 18.12 Document intentional fall-through-like shared handling with or-patterns, not by stacking empty cases.

> Why? Empty cases are easy to misread.
> **Suggestion.**

```python
# bad
case 401:
  ...
case 403:
  ...  # copy-paste

# good
case 401 | 403:
  raise AuthError()
```
