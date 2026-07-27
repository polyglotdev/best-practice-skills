<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 15. Comprehensions

Comprehensions are fine when they stay readable.
[pyguide §2.7](https://google.github.io/styleguide/pyguide.html#s2.7-list_comprehensions) rejects complex ones.

**Tool alignment:** Comprehension complexity is **Suggestion**.

## 15.1 Keep comprehensions to one or two clauses; escalate to loops when logic nests.

> Why? Dense comprehensions hide bugs.
> **Suggestion.**

```python
# bad
result = [f(x, y) for x in xs if p(x) for y in ys if q(x, y) if r(y)]

# good - for-loops with names
```

## 15.2 Prefer comprehensions over `map`/`filter` with lambdas for simple transforms.

> Why? Comprehensions are the language-native form.
> **Suggestion.**

```python
# bad
list(map(lambda x: x.strip(), rows))

# good
[row.strip() for row in rows]
```

## 15.3 Use dict/set comprehensions instead of loops that build empty collections.

> Why? They state intent in one expression.
> **Suggestion.**

```python
# bad
index = {}
for user in users:
  index[user.id] = user

# good
index = {user.id: user for user in users}
```

## 15.4 Do not put side effects inside comprehensions.

> Why? Comprehensions are for building values.
> **Suggestion.**

```python
# bad
[save(user) for user in users]

# good
for user in users:
  save(user)
```

## 15.5 Prefer generator expressions when feeding a single consumer.

> Why? Avoid allocating an intermediate list.
> **Suggestion.**

```python
# bad
sum([value for value in values if value > 0])

# good
sum(value for value in values if value > 0)
```

## 15.6 Name complex predicates as functions before using them in a comprehension.

> Why? Inline `if` soups are unreadable.
> **Suggestion.**

```python
# bad
[u for u in users if u.active and u.role != 'guest' and u.email]

# good
[u for u in users if is_billable(u)]
```

## 15.7 Avoid walrus-heavy comprehensions unless the assignment clearly helps.

> Why? Nested `:=` is a review tax.
> **Suggestion.**

```python
# bad - multiple := in one comprehension
# good - loop with named temps
```

## 15.8 Do not use comprehensions to emulate `any`/`all` with side effects.

> Why? Use `any`/`all` for predicates.
> **Suggestion.**

```python
# bad
if [1 for x in xs if pred(x)]:
  ...

# good
if any(pred(x) for x in xs):
  ...
```

## 15.9 Keep conditionals in comprehensions as filters, not as ternary value logic trees.

> Why? Complex value ternaries belong in helper functions.
> **Suggestion.**

```python
# bad
[a if c else b if d else e for x in xs]

# good
[choose(x) for x in xs]
```

## 15.10 Prefer unpacking clarity over clever nested comprehensions for matrices.

> Why? Nested loops are clearer for 2D transforms.
> **Suggestion.**

```python
# bad - 2D comprehension with conditionals
# good - nested for-loops
```

## 15.11 Do not mutate the iterated collection inside a comprehension filter.

> Why? Same hazard as iterator mutation.
> **Suggestion.**

```python
# bad - filter calls method that mutates source
# good - pure predicate
```

## 15.12 Use comprehensions for data shaping; use pandas/SQL/polars for heavy tabular work.

> Why? Python loops over millions of rows are the wrong tool.
> **Suggestion.**

```python
# bad - nested comprehensions over huge CSV
# good - vectorized tool or DB query
```
