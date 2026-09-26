import { useState, type ChangeEvent, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { HandsomeDan } from '../components/Brand'
import { useAuth } from '../useAuth'

const EMPTY = { first_name: '', last_name: '', email: '', password: '', confirm_password: '' }
type Field = keyof typeof EMPTY

function validate(form: typeof EMPTY): Partial<Record<Field, string>> {
  const errors: Partial<Record<Field, string>> = {}
  if (!form.first_name.trim()) errors.first_name = 'Enter your first name.'
  if (!form.last_name.trim()) errors.last_name = 'Enter your last name.'
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(form.email.trim())) errors.email = 'Enter a valid email address.'
  if (form.password.length < 8) errors.password = 'Use at least 8 characters.'
  if (form.confirm_password !== form.password) errors.confirm_password = "Passwords don't match."
  return errors
}

export default function CreateAccount() {
  const { user, register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState(EMPTY)
  const [touched, setTouched] = useState(false)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (user && !submitting) return <Navigate to="/products" replace />

  const errors = touched ? validate(form) : {}
  const set = (key: Field) => (e: ChangeEvent<HTMLInputElement>) => setForm((f) => ({ ...f, [key]: e.target.value }))

  async function submit(e: FormEvent) {
    e.preventDefault()
    setTouched(true)
    setError('')
    if (Object.keys(validate(form)).length) return
    setSubmitting(true)
    try {
      await register(form)
      navigate('/products', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create your account. Please try again.')
      setSubmitting(false)
    }
  }

  const field = (key: Field, label: string, type: string, autoComplete: string) => (
    <label>
      {label}
      <input
        type={type}
        autoComplete={autoComplete}
        value={form[key]}
        onChange={set(key)}
        aria-invalid={!!errors[key]}
        aria-describedby={errors[key] ? `${key}-error` : undefined}
      />
      {errors[key] && (
        <span className="field-error" id={`${key}-error`}>
          {errors[key]}
        </span>
      )}
    </label>
  )

  return (
    <div className="container auth">
      <form className="auth-card" onSubmit={submit} noValidate>
        <HandsomeDan size={64} className="auth-dan dan-wiggle" />
        <h1>Join Campus Customs</h1>
        <p className="auth-sub">Save your favorites and get help from our shopping assistant.</p>
        <div className="auth-row">
          {field('first_name', 'First name', 'text', 'given-name')}
          {field('last_name', 'Last name', 'text', 'family-name')}
        </div>
        {field('email', 'Email', 'email', 'email')}
        {field('password', 'Password', 'password', 'new-password')}
        {field('confirm_password', 'Confirm password', 'password', 'new-password')}
        {error && (
          <p className="notice notice-error" role="alert">
            {error}
          </p>
        )}
        <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
          {submitting ? 'Creating your account…' : 'Create account'}
        </button>
        <p className="auth-switch">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </form>
    </div>
  )
}
