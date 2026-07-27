<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 22. Concurrency & Ractors

On Ruby 4.0 the everyday concurrency tools are still **Threads** (parallelism
subject to the GVL for most CRuby CPU work; excellent for IO waits) and
**Fibers** (cooperative lightweight concurrency, including the Fiber
scheduler / non-blocking IO). **Ractor** exists for memory-isolated CPU-bound
work and message passing; it is not the default model for typical web, job,
or script code. Prefer Threads + Fibers unless you have a measured need for
isolation that outweighs Ractor's sharing constraints.

There is little normative rubystyle.guide material for concurrency; treat
this chapter as Ruby 4.0 language practice aligned with
[Ractor](https://docs.ruby-lang.org/en/4.0/Ractor.html),
[Thread](https://docs.ruby-lang.org/en/4.0/Thread.html), and
[Fiber](https://docs.ruby-lang.org/en/4.0/Fiber.html) docs. RuboCop does not
effectively enforce a concurrency model here — nearly every rule is a
**Suggestion**.

## 22.1 Prefer Threads for concurrent IO; do not assume Threads deliver multi-core CPU speedup on CRuby.

> Why? Waiting on the network or disk releases the GVL; crunching numbers in
> pure Ruby usually does not. Reach for Threads (or a Thread pool) for
> overlapping IO. For CPU-bound pure Ruby, consider multiple processes,
> native extensions that release the GVL, or a carefully scoped Ractor —
> not "spawn more Threads and hope." **Suggestion.**

```ruby
# bad — expecting 8 Threads to use 8 cores on pure-Ruby factorial
threads = Array.new(8) { |i| Thread.new { heavy_pure_ruby_compute(i) } }
threads.each(&:join)

# good — overlap IO
urls = %w[https://example.com/a https://example.com/b]
threads = urls.map { |url| Thread.new { Net::HTTP.get(URI(url)) } }
bodies = threads.map(&:value)
```

## 22.2 Give every Thread an owner: join it, bound it, or supervise it; never fire-and-forget.

> Why? Leaked Threads accumulate, hold GVL pressure, and hide exceptions
> (depending on `Thread#abort_on_exception` / `report_on_exception`). Return
> a join handle, use a pool, or run under a supervisor that waits.
> **Suggestion.**

```ruby
# bad
def ping_async(url)
  Thread.new { Net::HTTP.get(URI(url)) }
end

# good
def ping_async(url)
  Thread.new { Net::HTTP.get(URI(url)) }.tap do |thread|
    thread.report_on_exception = true
  end
end

thread = ping_async(url)
body = thread.value # joins and re-raises
```

## 22.3 Prefer Thread-safe queues and mutexes over ad-hoc shared mutable state.

> Why? Shared arrays/hashes mutated from multiple Threads race. Use
> `Queue` / `SizedQueue` for handoffs and `Mutex#synchronize` for critical
> sections. Prefer message passing shapes even with Threads. **Suggestion.**

```ruby
# bad
results = []
workers = jobs.map do |job|
  Thread.new { results << process(job) } # race on Array#<<
end
workers.each(&:join)

# good
queue = Queue.new
jobs.each { |job| queue << job }
results = Queue.new
workers = Array.new(4) do
  Thread.new do
    while (job = queue.pop(true) rescue nil)
      results << process(job)
    end
  end
end
workers.each(&:join)
```

## 22.4 Prefer Fiber (and the Fiber scheduler) for high-concurrency IO inside a Thread when the stack supports it.

> Why? Fibers are cheaper than Threads for massive concurrency of waiting
> IO when using a scheduler (e.g. libraries built on non-blocking IO). Do
> not invent a Fiber scheduler in app code — use battle-tested adapters.
> Fibers are cooperative: a Fiber that never yields stalls its Thread.
> **Suggestion.**

```ruby
# bad — one OS Thread per connection when a Fiber scheduler is available
connections.each do |conn|
  Thread.new { conn.handle }
end

# good — conceptual shape with a scheduler-aware library
# (exact API depends on the server / async gem you choose)
Fiber.set_scheduler(SomeScheduler.new)
connections.each do |conn|
  Fiber.schedule { conn.handle }
end
```

## 22.5 Do not confuse Fibers with Threads: Fibers do not run in parallel on their own.

> Why? `Fiber.yield` / `Fiber#resume` are cooperative. CPU-bound work inside
> a Fiber still holds the Thread (and GVL). Use Fibers for structuring
> concurrency, not for multi-core. **Suggestion.**

```ruby
# bad — expecting Fibers to parallelize CPU work
fibers = Array.new(4) do |i|
  Fiber.new { heavy_pure_ruby_compute(i) }
end
fibers.each(&:resume)

# good — Fibers for interleaved IO state machines on one Thread
fiber = Fiber.new do
  request = Fiber.yield
  response = fetch(request)
  Fiber.yield response
end
```

## 22.6 Use Ractor when you need memory isolation or CPU isolation — not as a default Thread replacement.

> Why? Ractors cannot freely share most Ruby objects; they communicate by
> messaging (copy/move/shareable). That isolation is the feature — and the
> cost. Typical Rails request/job code should stay on Threads. Introduce
> Ractors for sandboxed CPU work, parallel CPU pipelines with shareable
> inputs, or explicit isolation boundaries. **Suggestion.**

```ruby
# bad — rewriting ordinary IO workers as Ractors for fashion
ractors = urls.map do |url|
  Ractor.new(url) { |u| Net::HTTP.get(URI(u)) }
end

# good — Ractor for isolated CPU-bound pure computation
worker = Ractor.new do
  loop do
    payload = Ractor.receive
    Ractor.yield compute_shareable_result(payload)
  end
end

worker.send(shareable_job)
result = worker.take
```

## 22.7 Prefer shareable / moved objects at Ractor boundaries; design messages as Data or primitives.

> Why? Non-shareable objects raise on send. Prefer deep-freeze,
> `Ractor.make_shareable`, immutable `Data` values, or move semantics.
> Keep the message schema tiny and documented. **Suggestion.**

```ruby
# bad — sending a mutable ActiveRecord-like graph into a Ractor
ractor.send(user)

# good
Job = Data.define(:id, :payload)
job = Job.new(id: 1, payload: { 'n' => 10 })
ractor.send(Ractor.make_shareable(job))
```

## 22.8 Prefer `Thread#value` / explicit error channels over swallowing Thread exceptions.

> Why? By default a Thread exception can die quietly depending on flags.
> Set `report_on_exception`, join via `#value`, or push errors onto a
> queue. Silent failure is worse than a loud crash in most services.
> **Suggestion.**

```ruby
# bad
Thread.new do
  risky_call
rescue StandardError
  nil
end

# good
thread = Thread.new { risky_call }
begin
  thread.value
rescue StandardError => e
  logger.error(e.full_message)
  raise
end
```

## 22.9 Prefer timeouts around external IO; do not rely on hope.

> Why? Hung sockets stall Threads and pools. Use `Timeout` sparingly (it is
> unsafe with some non-IO code); prefer per-library timeouts
> (`open_timeout`, `read_timeout`, Redis/HTTP client settings).
> **Suggestion.**

```ruby
# bad
body = Net::HTTP.get(URI(url)) # no timeouts

# good
uri = URI(url)
Net::HTTP.start(uri.host, uri.port, use_ssl: uri.scheme == 'https',
                open_timeout: 5, read_timeout: 5) do |http|
  http.request(Net::HTTP::Get.new(uri))
end
```

## 22.10 Prefer process-level parallelism for multi-core MRI CPU work when Ractor is a poor fit.

> Why? Forked workers / separate processes (Sidekiq processes, Puma
> workers, `Parallel` with processes) remain the boring, reliable way to use
> multiple cores for Ruby CPU work that does not fit Ractor's constraints.
> **Suggestion.**

```ruby
# good — conceptual: multiple processes, each single-threaded CPU worker
# (orchestration via your process manager, not a bespoke Thread pool)
```

## 22.11 Avoid mutating constants and class variables from concurrent Threads.

> Why? Autoload, constant assignment, and class-variable writes are
> concurrency hazards. Prefer instance state owned by one Thread, or
> concurrent structures with clear synchronization. **Suggestion.**

```ruby
# bad
COUNTER = 0
mutex = Mutex.new # still wrong if something assigns COUNTER =
threads = Array.new(10) do
  Thread.new { COUNTER += 1 } # raises on frozen / is a race if not frozen
end

# good
counter = 0
mutex = Mutex.new
threads = Array.new(10) do
  Thread.new do
    mutex.synchronize { counter += 1 }
  end
end
threads.each(&:join)
```

## 22.12 Prefer Concurrent Ruby (or framework pools) over hand-rolled Thread pools in apps.

> Why? Bounded pools, rejection policies, and lifecycle hooks are easy to
> get wrong. In Rails, prefer ActiveJob / the framework's executor wrappers;
> in libraries, prefer mature pool implementations. **Suggestion.**

```ruby
# bad — unbounded Thread spawn per job
jobs.each { |job| Thread.new { job.call } }

# good — bounded work via a queue + fixed workers (or a gem pool)
pool_size = 4
queue = SizedQueue.new(pool_size * 2)
# ... fixed workers consuming queue ...
```

## 22.13 Do not share database connections or non-threadsafe clients across Threads without a pool.

> Why? ActiveRecord and many clients are request/thread checked out from a
> pool. Checking out once and using across Threads corrupts state. Use the
> pool's checkout rules; wrap Threads with the framework executor when
> inside Rails. **Suggestion.**

```ruby
# bad
conn = ActiveRecord::Base.connection
threads = Array.new(4) { Thread.new { conn.select_value('SELECT 1') } }

# good — each Thread checks out via AR's pool (Rails executor omitted)
threads = Array.new(4) do
  Thread.new do
    ActiveRecord::Base.connection_pool.with_connection do
      ActiveRecord::Base.connection.select_value('SELECT 1')
    end
  end
end
threads.each(&:join)
```

## 22.14 Prefer deterministic scheduling in tests; do not sleep-loop to "wait for the Thread".

> Why? `sleep 0.5` flakes. Prefer joining Threads, using queues as
> barriers, or injecting fakes that run synchronously in tests.
> **Suggestion.**

```ruby
# bad
Thread.new { @done = true }
sleep 0.5
expect(@done).to be(true)

# good
thread = Thread.new { work }
thread.join
expect(result).to eq(expected)
```

## 22.15 Document any intentional GVL-release or Ractor boundary in library code.

> Why? Callers need to know whether a method is safe to call from multiple
> Threads, whether it blocks the GVL for a long time, and whether arguments
> must be shareable. A one-line comment at the API boundary prevents misuse.
> **Suggestion.**

```ruby
# good
# Thread-safe: uses an internal Mutex. Releases GVL during the C HMAC.
# Not Ractor-shareable: instances keep a mutable buffer.
def digest(data)
  # ...
end
```
