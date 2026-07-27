<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 27. Annotations & Use-Site Targets

In Java, an annotation goes on a declaration and stays there. In Kotlin it does
not, because one Kotlin declaration is several JVM declarations. Writing
`class User(val email: String)` produces a constructor parameter, a private
backing field, a getter, a Kotlin property that has no Java counterpart at all,
and — if it were a `var` — a setter and a setter parameter. An annotation you
write once has to land on one or more of those, and *which* ones it lands on
decides whether the framework reading it ever sees it. Most Kotlin annotation
bugs are not "the annotation is wrong"; they are "the annotation is somewhere
the reflection never looks."

Placement comes from the Android Kotlin style guide's
[annotations](https://developer.android.com/kotlin/style-guide#annotations)
and
[file-level annotations](https://developer.android.com/kotlin/style-guide#file-level_annotations)
sections and the matching
[Kotlin coding conventions: Annotations](https://kotlinlang.org/docs/coding-conventions.html#annotations),
[File annotations](https://kotlinlang.org/docs/coding-conventions.html#file-annotations),
and
[Modifiers order](https://kotlinlang.org/docs/coding-conventions.html#modifiers-order).
Semantics come from the Kotlin language documentation on
[annotations](https://kotlinlang.org/docs/annotations.html), which is where the
use-site target list and the default-target rules live.

Three neighbouring topics are deferred. The **semantics of the JVM interop
annotations** — what `@JvmStatic` actually generates, when `@JvmOverloads` is
worth it, how `@Throws` interacts with Java's checked exceptions — is
[Chapter 28](28-java-interop.md); §27.18 covers only where to write them.
**Bean Validation on Spring configuration and request bodies** is
[Chapter 43](43-spring-configuration-properties.md) and
[Chapter 44](44-spring-web-and-coroutines.md); §27.7 states the language-level
rule those chapters rely on. **KDoc**, including `@param`/`@return` block tags,
which are documentation markup and not annotations, is
[Chapter 4](04-kdoc.md).

**Tool alignment:** ktlint's `standard:annotation` owns annotation line
breaking and `standard:annotation-spacing` owns the blank-line rules around
annotations, so §27.1 to §27.4 are formatting rules that the formatter already
applies — they are stated here because the *use-site target* syntax is
inseparable from them. Nothing mechanically verifies that an annotation reached
the element a framework reads, so every target rule is a **Suggestion**.

## 27.1 Put each member or type annotation on its own line immediately before the declaration, at the same indentation.

> Why? The Android Kotlin style guide's
> [annotations](https://developer.android.com/kotlin/style-guide#annotations)
> section states it directly: "Member or type annotations are placed on
> separate lines immediately prior to the annotated construct," with the
> relaxations that "annotations without arguments can be placed on a single
> line" and "when only a single annotation without arguments is present, it may
> be placed on the same line as the declaration."
> [Kotlin coding conventions: Annotations](https://kotlinlang.org/docs/coding-conventions.html#annotations)
> agrees. The reason to keep argument-carrying annotations on their own lines
> is that they are code: `@Retention(SOURCE)` and `@Scheduled(cron = "0 0 * * *")`
> are declarations a reviewer reads, and burying them at the end of a
> declaration line hides them.
> **Violation — enforced by `ktlint/standard:annotation`.**

```kotlin
// bad — argument-carrying annotations crowded onto the declaration line
@Retention(SOURCE) @Target(FUNCTION, PROPERTY_SETTER, FIELD) annotation class Global

@Scheduled(cron = "0 0 3 * * *") @Transactional fun reconcile() { /* ... */ }

// good
@Retention(SOURCE)
@Target(FUNCTION, PROPERTY_SETTER, FIELD)
annotation class Global

// good — argument-less annotations may share a line
@JvmField @Volatile
var disposable: Disposable? = null

// good — a single argument-less annotation may sit on the declaration line
@Test fun selectAll() {
    // ...
}
```

## 27.2 Place all annotations before all modifiers.

> Why?
> [Kotlin coding conventions: Modifiers order](https://kotlinlang.org/docs/coding-conventions.html#modifiers-order)
> fixes the order of the modifier keywords themselves — visibility, then
> `expect`/`actual`, then `final`/`open`/`abstract`/`sealed`/`const`, and so on
> down to `operator` and `data` — and then adds one sentence about annotations:
> "Place all annotations before modifiers." A declaration read left to right
> should therefore go *annotations, modifiers, keyword, name*, every time.
> Interleaving them (`private @Named("Foo") val foo`) is legal Kotlin and reads
> as noise, because the reader has to re-scan the line to find where the
> declaration actually starts. **Suggestion.**

```kotlin
// bad — annotation buried between modifiers
private @Named("primary") val dataSource: DataSource

@JvmField internal @Volatile var cursor: Long = 0L

// good
@Named("primary")
private val dataSource: DataSource

@JvmField @Volatile
var cursor: Long = 0L
```

## 27.3 Put file annotations after the file comment, before the `package` statement, separated by a blank line.

> Why?
> [Kotlin coding conventions: File annotations](https://kotlinlang.org/docs/coding-conventions.html#file-annotations)
> gives both the position and the reason for the blank line: file annotations
> are "placed after the file comment (if any), before the `package` statement,
> and are separated from `package` with a blank line (to emphasize the fact
> that they target the file and not the package)." The Android style guide's
> [file-level annotations](https://developer.android.com/kotlin/style-guide#file-level_annotations)
> section places them the same way. The blank line is the only visual cue a
> reader has that the annotation targets the file rather than the package — and
> `@file:JvmName` is a binary-API decision, so it deserves to be noticed rather
> than skimmed past on the way to the imports. **Suggestion.**

```kotlin
// bad — no blank line, so `@file:JvmName` reads as annotating the package
/**
 * Copyright 2026 Example Ltd.
 */
@file:JvmName("FooBar")
package foo.bar

import java.time.Instant

// good
/**
 * Copyright 2026 Example Ltd.
 */
@file:JvmName("FooBar")

package foo.bar

import java.time.Instant
```

## 27.4 Use the `@[...]` bracket form only with an explicit use-site target, and only to combine two or more argument-less annotations.

> Why? The Android Kotlin style guide's
> [annotations](https://developer.android.com/kotlin/style-guide#annotations)
> section constrains the form precisely: "`@[...]` syntax may only be used with
> an explicit use-site target, and only for combining 2 or more annotations
> without arguments on a single line." The
> [Kotlin annotations reference](https://kotlinlang.org/docs/annotations.html)
> describes the same form as a way to "avoid repeating the target", and notes
> it cannot be used with the `all` meta-target. Outside that shape it is a
> compact way to obscure which annotations carry which arguments, and it buys
> nothing over one annotation per line. **Suggestion.**

```kotlin
// bad — bracket form with no use-site target, and with an argument inside
@[Volatile Transient]
var cursor: Long = 0L

@field:[Named("primary") Volatile]
var disposable: Disposable? = null

// good
@field:[Volatile Transient]
var cursor: Long = 0L

// good — the reference's own example: two markers, one setter target
class Example {
    @set:[Inject VisibleForTesting]
    var collaborator: Collaborator = NoopCollaborator
}
```

## 27.5 Before annotating a property, know which JVM elements that property generates.

> Why? A `val` in a primary constructor generates a constructor parameter, a
> backing field, a getter, and a Kotlin-only property descriptor; a `var` adds
> a setter and a setter parameter; a `by lazy` property adds a delegate field;
> an extension property adds a receiver parameter. Each of those is a separate
> annotation site, and the
> [use-site target list](https://kotlinlang.org/docs/annotations.html) names
> them all: `param`, `field`, `get`, `set`, `setparam`, `property`, `delegate`,
> `receiver`, plus `file` and the `all` meta-target. A framework reads exactly
> one of these — Hibernate Validator resolves constraints from fields and
> getters, JPA maps fields or property accessors depending on where `@Id` sits,
> a JSON binder reads the creator parameters — so "where does this annotation
> go?" has a factual answer, not a stylistic one. Note that `@property:`
> annotations are not visible to Java at all. **Suggestion.**

```kotlin
// bad — one annotation, five possible destinations, no decision made
class Account(
    @Sensitive var iban: String,
)

// good — say which element you meant
class Account(
    // the backing field, which is what a field-scanning mapper reads
    @field:Sensitive
    // the getter, which is what a getter-scanning serializer reads
    @get:Sensitive
    var iban: String,
)
```

## 27.6 Know the Kotlin 2.4 default-target rule — and do not lean on it.

> Why? When you omit the use-site target, the compiler does not guess: it
> intersects the annotation's own `@Target` with the applicable sites and then,
> per the
> [Kotlin annotations reference](https://kotlinlang.org/docs/annotations.html),
> "chooses one or more of them in the following order: 1. The constructor
> parameter target (`param`). 2. The property target (`property`). 3. The field
> target (`field`), if it's applicable and the property target (`property`)
> isn't." The reference's own example shows the consequence: a Jakarta `@Email`
> on a primary-constructor property applies "to both the constructor parameter
> and the field targets", because the property is declared in the primary
> constructor and has no custom accessors; the same annotation on a body
> property "only applies to the field target". These defaulting rules became Stable in
> Kotlin 2.4; they were introduced in Kotlin 2.2 behind
> `-Xannotation-default-target=param-property`, where the older behaviour
> (first applicable target only) stayed available as
> `-Xannotation-default-target=first-only`. So the default is now usually
> right — and it still depends on the annotation's `@Target`, on the compiler
> flags of whichever module is being built, and on whether the property sits in
> the constructor. Write the target when correctness depends on it.
> **Suggestion.**

```kotlin
// bad — relies on the default, so the same source means different things
// under `first-only` (param only) and under the 2.4 default (param + field).
// A field-reading validator sees nothing in the first case.
data class SignupRequest(
    @NotBlank val username: String,
    @Email val email: String,
)

// good — one reading, on every compiler, in every module
data class SignupRequest(
    @field:NotBlank val username: String,
    @field:Email val email: String,
)
```

## 27.7 Target Bean Validation constraints at the element the validator actually reads — `@field:` unless you have a reason otherwise.

> Why? Jakarta constraint annotations such as `@NotBlank`, `@Email`, `@Min`,
> and `@Size` declare Java targets that include `PARAMETER`, so a bare
> `@NotBlank` on a primary-constructor property can resolve to the constructor
> parameter — and a validator walking fields and getters will never see it. The
> failure mode is the worst kind: the code compiles, the annotation is right
> there in the source, and validation silently passes everything. `@field:`
> puts the constraint where field-and-getter-based validation looks; use
> `@get:` when the value is computed by a custom getter and there is no backing
> field to annotate. For the Spring binding and web-layer specifics, see
> [Chapter 43](43-spring-configuration-properties.md) and
> [Chapter 44](44-spring-web-and-coroutines.md). **Suggestion.**

```kotlin
// bad — the constraint may land on the constructor parameter, and a computed
// property has no field for it to land on at all
data class Registration(
    @Size(min = 8) val password: String,
    val firstName: String,
    val lastName: String,
) {
    @Size(max = 100)
    val fullName: String get() = "$firstName $lastName"
}

// good
data class Registration(
    @field:Size(min = 8) val password: String,
    val firstName: String,
    val lastName: String,
) {
    @get:Size(max = 100)
    val fullName: String get() = "$firstName $lastName"
}
```

## 27.8 For serialization annotations, target the element the library binds from, and be consistent across the class.

> Why? A JSON binder does not read "the property" — it reads creator
> parameters when deserialising through a constructor, and getters (or fields)
> when serialising. Those are different annotation sites, so an unqualified
> annotation can rename the output without renaming the input, or the reverse,
> and you get an object that round-trips through your own API incorrectly. The
> asymmetry is invisible in a unit test that only checks one direction. Decide
> per class whether you are annotating the creator parameter (`@param:`), the
> getter (`@get:`), the field (`@field:`), or all of them, and apply the same
> choice throughout. **Suggestion.**

```kotlin
// bad — the target is left to the default, so serialisation and
// deserialisation can disagree about the wire name
data class Payment(
    @JsonProperty("amount_minor") val amountMinor: Long,
    @JsonIgnore val internalTraceId: String,
)

// good — explicit on both directions
data class Payment(
    @param:JsonProperty("amount_minor")
    @get:JsonProperty("amount_minor")
    val amountMinor: Long,
    @get:JsonIgnore
    val internalTraceId: String,
)
```

## 27.9 Use `@delegate:` to annotate the field that stores a delegate.

> Why? For `val cache: Map<K, V> by lazy { ... }` the compiler generates a
> synthetic field holding the `Lazy` instance and a getter that reads through
> it. A plain annotation on that property resolves against the property's own
> applicable targets — never against the delegate field — which is why
> `@Transient` on a `by lazy` property does not keep the delegate out of Java
> serialization. `@delegate:` is the only way to name that field. This is one
> of the few targets with no plausible alternative, so its absence is almost
> always a bug rather than a style choice. **Suggestion.**

```kotlin
// bad — the annotation lands on the property, not the Lazy field, so the
// delegate is still serialized
class Report(private val rows: List<Row>) : java.io.Serializable {
    @Transient
    val summary: Summary by lazy { computeSummary(rows) }
}

// good
class Report(private val rows: List<Row>) : java.io.Serializable {
    @delegate:Transient
    val summary: Summary by lazy { computeSummary(rows) }
}
```

## 27.10 Use `@receiver:` to annotate the receiver of an extension function or property.

> Why? An extension's receiver is a parameter in the generated static method,
> but it has no name you can write, so it is the one parameter you cannot
> annotate positionally. Without `@receiver:` an annotation written before the
> function goes to the function itself; with it, the annotation lands on the
> receiver parameter, which is what nullability tooling, validation, and
> parameter-level checks read. If you find yourself unable to express a
> constraint on the receiver, that is also a signal the function may be better
> as an ordinary function with a named parameter — see
> [Chapter 8](08-functions.md). **Suggestion.**

```kotlin
// bad — @NotBlank annotates the function, where nothing validates it
@NotBlank
fun String.toSlug(): String = lowercase().replace(NON_ALNUM, "-")

// good
fun @receiver:NotBlank String.toSlug(): String = lowercase().replace(NON_ALNUM, "-")
```

## 27.11 Use `@setparam:` for a constraint that belongs to the value being assigned, not to the stored field.

> Why? A `var` property generates a setter whose single parameter is the
> incoming value. A constraint on the *field* describes the state the object
> may hold; a constraint on the *setter parameter* describes what a caller is
> allowed to pass. Those are usually the same, but not always — a field may
> legitimately start `null` while every assignment must be non-null, and a
> field-targeted constraint cannot express that. `@setparam:` is also what a
> Java caller's parameter-level nullability tooling reads when it calls your
> setter. **Suggestion.**

```kotlin
// bad — field-only constraint; a Java caller passing null to setNickname()
// gets no parameter-level signal, and the initial null state is disallowed
class Profile {
    @field:NotBlank
    var nickname: String? = null
}

// good — the field may start empty; every assignment must not be
class Profile {
    @setparam:NotBlank
    var nickname: String? = null
}
```

## 27.12 Use `@all:` when an annotation genuinely belongs on every generated element — not as a way to avoid deciding.

> Why? The `all` meta-target propagates one annotation to `param`, `property`,
> `field`, `get`, and (for a `var`) `setparam`. It became **Stable in Kotlin
> 2.4**; it was Experimental in Kotlin 2.2 behind `-Xannotation-target-all`.
> It is the right tool when a marker really is about the property as a whole —
> a `@Sensitive` or `@PersonalData` tag that every consumer should see
> regardless of which element it reflects over. It is the wrong tool as a
> shotgun, because it puts constraints on elements you did not think about, and
> a validator that scans both fields and getters will then run the same check
> twice. It also has hard limits: it cannot be combined with the `@[...]`
> bracket form (`@all:[A B]` is forbidden — write `@all:A @all:B`), it cannot
> be used with delegated properties, and it does not propagate to types,
> extension or context receivers, or parameters.
> **Suggestion.**

```kotlin
// bad — @all: used to dodge the question; the constraint now runs on the
// field and the getter, and the annotation is not even applicable everywhere
data class Registration(
    @all:Size(min = 8) val password: String,
)

// bad — forbidden combination
data class User(
    @all:[Sensitive PersonalData] val email: String,
)

// good — a marker that genuinely belongs everywhere
data class User(
    @all:PersonalData val email: String,
    @field:Size(max = 64) val displayName: String,
)
```

## 27.13 Declare your own annotations with an explicit `@Target` and `@Retention`.

> Why? Both defaults are permissive. An annotation declared with no `@Target`
> is applicable almost everywhere, so nothing stops a colleague putting your
> class-level marker on a local variable, and nothing documents where you meant
> it to go. `@Retention` defaults to `RUNTIME`, which keeps the annotation in
> the class file and reflectable — right for anything a framework scans, wasted
> metadata for a compile-time-only marker, which should be
> `AnnotationRetention.SOURCE`. Add `@MustBeDocumented` when the annotation is
> part of the public contract (KDoc will then include it) and `@Repeatable`
> only when repetition has a defined meaning. **Suggestion.**

```kotlin
// bad — applicable anywhere, retained at runtime for no reason, undocumented
annotation class Experimental

// good
@Target(AnnotationTarget.CLASS, AnnotationTarget.FUNCTION)
@Retention(AnnotationRetention.SOURCE)
@MustBeDocumented
annotation class InternalUseOnly(val reason: String)

// good — runtime retention because a scanner reads it, repeatable because
// several tags on one endpoint is meaningful
@Target(AnnotationTarget.FUNCTION)
@Retention(AnnotationRetention.RUNTIME)
@Repeatable
@MustBeDocumented
annotation class AuditEvent(val name: String)
```

## 27.14 Keep annotation parameters to compile-time constants, and use array syntax for multi-valued ones.

> Why? An annotation argument must be a constant expression, an array of them,
> a `KClass` literal, an enum constant, or another annotation — you cannot pass
> a computed value, a `Duration`, or an object. That constraint pushes you
> toward `String`, `Int`, `Boolean`, enums, and `KClass`, and toward parsing
> anything richer at the point of use.
> [Kotlin coding conventions: Collection literals in annotations](https://kotlinlang.org/docs/coding-conventions.html#collection-literals-in-annotations)
> shows the multi-valued form and its wrapping: an `Array<String>` parameter
> takes bracketed values, one per line, with a trailing comma. Note this
> bracket syntax inside an annotation is long-standing and unrelated to the
> collection literals of §26.19, which are Experimental in Kotlin 2.4.
> **Suggestion.**

```kotlin
// bad — a Duration parameter will not compile as an annotation argument, and
// a comma-joined string re-invents parsing the compiler already does
annotation class Cached(val ttl: Duration, val tags: String)

@Cached(ttl = Duration.ofMinutes(5), tags = "reports,billing")
fun monthlySummary(): Summary = TODO()

// good
annotation class ApplicableFor(val services: Array<String>)

@ApplicableFor([
    "serializer",
    "balancer",
    "database",
    "inMemoryCache",
])
fun run() {}

annotation class Cached(val ttlSeconds: Long)

@Cached(ttlSeconds = 300)
fun monthlySummary(): Summary = TODO()
```

## 27.15 Scope every `@Suppress` to the narrowest declaration, name the exact diagnostic, and say why.

> Why? `@Suppress` silences a compiler diagnostic, which means it silences it
> for everything inside the annotated element — a file-level
> `@file:Suppress("UNCHECKED_CAST")` disables that check for every cast in the
> file, including the ones added next year by someone who never saw the
> annotation. Narrow it to the smallest declaration that contains the genuinely
> unavoidable case, name one diagnostic rather than a list, and put the
> justification next to it, because a bare suppression is indistinguishable
> from an unreviewed one. The same reasoning applies to `@Suppress` of a detekt
> rule id and to `ktlint-disable` directives — see
> [Chapter 47](47-ktlint-and-detekt.md). **Suggestion.**

```kotlin
// bad — whole-file, several diagnostics, no reason
@file:Suppress("UNCHECKED_CAST", "NOTHING_TO_INLINE", "UNUSED_PARAMETER")

package com.example.serde

// good — one diagnostic, one declaration, one reason
// The registry is keyed by KClass<T> and only ever stores a Codec<T> for
// that key, so this cast is checked by the put-side API.
@Suppress("UNCHECKED_CAST")
private fun <T : Any> codecFor(type: KClass<T>): Codec<T> =
    codecs.getValue(type) as Codec<T>
```

## 27.16 Deprecate with a message, a `ReplaceWith` when a mechanical replacement exists, and a `DeprecationLevel` that escalates over time.

> Why? `@Deprecated` takes a required `message`, an optional
> `replaceWith: ReplaceWith`, and a `level: DeprecationLevel` defaulting to
> `WARNING`. `ReplaceWith` is not documentation — the IDE offers it as an
> automatic fix, so supplying it converts a migration into a keystroke, and
> its `imports` parameter carries any import the replacement needs.
> `DeprecationLevel` is the migration schedule expressed in the type system:
> `WARNING` announces, `ERROR` breaks compilation while keeping the symbol
> callable from already-compiled code, and `HIDDEN` removes it from the
> compiler's view entirely while preserving binary compatibility. A deprecation
> that stays at `WARNING` forever is a deprecation nobody acts on.
> **Suggestion.**

```kotlin
// bad — no message content, no replacement, no plan
@Deprecated("deprecated")
fun sendEmail(to: String, body: String) { /* ... */ }

// good — says what to do, and the IDE can do it
@Deprecated(
    message = "Use send(Message) so attachments and headers survive.",
    replaceWith = ReplaceWith(
        expression = "send(Message(to = to, body = body))",
        imports = ["com.example.mail.Message"],
    ),
    level = DeprecationLevel.WARNING,
)
fun sendEmail(to: String, body: String) { /* ... */ }

// good — one release later, the same symbol escalates
@Deprecated(
    message = "Use send(Message). Removed in 4.0.",
    replaceWith = ReplaceWith("send(Message(to = to, body = body))"),
    level = DeprecationLevel.ERROR,
)
fun sendEmail(to: String, body: String) { /* ... */ }
```

## 27.17 Gate unstable API behind `@RequiresOptIn`, and consume opt-in API with `@OptIn` at the narrowest scope — not a module-wide compiler flag.

> Why? `@RequiresOptIn` is the mechanism the whole Kotlin ecosystem uses to
> mark API that may change, including every experimental stdlib and coroutines
> API this skill flags. Declaring your own marker (an annotation class
> annotated `@RequiresOptIn`) forces callers to acknowledge the risk in code,
> which is a reviewable event; its `level` defaults to
> `RequiresOptIn.Level.ERROR`, and downgrading to `WARNING` should be a
> deliberate choice. On the consuming side, `@OptIn(Marker::class)` on the one
> function that needs it keeps the acknowledgement next to the risk; adding
> `-opt-in=` to the module's compiler options silently opts in every current
> and future use in the module, which is exactly the blanket the mechanism
> exists to prevent. This is also the correct way to consume the Experimental
> features named in `SKILL.md` where they are annotation-gated rather than
> flag-gated. **Suggestion.**

```kotlin
// bad — module-wide opt-in in the build script, so nothing in the source
// records that any of this is unstable, and next year's call sites inherit
// the opt-in without anyone reviewing it
// build.gradle.kts:
//   kotlin { compilerOptions { optIn.add("com.example.ExperimentalStreamingApi") } }
fun decodeAll(inputs: List<String>): List<ByteArray> =
    inputs.map { streamingDecoder().decode(it) }

// good — declare your own marker for your own unstable surface
@RequiresOptIn(
    message = "The streaming decoder API is unstable and may change in 2.x.",
    level = RequiresOptIn.Level.ERROR,
)
@Retention(AnnotationRetention.BINARY)
@Target(AnnotationTarget.CLASS, AnnotationTarget.FUNCTION)
annotation class ExperimentalStreamingApi

@ExperimentalStreamingApi
fun streamingDecoder(): StreamingDecoder = TODO()

// good — and acknowledge someone else's marker at the call site that needs it
@OptIn(ExperimentalStreamingApi::class)
fun decodeAll(inputs: List<String>): List<ByteArray> =
    inputs.map { streamingDecoder().decode(it) }
```

## 27.18 Write the JVM interop annotations on the element they target — `@get:JvmName` on a property, `@JvmField` only on a field-backed one.

> Why? The interop annotations have narrow `@Target` sets and will not silently
> relocate. `@JvmName` targets functions, getters, setters, and files, so a
> bare `@JvmName` on a property is a compile error and `@get:JvmName` /
> `@set:JvmName` is the working form. `@JvmField` targets the field and only
> applies to a property with a backing field, no custom accessors, and
> non-private visibility — it removes the getter entirely, which is a binary
> API decision, not a formatting one. `@JvmStatic` belongs on a member of an
> `object` or `companion object`, `@JvmOverloads` on a function or constructor
> with default parameter values, and `@Throws` on the function whose Java
> callers need the `throws` clause. What each one *does* to the generated
> bytecode, and when the trade is worth making, is
> [Chapter 28](28-java-interop.md). **Suggestion.**

```kotlin
// bad — @JvmName is not applicable to a property; @JvmField on a property
// with a custom getter has no field to annotate; @JvmStatic outside a
// companion has no static context
class Rectangle(val width: Int, val height: Int) {
    @JvmName("getAreaInPixels")
    val area: Int get() = width * height

    @JvmField
    val diagonal: Double get() = hypot(width.toDouble(), height.toDouble())

    @JvmStatic
    fun unit(): Rectangle = Rectangle(1, 1)
}

// good
class Rectangle @JvmOverloads constructor(
    val width: Int,
    val height: Int = width,
) {
    @get:JvmName("getAreaInPixels")
    val area: Int get() = width * height

    @JvmField
    val label: String = "${width}x$height"

    @Throws(IllegalArgumentException::class)
    fun scaledBy(factor: Int): Rectangle {
        require(factor > 0) { "factor must be positive, was $factor" }
        return Rectangle(width * factor, height * factor)
    }

    companion object {
        @JvmStatic
        fun unit(): Rectangle = Rectangle(1, 1)
    }
}
```
