<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 21. Truthiness & Comparisons

[pyguide §2.14](https://google.github.io/styleguide/pyguide.html#s2.14-truefalse-evaluations) covers boolean
evaluations. Combine with Ruff `E711`/`E712`.

**Tool alignment:** `E711`, `E712`, `E721`, `F632` are **Violation** where applicable.

## 21.1 Use `is` / `is not` for `None` comparisons.

> Why? Identity is correct for None.
> **Violation - enforced by `E711`.**

```python
# bad
if value == None:
  ...

# good
if value is None:
  ...
```

## 21.2 Do not compare booleans with `== True`/`== False`.

> Why? Use truthiness directly.
> **Violation - enforced by `E712`.**

```python
# bad
if ready == True:
  ...

# good
if ready:
  ...
```

## 21.3 Use `isinstance` instead of comparing `type(x) is`.

> Why? `E721` flags type comparisons that break subclasses.
> **Violation - enforced by `E721`.**

```python
# bad
if type(value) is list:
  ...

# good
if isinstance(value, list):
  ...
```

## 21.4 Prefer explicit `is None` when empty containers are valid data.

> Why? Truthiness collapses `[]` and `None`.
> **Suggestion.**

```python
# bad
if not items:
  return  # cannot tell None from []

# good
if items is None:
  return
if not items:
  return
```

## 21.5 Do not use `==` to compare singletons like `True`/`False`/`None`.

> Why? Use identity.
> **Suggestion.**

```python
# bad
if flag == True:
  ...

# good
if flag:
  ...
```

## 21.6 Avoid chained comparisons that mix incompatible types.

> Why? They can hide TypeErrors.
> **Suggestion.**

```python
# bad
if a < b < '9':
  ...

# good - ensure comparable types
```

## 21.7 Use `math.isclose` for floats.

> Why? Exact equality is brittle.
> **Suggestion.**

```python
# bad
if total == 0.3:
  ...

# good
if math.isclose(total, 0.3):
  ...
```

## 21.8 Prefer `x in options` over long `or` chains.

> Why? Membership scales.
> **Suggestion.**

```python
# bad
if x == 1 or x == 2 or x == 3:
  ...

# good
if x in {1, 2, 3}:
  ...
```

## 21.9 Do not write `if x != None` via equality.

> Why? Same as E711.
> **Violation - enforced by `E711`.**

```python
# bad
if x != None:
  ...

# good
if x is not None:
  ...
```

## 21.10 Treat unknown objects as opaque; narrow with `isinstance` before attribute access.

> Why? EAFP still needs intentional narrowing in typed code.
> **Suggestion.**

```python
# bad
value.id  # value: object

# good
if isinstance(value, User):
  return value.id
```

## 21.11 Avoid `not not x` / double negation cleverness.

> Why? Use `bool(x)` if you need a real bool.
> **Suggestion.**

```python
# bad
flag = not not value

# good
flag = bool(value)
```

## 21.12 Do not use `is` for string/int equality.

> Why? Identity for interning is not a contract.
> **Suggestion.**

```python
# bad
if name is 'Ada':
  ...

# good
if name == 'Ada':
  ...
```
