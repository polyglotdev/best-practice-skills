"""Chapters 11-26 for best-practice-python."""

from __future__ import annotations

from scripts.python_skill._render import Rule, write_chapter

PY = 'https://google.github.io/styleguide/pyguide.html'


def _r(*rules: Rule) -> list[Rule]:
  assert len(rules) >= 12
  return list(rules)


def build() -> None:
  write_chapter(
    '11-generics-and-pep695.md',
    'Generics & PEP 695',
    f"""Python 3.12 makes PEP 695 type-parameter syntax the preferred way to
write generics. [pyguide §3.19.15]({PY}#s3.19.15-generics) and
[§3.19.10]({PY}#s3.19.10-typevars) remain relevant; prefer the new form
when it clarifies.""",
    'Generics guidance is **Suggestion** (no `UP` enabled). Keep '
    '`target-version = \'py312\'` so Ruff can eventually enforce modern forms.',
    _r(
      Rule('Prefer PEP 695 `def f[T](...):` / `class Box[T]:` over `TypeVar` for new code.', 'The new syntax scopes type params to the declaration and reads like other languages.', 'Suggestion', None, """# bad\nfrom typing import TypeVar\nT = TypeVar('T')\ndef first(items: list[T]) -> T: ...\n\n# good\ndef first[T](items: list[T]) -> T:\n  return items[0]"""),
      Rule('Use bounds and constraints on type parameters explicitly.', 'Unbounded params become `Any`-shaped in practice.', 'Suggestion', None, """# bad\ndef sort_key[T](value: T) -> T: ...\n\n# good\ndef sort_key[T: str](value: T) -> T:\n  return value.lower()  # type: ignore[return-value]"""),
      Rule('Prefer `type Alias[T] = ...` for generic aliases on 3.12.', 'PEP 695 aliases are clearer than `TypeAlias` assignments.', 'Suggestion', None, """# bad\nfrom typing import TypeAlias\nResult: TypeAlias = tuple[bool, str]\n\n# good\ntype Result = tuple[bool, str]"""),
      Rule('Do not mix old `TypeVar` and PEP 695 params in one declaration.', 'Mixing styles confuses checkers and readers.', 'Suggestion', None, """# bad  -  TypeVar plus [T] in the same API surface\n# good  -  pick PEP 695 for new APIs"""),
      Rule('Use `TypeVarTuple` / `*` unpacking only when variadic types are real.', 'Most APIs need one or two params, not variadic generics.', 'Suggestion', None, """# bad  -  Variadic for a fixed pair\n# good  -  tuple[T, U] or a dataclass"""),
      Rule('Parametrize protocols and ABCs the same way you parametrize classes.', 'Generic protocols keep repositories and factories honest.', 'Suggestion', None, """# bad\nclass Repo(Protocol):\n  def get(self, key: str) -> object: ...\n\n# good\nclass Repo[T](Protocol):\n  def get(self, key: str) -> T: ..."""),
      Rule('Avoid `Any` as a generic escape hatch.', 'If you need escape, isolate it at a boundary with a comment.', 'Suggestion', None, """# bad\ndef parse[T](raw: str) -> T:\n  return json.loads(raw)  # type: ignore\n\n# good\ndef parse_object(raw: str) -> dict[str, object]:\n  data = json.loads(raw)\n  if not isinstance(data, dict):\n    raise TypeError('object expected')\n  return data"""),
      Rule('Keep variance explicit only when declaring libraries that need it.', 'Application code rarely needs `covariant=True` TypeVars.', 'Suggestion', None, """# bad  -  cargo-cult variance in app code\n# good  -  default invariance unless you ship a typed library API"""),
      Rule('Prefer concrete aliases at application edges over leaking bare type params.', 'Call sites should see `OrderRepo`, not `Repo[Order]` everywhere if one binding dominates.', 'Suggestion', None, """# bad  -  Repo[Order] repeated 40 times\n# good\ntype OrderRepo = Repo[Order]"""),
      Rule('Do not invent phantom type parameters that never appear in the signature.', 'Unused type params are lies.', 'Suggestion', None, """# bad\nclass Service[T]:\n  def ping(self) -> str:\n    return 'ok'\n\n# good\nclass Service:\n  def ping(self) -> str:\n    return 'ok'"""),
      Rule('Use `typing.overload` for small finite signature sets; do not fake them with generics.', 'Overloads document distinct return types per input.', 'Suggestion', None, """# bad  -  return Any\n# good  -  @overload pairs for str vs bytes inputs"""),
      Rule('Test generic helpers with at least two concrete type arguments in unit tests.', 'Generics that only ever see one type are premature.', 'Suggestion', None, """# bad  -  only tested with str\n# good  -  tests for str and int specializations"""),
    ),
  )

  write_chapter(
    '12-exceptions.md',
    'Exceptions',
    f"""Exceptions are the error mechanism. [pyguide §2.4]({PY}#s2.4-exceptions)
rejects using them for normal control flow and rejects bare excepts.""",
    '`E722` (bare except) is **Violation**. Hierarchy and raising style are '
    '**Suggestion**.',
    _r(
      Rule('Catch specific exceptions; never bare `except:`.', 'Bare except catches `KeyboardInterrupt` and `SystemExit`.', 'Violation', 'E722', """# bad\ntry:\n  parse(raw)\nexcept:\n  return None\n\n# good\ntry:\n  parse(raw)\nexcept ValueError:\n  return None"""),
      Rule('Do not use exceptions for ordinary control flow.', 'Expected emptiness is a return value or Result-like type, not `raise`.', 'Suggestion', None, """# bad\ndef find(name: str) -> User:\n  raise StopIteration\n\n# good\ndef find(name: str) -> User | None:\n  return None"""),
      Rule('Raise `ValueError` / `TypeError` / domain errors with actionable messages.', 'Empty raises waste operators.', 'Suggestion', None, """# bad\nraise ValueError()\n\n# good\nraise ValueError(f'rate must be in [0, 1], got {rate}')"""),
      Rule('Define a small domain exception hierarchy rooted at one package error type.', 'Callers catch the root; internals raise leaves.', 'Suggestion', None, """# bad  -  raise Exception('nope')\n# good\nclass OrdersError(Exception):\n  ...\n\nclass OrderNotFoundError(OrdersError):\n  ..."""),
      Rule('Prefer exception chaining with `raise ... from err` when translating errors.', 'Chaining preserves cause for logs and Sentry.', 'Suggestion', None, """# bad\nexcept KeyError:\n  raise OrderNotFoundError(order_id)\n\n# good\nexcept KeyError as err:\n  raise OrderNotFoundError(order_id) from err"""),
      Rule('Do not catch `Exception` unless at a process/request boundary that logs and re-shapes.', 'Broad catches in libraries hide bugs.', 'Suggestion', None, """# bad\ndef helper():\n  try:\n    work()\n  except Exception:\n    pass\n\n# good  -  boundary only\ntry:\n  work()\nexcept Exception:\n  logger.exception('request failed')\n  raise"""),
      Rule('Never use `assert` for runtime input validation in production APIs.', '`assert` can be stripped with `-O`. Use `raise` / Pydantic.', 'Suggestion', None, """# bad\nassert rate >= 0\n\n# good\nif rate < 0:\n  raise ValueError('rate must be >= 0')"""),
      Rule('Map domain errors to HTTP errors at the FastAPI boundary, not deep in repositories.', 'See chapter 36. Repositories raise domain exceptions.', 'Suggestion', None, """# bad  -  HTTPException inside SQL helper\n# good  -  OrderNotFoundError in repo; handler maps to 404"""),
      Rule('Avoid returning `(value, error)` tuples when exceptions express failure better.', 'Dual returns recreate Go without its compiler help.', 'Suggestion', None, """# bad\ndef load() -> tuple[Config | None, Exception | None]:\n  ...\n\n# good\ndef load() -> Config:\n  ..."""),
      Rule('Clean up with `finally` or context managers, not duplicated cleanup in `except` and success paths.', 'See chapter 13.', 'Suggestion', None, """# bad  -  close() copied three times\n# good  -  with open(...) as handle:"""),
      Rule('Do not raise string exceptions or non-`BaseException` values.', 'Only exception instances are valid.', 'Suggestion', None, """# bad\nraise 'failed'  # type: ignore[misc]\n\n# good\nraise RuntimeError('failed')"""),
      Rule('Keep `except` clauses ordered from most specific to least specific.', 'Broad handlers first shadow useful specifics.', 'Suggestion', None, """# bad\nexcept Exception:\n  ...\nexcept ValueError:\n  ...\n\n# good\nexcept ValueError:\n  ...\nexcept Exception:\n  ..."""),
    ),
  )

  write_chapter(
    '13-context-managers.md',
    'Context Managers',
    f"""Context managers own setup/teardown. [pyguide §3.11]({PY}#s3.11-files-sockets-closeables)
requires closing files, sockets, and similar resources.""",
    'Resource-closing discipline is **Suggestion** under the shipped select '
    '(no `SIM`/`PTH`).',
    _r(
      Rule('Always open files with a `with` statement.', 'Manual `close()` is easy to skip on exceptions.', 'Suggestion', None, """# bad\nhandle = open(path)\ndata = handle.read()\nhandle.close()\n\n# good\nwith path.open() as handle:\n  data = handle.read()"""),
      Rule('Prefer `contextlib.contextmanager` / `asynccontextmanager` for ad-hoc helpers.', 'Lightweight generators beat full classes for simple cases.', 'Suggestion', None, """# bad  -  40-line class for a lock helper\n# good\n@contextmanager\ndef locked(lock: Lock):\n  lock.acquire()\n  try:\n    yield\n  finally:\n    lock.release()"""),
      Rule('Do not open resources in `__init__` without a matching close protocol.', 'Prefer context managers for lifetimes.', 'Suggestion', None, """# bad\nclient = ApiClient()  # opens sockets in __init__\n# good\nwith ApiClient() as client:\n  ..."""),
      Rule('Use `ExitStack` when the number of context managers is dynamic.', 'Variable `with` depth needs a stack.', 'Suggestion', None, """# bad  -  nested with that grows with N files\n# good  -  ExitStack enters each path in a loop"""),
      Rule('Keep context-manager bodies short; do not hide business transactions inside unrelated `with` blocks.', 'Readers should see what is being protected.', 'Suggestion', None, """# bad  -  entire request inside a file with\n# good  -  with only wraps the file IO section"""),
      Rule('For FastAPI, use lifespan/`asynccontextmanager` for app-scoped resources.', 'Global clients at import time complicate tests.', 'Suggestion', None, """# bad\nredis = Redis.from_url(URL)\n\n# good  -  attach to app.state in lifespan"""),
      Rule('Do not suppress exceptions in `__exit__` unless that is the documented contract.', 'Returning true swallows bugs.', 'Suggestion', None, """# bad\ndef __exit__(self, *args):\n  return True\n\n# good\ndef __exit__(self, exc_type, exc, tb):\n  self.close()\n  return False"""),
      Rule('Prefer `pathlib.Path.open` over bare `open` for path-typed APIs.', 'Keeps path types consistent.', 'Suggestion', None, """# bad\nopen(str(path))\n\n# good\npath.open()"""),
      Rule('Close DB sessions via dependency/context managers, never leak them across requests.', 'Session-per-request is the default web pattern.', 'Suggestion', None, """# bad  -  module-level Session()\n# good  -  yield session in a FastAPI dependency"""),
      Rule('Use `closing()` for objects that have `.close()` but no context manager.', 'stdlib helper fills gaps.', 'Suggestion', None, """# bad  -  manual close on urlopen-like objects\n# good\nfrom contextlib import closing\nwith closing(obj) as handle:\n  ..."""),
      Rule('Avoid context managers that perform surprising remote calls on enter.', 'Enter should be cheap and local when possible.', 'Suggestion', None, """# bad  -  with Client() hits network for auth every time\n# good  -  explicit connect(); with only scopes the session"""),
      Rule('Pair every lock acquisition with a context manager.', 'Manual acquire/release deadlocks under exceptions.', 'Suggestion', None, """# bad\nlock.acquire()\nmutate()\nlock.release()\n\n# good\nwith lock:\n  mutate()"""),
    ),
  )

  write_chapter(
    '14-iterators-and-generators.md',
    'Iterators & Generators',
    f"""Iterators and generators express streaming work.
[pyguide §2.9]({PY}#s2.9-generators) covers generator decisions.""",
    'Iterator style is **Suggestion**.',
    _r(
      Rule('Prefer generators for large or infinite sequences.', 'Materializing huge lists wastes memory.', 'Suggestion', None, """# bad\ndef read_lines(path: Path) -> list[str]:\n  return path.read_text().splitlines()\n\n# good\ndef read_lines(path: Path) -> Iterator[str]:\n  with path.open() as handle:\n    for line in handle:\n      yield line.rstrip('\\n')"""),
      Rule('Use generator `send`/`throw` rarely; prefer plain iterators and async streams.', 'Coroutines-as-generators are hard to follow.', 'Suggestion', None, """# bad  -  send-based protocol for ordinary pipelines\n# good  -  next()/for-loops or async iterators"""),
      Rule('Annotate generators as `Iterator[T]` / `Iterable[T]` / `Generator[T, None, R]`.', 'Precise types document yield vs return.', 'Suggestion', None, """# bad\ndef walk(nodes):\n  yield from nodes\n\n# good\ndef walk(nodes: Iterable[Node]) -> Iterator[Node]:\n  yield from nodes"""),
      Rule('Prefer `yield from` when delegating to another iterable.', 'Manual loops reimplement delegation badly.', 'Suggestion', None, """# bad\nfor item in inner:\n  yield item\n\n# good\nyield from inner"""),
      Rule('Do not mutate a list while iterating it; iterate a copy or build a new list.', 'Live mutation skips elements.', 'Suggestion', None, """# bad\nfor item in items:\n  if bad(item):\n    items.remove(item)\n\n# good\nitems[:] = [item for item in items if not bad(item)]"""),
      Rule('Exhaust or close generators that hold resources.', 'Contextlib and `closing` help.', 'Suggestion', None, """# bad  -  leave a generator holding a file open\n# good  -  wrap in context manager that closes"""),
      Rule('Prefer stdlib iterators (`itertools`) over hand-rolled index arithmetic.', 'Index loops hide off-by-ones.', 'Suggestion', None, """# bad\ni = 0\nwhile i < len(items):\n  ...\n  i += 1\n\n# good\nfor item in items:\n  ..."""),
      Rule('Return iterators from public APIs only when streaming is part of the contract; otherwise return concrete collections.', 'Callers often need `len` and multiple passes.', 'Suggestion', None, """# bad  -  returns mysterious generator from a small in-memory API\n# good  -  list[User] for small results; Iterator for streams"""),
      Rule('Do not implement `__iter__` that returns `self` unless the object is a single-pass iterator.', 'Reusable iterables should return a fresh iterator.', 'Suggestion', None, """# bad  -  container exhausted after one for-loop\n# good  -  __iter__ returns iter(self._items)"""),
      Rule('Use generator expressions for one-shot pipelines; use lists when you need reuse.', 'Genexps are lazy and single-pass.', 'Suggestion', None, """# bad\nrows = (normalize(r) for r in raw)\nfirst = list(rows)\nsecond = list(rows)  # empty\n\n# good\nrows = [normalize(r) for r in raw]"""),
      Rule('Avoid `next()` without a default when emptiness is expected.', 'Catching `StopIteration` at call sites is noisy.', 'Suggestion', None, """# bad\nitem = next(iterator)\n\n# good\nitem = next(iterator, None)"""),
      Rule('Name generator functions as verbs that imply streaming (`iter_`, `walk_`, `stream_`).', 'Names that look eager surprise callers.', 'Suggestion', None, """# bad\ndef users() -> Iterator[User]:\n  ...\n\n# good\ndef iter_users() -> Iterator[User]:\n  ..."""),
    ),
  )

  write_chapter(
    '15-comprehensions.md',
    'Comprehensions',
    f"""Comprehensions are fine when they stay readable.
[pyguide §2.7]({PY}#s2.7-list_comprehensions) rejects complex ones.""",
    'Comprehension complexity is **Suggestion**.',
    _r(
      Rule('Keep comprehensions to one or two clauses; escalate to loops when logic nests.', 'Dense comprehensions hide bugs.', 'Suggestion', None, """# bad\nresult = [f(x, y) for x in xs if p(x) for y in ys if q(x, y) if r(y)]\n\n# good  -  for-loops with names"""),
      Rule('Prefer comprehensions over `map`/`filter` with lambdas for simple transforms.', 'Comprehensions are the language-native form.', 'Suggestion', None, """# bad\nlist(map(lambda x: x.strip(), rows))\n\n# good\n[row.strip() for row in rows]"""),
      Rule('Use dict/set comprehensions instead of loops that build empty collections.', 'They state intent in one expression.', 'Suggestion', None, """# bad\nindex = {}\nfor user in users:\n  index[user.id] = user\n\n# good\nindex = {user.id: user for user in users}"""),
      Rule('Do not put side effects inside comprehensions.', 'Comprehensions are for building values.', 'Suggestion', None, """# bad\n[save(user) for user in users]\n\n# good\nfor user in users:\n  save(user)"""),
      Rule('Prefer generator expressions when feeding a single consumer.', 'Avoid allocating an intermediate list.', 'Suggestion', None, """# bad\nsum([value for value in values if value > 0])\n\n# good\nsum(value for value in values if value > 0)"""),
      Rule('Name complex predicates as functions before using them in a comprehension.', 'Inline `if` soups are unreadable.', 'Suggestion', None, """# bad\n[u for u in users if u.active and u.role != 'guest' and u.email]\n\n# good\n[u for u in users if is_billable(u)]"""),
      Rule('Avoid walrus-heavy comprehensions unless the assignment clearly helps.', 'Nested `:=` is a review tax.', 'Suggestion', None, """# bad  -  multiple := in one comprehension\n# good  -  loop with named temps"""),
      Rule('Do not use comprehensions to emulate `any`/`all` with side effects.', 'Use `any`/`all` for predicates.', 'Suggestion', None, """# bad\nif [1 for x in xs if pred(x)]:\n  ...\n\n# good\nif any(pred(x) for x in xs):\n  ..."""),
      Rule('Keep conditionals in comprehensions as filters, not as ternary value logic trees.', 'Complex value ternaries belong in helper functions.', 'Suggestion', None, """# bad\n[a if c else b if d else e for x in xs]\n\n# good\n[choose(x) for x in xs]"""),
      Rule('Prefer unpacking clarity over clever nested comprehensions for matrices.', 'Nested loops are clearer for 2D transforms.', 'Suggestion', None, """# bad  -  2D comprehension with conditionals\n# good  -  nested for-loops"""),
      Rule('Do not mutate the iterated collection inside a comprehension filter.', 'Same hazard as iterator mutation.', 'Suggestion', None, """# bad  -  filter calls method that mutates source\n# good  -  pure predicate"""),
      Rule('Use comprehensions for data shaping; use pandas/SQL/polars for heavy tabular work.', 'Python loops over millions of rows are the wrong tool.', 'Suggestion', None, """# bad  -  nested comprehensions over huge CSV\n# good  -  vectorized tool or DB query"""),
    ),
  )

  write_chapter(
    '16-strings.md',
    'Strings',
    f"""String formatting and logging interact.
[pyguide §3.10]({PY}#s3.10-strings) and [§3.10.1]({PY}#s3.10.1-logging) matter.""",
    '`F541` (f-string without placeholders) is **Violation**. Other string '
    'rules are **Suggestion**.',
    _r(
      Rule('Prefer f-strings for eager formatting; use `%`/`extra=` for logging laziness.', 'Logging should not format if the line is filtered out.', 'Suggestion', None, """# bad\nlogger.info(f'user={user_id} failed')\n\n# good\nlogger.info('user=%s failed', user_id)"""),
      Rule('Do not write f-strings without placeholders.', 'They are pointless string literals. `F541`.', 'Violation', 'F541', """# bad\nmsg = f'hello'\n\n# good\nmsg = 'hello'"""),
      Rule('Use single quotes per house style; reserve doubles to avoid escapes.', 'Matches `ruff format` quote-style.', 'Violation', 'ruff format', """# bad\nname = \"Ada\"\n\n# good\nname = 'Ada'"""),
      Rule('Prefer `str.removeprefix` / `removesuffix` over brittle slices.', 'Slices break when the prefix is absent.', 'Suggestion', None, """# bad\nvalue = text[4:] if text.startswith('the ') else text\n\n# good\nvalue = text.removeprefix('the ')"""),
      Rule('Do not concatenate many strings with `+` in a loop; use `join` or a list.', 'Quadratic behavior appears under load.', 'Suggestion', None, """# bad\nout = ''\nfor part in parts:\n  out += part\n\n# good\nout = ''.join(parts)"""),
      Rule('Keep user-facing error messages clear; keep logs structured.', f'[pyguide §3.10.2]({PY}#s3.10.2-error-messages).', 'Suggestion', None, """# bad\nraise ValueError('err')\n\n# good\nraise ValueError('order_id must be a non-empty string')"""),
      Rule('Use raw strings for regexes.', 'Escaping hell is optional.', 'Suggestion', None, """# bad\npattern = '\\\\d+'\n\n# good\npattern = r'\\d+'"""),
      Rule('Normalize newlines and strip edges at trust boundaries.', 'Do not sprinkle `.strip()` randomly deep in core logic.', 'Suggestion', None, """# bad  -  strip in five helpers\n# good  -  normalize once when reading input"""),
      Rule('Avoid `str.encode` defaults surprises; be explicit with UTF-8.', 'Explicit encodings survive locale differences.', 'Suggestion', None, """# bad\ndata = text.encode()\n\n# good\ndata = text.encode('utf-8')"""),
      Rule('Do not use string exceptions or stringly typed enums; use Enum/Literal.', 'See chapters 18-19.', 'Suggestion', None, """# bad\nstatus = 'ok'\n\n# good\nstatus = Status.OK"""),
      Rule('Prefer `textwrap.dedent` for multiline literals embedded in code.', 'Keeps indentation readable under 2-space house style.', 'Suggestion', None, """# bad  -  weird margins in SQL strings\n# good\nsql = dedent('''\n  select 1\n  ''')"""),
      Rule('Never build SQL/HTML with f-strings from user input.', 'Use parameters / templates to avoid injection.', 'Suggestion', None, """# bad\ncur.execute(f'select * from users where id = \\'{user_id}\\'')\n\n# good\ncur.execute('select * from users where id = %s', (user_id,))"""),
    ),
  )

  write_chapter(
    '17-collections.md',
    'Collections',
    f"""Prefer the right collection and the abstract type at boundaries.
[pyguide §2.8]({PY}#s2.8-default-iterators-and-operators) encourages
idiomatic membership and iteration.""",
    'Collection choices are **Suggestion**. `F601`/`F602` catch repeated dict keys.',
    _r(
      Rule('Annotate returns as `list`/`dict` when concrete; accept `Sequence`/`Mapping` as inputs.', 'Widened inputs, precise outputs.', 'Suggestion', None, """# bad\ndef ids(users: list[User]) -> list[str]:\n  return [u.id for u in users]\n\n# good\ndef ids(users: Sequence[User]) -> list[str]:\n  return [u.id for u in users]"""),
      Rule('Use `in` for membership, not manual loops.', 'Idiomatic and clearer.', 'Suggestion', None, """# bad\nfound = False\nfor x in items:\n  if x == target:\n    found = True\n\n# good\nfound = target in items"""),
      Rule('Prefer `dict` insertion order (3.7+) over `OrderedDict` unless you need its extras.', 'OrderedDict is rarely required now.', 'Suggestion', None, """# bad  -  OrderedDict by habit\n# good  -  plain dict"""),
      Rule('Use `setdefault` / `defaultdict` carefully; prefer clarity over cleverness.', 'Hidden inserts surprise readers.', 'Suggestion', None, """# bad  -  dense setdefault chains\n# good  -  defaultdict or explicit if/else"""),
      Rule('Do not use a list as a queue; use `collections.deque`.', 'List pop(0) is O(n).', 'Suggestion', None, """# bad\nqueue = []\nqueue.pop(0)\n\n# good\nqueue: deque[str] = deque()\nqueue.popleft()"""),
      Rule('Catch duplicate literal keys in dict displays.', '`F601` flags repeated keys.', 'Violation', 'F601', """# bad\nconfig = {'host': 'a', 'host': 'b'}\n\n# good\nconfig = {'host': 'b'}"""),
      Rule('Prefer tuples for fixed-length records; lists for homogeneous sequences.', 'Tuples signal immutability of shape.', 'Suggestion', None, """# bad\npoint = [1, 2]\n\n# good\npoint = (1, 2)"""),
      Rule('Use `enumerate` instead of `range(len(...))`.', 'Cleaner and harder to desync.', 'Suggestion', None, """# bad\nfor i in range(len(items)):\n  print(i, items[i])\n\n# good\nfor i, item in enumerate(items):\n  print(i, item)"""),
      Rule('Use `zip(..., strict=True)` on 3.10+ when lengths must match.', 'Silent truncation hides bugs.', 'Suggestion', None, """# bad\nfor a, b in zip(left, right):\n  ...\n\n# good\nfor a, b in zip(left, right, strict=True):\n  ..."""),
      Rule('Prefer `collections.Counter` for tallying.', 'Hand-rolled counters reimplement edge cases.', 'Suggestion', None, """# bad\ncounts: dict[str, int] = {}\nfor item in items:\n  counts[item] = counts.get(item, 0) + 1\n\n# good\ncounts = Counter(items)"""),
      Rule('Do not mutate dicts while iterating keys; iterate `list(keys)` or build a new dict.', 'RuntimeError awaits.', 'Suggestion', None, """# bad\nfor key in data:\n  if stale(key):\n    del data[key]\n\n# good\ndata = {k: v for k, v in data.items() if not stale(k)}"""),
      Rule('Expose read-only views (`MappingProxyType` / tuples) when sharing internal collections.', 'Prevents accidental caller mutation.', 'Suggestion', None, """# bad\nreturn self._items  # mutable alias\n\n# good\nreturn tuple(self._items)"""),
    ),
  )

  write_chapter(
    '18-pattern-matching.md',
    'Pattern Matching',
    """`match` / `case` (PEP 634+) is the structured alternative to long
`if/elif` type trees. Use it for closed shapes; do not use it as a fancy
switch for booleans.""",
    'Pattern-matching style is **Suggestion**.',
    _r(
      Rule('Use `match` for structured destructuring of tagged shapes, not for simple equality chains of primitives unless clarity wins.', 'Overusing match for booleans hurts.', 'Suggestion', None, """# bad\nmatch ready:\n  case True:\n    start()\n  case False:\n    stop()\n\n# good\nif ready:\n  start()\nelse:\n  stop()"""),
      Rule('Prefer sealed-like unions (`A | B`) with match over `isinstance` ladders when you control the types.', 'Exhaustiveness is easier to see.', 'Suggestion', None, """# bad  -  long isinstance chain\n# good  -  match event with case Created()/case Updated()"""),
      Rule('Use capture names carefully; avoid bare names that always match.', 'A single bare name case is a catch-all.', 'Suggestion', None, """# bad\nmatch value:\n  case x:\n    return x\n\n# good\nmatch value:\n  case int() as n:\n    return n\n  case _:\n    raise TypeError(type(value))"""),
      Rule('Put `|` or-patterns for shared handling; duplicate case bodies are a smell.', 'Or-patterns keep handling unified.', 'Suggestion', None, """# bad  -  duplicated bodies\n# good\ncase 401 | 403:\n  raise AuthError()"""),
      Rule('Use guards (`case x if ...`) sparingly; complex guards belong in helpers.', 'Guards can hide the shape being matched.', 'Suggestion', None, """# bad  -  giant guard expression\n# good  -  case User() as user if is_billable(user):"""),
      Rule('Prefer matching mapping keys explicitly over matching entire dicts loosely.', 'Precise keys document required payload shape.', 'Suggestion', None, """# bad\ncase {'type': t, **rest}:\n  ...\n\n# good\ncase {'type': 'order', 'id': str() as order_id}:\n  ..."""),
      Rule('Keep match statements exhaustive for domain unions; include `case _` only at boundaries.', 'Silent `_` swallows new variants.', 'Suggestion', None, """# bad  -  case _ everywhere in core logic\n# good  -  case _ at the HTTP edge with logging"""),
      Rule('Do not match on Pydantic models as if they were dicts unless you convert deliberately.', 'Model instances use class patterns.', 'Suggestion', None, """# bad  -  case {'id': ...} on a BaseModel instance\n# good  -  case Order(id=order_id):"""),
      Rule('Avoid deeply nested matches; extract functions per variant.', 'Nested matches recreate callback hell.', 'Suggestion', None, """# bad  -  match inside match inside match\n# good  -  dispatch to handle_created/handle_updated"""),
      Rule('Use class patterns with keyword attributes for dataclasses and similar.', 'Positional class patterns are brittle under field reordering.', 'Suggestion', None, """# bad\ncase Point(x, y):\n  ...\n\n# good\ncase Point(x=x, y=y):\n  ..."""),
      Rule('Do not use match to reinvent polymorphism when a method on the type is clearer.', 'OOP dispatch still wins for open sets.', 'Suggestion', None, """# bad  -  match on type to call methods\n# good  -  animal.speak()"""),
      Rule('Document intentional fall-through-like shared handling with or-patterns, not by stacking empty cases.', 'Empty cases are easy to misread.', 'Suggestion', None, """# bad\ncase 401:\n  ...\ncase 403:\n  ...  # copy-paste\n\n# good\ncase 401 | 403:\n  raise AuthError()"""),
    ),
  )

  write_chapter(
    '19-enums.md',
    'Enums',
    """Enums replace stringly-typed status codes. Prefer `enum.Enum` /
`StrEnum` (3.11+) for closed sets of values.""",
    'Enum style is **Suggestion**.',
    _r(
      Rule('Use enums for closed sets of values that appear in APIs and DB columns.', 'Typos in string statuses become silent bugs.', 'Suggestion', None, """# bad\nif status == 'acive':\n  ...\n\n# good\nif status is Status.ACTIVE:\n  ..."""),
      Rule('Prefer `StrEnum` when values serialize to strings (JSON, CSV).', 'Keeps wire format and type safety aligned.', 'Suggestion', None, """# bad\nclass Status(Enum):\n  ACTIVE = 'active'\n\n# good\nclass Status(StrEnum):\n  ACTIVE = 'active'"""),
      Rule('Compare enums with `is` for singletons, or equality when values matter.', 'Identity works for enum members.', 'Suggestion', None, """# bad\nif status == 'active':\n  ...\n\n# good\nif status is Status.ACTIVE:\n  ..."""),
      Rule('Do not add mutable state to enum members.', 'Enum members are singletons.', 'Suggestion', None, """# bad  -  member attributes that change at runtime\n# good  -  keep enums as pure values"""),
      Rule('Use `enum.auto()` when values are opaque; use explicit values when they are part of a protocol.', 'Wire formats need stable values.', 'Suggestion', None, """# bad  -  auto() for HTTP-facing codes\n# good  -  explicit string/int values for APIs"""),
      Rule('Namespace related values in one Enum rather than many module constants.', 'Discoverability beats scattered constants.', 'Suggestion', None, """# bad\nSTATUS_ACTIVE = 'active'\nSTATUS_INACTIVE = 'inactive'\n\n# good\nclass Status(StrEnum):\n  ACTIVE = 'active'\n  INACTIVE = 'inactive'"""),
      Rule('Export enums from domain modules, not from route modules.', 'Routes should import domain types.', 'Suggestion', None, """# bad  -  Status defined in router.py\n# good  -  Status in domain/orders.py"""),
      Rule('Teach Pydantic/FastAPI to use enums directly on fields.', 'OpenAPI then shows allowed values.', 'Suggestion', None, """# bad\nstatus: str\n\n# good\nstatus: Status"""),
      Rule('Avoid `IntEnum` unless an external integer protocol requires it.', 'Ints invite accidental arithmetic.', 'Suggestion', None, """# bad  -  IntEnum for roles\n# good  -  StrEnum for roles"""),
      Rule('Provide a parse helper that raises domain errors for unknown values.', 'Raw `Status(value)` tracebacks are harsh at boundaries.', 'Suggestion', None, """# bad\nStatus(raw)\n\n# good\ndef parse_status(raw: str) -> Status:\n  try:\n    return Status(raw)\n  except ValueError as err:\n    raise ValidationError(f'unknown status {raw!r}') from err"""),
      Rule('Do not iterate enums for authorization logic without tests for new members.', 'Adding a member can widen access accidentally.', 'Suggestion', None, """# bad  -  for status in Status: allow()\n# good  -  frozenset of allowed statuses tested explicitly"""),
      Rule('Keep enum names `UPPER_SNAKE` members and `CapWords` class names.', 'Matches pyguide naming.', 'Suggestion', None, """# bad\nclass status(Enum):\n  Active = 'active'\n\n# good\nclass Status(StrEnum):\n  ACTIVE = 'active'"""),
    ),
  )

  write_chapter(
    '20-dates-and-times.md',
    'Dates & Times',
    """Always be explicit about timezones. Prefer aware datetimes and store UTC.""",
    'Datetime rules are **Suggestion** (no `DTZ` enabled in shipped select).',
    _r(
      Rule('Prefer timezone-aware datetimes; ban naive datetimes at boundaries.', 'Naive datetimes are ambiguous.', 'Suggestion', None, """# bad\ndatetime.now()\n\n# good\ndatetime.now(UTC)"""),
      Rule('Store and transmit UTC; convert to local zones only at the UI edge.', 'Server-local time is not a format.', 'Suggestion', None, """# bad  -  store America/New_York in DB\n# good  -  store UTC, convert on display"""),
      Rule('Use `datetime.UTC` (3.11+) instead of `timezone.utc` in new code.', 'Shorter and canonical.', 'Suggestion', None, """# bad\nfrom datetime import timezone\ndatetime.now(timezone.utc)\n\n# good\nfrom datetime import UTC\ndatetime.now(UTC)"""),
      Rule('Do not use `datetime.utcnow()`; it returns naive UTC.', 'Deprecated footgun.', 'Suggestion', None, """# bad\ndatetime.utcnow()\n\n# good\ndatetime.now(UTC)"""),
      Rule('Prefer `date` when the value has no time component.', 'Fake midnights create DST bugs.', 'Suggestion', None, """# bad\nbirthday = datetime(1990, 1, 1, tzinfo=UTC)\n\n# good\nbirthday = date(1990, 1, 1)"""),
      Rule('Use `timedelta` for durations; do not invent second-int APIs without units in the name.', 'Units belong in names (`timeout_s`).', 'Suggestion', None, """# bad\nsleep(5)  # minutes or seconds?\n\n# good\nsleep(timedelta(seconds=5).total_seconds())"""),
      Rule('Serialize with ISO 8601 (`datetime.isoformat` / `date.fromisoformat`).', 'Custom formats break clients.', 'Suggestion', None, """# bad\nts.strftime('%m/%d/%Y')\n\n# good\nts.isoformat()"""),
      Rule('Parse external timestamps with explicit zone handling.', 'Reject ambiguous inputs.', 'Suggestion', None, """# bad  -  assume local\n# good  -  fromisoformat and require tzinfo"""),
      Rule('Do not compare aware and naive datetimes.', 'Python raises (or worse, in older code paths).', 'Suggestion', None, """# bad\naware > naive\n\n# good  -  normalize both sides"""),
      Rule('Use monotonic clocks (`time.monotonic`) for measuring durations.', 'Wall clocks jump.', 'Suggestion', None, """# bad\nstart = time.time()\n...\nelapsed = time.time() - start\n\n# good\nstart = time.monotonic()\n...\nelapsed = time.monotonic() - start"""),
      Rule('Keep cron/business calendars in well-tested helpers; do not sprinkle DST math.', 'Calendar math is a library problem.', 'Suggestion', None, """# bad  -  hand-rolled DST adjust\n# good  -  zoneinfo / trusted library"""),
      Rule('In Pydantic models, prefer `datetime` fields with aware values and configure JSON encoders consistently.', 'See chapter 35.', 'Suggestion', None, """# bad  -  str timestamps mixed with datetime fields\n# good  -  datetime fields throughout"""),
    ),
  )

  write_chapter(
    '21-truthiness-and-comparisons.md',
    'Truthiness & Comparisons',
    f"""[pyguide §2.14]({PY}#s2.14-truefalse-evaluations) covers boolean
evaluations. Combine with Ruff `E711`/`E712`.""",
    '`E711`, `E712`, `E721`, `F632` are **Violation** where applicable.',
    _r(
      Rule('Use `is` / `is not` for `None` comparisons.', 'Identity is correct for None.', 'Violation', 'E711', """# bad\nif value == None:\n  ...\n\n# good\nif value is None:\n  ..."""),
      Rule('Do not compare booleans with `== True`/`== False`.', 'Use truthiness directly.', 'Violation', 'E712', """# bad\nif ready == True:\n  ...\n\n# good\nif ready:\n  ..."""),
      Rule('Use `isinstance` instead of comparing `type(x) is`.', '`E721` flags type comparisons that break subclasses.', 'Violation', 'E721', """# bad\nif type(value) is list:\n  ...\n\n# good\nif isinstance(value, list):\n  ..."""),
      Rule('Prefer explicit `is None` when empty containers are valid data.', 'Truthiness collapses `[]` and `None`.', 'Suggestion', None, """# bad\nif not items:\n  return  # cannot tell None from []\n\n# good\nif items is None:\n  return\nif not items:\n  return"""),
      Rule('Do not use `==` to compare singletons like `True`/`False`/`None`.', 'Use identity.', 'Suggestion', None, """# bad\nif flag == True:\n  ...\n\n# good\nif flag:\n  ..."""),
      Rule('Avoid chained comparisons that mix incompatible types.', 'They can hide TypeErrors.', 'Suggestion', None, """# bad\nif a < b < '9':\n  ...\n\n# good  -  ensure comparable types"""),
      Rule('Use `math.isclose` for floats.', 'Exact equality is brittle.', 'Suggestion', None, """# bad\nif total == 0.3:\n  ...\n\n# good\nif math.isclose(total, 0.3):\n  ..."""),
      Rule('Prefer `x in options` over long `or` chains.', 'Membership scales.', 'Suggestion', None, """# bad\nif x == 1 or x == 2 or x == 3:\n  ...\n\n# good\nif x in {1, 2, 3}:\n  ..."""),
      Rule('Do not write `if x != None` via equality.', 'Same as E711.', 'Violation', 'E711', """# bad\nif x != None:\n  ...\n\n# good\nif x is not None:\n  ..."""),
      Rule('Treat unknown objects as opaque; narrow with `isinstance` before attribute access.', 'EAFP still needs intentional narrowing in typed code.', 'Suggestion', None, """# bad\nvalue.id  # value: object\n\n# good\nif isinstance(value, User):\n  return value.id"""),
      Rule('Avoid `not not x` / double negation cleverness.', 'Use `bool(x)` if you need a real bool.', 'Suggestion', None, """# bad\nflag = not not value\n\n# good\nflag = bool(value)"""),
      Rule('Do not use `is` for string/int equality.', 'Identity for interning is not a contract.', 'Suggestion', None, """# bad\nif name is 'Ada':\n  ...\n\n# good\nif name == 'Ada':\n  ..."""),
    ),
  )

  write_chapter(
    '22-properties-and-descriptors.md',
    'Properties & Descriptors',
    f"""[pyguide §2.13]({PY}#s2.13-properties) defines when properties are
appropriate. Descriptors are rare outside frameworks.""",
    'Property guidance is **Suggestion**.',
    _r(
      Rule('Use `@property` for cheap derived values.', 'Hidden IO in properties surprises.', 'Suggestion', None, """# bad\n@property\ndef users(self) -> list[User]:\n  return self._db.fetch_users()\n\n# good\ndef load_users(self) -> list[User]:\n  return self._db.fetch_users()"""),
      Rule('Prefer methods when computation is non-trivial or cached state is involved.', 'Caches need explicit invalidation APIs.', 'Suggestion', None, """# bad  -  property with LRU side effects\n# good  -  get_report() method"""),
      Rule('Do not invent setters that silently coerce invalid data.', 'Raise instead.', 'Suggestion', None, """# bad\n@email.setter\ndef email(self, value: str) -> None:\n  self._email = value or 'unknown'\n\n# good  -  validate and raise"""),
      Rule('Keep descriptors for framework/library authors, not app business logic.', 'Descriptors are hard to reason about in apps.', 'Suggestion', None, """# bad  -  custom descriptor for order total\n# good  -  function or property"""),
      Rule('Document property side effects if any exist (they usually should not).', 'Surprises belong in method names.', 'Suggestion', None, """# bad  -  silent lazy remote fetch\n# good  -  method named fetch_"""),
      Rule('Prefer dataclass fields / Pydantic fields over hand-rolled descriptor validation in apps.', 'Ecosystem tools already solve this.', 'Suggestion', None, """# bad  -  FieldDescriptor for every attribute\n# good  -  pydantic BaseModel"""),
      Rule('Avoid properties that mutate other properties as a chain reaction.', 'Setter cascades are debugging traps.', 'Suggestion', None, """# bad  -  setting width mutates height mutates area mutates width\n# good  -  explicit recompute method"""),
      Rule('Expose read-only attributes with `@property` (no setter) instead of public fields you hope nobody writes.', 'Makes intent clear.', 'Suggestion', None, """# bad\nself.id = value  # public\n\n# good\n@property\ndef id(self) -> str:\n  return self._id"""),
      Rule('Do not use properties to paper over poor naming of methods.', 'Verbs should be methods.', 'Suggestion', None, """# bad\n@property\ndef save(self):\n  ...\n\n# good\ndef save(self) -> None:\n  ..."""),
      Rule('Cache with `functools.cached_property` only for immutable instances.', 'Mutable objects + cached_property stale easily.', 'Suggestion', None, """# bad  -  cached_property on mutable entity\n# good  -  cached_property on frozen/dataclass(frozen=True)"""),
      Rule('Keep property implementations short enough to read inline.', 'Long properties should be methods.', 'Suggestion', None, """# bad  -  40-line property\n# good  -  method"""),
      Rule('For FastAPI response models, expose data as fields, not as properties that hit the DB during serialization.', 'Serialization-time IO is a footgun.', 'Suggestion', None, """# bad  -  @property on model triggers lazy load during response\n# good  -  eager load / compute before returning"""),
    ),
  )

  write_chapter(
    '23-decorators.md',
    'Decorators',
    f"""[pyguide §2.17]({PY}#s2.17-function-and-method-decorators) covers
decorator discipline. Preserve signatures with `functools.wraps`.""",
    'Decorator rules are **Suggestion**.',
    _r(
      Rule('Always use `@functools.wraps(fn)` in decorator wrappers.', 'Otherwise tracebacks and OpenAPI names break.', 'Suggestion', None, """# bad\ndef deco(fn):\n  def wrapper(*args, **kwargs):\n    return fn(*args, **kwargs)\n  return wrapper\n\n# good\ndef deco(fn):\n  @wraps(fn)\n  def wrapper(*args, **kwargs):\n    return fn(*args, **kwargs)\n  return wrapper"""),
      Rule('Prefer ParamSpec/`Concatenate` when typing decorators.', 'Keeps FastAPI routes typed.', 'Suggestion', None, """# bad  -  wrapper -> Callable[..., Any]\n# good  -  ParamSpec typed decorator"""),
      Rule('Keep decorators tiny and composable; avoid mega-decorators that auth+log+retry+trace.', 'Split cross-cutting concerns.', 'Suggestion', None, """# bad  -  @swiss_army\n# good  -  @retry @traced @require_auth"""),
      Rule('Do not use decorators to mutate global registries at import time without an explicit app wiring path.', 'Import side effects hurt tests.', 'Suggestion', None, """# bad  -  @register_handler on import\n# good  -  explicit router.includes"""),
      Rule('Preserve async-ness: async wrappers for async callables.', 'Awaiting a sync wrapper is a bug.', 'Suggestion', None, """# bad  -  sync wrapper around async def\n# good  -  async def wrapper with await fn()"""),
      Rule('Document decorator semantics (pre/post, exception policy) in the decorator docstring.', 'Call sites cannot see the wrapper body.', 'Suggestion', None, """# bad  -  undocumented retry policy\n# good  -  docstring states attempts/backoff"""),
      Rule('Avoid stacking more than three decorators without a strong reason.', 'Order becomes unknowable.', 'Suggestion', None, """# bad  -  six stacked decorators\n# good  -  combine or simplify middleware"""),
      Rule('Prefer FastAPI dependencies over custom decorators for request-scoped auth/DB.', 'Dependencies are testable and visible in signatures.', 'Suggestion', None, """# bad  -  @auth_required hiding Depends\n# good  -  user: Annotated[User, Depends(require_user)]"""),
      Rule('Do not swallow exceptions inside decorators unless that is the product behavior.', 'Silent failures cross every call site.', 'Suggestion', None, """# bad  -  except Exception: return None in wrapper\n# good  -  let it raise; log at boundary"""),
      Rule('Use class decorators sparingly; prefer functions or metaclasses only when required.', 'Class decorators obscure construction.', 'Suggestion', None, """# bad  -  @register on every model class\n# good  -  explicit registry.add(Model)"""),
      Rule('Ensure decorators work on methods (mind `self`/`cls`).', 'Broken method decorators show up late.', 'Suggestion', None, """# bad  -  wrapper loses self\n# good  -  tests cover instance method decoration"""),
      Rule('Prefer context managers for temporary state over decorators that mutate process globals.', 'Globals + decorators race.', 'Suggestion', None, """# bad  -  @use_timezone mutates global TZ\n# good  -  with timezone_context(...):"""),
    ),
  )

  write_chapter(
    '24-concurrency.md',
    'Concurrency',
    f"""[pyguide §2.18]({PY}#s2.18-threading) is brief: threads need care.
Prefer asyncio for IO-bound FastAPI services; use threads/processes
deliberately for blocking or CPU work.""",
    'Concurrency guidance is **Suggestion**.',
    _r(
      Rule('Do not share mutable state across threads without locks or queues.', 'Races are silent.', 'Suggestion', None, """# bad  -  global counter += 1 from threads\n# good  -  queue workers or asyncio"""),
      Rule('Prefer `concurrent.futures` over raw `ThreadPoolExecutor` management when bridging blocking IO.', 'Clear lifecycle.', 'Suggestion', None, """# bad  -  hand-managed threads\n# good  -  asyncio.to_thread / run_in_executor"""),
      Rule('Never call blocking IO directly inside async request handlers.', 'See chapter 31.', 'Suggestion', None, """# bad\nasync def get():\n  return Path('x').read_text()\n\n# good\nasync def get():\n  return await asyncio.to_thread(Path('x').read_text)"""),
      Rule('Use processes (or native extensions) for CPU-bound work, not threads, because of the GIL.', 'Threads will not speed pure Python CPU loops.', 'Suggestion', None, """# bad  -  ThreadPool for CPU crunch\n# good  -  ProcessPoolExecutor or a worker service"""),
      Rule('Give every thread/task a clear owner and shutdown path.', 'Orphan workers hang exits.', 'Suggestion', None, """# bad  -  fire thread and forget\n# good  -  lifespan starts/stops workers"""),
      Rule('Prefer immutable messages over shared objects between workers.', 'Queues of values beat shared graphs.', 'Suggestion', None, """# bad  -  pass live ORM object across threads\n# good  -  pass ids/DTOs"""),
      Rule('Do not ignore `threading`/`asyncio` cancellation semantics when shutting down.', 'Clean flush matters.', 'Suggestion', None, """# bad  -  os._exit from worker\n# good  -  cooperative shutdown event"""),
      Rule('Avoid `time.sleep` in async code; use `asyncio.sleep`.', 'Sleep blocks the event loop.', 'Suggestion', None, """# bad\nawaitable = time.sleep(1)\n\n# good\nawait asyncio.sleep(1)"""),
      Rule('Document thread-safety of public helpers.', 'Callers cannot guess.', 'Suggestion', None, """# bad  -  silent non-thread-safe cache\n# good  -  docstring: not thread-safe"""),
      Rule('Prefer one concurrency model per service: asyncio-first for FastAPI.', 'Mixing models needs explicit bridges.', 'Suggestion', None, """# bad  -  threads + asyncio + processes ad hoc\n# good  -  asyncio core; to_thread at edges"""),
      Rule('Protect caches with locks or use asyncio-safe structures.', 'Torn reads produce ghosts.', 'Suggestion', None, """# bad  -  dict cache from many tasks without care\n# good  -  dedicated cache with locking or Redis"""),
      Rule('Do not daemonize threads to avoid writing shutdown code.', 'Daemon threads drop work on exit.', 'Suggestion', None, """# bad  -  Thread(daemon=True) for billing\n# good  -  managed worker with flush"""),
    ),
  )

  write_chapter(
    '25-logging.md',
    'Logging',
    f"""[pyguide §3.10.1]({PY}#s3.10.1-logging) requires lazy interpolation for
logging. Prefer structured logs in services.""",
    'Logging style is **Suggestion** (no `G`/`LOG` rules enabled).',
    _r(
      Rule('Use `logging` (or a structured wrapper) rather than `print` for diagnostics.', 'Print bypasses levels and aggregation.', 'Suggestion', None, """# bad\nprint('user', user_id)\n\n# good\nlogger.info('user_login', extra={'user_id': user_id})"""),
      Rule('Use lazy %-style or structured fields; avoid eager f-strings in hot log lines.', 'Formatting cost matters under load.', 'Suggestion', None, """# bad\nlogger.info(f'user={user_id}')\n\n# good\nlogger.info('user=%s', user_id)"""),
      Rule('Name loggers after modules: `logger = logging.getLogger(__name__)`.', 'Hierarchy enables filtering.', 'Suggestion', None, """# bad\nlogger = logging.getLogger('app')\n\n# good\nlogger = logging.getLogger(__name__)"""),
      Rule('Log errors with `logger.exception` inside except blocks.', 'Captures stack traces.', 'Suggestion', None, """# bad\nexcept Exception as err:\n  logger.error(str(err))\n\n# good\nexcept Exception:\n  logger.exception('handler failed')"""),
      Rule('Never log secrets, tokens, or raw PII.', 'Redact at the source.', 'Suggestion', None, """# bad\nlogger.info('token=%s', token)\n\n# good\nlogger.info('token_fingerprint=%s', hash_token(token))"""),
      Rule('Prefer structured key/value fields over prose paragraphs.', 'Queryable logs beat novels.', 'Suggestion', None, """# bad\nlogger.info(f'User {user} did {action} at {ts}')\n\n# good\nlogger.info('user_action', extra={'user_id': user, 'action': action})"""),
      Rule('Configure logging in one place (lifespan / dictConfig), not in every module.', 'Module-level basicConfig races.', 'Suggestion', None, """# bad  -  basicConfig in library imports\n# good  -  configure in create_app/lifespan"""),
      Rule('Use appropriate levels: debug for diagnostics, info for lifecycle, warning for recoverable, error for failures.', 'Everything-as-info is useless.', 'Suggestion', None, """# bad  -  logger.info for stack traces\n# good  -  logger.exception for failures"""),
      Rule('Include request/correlation ids in context for FastAPI services.', 'Otherwise incidents are unsearchable.', 'Suggestion', None, """# bad  -  log lines with no request id\n# good  -  bind request_id in middleware/contextvar"""),
      Rule('Do not catch-and-log-and-ignore unless the error is truly optional.', 'Logged-and-dropped errors still drop work.', 'Suggestion', None, """# bad\nexcept Exception:\n  logger.exception('ignored')\n\n# good  -  re-raise or return explicit fallback"""),
      Rule('Avoid logging entire request bodies by default.', 'Size and PII hazards.', 'Suggestion', None, """# bad  -  logger.debug(await request.body())\n# good  -  log route, user, latency, status"""),
      Rule('Test that failure paths emit the log record you claim in runbooks.', 'Unlogged failures waste oncall.', 'Suggestion', None, """# bad  -  assume logger.exception exists\n# good  -  caplog assertion in unit test"""),
    ),
  )

  write_chapter(
    '26-testing.md',
    'Testing',
    """pytest is the default test runner. Prefer fast unit tests; use
httpx/`TestClient` / `AsyncClient` for FastAPI (chapter 38).""",
    'Testing style is **Suggestion** (no `PT` enabled).',
    _r(
      Rule('Name tests `test_<behavior>_<condition>` and keep one assert-focus per test.', 'Long tests hide failures.', 'Suggestion', None, """# bad\ndef test_all():\n  ...\n\n# good\ndef test_discount_applies_for_loyalty_members():\n  ..."""),
      Rule('Prefer plain asserts with pytest; do not reinvent assertion helpers that hide diffs.', 'pytest rewrites asserts.', 'Suggestion', None, """# bad\nself.assertEqual(a, b)\n\n# good\nassert a == b"""),
      Rule('Use fixtures for arrangement; keep fixtures thin and composable.', 'God fixtures couple suites.', 'Suggestion', None, """# bad  -  fixture that builds entire prod graph\n# good  -  small fixtures assembled in tests"""),
      Rule('Do not hit real networks in unit tests; fake at Protocol boundaries.', 'Flakes are not CI.', 'Suggestion', None, """# bad  -  tests call prod HTTP\n# good  -  fake SupportsBilling"""),
      Rule('Parametrize edge cases with `@pytest.mark.parametrize`.', 'Copy-paste tests drift.', 'Suggestion', None, """# bad  -  five near-identical tests\n# good  -  parametrize inputs/expected"""),
      Rule('Mark slow/integration tests explicitly and keep default suite fast.', 'Developers skip slow unmarked suites.', 'Suggestion', None, """# bad  -  30s DB test in default path unlabeled\n# good  -  @pytest.mark.integration"""),
      Rule('Avoid testing private functions directly when public behavior covers them.', 'Private tests brittle.', 'Suggestion', None, """# bad  -  assert _normalize()\n# good  -  assert public parse() outcomes"""),
      Rule('Freeze time with a dedicated helper for time-dependent logic.', 'Sleeping in tests is banned.', 'Suggestion', None, """# bad  -  time.sleep(2)\n# good  -  freezegun/clock fixture"""),
      Rule('Prefer deterministic seeds for any randomness.', 'Flaky tests are defects.', 'Suggestion', None, """# bad  -  random.random() unseeded\n# good  -  random.Random(0)"""),
      Rule('Put shared helpers in `conftest.py` or `tests/helpers/`, not in production packages.', 'Prod must not import pytest.', 'Suggestion', None, """# bad  -  app/testing_utils.py imported by prod\n# good  -  tests/helpers/factories.py"""),
      Rule('Assert on observable outcomes, not on log text, unless logging is the product.', 'Log wording changes constantly.', 'Suggestion', None, """# bad  -  assert 'saved' in caplog.text for business rule\n# good  -  assert repository saved entity"""),
      Rule('Keep tests 2-space / single-quote consistent via Ruff; do not special-case test style.', 'Same formatter as prod.', 'Violation', 'ruff format', """# bad  -  four-space tests\n# good  -  ruff format tests too"""),
    ),
  )
