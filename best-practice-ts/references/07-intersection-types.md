<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 7. Intersection Types

## 7.1 Use `&` to compose small, orthogonal object shapes; prefer `interface extends` once composition gets deep or recursive.

> Why? Intersections of two or three flat shapes are readable inline;
> deeply nested intersections produce confusing hover types and slower
> checking compared to a resolved `interface extends` chain.

```ts
// good — shallow, ad hoc composition
type Timestamped = { createdAt: Date; updatedAt: Date }
type Named = { name: string }
type Widget = Timestamped & Named & { id: string }
```

## 7.2 Never intersect two primitive types that produce `never`; that is a signal the modeling is wrong.

> Why? `string & number` collapses to `never`, which is almost always an
> authoring mistake rather than an intended type — the compiler will not
> catch every case if it's buried inside a generic.

```ts
// bad
type Weird = string & number // never — dead type

// good
type Id = string | number
```

## 7.3 Do not use an intersection to try to "override" a property with an incompatible type.

> Why? Intersecting two object types with the same property name and
> incompatible types collapses that property to `never`, silently making
> the object unconstructable rather than raising an error at the
> intersection site.

```ts
// bad
type Base = { id: string }
type Broken = Base & { id: number } // id: never

// good — use Omit to replace a field explicitly
type Fixed = Omit<Base, 'id'> & { id: number }
```
