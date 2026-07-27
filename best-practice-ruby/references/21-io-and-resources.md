<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 21. IO & Resources

Files, sockets, and process streams leak when you forget to close them.
The Ruby Style Guide covers the basics under
[auto-release-resources](https://rubystyle.guide/#auto-release-resources),
[release-resources](https://rubystyle.guide/#release-resources),
[file-read](https://rubystyle.guide/#file-read),
[file-write](https://rubystyle.guide/#file-write),
[file-classes](https://rubystyle.guide/#file-classes),
[atomic-file-operations](https://rubystyle.guide/#atomic-file-operations),
[null-devices](https://rubystyle.guide/#null-devices), and
[global-stdout](https://rubystyle.guide/#global-stdout).

**Tool alignment:** enabled cops that touch IO include `Style/Dir`,
`Style/ExpandPathArguments`, `Style/FetchEnvVar`, `Style/GlobalStdStream`,
`Style/StderrPuts`, `Security/Open`, `Rails/FilePath`, and
`Rails/RootPathnameMethods`. Prefer block forms for open resources even when
a dedicated AutoResourceCleanup cop is not enabled in this skill's effective
set.

## 21.1 Prefer block forms of `File.open`, `IO.popen`, and similar so resources auto-close.

> Why? [auto-release-resources](https://rubystyle.guide/#auto-release-resources)
> and [release-resources](https://rubystyle.guide/#release-resources) exist
> because forgotten `#close` calls leak descriptors. The block form ensures
> close on success and failure. **Suggestion.**

```ruby
# bad
f = File.open(path, 'r')
data = f.read
f.close

# good
data = File.open(path, 'r') { |f| f.read }

# good — shorthand
data = File.read(path)
```

## 21.2 Prefer `File.read` / `File.binread` and `File.write` / `File.binwrite` for whole-file IO.

> Why? [file-read](https://rubystyle.guide/#file-read) and
> [file-write](https://rubystyle.guide/#file-write) prefer the one-liners
> over open/read/close boilerplate for entire files. Use streaming APIs for
> large files. **Suggestion** — `Style/FileRead` / `Style/FileWrite` exist
> upstream but are not in this skill's effective-enabled set.

```ruby
# bad
File.open(path, 'w') do |f|
  f.write(payload)
end

# good
File.write(path, payload)
raw = File.binread(path)
```

## 21.3 Prefer `File` / `Pathname` utilities over shelling out for file metadata.

> Why? [file-classes](https://rubystyle.guide/#file-classes) — `File.exist?`,
> `File.size`, `File.mtime`, and friends beat `` `ls` `` and brittle parsing.
> **Suggestion.**

```ruby
# bad
mtime = `stat -f %m #{path}`.to_i

# good
mtime = File.mtime(path)
size = File.size?(path)
```

## 21.4 Prefer atomic replace patterns when rewriting files that others may read.

> Why? [atomic-file-operations](https://rubystyle.guide/#atomic-file-operations)
> — write to a tempfile in the same directory, then `rename` over the
> destination so readers never see a partial file. **Suggestion** —
> `Lint/NonAtomicFileOperation` is not effectively enabled here.

```ruby
# bad — readers can observe a truncated file
File.write(config_path, new_contents)

# good
require 'tempfile'
dir = File.dirname(config_path)
Tempfile.create(['config', '.yml'], dir) do |tmp|
  tmp.write(new_contents)
  tmp.flush
  tmp.fsync
  File.rename(tmp.path, config_path)
end
```

## 21.5 Prefer `File::NULL` (or `IO::NULL`) over hard-coded `/dev/null`.

> Why? [null-devices](https://rubystyle.guide/#null-devices) keeps code
> portable to Windows (`NUL`). **Suggestion.**

```ruby
# bad
system('cmd', out: '/dev/null', err: '/dev/null')

# good
system('cmd', out: File::NULL, err: File::NULL)
```

## 21.6 Prefer `$stdout` / `$stderr` over `STDOUT` / `STDERR` constants.

> Why? [global-stdout](https://rubystyle.guide/#global-stdout) —
> reassignment and redirection target the globals; the constants can be
> surprising when libraries swap streams. **Violation.**

> Enforced by: Style/GlobalStdStream.

```ruby
# bad
STDOUT.puts 'hello'
STDERR.puts 'boom'

# good
$stdout.puts 'hello'
$stderr.puts 'boom'
```

## 21.7 Prefer `$stderr.puts` over `warn` only when you intentionally skip the warning pipeline; otherwise prefer `warn`.

> Why? `Style/StderrPuts` wants `warn` for warning-shaped messages so
> `Warning` filters and `-W` interact correctly. Reserve raw `$stderr.puts`
> for non-warning diagnostics. See also chapter 23. **Violation.**

> Enforced by: Style/StderrPuts.

```ruby
# bad — warning-shaped message bypassing warn
$stderr.puts 'DEPRECATED: use NewApi'

# good
warn 'DEPRECATED: use NewApi'
```

## 21.8 Prefer `__dir__` over `File.dirname(__FILE__)`.

> Why? `Style/Dir` shortens the idiom and avoids `__FILE__` expansion
> pitfalls with relative requires. **Violation.**

> Enforced by: Style/Dir.

```ruby
# bad
fixture = File.expand_path('../fixtures/data.json', File.dirname(__FILE__))

# good
fixture = File.expand_path('../fixtures/data.json', __dir__)
```

## 21.9 Prefer `File.expand_path(path, dir)` argument order that RuboCop expects.

> Why? `Style/ExpandPathArguments` flags awkward
> `File.expand_path(File.join(...))` forms. Keep expansions obvious.
> **Violation.**

> Enforced by: Style/ExpandPathArguments.

```ruby
# bad
path = File.expand_path(File.join(__dir__, 'data', 'file.txt'))

# good
path = File.expand_path('data/file.txt', __dir__)
```

## 21.10 Prefer `ENV.fetch` for required configuration.

> Why? `ENV['KEY']` silently returns `nil`.
> `Style/FetchEnvVar` prefers `fetch` (with default or key error).
> **Violation.**

> Enforced by: Style/FetchEnvVar.

```ruby
# bad
database_url = ENV['DATABASE_URL']

# good
database_url = ENV.fetch('DATABASE_URL')
timeout = Integer(ENV.fetch('TIMEOUT', '30'))
```

## 21.11 Prefer Rails root helpers over stringy `Rails.root.join` mistakes.

> Why? `Rails/FilePath` and `Rails/RootPathnameMethods` keep paths
> `Pathname`-clean and avoid `#{Rails.root}/foo` interpolation bugs.
> **Violation.**

> Enforced by: Rails/FilePath.

```ruby
# bad
path = "#{Rails.root}/storage/#{name}"

# good
path = Rails.root.join('storage', name)
```

## 21.12 Do not pass unsanitized user input to `open`, `Kernel#open`, or URI openers.

> Why? `open('|rm -rf /')` is a classic injection.
> `Security/Open` flags dangerous `open` usage. Prefer `File.open` /
> `URI.parse` + explicit HTTP client. **Violation.**

> Enforced by: Security/Open.

```ruby
# bad
open(params[:url]).read

# good
File.open(path, 'r') { |f| f.read }

# good — HTTP via a real client
response = Net::HTTP.get(URI.parse(url))
```

## 21.13 Stream large inputs; do not `File.read` multi-gigabyte artifacts into memory.

> Why? Whole-file helpers are for configuration and small payloads. Prefer
> `each_line`, `readpartial`, or `IO.copy_stream` for large data.
> **Suggestion.**

```ruby
# bad
File.read(huge_path).each_line { |line| handle(line) }

# good
File.foreach(huge_path) { |line| handle(line) }
```

## 21.14 Prefer binary mode for non-text IO; set external encodings deliberately for text.

> Why? Default encodings depend on locale. Use `'rb'` / `'wb'` for bytes and
> `'r:UTF-8'` (or similar) when you mean text. **Suggestion.**

```ruby
# bad — text mode on a PNG
data = File.read('avatar.png')

# good
data = File.binread('avatar.png')
text = File.read('readme.md', encoding: 'UTF-8')
```

## 21.15 Close or use block form for sockets, Tempfiles, and DB-adjacent IO wrappers you open yourself.

> Why? The same auto-release rule applies beyond `File`. Prefer
> `Tempfile.create` blocks, `TCPSocket.open` blocks, and library helpers that
> manage lifetime. **Suggestion.**

```ruby
# bad
tmp = Tempfile.new('export')
tmp.write(payload)
tmp.close
upload(tmp.path)
tmp.unlink

# good
Tempfile.create('export') do |tmp|
  tmp.write(payload)
  tmp.flush
  upload(tmp.path)
end
```

## 21.16 Prefer `IO.copy_stream` for efficient stream-to-stream copies.

> Why? Manual looped `read` / `write` is easy to get wrong on partial reads.
> `IO.copy_stream` is concise and uses sendfile when available. **Suggestion.**

```ruby
# bad
File.open(dest, 'wb') do |out|
  File.open(src, 'rb') do |inp|
    while (chunk = inp.read(16_384))
      out.write(chunk)
    end
  end
end

# good
File.open(src, 'rb') do |inp|
  File.open(dest, 'wb') do |out|
    IO.copy_stream(inp, out)
  end
end
```
