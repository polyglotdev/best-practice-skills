<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 34. Forms

## 34.1 Prefer uncontrolled inputs read via `FormData` on submit for simple forms; reach for a form library only when you need field-level validation, complex cross-field rules, or dynamic field arrays.

> Why? An uncontrolled form with native `FormData` avoids a `useState` (and
> a re-render) per keystroke per field, and matches the platform's native
> submit/reset behavior. A form library earns its cost once validation
> complexity grows.

```jsx
// bad — controlled state for a trivial two-field form, one render per keystroke
function ContactForm({ onSubmit }) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')

  function handleSubmit(event) {
    event.preventDefault()
    onSubmit({ name, email })
  }

  return (
    <form onSubmit={handleSubmit}>
      <input value={name} onChange={(e) => setName(e.target.value)} name="name" />
      <input value={email} onChange={(e) => setEmail(e.target.value)} name="email" />
    </form>
  )
}
```

```jsx
// good — uncontrolled, read once on submit
function ContactForm({ onSubmit }) {
  function handleSubmit(event) {
    event.preventDefault()
    const formData = new FormData(event.currentTarget)
    onSubmit({
      name: formData.get('name'),
      email: formData.get('email')
    })
  }

  return (
    <form onSubmit={handleSubmit}>
      <input name="name" defaultValue="" />
      <input name="email" defaultValue="" />
    </form>
  )
}
```

## 34.2 For forms with nontrivial validation, use `react-hook-form` (or an equivalent uncontrolled-first library) rather than hand-rolling validation state.

> Why? Hand-rolled validation tends to re-render on every keystroke,
> duplicates logic that a mature library has already solved (error
> messages, touched/dirty tracking, schema validation), and grows
> unmaintainable as fields multiply.

```jsx
// bad — hand-rolled validation state ballooning per field
function SignupForm() {
  const [email, setEmail] = useState('')
  const [emailError, setEmailError] = useState('')
  const [password, setPassword] = useState('')
  const [passwordError, setPasswordError] = useState('')
  // ...repeated per field, growing quadratically with form size
}
```

```jsx
// good
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8)
})

function SignupForm({ onSubmit }) {
  const {
    register,
    handleSubmit,
    formState: { errors }
  } = useForm({ resolver: zodResolver(schema) })

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('email')} />
      {errors.email && <span role="alert">{errors.email.message}</span>}
      <input {...register('password')} type="password" />
      {errors.password && <span role="alert">{errors.password.message}</span>}
    </form>
  )
}
```

## 34.3 Always give every form control a `name` attribute and associate a `<label>` via `htmlFor`/`id` (or wrap the input in the label).

> Why? `name` is what makes `FormData` and native form submission work at
> all; a real label association is required for screen readers and for
> clicking the label text to focus the field.

```jsx
// bad — no name, no label association
<input placeholder="Email" />
```

```jsx
// good
<label htmlFor="email">Email</label>
<input id="email" name="email" type="email" />
```

## 34.4 Never use `placeholder` as a replacement for a `<label>`.

> Why? Placeholder text disappears the moment the user types, has
> insufficient contrast requirements under WCAG, and is not reliably
> announced the same way as a label by all assistive technology.

```jsx
// bad — no persistent, accessible label
<input placeholder="Email address" />
```

```jsx
// good
<label htmlFor="email">Email address</label>
<input id="email" name="email" placeholder="ada@example.com" />
```

## 34.5 Use the appropriate `type`, `inputMode`, and `autoComplete` attributes on every input.

> Why? Correct `type`/`inputMode` gives mobile users the right keyboard
> (numeric, email, tel) and enables native browser validation for free;
> `autoComplete` lets password managers and browser autofill work
> correctly, which is itself an accessibility and security benefit.

```jsx
// bad — generic text input for structured data
<input name="email" />
<input name="phone" />
```

```jsx
// good
<input name="email" type="email" autoComplete="email" />
<input name="phone" type="tel" inputMode="tel" autoComplete="tel" />
```

## 34.6 Disable the submit button (or show a pending state) while a submission is in flight, using `useFormStatus`/`useActionState` in React 19 forms, or local state otherwise.

> Why? Without a pending indicator, users double-click submit buttons on
> slow networks, causing duplicate submissions.

```tsx
// bad — no pending state, double-submit is easy
function SaveButton() {
  return <button type="submit">Save</button>
}
```

```tsx
// good — React 19 Server Action form
function SaveButton() {
  const { pending } = useFormStatus()
  return (
    <button type="submit" disabled={pending}>
      {pending ? 'Saving…' : 'Save'}
    </button>
  )
}
```
