<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 16. Strings

String formatting and logging interact.
[pyguide §3.10](https://google.github.io/styleguide/pyguide.html#s3.10-strings) and [§3.10.1](https://google.github.io/styleguide/pyguide.html#s3.10.1-logging) matter.

**Tool alignment:** `F541` (f-string without placeholders) is **Violation**. Other string rules are **Suggestion**.

## 16.1 Prefer f-strings for eager formatting; use `%`/`extra=` for logging laziness.

> Why? Logging should not format if the line is filtered out.
> **Suggestion.**

```python
# bad
logger.info(f'user={user_id} failed')

# good
logger.info('user=%s failed', user_id)
```

## 16.2 Do not write f-strings without placeholders.

> Why? They are pointless string literals. `F541`.
> **Violation - enforced by `F541`.**

```python
# bad
msg = f'hello'

# good
msg = 'hello'
```

## 16.3 Use single quotes per house style; reserve doubles to avoid escapes.

> Why? Matches `ruff format` quote-style.
> **Violation - enforced by `ruff format`.**

```python
# bad
name = "Ada"

# good
name = 'Ada'
```

## 16.4 Prefer `str.removeprefix` / `removesuffix` over brittle slices.

> Why? Slices break when the prefix is absent.
> **Suggestion.**

```python
# bad
value = text[4:] if text.startswith('the ') else text

# good
value = text.removeprefix('the ')
```

## 16.5 Do not concatenate many strings with `+` in a loop; use `join` or a list.

> Why? Quadratic behavior appears under load.
> **Suggestion.**

```python
# bad
out = ''
for part in parts:
  out += part

# good
out = ''.join(parts)
```

## 16.6 Keep user-facing error messages clear; keep logs structured.

> Why? [pyguide §3.10.2](https://google.github.io/styleguide/pyguide.html#s3.10.2-error-messages).
> **Suggestion.**

```python
# bad
raise ValueError('err')

# good
raise ValueError('order_id must be a non-empty string')
```

## 16.7 Use raw strings for regexes.

> Why? Escaping hell is optional.
> **Suggestion.**

```python
# bad
pattern = '\\d+'

# good
pattern = r'\d+'
```

## 16.8 Normalize newlines and strip edges at trust boundaries.

> Why? Do not sprinkle `.strip()` randomly deep in core logic.
> **Suggestion.**

```python
# bad - strip in five helpers
# good - normalize once when reading input
```

## 16.9 Avoid `str.encode` defaults surprises; be explicit with UTF-8.

> Why? Explicit encodings survive locale differences.
> **Suggestion.**

```python
# bad
data = text.encode()

# good
data = text.encode('utf-8')
```

## 16.10 Do not use string exceptions or stringly typed enums; use Enum/Literal.

> Why? See chapters 18-19.
> **Suggestion.**

```python
# bad
status = 'ok'

# good
status = Status.OK
```

## 16.11 Prefer `textwrap.dedent` for multiline literals embedded in code.

> Why? Keeps indentation readable under 2-space house style.
> **Suggestion.**

```python
# bad - weird margins in SQL strings
# good
sql = dedent('''
  select 1
  ''')
```

## 16.12 Never build SQL/HTML with f-strings from user input.

> Why? Use parameters / templates to avoid injection.
> **Suggestion.**

```python
# bad
cur.execute(f'select * from users where id = \'{user_id}\'')

# good
cur.execute('select * from users where id = %s', (user_id,))
```
