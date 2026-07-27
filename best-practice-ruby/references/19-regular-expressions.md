<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 19. Regular Expressions

Regular expressions are a sharp tool: perfect for token shapes and awful for
parsing HTML or encoding business rules as punctuation. The Ruby Style Guide
collects the rules under
[regular-expressions](https://rubystyle.guide/#regular-expressions), with
focused anchors for
[percent-r](https://rubystyle.guide/#percent-r),
[multi-line-regexes](https://rubystyle.guide/#multi-line-regexes),
[caret-and-dollar-regexp](https://rubystyle.guide/#caret-and-dollar-regexp),
[non-capturing-regexp](https://rubystyle.guide/#non-capturing-regexp),
[named captures](https://rubystyle.guide/#refer-named-regexp-captures-by-name),
[no numbered regexes](https://rubystyle.guide/#no-numbered-regexes),
[do-not-mix-named-and-numbered-captures](https://rubystyle.guide/#do-not-mix-named-and-numbered-captures),
[no-perl-regexp-last-matchers](https://rubystyle.guide/#no-perl-regexp-last-matchers),
[no-regexp-for-plaintext](https://rubystyle.guide/#no-regexp-for-plaintext),
[dont-abuse-gsub](https://rubystyle.guide/#dont-abuse-gsub),
[comment-regexes](https://rubystyle.guide/#comment-regexes), and
[regexp-string-index](https://rubystyle.guide/#regexp-string-index).

**Tool alignment:** enabled cops include `Style/RegexpLiteral`,
`Style/RedundantRegexpCharacterClass`, `Style/RedundantRegexpEscape`,
`Style/PerlBackrefs`, `Lint/AmbiguousRegexpLiteral`,
`Lint/MixedRegexpCaptureTypes`, `Lint/OutOfRangeRegexpRef`,
`Lint/RegexpAsCondition`, `Lint/UriRegexp`, `Performance/RegexpMatch`,
`Performance/RedundantMatch`, and `Performance/ConstantRegexp`.

## 19.1 Prefer `%r` for regexes that contain many `/` characters.

> Why? Escaping slashes inside `/.../` is noise.
> [percent-r](https://rubystyle.guide/#percent-r) and `Style/RegexpLiteral`
> prefer `%r{...}` when the pattern is slash-heavy (paths, URLs).
> **Violation** under the project's RegexpLiteral style.

> Enforced by: Style/RegexpLiteral.

```ruby
# bad
path = /\/users\/\d+\/posts/

# good
path = %r{/users/\d+/posts}
```

## 19.2 Prefer ordinary string methods when you are matching plaintext.

> Why? `/foo/` for a fixed substring is slower to read and often slower to
> run than `include?`, `start_with?`, or `end_with?`.
> [no-regexp-for-plaintext](https://rubystyle.guide/#no-regexp-for-plaintext)
> is the guide's rule of thumb. **Suggestion** (performance cops may also
> suggest `start_with?` / `end_with?`).

```ruby
# bad
redirect if path =~ %r{\A/admin}

# good
redirect if path.start_with?('/admin')
ok = name.include?('test')
```

## 19.3 Prefer `match?` when you only need a boolean.

> Why? `=~` and `match` allocate `MatchData` (and set `$~`).
> `Performance/RegexpMatch` prefers `match?` for predicates.
> **Violation.**

> Enforced by: Performance/RegexpMatch.

```ruby
# bad
valid = !!(email =~ EMAIL_RE)

# good
valid = EMAIL_RE.match?(email)
```

## 19.4 Prefer `string.match?(regexp)` / `regexp.match?(string)` over `string =~ regexp` for clarity.

> Why? `Performance/RedundantMatch` and modern style prefer the predicate
> form. Keep `match` when you need captures. **Violation** when the match
> result is unused.

> Enforced by: Performance/RedundantMatch.

```ruby
# bad
do_work if string =~ /pattern/

# good
do_work if string.match?(/pattern/)
```

## 19.5 Freeze or assign constant regexps that are reused; avoid rebuilding literals in hot loops.

> Why? `Performance/ConstantRegexp` wants regexps that do not depend on
> loop state to be constants (or otherwise not reconstructed each time).
> **Violation.**

> Enforced by: Performance/ConstantRegexp.

```ruby
# bad
lines.each do |line|
  next unless line.match?(/\A\d+\z/)
end

# good
INTEGER_LINE = /\A\d+\z/

lines.each do |line|
  next unless INTEGER_LINE.match?(line)
end
```

## 19.6 Use `\A` and `\z` for whole-string anchors; reserve `^` / `$` for line anchors.

> Why? `^` and `$` match at line boundaries inside multiline strings, which
> is a validation bypass classic.
> [caret-and-dollar-regexp](https://rubystyle.guide/#caret-and-dollar-regexp)
> requires `\A` / `\z` when you mean the whole string. **Suggestion.**

```ruby
# bad — passes for "evil\nemail@example.com" in multiline mode concerns
EMAIL = /^[^@]+@[^@]+$/

# good
EMAIL = /\A[^@]+@[^@]+\z/
```

## 19.7 Prefer non-capturing groups when you only need grouping.

> Why? `(?:...)` documents that the group is for precedence/quantifiers, not
> extraction. [non-capturing-regexp](https://rubystyle.guide/#non-capturing-regexp)
> keeps `$1` / named captures meaningful. **Suggestion.**

```ruby
# bad — unused capture
TOKEN = /(foo|bar)-\d+/

# good
TOKEN = /(?:foo|bar)-\d+/
```

## 19.8 Prefer named captures and refer to them by name.

> Why? Numbered captures rot when the pattern changes.
> [refer-named-regexp-captures-by-name](https://rubystyle.guide/#refer-named-regexp-captures-by-name)
> and [no-numbered-regexes](https://rubystyle.guide/#no-numbered-regexes)
> push named groups. **Suggestion.**

```ruby
# bad
if (m = path.match(%r{/users/(\d+)/posts/(\d+)}))
  user_id = m[1]
  post_id = m[2]
end

# good
PATTERN = %r{/users/(?<user_id>\d+)/posts/(?<post_id>\d+)}

if (m = PATTERN.match(path))
  user_id = m[:user_id]
  post_id = m[:post_id]
end
```

## 19.9 Do not mix named and numbered captures in one regexp.

> Why? Mixing makes MatchData indexing surprising and is easy to break.
> [do-not-mix-named-and-numbered-captures](https://rubystyle.guide/#do-not-mix-named-and-numbered-captures)
> and `Lint/MixedRegexpCaptureTypes` forbid it. **Violation.**

> Enforced by: Lint/MixedRegexpCaptureTypes.

```ruby
# bad
/\A(?<name>\w+)-(\d+)\z/

# good
/\A(?<name>\w+)-(?<id>\d+)\z/
```

## 19.10 Prefer MatchData over Perl `$1` / `$2` / `$&` globals.

> Why? Threading and nested matches make `$1` brittle.
> [no-perl-regexp-last-matchers](https://rubystyle.guide/#no-perl-regexp-last-matchers)
> and `Style/PerlBackrefs` prefer explicit MatchData. **Violation.**

> Enforced by: Style/PerlBackrefs.

```ruby
# bad
if name =~ /(.*)\.(.*)/
  puts $1
end

# good
if (m = name.match(/(?<base>.*)\.(?<ext>.*)/))
  puts m[:base]
end
```

## 19.11 Prefer `x` (extended) mode with comments for non-trivial patterns.

> Why? [comment-regexes](https://rubystyle.guide/#comment-regexes) and
> [multi-line-regexes](https://rubystyle.guide/#multi-line-regexes) make
> long patterns reviewable. Document each arm. **Suggestion.**

```ruby
# bad
PHONE = /\A(?:\+?\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}\z/

# good
PHONE = %r{
  \A
  (?:\+?\d{1,3}[- ]?)? # optional country code
  \(?\d{3}\)?          # area code
  [- ]?
  \d{3}[- ]?\d{4}
  \z
}x
```

## 19.12 Do not abuse `gsub` for simple prefix/suffix/character cleanup.

> Why? [dont-abuse-gsub](https://rubystyle.guide/#dont-abuse-gsub) —
> `delete_prefix`, `delete_suffix`, `tr`, `delete`, and `squeeze` are clearer
> (and often faster). Performance cops cover several of these rewrites.
> **Suggestion.**

```ruby
# bad
slug = title.gsub(/\A\s+/, '').gsub(/\s+\z/, '')
slug = slug.gsub(' ', '-')

# good
slug = title.strip.tr(' ', '-')
```

## 19.13 Prefer `string[regexp]` / `string[regexp, capture]` for simple extractions.

> Why? [regexp-string-index](https://rubystyle.guide/#regexp-string-index)
> is idiomatic for one-off extractions without a full MatchData dance.
> **Suggestion.**

```ruby
# acceptable verbose
m = line.match(/id=(?<id>\d+)/)
id = m && m[:id]

# good — index form for a single capture
id = line[/id=(\d+)/, 1]
```

## 19.14 Do not use a regexp literal as a standalone condition without a match intent.

> Why? `if /foo/` matches against `$_`, which is almost never what you want
> in application code. `Lint/RegexpAsCondition` flags it. **Violation.**

> Enforced by: Lint/RegexpAsCondition.

```ruby
# bad
if /active/
  process
end

# good
if status.match?(/active/)
  process
end
```

## 19.15 Prefer URI library parsers over hand-rolled URL regexps.

> Why? `Lint/UriRegexp` flags outdated `URI.regexp` usage; prefer
> `URI.parse` / `URI::DEFAULT_PARSER` carefully, or a dedicated validator.
> Hand-rolled URL regexps are chronically wrong. **Violation** for the
> deprecated API; **Suggestion** for "use a parser".

> Enforced by: Lint/UriRegexp.

```ruby
# bad
url =~ URI.regexp

# good
uri = URI.parse(url)
raise ArgumentError unless uri.is_a?(URI::HTTP)
```

## 19.16 Drop redundant character classes and escapes; trust RuboCop autocorrect.

> Why? `[0-9]` vs `\d` debates aside, redundant escapes (`\:`) and useless
> character-class wrappers hurt readability.
> `Style/RedundantRegexpEscape` and `Style/RedundantRegexpCharacterClass`
> clean these up. **Violation.**

> Enforced by: Style/RedundantRegexpEscape.

```ruby
# bad
/\Ahttps\:\/\/example\.com\z/

# good
/\Ahttps:\/\/example\.com\z/
# or
%r{\Ahttps://example\.com\z}
```

## 19.17 Avoid ambiguous regexp literals next to `/` division or method calls.

> Why? `Lint/AmbiguousRegexpLiteral` catches forms that humans and parsers
> disagree on. Add parentheses or use `%r`. **Violation.**

> Enforced by: Lint/AmbiguousRegexpLiteral.

```ruby
# bad — ambiguous depending on context
assert /pattern/ =~ string

# good
assert(/pattern/.match?(string))
assert(%r{pattern}.match?(string))
```
