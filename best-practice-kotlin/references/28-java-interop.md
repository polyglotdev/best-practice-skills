<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 28. Java Interop

Kotlin's interoperability with Java is the reason most teams can adopt it at
all, and it is also where most of Kotlin's guarantees quietly stop holding.
A Java method has no opinion about nullability, no default arguments, no
`internal`, and a checked-exception contract that Kotlin does not enforce.
Every one of those gaps is a place where correct-looking Kotlin compiles and
then fails at runtime, or where a Kotlin API that reads beautifully from
Kotlin is unusable from Java.

This chapter covers both directions. The first half is **calling Java from
Kotlin** — platform types, nullability annotations, SAM conversion, property
mapping, arrays, varargs, and checked exceptions — drawn from
[Calling Java from Kotlin](https://kotlinlang.org/docs/java-interop.html) and
the coding conventions on
[platform types](https://kotlinlang.org/docs/coding-conventions.html#platform-types).
The second half is **calling Kotlin from Java** — `@JvmStatic`, `@JvmField`,
`@JvmOverloads`, `@JvmName`, `@Throws`, file facade classes, `internal`
mangling, and interface default methods — drawn from
[Calling Kotlin from Java](https://kotlinlang.org/docs/java-to-kotlin-interop.html).

One topic is deliberately deferred. The *nullability discipline* itself —
why `!!` is banned, what to write instead, and how smart casting behaves —
is [Chapter 6, Null Safety](06-null-safety.md); §28.1 states only the
boundary rule that chapter depends on. Value class mangling is introduced
here in §28.13 but the design question of *when* to reach for a value class
is [Chapter 12, Value Classes](12-value-classes.md).

**Tool alignment:** `detekt/HasPlatformType` reports a public declaration
whose type was inferred from a platform type, which is exactly the §28.1
failure — though it is conservative and only inspects public API.
`detekt/UnsafeCallOnNullableType` catches the `!!` that a platform type
usually invites. (`detekt/UnsafeCast` sounds relevant here but is not: its
documented purpose is to report "casts that will never succeed", so it does
**not** flag the unchecked `as` on a raw Java collection.) Rules a named
check enforces are marked **Violation**; the rest are **Suggestion**.

## 28.1 Give every value crossing the Java boundary an explicit Kotlin type at the point it arrives.

> Why? A type coming from unannotated Java is a *platform type*, written
> `T!` in tooltips and error messages, which
> [the reference](https://kotlinlang.org/docs/java-interop.html#null-safety-and-platform-types)
> defines as "`T` or `T?`". Kotlin performs **no** null checks on a platform
> type: it will let you call a method on it, pass it where a non-null `T` is
> required, and store it in a non-null field, and the NPE surfaces somewhere
> else entirely. The documentation's own remedy is this rule: "add an
> explicit type annotation to your Kotlin variable to restore null-safety
> checks." Writing the type is a decision — you are asserting either "this
> is always present" or "this may be absent" — and once written, the
> compiler enforces it everywhere downstream.
> **Violation — enforced by `detekt/HasPlatformType`** for public
> declarations. See [Chapter 6, §6.10](06-null-safety.md).

```kotlin
// bad — `name` is String!, so the compiler checks nothing; the NPE lands
// three call frames away, inside greet()
fun welcome(user: LegacyUser) {
    val name = user.getDisplayName() // inferred String! from unannotated Java
    greet(name)                      // accepted even if getDisplayName() returns null
}

// good — the boundary states what is actually true, and the compiler
// enforces it from here on
fun welcome(user: LegacyUser) {
    val name: String? = user.getDisplayName()
    greet(name ?: "there")
}

// good — when absence is genuinely a bug, say so at the boundary
fun welcome(user: LegacyUser) {
    val name: String = requireNotNull(user.getDisplayName()) {
        "legacy user ${user.getId()} has no display name"
    }
    greet(name)
}
```

## 28.2 Turn on `-Xjsr305=strict` so JSR-305 nullability annotations become compile errors instead of warnings.

> Why? [The reference](https://kotlinlang.org/docs/java-interop.html#jsr-305-support)
> states that "the default behavior is the same to `-Xjsr305=warn`" — so a
> Java library that has carefully annotated `@Nonnull` and `@Nullable` gives
> you a *warning* you will scroll past, not a type error. Under `strict`,
> `@Nonnull String` arrives as Kotlin `String` and `@Nullable String`
> arrives as `String?`, and the platform-type hole in §28.1 closes for every
> annotated dependency you have. The flag is a one-line build change that
> converts a whole class of runtime NPEs into compile failures.
> **Suggestion** — no analyser can tell that you *omitted* a compiler flag.

```kotlin
// bad — build.gradle.kts with no opt-in; annotated Java still arrives as
// platform types and mismatches are warnings
kotlin {
    compilerOptions {
        jvmTarget.set(JvmTarget.JVM_21)
    }
}

// good
kotlin {
    compilerOptions {
        jvmTarget.set(JvmTarget.JVM_21)
        freeCompilerArgs.addAll(
            "-Xjsr305=strict",
        )
    }
}
```

## 28.3 On Java you own, annotate with JSpecify `@NullMarked` at the package level rather than annotating declaration by declaration.

> Why? Kotlin understands
> [JSpecify's `org.jspecify.annotations`](https://kotlinlang.org/docs/java-interop.html#nullability-annotations)
> — `@Nullable`, `@NonNull`, `@NullMarked`, `@NullUnmarked` — and the
> reference states that "by default, the Kotlin compiler reports nullability
> mismatches for JSpecify annotations as errors." `@NullMarked` "marks all
> types within a scope as non-nullable by default unless annotated
> otherwise", which inverts the burden: you annotate the handful of things
> that genuinely can be null instead of the hundreds that cannot. A
> per-declaration approach always leaves gaps, and every gap is a platform
> type. Kotlin also recognises JetBrains, Android, JSR-305, FindBugs,
> Eclipse, Lombok, RxJava 3, and Vert.x flavours — but pick **one** per
> codebase. **Suggestion.**

```kotlin
// bad — only some of the Java is annotated, so Kotlin sees a mix of String and
// String! and no reader can tell which gaps are deliberate
fun summarise(repo: OrderRepository): String {
    val order = repo.findById(id)       // Order? — annotated, checked
    val all = repo.findAll()            // (Mutable)List<Order!>! — unchecked
    return "${all.size} orders, latest ${order?.id}"
}

// good — with @NullMarked on the package, everything unannotated is non-null,
// and only findById is nullable
fun summarise(repo: OrderRepository): String {
    val order: Order? = repo.findById(id)
    val all: List<Order> = repo.findAll()
    return "${all.size} orders, latest ${order?.id}"
}
```

```java
// good — the Java side: package-info.java makes non-null the default, and only
// the genuinely absent case carries an annotation
@NullMarked
package com.example.orders;

import org.jspecify.annotations.NullMarked;
```

```java
// good — the repository itself, inside that package
package com.example.orders;

import org.jspecify.annotations.Nullable;

public final class OrderRepository {
    public @Nullable Order findById(String id) { ... }
    public List<Order> findAll() { ... }   // arrives in Kotlin as List<Order>
}
```

## 28.4 Let SAM conversion write the implementation of a Java functional interface — and remember it does not work for abstract classes.

> Why? [The reference](https://kotlinlang.org/docs/java-interop.html#sam-conversions)
> is explicit that "Kotlin function literals can be automatically converted
> into implementations of Java interfaces with a single non-default method",
> which turns a five-line anonymous object into a lambda. The trap is in the
> next sentence: "SAM conversions only work for interfaces, not for abstract
> classes, even if those also have just a single abstract method." Reaching
> for a lambda against an abstract class produces a type mismatch that reads
> confusingly, and the fix is an `object :` expression, not a cast.
> **Suggestion.**

```kotlin
// bad — an anonymous object where a lambda would do
executor.execute(object : Runnable {
    override fun run() {
        reindex()
    }
})

// good — SAM conversion; the Java signature is void execute(Runnable)
executor.execute { reindex() }

// good — an abstract class has no SAM conversion, so `object :` is correct,
// not a workaround
val task = object : TimerTask() { // TimerTask is an abstract class
    override fun run() {
        reindex()
    }
}
```

## 28.5 Access Java getters and setters as Kotlin properties, and know the three shapes where that mapping does not happen.

> Why? [The reference](https://kotlinlang.org/docs/java-interop.html#getters-and-setters)
> maps "no-argument methods with names starting with `get` and
> single-argument methods with names starting with `set`" onto properties,
> so `calendar.firstDayOfWeek = Calendar.MONDAY` calls
> `setFirstDayOfWeek`. Three shapes fall outside the rule and force method
> syntax, and guessing wrong costs a compile error you will misread as a
> missing dependency: (1) a setter with no matching getter — "if the Java
> class only has a setter, it isn't visible as a property in Kotlin because
> Kotlin doesn't support set-only properties"; (2) a getter that does not
> follow the `get`/`is` convention; (3) a `get` method that takes an
> argument. Note also that `is`-prefixed accessors map to a property named
> after the getter, so `isLenient()` becomes `isLenient`, not `lenient`.
> **Suggestion.**

```kotlin
// bad — method syntax where a property exists, and a guessed property where
// none does
val day = calendar.getFirstDayOfWeek()
calendar.setFirstDayOfWeek(Calendar.MONDAY)
connection.readTimeout = 5_000  // compile error: setter-only in this Java API

// good
val day = calendar.firstDayOfWeek
calendar.firstDayOfWeek = Calendar.MONDAY
if (!calendar.isLenient) {          // isLenient(), not getLenient()
    calendar.isLenient = true       // setLenient(true)
}
connection.setReadTimeout(5_000)    // setter-only: method syntax is correct
val body = response.fetchBody()     // non-conventional name: not a property
```

## 28.6 Use the primitive array types for primitive Java arrays; `Array<Int>` is not `int[]`.

> Why? [The reference](https://kotlinlang.org/docs/java-interop.html#java-arrays)
> states that specialized classes exist "for every type of primitive array
> (`IntArray`, `DoubleArray`, `CharArray`, and so on)", that "they are not
> related to the `Array` class", and that they "are compiled down to Java's
> primitive arrays for maximum performance". `Array<Int>` compiles to
> `Integer[]` — a different JVM type, which will not bind to a Java `int[]`
> parameter, and which boxes every element. Getting this wrong produces a
> signature mismatch that looks like a missing overload. Note also that
> Kotlin arrays are invariant "unlike Java", so `Array<String>` is not an
> `Array<Any>` — a deliberate divergence that "prevents a possible runtime
> failure". **Suggestion.**

```kotlin
// bad — Integer[]; will not bind to a Java `void sum(int[] values)`
val values: Array<Int> = arrayOf(1, 2, 3)
stats.sum(values)

// good — compiles to int[]
val values: IntArray = intArrayOf(1, 2, 3)
stats.sum(values)

// good — reading a Java `String[]` gives Array<(out) String!>!, so §28.1
// applies: state the element nullability you actually expect
val tags: Array<String> = legacy.getTags()
```

## 28.7 Pass an array to a Java vararg method with the spread operator `*`.

> Why? Kotlin does not silently expand an array into a vararg call. The
> [reference](https://kotlinlang.org/docs/java-interop.html#java-varargs)
> shows the required form directly: "you need to use the spread operator `*`
> to pass the `IntArray`". Without it, the array is passed as a *single*
> argument, which for an `Object...` parameter compiles and silently
> produces a one-element vararg containing an array — a bug that survives
> code review and shows up as `[[Ljava.lang.Object;` in a log line.
> **Suggestion.**

```kotlin
// bad — for a Java `void log(Object... args)` this passes ONE argument that
// happens to be an array
val args = arrayOf(orderId, total)
legacyLogger.log(args)

// good
val args = arrayOf(orderId, total)
legacyLogger.log(*args)

// good — primitive varargs need the matching primitive array
val indices = intArrayOf(0, 1, 2, 3)
javaObj.removeIndicesVarArg(*indices)
```

## 28.8 Treat a Java checked exception as a real failure mode even though Kotlin will not make you catch it.

> Why? [The reference](https://kotlinlang.org/docs/java-interop.html#checked-exceptions)
> is unambiguous: "in Kotlin, all exceptions are unchecked... when you call
> a Java method that declares a checked exception, Kotlin does not force you
> to do anything." The compiler's silence is not evidence that the call
> cannot fail. `IOException`, `SQLException`, and `InterruptedException`
> still propagate at runtime; they simply do so out of a function whose
> signature never mentioned them. Handle where you can act, translate to
> your own domain error where you cannot, and document what escapes. See
> [Chapter 24, Exceptions & `Result`](24-exceptions-and-result.md) for the
> handling policy. **Suggestion.**

```kotlin
// bad — compiles cleanly; IOException escapes a function whose signature and
// KDoc both claim it always returns a Config
fun loadConfig(path: Path): Config =
    Config.parse(Files.readString(path))

// good — the failure is translated at the boundary where it can be named
fun loadConfig(path: Path): Config =
    try {
        Config.parse(Files.readString(path))
    } catch (e: IOException) {
        throw ConfigUnavailableException("cannot read config at $path", e)
    }
```

## 28.9 Annotate a companion-object member with `@JvmStatic` when Java callers should reach it as a static.

> Why? Without it, a Java caller must write `Foo.Companion.create()` —
> [the reference](https://kotlinlang.org/docs/java-to-kotlin-interop.html#static-methods)
> notes that `@JvmStatic` makes the compiler "generate both a static method
> in the enclosing class of the object and an instance method in the object
> itself", so both call styles work. Leaving it off does not break Java
> callers, it just exports an awkward API that every Java consumer has to
> learn. Apply it to factory functions and constants that are part of your
> published surface; skip it for members only Kotlin calls, because each one
> costs an extra generated method. **Suggestion.**

```kotlin
// bad — Java must write OrderId.Companion.parse("...")
class OrderId private constructor(val value: String) {
    companion object {
        fun parse(raw: String): OrderId = OrderId(raw.trim())
    }
}

// good — Java writes OrderId.parse("..."), Kotlin is unchanged
class OrderId private constructor(val value: String) {
    companion object {
        @JvmStatic
        fun parse(raw: String): OrderId = OrderId(raw.trim())
    }
}
```

## 28.10 Use `@JvmField` — or `const`, or `lateinit` — when a Kotlin property must appear to Java as a plain field.

> Why? A Kotlin property compiles to a private field plus accessors, so a
> Java caller sees `getComparator()`, not `COMPARATOR`. `@JvmField` exposes
> the backing field directly with "the same visibility as the underlying
> property". The reference lists the preconditions precisely — the property
> must have "a backing field", be "not private", have no `open`, `override`
> or `const` modifiers, and not be "a delegated property" — and violating
> any of them is a compile error, not a silent fallback. For compile-time
> constants use `const` instead, which "turns into static fields in Java" on
> its own. Do not reach for `@JvmField` merely to avoid writing accessors in
> Kotlin: it removes your ability to add validation later without breaking
> binary compatibility. **Suggestion.**

```kotlin
// bad — Java must call Key.Companion.getCOMPARATOR()
class Key(val value: Int) {
    companion object {
        val COMPARATOR: Comparator<Key> = compareBy { it.value }
    }
}

// good — Java writes Key.COMPARATOR
class Key(val value: Int) {
    companion object {
        @JvmField
        val COMPARATOR: Comparator<Key> = compareBy<Key> { it.value }
    }
}

// good — a compile-time constant needs no annotation
object Protocol {
    const val VERSION = 9
}
```

## 28.11 Annotate any function or constructor with default arguments with `@JvmOverloads` if Java is expected to call it.

> Why? [The reference](https://kotlinlang.org/docs/java-to-kotlin-interop.html#overloads-generation)
> states that a function with default parameter values "is visible in Java
> only as a full signature, with all parameters present" — so the whole
> point of the defaults evaporates the moment a Java caller arrives, and
> they must pass every argument explicitly, including the ones your API was
> designed to hide. `@JvmOverloads` generates one extra overload per
> defaulted parameter, "which has this parameter and all parameters to the
> right of it in the parameter list removed". Note the two limits: on a
> constructor the annotation goes *before* the `constructor` keyword, and it
> "can't be used on abstract methods, including methods defined in
> interfaces". **Suggestion.**

```kotlin
// bad — Java must write new Circle(0, 0, 1.0) and draw("x", 1, "red")
class Circle(centerX: Int, centerY: Int, radius: Double = 1.0) {
    fun draw(label: String, lineWidth: Int = 1, color: String = "red") { ... }
}

// good — Java gets new Circle(0, 0), draw("x"), draw("x", 2), and the rest
class Circle @JvmOverloads constructor(
    centerX: Int,
    centerY: Int,
    radius: Double = 1.0,
) {
    @JvmOverloads
    fun draw(label: String, lineWidth: Int = 1, color: String = "red") { ... }
}
```

## 28.12 Use `@JvmName` to resolve a JVM signature clash, and `@get:JvmName` / `@set:JvmName` to rename generated accessors.

> Why? Generic erasure makes `List<String>.filterValid()` and
> `List<Int>.filterValid()` collide on the JVM even though Kotlin resolves
> them fine. The reference's fix is `@JvmName("filterValidInt")`: "from
> Kotlin, they are accessible by the same name `filterValid`, but from Java
> it is `filterValid` and `filterValidInt`." The same annotation with a
> use-site target renames a property's accessors without you writing them by
> hand. One constraint worth internalising, which the interop page does not
> state but the compiler enforces: applying `@JvmName` to a member that
> participates in virtual dispatch (`open`, `override`, `abstract`, or an
> interface member) is rejected with the `INAPPLICABLE_JVM_NAME` diagnostic,
> because nothing could force an inheritor to repeat the rename. See
> [Chapter 27, Annotations & Use-Site Targets](27-annotations-and-use-site-targets.md)
> for use-site target syntax. **Suggestion.**

```kotlin
// bad — "platform declaration clash: two declarations have the same JVM
// signature"
fun List<String>.filterValid(): List<String> = filter { it.isNotBlank() }
fun List<Int>.filterValid(): List<Int> = filter { it > 0 }

// good
fun List<String>.filterValid(): List<String> = filter { it.isNotBlank() }

@JvmName("filterValidInt")
fun List<Int>.filterValid(): List<Int> = filter { it > 0 }

// good — Java sees x() and changeX(), Kotlin still sees `x`
@get:JvmName("x")
@set:JvmName("changeX")
var x: Int = 23
```

## 28.13 Add `@JvmName` to any function whose signature contains a value class, or Java cannot call it at all.

> Why? [The inline-class reference](https://kotlinlang.org/docs/inline-classes.html#mangling)
> explains that "functions using inline classes are mangled by adding some
> stable hashcode to the function name", so `fun compute(x: UInt)` is
> emitted as `public final void compute-<hashcode>(int x)`. A hyphen is not
> a legal Java identifier character, which makes the method *literally
> unnameable* from Java source. The documented remedy is this rule: "you
> should manually disable mangling: add the `@JvmName` annotation before the
> function declaration." Mangling exists for a real reason — two functions
> taking `Int` and `UInt` would otherwise clash — so removing it means you
> own the clash. See [Chapter 12, Value Classes](12-value-classes.md).
> **Suggestion.**

```kotlin
// bad — emitted as compute-<hashcode>(int); no Java source can call it
@JvmInline
value class UserId(val raw: Int)

fun compute(id: UserId) { ... }

// good
@JvmInline
value class UserId(val raw: Int)

@JvmName("computeUserId")
fun compute(id: UserId) { ... }
```

## 28.14 Name the generated file facade class with `@file:JvmName`, and use `@file:JvmMultifileClass` to merge several files into one.

> Why? Top-level declarations in `app.kt` compile "into static methods of a
> Java class named `org.example.AppKt`" — a name derived from the file, which
> means renaming a file silently breaks every Java caller, and `AppKt` is not
> a name you would ever choose. `@file:JvmName("DemoUtils")` fixes the
> exported name to something stable and intentional. When two files would
> generate the same facade — normally an error — `@file:JvmMultifileClass`
> in *all* of them makes the compiler "generate a single Java facade class
> which has the specified name and contains all the declarations". Both
> annotations must precede the `package` statement. **Suggestion.**

```kotlin
// bad — string-extensions.kt
// Java must call org.example.StringExtensionsKt.slugify(...), and renaming the
// file is a breaking change nobody notices
package org.example

fun String.slugify(): String = ...

// good — string-extensions.kt
// Java calls org.example.StringUtils.slugify(...) whatever the file is called
@file:JvmName("StringUtils")

package org.example

fun String.slugify(): String = ...
```

```kotlin
// good — two files merged into one facade, strings-case.kt
@file:JvmName("StringUtils")
@file:JvmMultifileClass

package org.example

fun String.slugify(): String = ...

// good — the second half of the same facade, strings-trim.kt
@file:JvmName("StringUtils")
@file:JvmMultifileClass

package org.example

fun String.squeeze(): String = ...
```

## 28.15 Declare `@Throws` on any Kotlin function whose Java callers must handle a checked exception.

> Why? The mirror image of §28.8. Because "Kotlin does not have checked
> exceptions... normally the Java signatures of Kotlin functions do not
> declare exceptions thrown" — so a Kotlin function that genuinely throws
> `IOException` presents Java with a signature that promises it cannot. The
> Java caller writes no `catch`, and if they *try* to, `javac` rejects it as
> unreachable. This matters most when implementing a Java interface whose
> contract declares a checked exception: `AutoCloseable.close`,
> `Callable.call`, `ObjectInputStream` hooks. **Suggestion.**

```kotlin
// bad — Java sees `void writeToFile()`; a caller cannot catch IOException,
// and javac rejects the attempt as unreachable
fun writeToFile() {
    throw IOException("disk full")
}

// good
@Throws(IOException::class)
fun writeToFile() {
    throw IOException("disk full")
}

// good — implementing a Java interface whose contract declares one
class Connection : AutoCloseable {
    @Throws(IOException::class)
    override fun close() { ... }
}
```

## 28.16 Never treat `internal` as an encapsulation boundary against Java.

> Why? [The reference](https://kotlinlang.org/docs/java-to-kotlin-interop.html#visibility)
> states it in four words: "`internal` declarations become `public` in
> Java." The compiler "mangles the names of `internal` members in bytecode",
> which prevents *accidental* overrides — but a determined or merely
> confused Java caller can still invoke the mangled name, and crucially "the
> names of public members of `internal` classes aren't mangled and remain
> callable from Java". In a mixed-language module, `internal` is a Kotlin
> convention, not a JVM guarantee. If something must be unreachable from
> Java, make it `private`, or move it behind a package boundary you control.
> See [Chapter 5, Declarations & Visibility](05-declarations-and-visibility.md).
> **Suggestion.**

```kotlin
// bad — "internal so Java can't touch it" is false: TokenCache is internal
// but its public members are not mangled and are callable from Java
internal class TokenCache {
    fun evictAll() { ... }   // callable from Java as new TokenCache().evictAll()
}

// good — private members are genuinely inaccessible; the public surface is
// deliberate
class TokenCache private constructor() {
    private fun evictAll() { ... }

    internal fun refresh() { ... } // mangled: emitted as refresh$moduleName

    companion object {
        internal fun create(): TokenCache = TokenCache()
    }
}
```

## 28.17 Set `-jvm-default=no-compatibility` on a new module; do not carry `DefaultImpls` you never needed.

> Why? Kotlin "compiles functions declared in interfaces to default methods
> unless configured otherwise", and the mode is chosen by the stable
> `-jvm-default` option, which
> [Kotlin 2.2](https://kotlinlang.org/docs/whatsnew22.html) introduced
> "replacing the deprecated `-Xjvm-default` option". The default, `enable`,
> also emits "compatibility bridges and `DefaultImpls` classes" so that code
> compiled against older Kotlin still links. `no-compatibility` "generates
> only default implementations in interfaces" and is documented as intended
> "for new codebases that don't interact with code that relies on
> `DefaultImpls` classes" — smaller output and a cleaner Java-facing
> interface. It is a binary-compatibility decision, so make it once, at
> module creation, and never flip it on a published artifact. If you still
> have `-Xjvm-default=all` in a build file, that option is deprecated:
> migrate it. **Suggestion.**

```kotlin
// bad — a 2.4 build still carrying the deprecated experimental flag
kotlin {
    compilerOptions {
        freeCompilerArgs.add("-Xjvm-default=all")
    }
}

// good — the stable option, on a module with no legacy Kotlin consumers
kotlin {
    compilerOptions {
        freeCompilerArgs.add("-jvm-default=no-compatibility")
    }
}
```

```kotlin
// the declaration this governs: `move` becomes a real Java default method
interface Robot {
    fun move() {
        println("~walking~")
    }

    fun speak()
}
```

## 28.18 Do not expose `data class` `copy()` as the Java-facing mutation API.

> Why? `copy()` is generated with a default value for *every* component, and
> §28.11's rule applies: Java sees only the full signature, so
> `order.copy(status = SHIPPED)` becomes
> `order.copy(order.getId(), order.getCustomerId(), SHIPPED, order.getTotal(), ...)`
> — every field respelled by hand at every call site, and a new field on the
> data class silently breaks every Java caller. `@JvmOverloads` cannot help:
> it does not apply to compiler-generated members. If Java consumers need to
> derive a modified instance, give them a named function that expresses the
> transition. See [Chapter 11, Data Classes](11-data-classes.md).
> **Suggestion.**

```kotlin
// bad — the Java call site is a 7-argument respelling that breaks whenever a
// component is added
data class Order(
    val id: OrderId,
    val customerId: CustomerId,
    val status: OrderStatus,
    val total: Money,
)

// good — a named transition Java can call with one argument
data class Order(
    val id: OrderId,
    val customerId: CustomerId,
    val status: OrderStatus,
    val total: Money,
) {
    fun withStatus(status: OrderStatus): Order = copy(status = status)
}
```

## 28.19 Keep Java and Kotlin sources in the same module compiled by the same task; do not split a package across modules to "keep the Java separate".

> Why? The Kotlin Gradle plugin compiles a module's Kotlin sources first,
> with the module's Java sources on its path, then runs `javac` with the
> Kotlin output on *its* classpath. That ordering is what lets Kotlin call
> Java and Java call Kotlin within one module, including mutual references.
> Splitting the same logical package across a `:legacy-java` module and a
> `:new-kotlin` module gives up that property: the dependency edge becomes
> one-directional, every shared type must be duplicated or hoisted, and
> `internal` (§28.16) stops meaning anything useful because the modules are
> separate compilation units. Migrate file by file inside one module
> instead. **Suggestion.**

```kotlin
// bad — settings.gradle.kts that splits one package by language, forcing a
// one-way dependency and duplicated model types
include(":orders-java")
include(":orders-kotlin")   // depends on :orders-java; the reverse is impossible

// good — one module, both source roots, one compilation
include(":orders")
```

```text
// good — the standard mixed layout inside :orders
orders/
  src/main/java/com/example/orders/LegacyOrderMapper.java
  src/main/kotlin/com/example/orders/OrderService.kt
  src/test/kotlin/com/example/orders/OrderServiceTest.kt
```
