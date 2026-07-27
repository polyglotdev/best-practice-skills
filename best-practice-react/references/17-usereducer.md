<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 17. useReducer

## 17.1 Reach for `useReducer` when a component has multiple state values that update together, or when the next state depends on complex logic over the action + previous state.

> Why? A reducer centralizes "what transitions are valid" in one pure
> function, which is easier to test and reason about than several
> `useState` calls that must be updated in lockstep by every handler.

```jsx
// bad — four handlers must each remember to update three states consistently
function Wizard() {
  const [step, setStep] = useState(0)
  const [isValid, setIsValid] = useState(false)
  const [errors, setErrors] = useState([])

  function next() {
    setStep((s) => s + 1)
    setIsValid(false)
    setErrors([])
  }
}
```

```tsx
// good
type WizardState = {
  step: number
  isValid: boolean
  errors: string[]
}

type WizardAction = { type: 'next' } | { type: 'setErrors', errors: string[] }

function wizardReducer(state: WizardState, action: WizardAction): WizardState {
  switch (action.type) {
    case 'next':
      return { step: state.step + 1, isValid: false, errors: [] }
    case 'setErrors':
      return { ...state, errors: action.errors, isValid: action.errors.length === 0 }
    default:
      return state
  }
}

function Wizard() {
  const [state, dispatch] = useReducer(wizardReducer, { step: 0, isValid: false, errors: [] })
  function next() {
    dispatch({ type: 'next' })
  }
}
```

## 17.2 Keep reducers pure — no side effects, no `fetch`, no timers inside a reducer function.

> Why? React may call a reducer more than once per action (Strict Mode
> double-invoke, or when replaying for concurrent features). Side effects
> inside a reducer will run extra times or at unexpected moments.

```jsx
// bad — side effect inside the reducer
function reducer(state, action) {
  if (action.type === 'save') {
    fetch('/api/save', { method: 'POST', body: JSON.stringify(state) })
  }
  return state
}
```

```jsx
// good — reducer only computes the next state; effects live in an effect or handler
function reducer(state, action) {
  if (action.type === 'save') {
    return { ...state, isSaving: true }
  }
  return state
}

function Form() {
  const [state, dispatch] = useReducer(reducer, initialState)

  useEffect(() => {
    if (!state.isSaving) return
    const controller = new AbortController()
    fetch('/api/save', {
      method: 'POST',
      body: JSON.stringify(state),
      signal: controller.signal
    })
    return () => controller.abort()
  }, [state.isSaving, state])
}
```

## 17.3 Name actions with a `type` discriminant and model them as a discriminated union in TypeScript.

> Why? A discriminated union lets `tsc` narrow `action.payload` correctly
> inside each `switch` branch and rejects typos in `action.type` at compile
> time.

```tsx
// bad — loose shape, payload is `any` in every branch
type Action = {
  type: string
  payload?: unknown
}
```

```tsx
// good
type Action =
  | { type: 'increment', amount: number }
  | { type: 'reset' }
```
