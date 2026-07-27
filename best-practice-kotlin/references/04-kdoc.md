<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 4. KDoc

KDoc is Kotlin's documentation format: a `/** ... */` block, written in Markdown,
with a small set of block tags and its own `[link]` syntax. This chapter covers
its mechanical shape, where it is required, and — the part no style guide
states — what a KDoc comment actually has to say to be worth the line count.

The mechanical rules come from the
[Android Kotlin style guide, Documentation](https://developer.android.com/kotlin/style-guide#documentation),
which owns
[block form and single-line form](https://developer.android.com/kotlin/style-guide#formatting_2),
[paragraphs](https://developer.android.com/kotlin/style-guide#paragraphs),
[block tags](https://developer.android.com/kotlin/style-guide#block_tags),
the [summary fragment](https://developer.android.com/kotlin/style-guide#summary_fragment),
and [where KDoc is required](https://developer.android.com/kotlin/style-guide#usage).
The tag semantics and link syntax come from
[Document Kotlin code: KDoc](https://kotlinlang.org/docs/kotlin-doc.html). The
preference for inlining parameter descriptions over tagging them comes from the
[Kotlin coding conventions, Documentation comments](https://kotlinlang.org/docs/coding-conventions.html#documentation-comments),
and it partly contradicts the Android guide's tag-ordering rule — §4.7 and §4.8
reconcile them.

Two neighbouring topics are deferred. **Non-doc comments** — `//` comments,
`TODO` markers, and the file-level licence header — are
[Chapter 2, Source Files & Structure](02-source-files-and-structure.md).
**Which declarations are public in the first place**, including explicit API
mode, is [Chapter 5, Declarations & Visibility](05-declarations-and-visibility.md);
KDoc obligations follow visibility, so that decision comes first.

**Tool alignment:** ktlint owns the physical layout of the comment block —
asterisk alignment, wrapping, indentation — under the formatting chain in
[Chapter 1](01-formatting-and-tooling.md), and this chapter never re-litigates
it. detekt ships a `comments` ruleset that covers several rules below —
`UndocumentedPublicClass`, `UndocumentedPublicFunction`,
`UndocumentedPublicProperty`, `DeprecatedBlockTag`, `EndOfSentenceFormat`,
`KDocReferencesNonPublicProperty`, and `OutdatedDocumentation` — but **every one
of them is inactive by default**. They only count as **Violation** once you turn
them on in `config/detekt/detekt.yml`; see [Chapter 47](47-ktlint-and-detekt.md).
Everything else here is a **Suggestion**, because no tool can judge whether a
sentence is worth reading.

## 4.1 Use the multi-line block form by default; the single-line form only when the entire comment fits on one line and carries no block tag.

> Why? The
> [Android Kotlin style guide, Formatting](https://developer.android.com/kotlin/style-guide#formatting_2)
> permits the compact form under two conditions at once: "the single-line form
> may be substituted when the entirety of the KDoc block (including comment
> markers) can fit on a single line. Note that this only applies when there are
> no block tags such as `@return`." The tag restriction is not cosmetic — a tag
> crammed onto a shared line stops being parsed as a tag by some renderers, and
> is invisible to a reader scanning the left margin for `@`. The block form is
> always acceptable, so when in doubt use it.

```kotlin
// bad — a block tag on the single-line form, and a comment that does not fit
/** Returns the tax owed. @return the tax in minor units. */
fun taxOwed(order: Order): Long = TODO()

// good — block form the moment a block tag appears
/**
 * The tax owed on [order], in minor units of the order's currency.
 *
 * @return zero when the shipping destination is a tax-exempt jurisdiction.
 */
fun taxOwed(order: Order): Long = TODO()

// good — single-line form: it fits, and there are no tags
/** The tax owed on [order], in minor units of the order's currency. */
fun taxOwed(order: Order): Long = TODO()
```

## 4.2 Separate paragraphs with a blank line containing only the aligned asterisk, and put one before the block-tag group.

> Why? The
> [Android Kotlin style guide, Paragraphs](https://developer.android.com/kotlin/style-guide#paragraphs)
> is precise about the mechanism: "one blank line — that is, a line containing
> only the aligned leading asterisk (`*`) — appears between paragraphs, and
> before the group of block tags if present." KDoc is Markdown, so a missing
> blank line is not a style problem but a rendering bug: consecutive lines are
> joined into one paragraph, and the summary fragment (§4.3) silently absorbs
> whatever follows it. The blank line before the tag group is what makes the
> tags scannable as a block rather than as more prose.

```kotlin
// bad — the summary and the detail render as one run-on paragraph, and the
// tag group has nothing separating it from the text above
/**
 * A pooled connection to the pricing service.
 * Closing a connection returns it to the pool rather than shutting the
 * socket, so a caller must not assume the peer sees a disconnect.
 * @throws IllegalStateException if the pool is already shut down.
 */
fun openConnection(): PricingConnection = TODO()

// good
/**
 * A pooled connection to the pricing service.
 *
 * Closing a connection returns it to the pool rather than shutting the
 * socket, so a caller must not assume the peer sees a disconnect.
 *
 * @throws IllegalStateException if the pool is already shut down.
 */
fun openConnection(): PricingConnection = TODO()
```

## 4.3 Open every KDoc with a summary fragment — a noun or verb phrase, not a complete sentence, and never one that starts by naming the mechanism.

> Why? The
> [Android Kotlin style guide, Summary fragment](https://developer.android.com/kotlin/style-guide#summary_fragment)
> explains the stakes: "this fragment is very important: it is the only part of
> the text that appears in certain contexts such as class and method indexes."
> The required form is exact — "this is a fragment — a noun phrase or verb
> phrase, not a complete sentence. It does not begin with '`A `Foo` is a...`',
> or '`This method returns...`', nor does it have to form a complete imperative
> sentence like '`Save the record.`'. However, the fragment is capitalized and
> punctuated as if it were a complete sentence." The reason is density: in an
> index the fragment is truncated, so every character spent on "This method
> returns" is a character not spent on what it returns.
> **Violation if enabled — `detekt/EndOfSentenceFormat`** checks that the first
> sentence ends in proper punctuation; it is inactive by default.

```kotlin
// bad — a complete sentence that spends its first four words on scaffolding
/**
 * This function returns the canonical name of the given account.
 */
fun canonicalName(account: Account): String = TODO()

// good — a noun phrase, capitalized and punctuated like a sentence
/**
 * The canonical name of [account]: its registered legal name folded to
 * lowercase, with punctuation and diacritics removed.
 */
fun canonicalName(account: Account): String = TODO()
```

## 4.4 Write KDoc for every public type, and for every public or protected member of one.

> Why? The
> [Android Kotlin style guide, Usage](https://developer.android.com/kotlin/style-guide#usage)
> sets the floor: "at the minimum, KDoc is present for every `public` type, and
> every `public` or `protected` member of such a type, with a few exceptions
> noted below." `protected` is in the list for a reason people miss — a
> protected member is API, just aimed at a subclass author rather than a caller,
> and a subclass author has strictly less context than you do about when the
> hook fires and what it may do. **Violation if enabled — `detekt/UndocumentedPublicClass`,
> `detekt/UndocumentedPublicFunction`, and `detekt/UndocumentedPublicProperty`**;
> all three are inactive by default.

```kotlin
// bad — public API and a subclass hook, both undocumented
open class Ledger {
    fun post(entry: Entry): PostingId = TODO()

    protected open fun onPosted(id: PostingId) {}
}

// good
/** An append-only record of [Entry] values for a single account. */
open class Ledger {
    /**
     * Appends [entry] and returns the identifier assigned to it.
     *
     * Posting is atomic: a failure leaves the ledger exactly as it was.
     */
    fun post(entry: Entry): PostingId = TODO()

    /**
     * Called after [post] commits, on the posting thread.
     *
     * Implementations must not block — a slow callback delays every
     * subsequent post on this ledger.
     */
    protected open fun onPosted(id: PostingId) {}
}
```

## 4.5 Cite the self-explanatory exception only when there is genuinely nothing to add — never to skip a term the reader may not know.

> Why? The
> [Android Kotlin style guide](https://developer.android.com/kotlin/style-guide#exception_self-explanatory_functions)
> grants the exception narrowly: "KDoc is optional for 'simple, obvious'
> functions like `getFoo` and properties like `foo`, in cases where there really
> and truly is nothing else worthwhile to say but 'Returns the foo'." Then it
> closes the loophole in the next breath: "it is not appropriate to cite this
> exception to justify omitting relevant information that a typical reader might
> need to know. For example, for a function named `getCanonicalName` or property
> named `canonicalName`, don't omit its documentation... if a typical reader may
> have no idea what the term 'canonical name' means!" The abuse is
> characteristic: the exception gets cited for exactly the declarations whose
> names contain a domain term, which are the ones most in need of definition.

```kotlin
// bad — the exception cited for a name built on an undefined domain term
/** Returns the canonical name. */
val canonicalName: String get() = TODO()

// good — genuinely nothing to add, so add nothing
val id: OrderId get() = TODO()

// good — the domain term gets defined, because a reader cannot guess it
/**
 * The order's canonical name: the customer's registered legal name folded
 * to lowercase with punctuation removed.
 *
 * Two orders from the same customer always share a canonical name, even
 * when the names as entered differ.
 */
val canonicalName: String get() = TODO()
```

## 4.6 Leave an override undocumented when it keeps the supertype's contract; document it when it narrows or strengthens one.

> Why? The
> [Android Kotlin style guide](https://developer.android.com/kotlin/style-guide#exception_overrides)
> states the exception in one line: "KDoc is not always present on a method that
> overrides a supertype method." Copying the supertype's text into the override
> is worse than leaving it blank, because the copy is now a second source of
> truth that will drift the first time the interface changes and no tool will
> notice. The corollary is the part people skip: when the override *does* change
> what a caller can rely on — it now blocks, it now throws something new, it now
> has a stricter precondition — that difference is exactly what has to be
> written down, because it is nowhere else.

```kotlin
// bad — copied text, now free to drift out of sync with the interface
interface Cache {
    /** Removes every entry. */
    fun clear()
}

class LruCache : Cache {
    /** Removes every entry. */
    override fun clear() = TODO()
}

// good — nothing to say, so say nothing
class LruCache : Cache {
    override fun clear() = TODO()
}

// good — the override changes the contract, so the difference is documented
class DiskCache(private val root: Path) : Cache {
    /**
     * Removes every entry and deletes the backing directory under [root].
     *
     * Unlike the in-memory caches, this performs blocking filesystem I/O
     * and may take proportionally longer with cache size.
     */
    override fun clear() = TODO()
}
```

## 4.7 Fold parameter and return descriptions into the prose with `[links]`; reserve `@param` and `@return` for descriptions too long to fit the flow.

> Why? The
> [Kotlin coding conventions, Documentation comments](https://kotlinlang.org/docs/coding-conventions.html#documentation-comments)
> are unambiguous: "generally, avoid using `@param` and `@return` tags. Instead,
> incorporate the description of parameters and return values directly into the
> documentation comment, and add links to parameters wherever they are
> mentioned. Use `@param` and `@return` only when a lengthy description is
> required which doesn't fit into the flow of the main text." A tag block that
> restates the signature is pure noise — `@param number the number to return the
> absolute value for` tells a reader nothing the declaration did not — and it
> pushes the one sentence that matters below the fold. Inlining also gives you
> the summary fragment for free, since the prose has to carry the information.

```kotlin
// bad — three lines of tags, zero information beyond the signature
/**
 * Returns the absolute value of the given number.
 *
 * @param number the number to return the absolute value for.
 * @return the absolute value.
 */
fun abs(number: Int): Int = TODO()

// good — the prose carries it, with a link to the parameter
/** The absolute value of [number]. */
fun abs(number: Int): Int = TODO()

// good — a tag earns its place when the description will not fit inline
/**
 * [source] transcoded into [target]'s container and codec.
 *
 * @param target only the container and codec fields are read. Bitrate,
 *     frame rate, and colour-space fields are ignored and recomputed from
 *     [source], because re-encoding at a higher bitrate than the input
 *     cannot recover detail the source never carried.
 */
fun transcode(source: Media, target: MediaSpec): Media = TODO()
```

## 4.8 When you do use block tags, emit them in the order `@constructor`, `@receiver`, `@param`, `@property`, `@return`, `@throws`, `@see` — and never with an empty description.

> Why? The
> [Android Kotlin style guide, Block tags](https://developer.android.com/kotlin/style-guide#block_tags)
> fixes both the order and the emptiness rule: "any of the standard 'block tags'
> that are used appear in the order `@constructor`, `@receiver`, `@param`,
> `@property`, `@return`, `@throws`, `@see`, and these never appear with an
> empty description. When a block tag doesn't fit on a single line, continuation
> lines are indented 4 spaces from the position of the `@`." A fixed order means
> a reader scanning a large API always finds `@throws` in the same place. An
> empty tag is worse than a missing one: it renders as a heading with no content
> and signals that someone intended to write something and did not.
> `@sample` is not in the guide's list — keep it adjacent to `@see` at the end
> of the group and stay consistent across the codebase.

```kotlin
// bad — scrambled order, and a @return with nothing after it
/**
 * A shipping quote.
 *
 * @see ShippingRate
 * @throws IllegalStateException if no carrier serves the destination.
 * @return
 * @param destination the destination postcode.
 */
fun quote(destination: String): Quote = TODO()

// good — @param, @return, @throws, @see, each carrying real text
/**
 * The cheapest shipping quote for [destination].
 *
 * @param destination a postcode in the carrier's own format; see
 *     [ShippingRate] for the per-carrier syntax.
 * @return the cheapest quote across every carrier serving [destination].
 * @throws IllegalStateException if no carrier serves [destination].
 * @see ShippingRate
 */
fun quote(destination: String): Quote = TODO()
```

## 4.9 Document a primary-constructor property with `@property`, and a plain constructor parameter with `@param`.

> Why? [Document Kotlin code: KDoc](https://kotlinlang.org/docs/kotlin-doc.html)
> distinguishes the two: `@param` "documents a value parameter of a function or
> a type parameter of a class, property or function", while `@property`
> "documents the property of a class which has the specified name" and exists
> for "documenting properties declared in the primary constructor, where putting
> a doc comment directly before the property definition would be awkward". The
> distinction
> is real in the rendered output — `@property` attaches the text to the property
> page a caller will actually read, while `@param` attaches it to the constructor
> signature, where a caller reading `order.destination` will never look. Use
> `@constructor` for anything about construction itself, such as a validation
> precondition. **Violation if enabled — `detekt/OutdatedDocumentation`** reports
> KDoc whose tags do not match the declaration signature; it is inactive by
> default.

```kotlin
// bad — @param on things that are properties, plus an empty description
/**
 * A shipment leg.
 *
 * @param origin
 * @param destination the destination airport code.
 */
class Leg(val origin: String, val destination: String)

// good — @property for constructor properties, @constructor for construction
/**
 * One leg of an itinerary.
 *
 * @constructor rejects a leg whose origin and destination are equal.
 * @property origin IATA code of the departure airport, uppercased.
 * @property destination IATA code of the arrival airport, uppercased.
 */
class Leg(val origin: String, val destination: String) {
    init {
        require(origin != destination) { "origin and destination must differ" }
    }
}
```

## 4.10 Never write KDoc that restates the declaration's name.

> Why? "Gets the user id" above `val userId: UserId` costs a reader three lines
> of vertical space and a context switch, and returns nothing they did not have.
> Worse, it *looks* documented, so it suppresses the instinct that would
> otherwise make someone write the sentence that is actually missing. The
> Android guide's self-explanatory exception (§4.5) exists precisely so you can
> write nothing here — take it. If you find yourself unable to say anything
> beyond the name, that is the signal to write nothing, not the signal to
> paraphrase.

```kotlin
// bad — every line is derivable from the signature directly above it
/** Gets the user id. */
val userId: UserId get() = TODO()

/** Sets the timeout. */
fun setTimeout(timeout: Duration) = TODO()

/** Default implementation of [OrderRepository]. */
class DefaultOrderRepository : OrderRepository

// good — say something a reader cannot derive...
/** Stable identifier assigned at signup; never reused after deletion. */
val userId: UserId get() = TODO()

/**
 * Applies to connections opened after this call. Requests already in
 * flight keep the timeout they started with.
 */
fun setTimeout(timeout: Duration) = TODO()

// ...or write nothing at all, under the self-explanatory exception (§4.5)
class DefaultOrderRepository : OrderRepository
```

## 4.11 Document the contract, not the implementation.

> Why? Anything a reader can learn by opening the body is not worth a comment,
> and worse, it is a comment that goes stale on the next refactor while looking
> authoritative. What a caller cannot see is the *guarantee*: what holds on
> return, what is left unchanged on failure, whether the result is order-stable,
> whether calling twice is the same as calling once. Those survive a rewrite of
> the body, which is exactly what makes them worth writing down.

```kotlin
// bad — narrates the current algorithm, so it rots at the next refactor
/**
 * Loops over the order lines, calls BigDecimal.add for each one, and
 * rounds with HALF_UP at the end.
 */
fun total(order: Order): Money = TODO()

// good — states what a caller may rely on, whatever the body becomes
/**
 * The sum of every line on [order], rounded to the currency's minor unit
 * using half-up rounding.
 *
 * The result does not depend on line order: two orders carrying the same
 * multiset of lines always total the same amount.
 */
fun total(order: Order): Money = TODO()
```

## 4.12 Say what a `null` result *means* and when it occurs; never just restate that the type is nullable.

> Why? The type already says `User?`. What it cannot say is whether `null` means
> "no such user", "user exists but is not visible to you", or "the lookup timed
> out and you should retry" — three cases a caller must handle differently and
> which the signature collapses into one. This is Kotlin's specific version of
> the general contract rule: the type system carries so much that the remaining
> documentation obligation is precisely the part it cannot express. Null-handling
> mechanics are [Chapter 6, Null Safety](06-null-safety.md).

```kotlin
// bad — the type already told us this
/**
 * Returns the user, or null.
 */
fun findUser(id: UserId): User? = TODO()

// good — says when null happens, and what it does not mean
/**
 * The user registered under [id], or `null` when no such user exists.
 *
 * A soft-deleted user is reported as absent. A caller that needs to tell
 * "never existed" from "deleted" must use [findUserIncludingDeleted].
 */
fun findUser(id: UserId): User? = TODO()
```

## 4.13 Document every exception a caller might reasonably catch — Kotlin has no checked exceptions, so KDoc is the only warning they get.

> Why? Kotlin removed checked exceptions, which means a function's throwing
> behaviour is invisible in its signature and invisible to the compiler. The
> caller finds out in production. KDoc's `@throws` is the entire replacement
> mechanism, and skipping it is not a documentation gap but a missing part of
> the API. Document the failures a caller can act on; do not enumerate every
> `NullPointerException` the JVM could theoretically raise. When a Java caller
> needs to catch the exception, the `@Throws` *annotation* is a separate,
> additional requirement — see [Chapter 28, Java Interop](28-java-interop.md).
> Exception design itself is [Chapter 24](24-exceptions-and-result.md).

```kotlin
// bad — throws two distinct exceptions, and nothing tells the caller
fun parseAmount(text: String, currency: Currency): Money = TODO()

// good
/**
 * [text] parsed as an amount in [currency], for example `"12.34"`.
 *
 * @throws NumberFormatException if [text] is not a decimal number.
 * @throws IllegalArgumentException if [text] carries more fraction digits
 *     than [currency] permits, which would require silent rounding.
 */
fun parseAmount(text: String, currency: Currency): Money = TODO()
```

## 4.14 Document the thread-safety and mutability contract of any type a caller could share.

> Why? Kotlin's type system says nothing about concurrent access. `val` freezes
> a reference, not the object behind it, and a `data class` with a `var`
> component looks immutable at a glance and is not. A caller deciding whether to
> hold one instance in a singleton, one per request, or one per coroutine has no
> way to answer that from the declaration. State the answer, including the
> negative one — "not thread-safe" is a complete and useful contract, whereas
> silence is read as "probably fine". Immutability itself is
> [Chapter 25](25-immutability.md).

```kotlin
// bad — mutable internal state, shareable shape, nothing said about either
class RateLimiter(private val permitsPerSecond: Int) {
    private var available: Int = permitsPerSecond

    fun tryAcquire(): Boolean = TODO()
}

// good
/**
 * A token bucket holding [permitsPerSecond] permits, refilled once a second.
 *
 * Not thread-safe. Confine an instance to a single coroutine, or guard
 * [tryAcquire] with a [kotlinx.coroutines.sync.Mutex]. An unguarded
 * instance shared across dispatchers loses permits under contention and
 * will admit more traffic than configured.
 */
class RateLimiter(private val permitsPerSecond: Int) {
    private var available: Int = permitsPerSecond

    fun tryAcquire(): Boolean = TODO()
}
```

## 4.15 For a `suspend` function, document whether it is main-safe, which dispatcher it needs, and what cancellation leaves behind.

> Why? The
> [Android coroutines best practices](https://developer.android.com/kotlin/coroutines/coroutines-best-practices)
> set the expectation the caller will hold you to: "suspend functions should be
> main-safe, meaning they're safe to call from the main thread. If a class is
> doing long-running blocking operations in a coroutine, it's in charge of
> moving the execution off the main thread using `withContext`." A caller cannot
> verify that from the signature, so if your function is main-safe, say so — and
> if it is not, that is a far more urgent thing to say. Cancellation deserves
> the same treatment: a caller needs to know whether cancelling mid-flight
> leaves a half-written file, an uncommitted transaction, or nothing at all.
> Dispatcher selection is [Chapter 34](34-dispatchers-and-context.md);
> cancellation semantics are [Chapter 35](35-cancellation-and-timeouts.md).

```kotlin
// bad — blocks the calling dispatcher, and the KDoc hides it
/**
 * Reads the report from disk.
 */
suspend fun readReport(path: Path): Report = parse(Files.readString(path))

// good — main-safe by construction, and the contract says so
/**
 * The report stored at [path].
 *
 * Main-safe: the blocking read is confined to [ioDispatcher], so this may
 * be called from any dispatcher. Cancelling the calling coroutine abandons
 * the read at the next suspension point and discards any partial result;
 * nothing is written, so no cleanup is required.
 *
 * @throws java.io.IOException if [path] is missing or unreadable.
 */
suspend fun readReport(path: Path): Report = withContext(ioDispatcher) {
    parse(Files.readString(path))
}
```

## 4.16 For a function returning `Flow`, document whether the flow is cold or hot, when it completes, and how it reports errors.

> Why? `Flow<T>` is the least self-describing type in common Kotlin. The
> declaration cannot tell a caller whether collecting twice opens two
> subscriptions or shares one, whether the flow ever completes, whether values
> emitted before collection are replayed, or whether an upstream failure arrives
> as a thrown exception from `collect` or as a modelled error value. Every one
> of those changes how the caller must write the collection site, and getting it
> wrong produces leaked subscriptions or a silently dropped error. The full
> treatment is [Chapter 36, `Flow`](36-flow.md) and
> [Chapter 37, `StateFlow` & `SharedFlow`](37-stateflow-and-sharedflow.md).

```kotlin
// bad — cold or hot? does it complete? what happens when the broker drops?
/**
 * Returns a flow of prices.
 */
fun prices(symbol: Symbol): Flow<Price> = TODO()

// good
/**
 * A cold [Flow] of price ticks for [symbol].
 *
 * A fresh broker subscription is opened per collector and closed when
 * collection stops, so two collectors cost two subscriptions.
 *
 * The flow never completes normally. A broker failure is thrown from
 * `collect` as a [PriceFeedException]; a caller that must survive one
 * should apply [kotlinx.coroutines.flow.retry] with its own backoff.
 */
fun prices(symbol: Symbol): Flow<Price> = TODO()
```

## 4.17 Write KDoc in Markdown: backticks for inline code, `[Name]` for element links. Javadoc's `{@code}` and `{@link}` do not exist here.

> Why? [Document Kotlin code: KDoc](https://kotlinlang.org/docs/kotlin-doc.html)
> specifies Markdown as KDoc's syntax for inline markup, and specifies that a
> link is written by putting the name of the element in square brackets, with
> `[display text][Name]` for a custom label and dot notation for qualified
> names. Javadoc tags are not translated — they render literally as
> `{@link #refresh()}` in the generated output. This is the single most common
> KDoc defect in a codebase migrated from Java, and it is invisible until
> someone builds the docs. The payoff for using `[Name]` is not just rendering:
> the IDE resolves the link, so renaming the target updates the comment and a
> broken link shows up as a warning.

```kotlin
// bad — Javadoc markup; KDoc renders these verbatim, braces and all
/**
 * Calls {@link #refresh()} and returns {@code true} on success.
 * See {@link RetryPolicy} for the backoff schedule.
 */
fun refreshAndReport(): Boolean = TODO()

// good — Markdown backticks and KDoc element links
/**
 * Calls [refresh] and returns `true` when the refresh succeeded.
 *
 * See [the retry policy][RetryPolicy] for the backoff schedule, and
 * [kotlin.time.Duration] for the units [RetryPolicy.initialDelay] uses.
 */
fun refreshAndReport(): Boolean = TODO()
```

## 4.18 Attach a usage example with `@sample` and a qualified function name rather than pasting a fenced code block.

> Why? [Document Kotlin code: KDoc](https://kotlinlang.org/docs/kotlin-doc.html)
> describes `@sample` as embedding the body of a function, named by its
> qualified name, into the generated documentation as a usage example. The
> difference from a pasted block is that the
> sample is real source: it compiles, it is refactored when you rename a
> parameter, and it fails the build if the API it demonstrates stops existing. A
> fenced block is a screenshot of code that was correct once. Point `@sample` at
> a function in a dedicated samples source set so the example is never shipped
> in production output — that placement is a Dokka convention rather than
> anything the KDoc page states.

```kotlin
// bad — a snippet nothing compiles, refactors, or type-checks
/**
 * Builds a client.
 *
 * ```
 * val client = HttpClient.build("https://api.example.com", 30)
 * ```
 */
fun build(baseUrl: String, timeout: Duration): HttpClient = TODO()

// good — the sample is compiled source that the refactoring tools can see
/**
 * An [HttpClient] bound to [baseUrl], failing any request that exceeds
 * [timeout].
 *
 * @sample com.example.samples.httpClientSample
 */
fun build(baseUrl: String, timeout: Duration): HttpClient = TODO()

// in the samples source set:
fun httpClientSample() {
    val client = build("https://api.example.com", 30.seconds)
    check(client.isReady)
}
```

## 4.19 Never write a `@deprecated` block tag; use the `@Deprecated` annotation.

> Why? [Document Kotlin code: KDoc](https://kotlinlang.org/docs/kotlin-doc.html)
> says it plainly: KDoc does not support a `@deprecated` tag, and directs you to
> the `@Deprecated` annotation instead. The tag is silently ignored, so it renders
> as ordinary prose and warns nobody — no compiler warning, no IDE strikethrough,
> no call-site diagnostic. The annotation does all three, and `replaceWith`
> gives the IDE an automated migration a caller can apply with one keystroke.
> **Violation if enabled — `detekt/DeprecatedBlockTag`**, which is inactive by
> default and is worth turning on for exactly this reason.

```kotlin
// bad — the tag is ignored; every existing call site compiles silently
/**
 * Sends the message.
 *
 * @deprecated use [send] instead.
 */
fun sendMessage(text: String) = TODO()

// good — warns at every call site and offers the automated fix
@Deprecated(
    message = "Superseded by send(Message); sendMessage cannot carry attachments.",
    replaceWith = ReplaceWith("send(Message(text))"),
    level = DeprecationLevel.WARNING,
)
fun sendMessage(text: String) = TODO()
```

## 4.20 Do not link a non-public declaration from public KDoc.

> Why? A `[link]` to a private property resolves inside the IDE and dangles in
> the generated documentation, where the reader has no access to the target and
> the renderer produces either a dead link or bare text. It also leaks the
> implementation into the contract — the reader now knows a `_cache` exists,
> which §4.11 says is not their business and which you are not free to rename.
> Describe the observable behaviour instead. **Violation if enabled —
> `detekt/KDocReferencesNonPublicProperty`**, inactive by default.

```kotlin
// bad — [_cache] is private, so the rendered docs point at nothing
class PriceBook {
    private val _cache = mutableMapOf<Symbol, Price>()

    /** Prices resolved so far, backed by [_cache]. */
    val cache: Map<Symbol, Price> get() = _cache
}

// good — describe what a caller can observe
class PriceBook {
    private val _cache = mutableMapOf<Symbol, Price>()

    /**
     * Prices resolved so far, as a read-only live view: entries appear as
     * [resolve] completes and are never evicted for the lifetime of this
     * instance.
     */
    val cache: Map<Symbol, Price> get() = _cache
}
```

## 4.21 Update the KDoc in the same commit as the signature it describes.

> Why? Documentation that contradicts the code is strictly worse than no
> documentation, because a reader trusts it and acts on it. The failure is
> systematic, not occasional: a parameter gets added, a `@param` for a deleted
> parameter survives, and the whole block keeps rendering as though it were
> current. Treat a stale tag as a compile error you happen to have to catch by
> hand — or make the tool catch it. **Violation if enabled —
> `detekt/OutdatedDocumentation` reports "any class, function or constructor
> with KDoc that does not match the declaration signature"**; it is inactive by
> default and is the single highest-value rule in the `comments` ruleset.

```kotlin
// bad — the signature gained `idempotencyKey` and lost `card`; the KDoc
// documents a function that no longer exists
/**
 * Charges [amount] to [card].
 *
 * @param card the card to charge.
 * @param amount the amount in minor units.
 */
fun charge(token: PaymentToken, amount: Money, idempotencyKey: String): Receipt =
    TODO()

// good
/**
 * Charges [amount] against [token], at most once per [idempotencyKey].
 *
 * @param idempotencyKey replaying a key seen before returns the original
 *     [Receipt] instead of charging again; keys are retained for 24 hours.
 */
fun charge(token: PaymentToken, amount: Money, idempotencyKey: String): Receipt =
    TODO()
```
