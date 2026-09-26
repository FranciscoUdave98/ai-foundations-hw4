import { useState, type FormEvent } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { HandsomeDan } from '../components/Brand'
import { useAuth } from '../useAuth'

export default function Login() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const next = (location.state as { from?: string } | null)?.from ?? '/products'

  if (user && !submitting) return <Navigate to={next} replace />

  async function submit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await login(email, password)
      navigate(next, { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not log in. Please try again.')
      setSubmitting(false)
    }
  }

  return (
    <div className="container auth">
      <form className="auth-card" onSubmit={submit} noValidate>
        <HandsomeDan size={64} className="auth-dan dan-wiggle" />
        <h1>Welcome back</h1>
        <p className="auth-sub">Log in to pick up your chat and saved picks.</p>
        <label>
          Email
          <input
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </label>
        <label>
          Password
          <input
            type="password"
            required
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        {error && (
          <p className="notice notice-error" role="alert">
            {error}
          </p>
        )}
        <button type="submit" className="btn btn-primary btn-block" disabled={submitting || !email || !password}>
          {submitting ? 'Logging in…' : 'Log in'}
        </button>
        <p className="auth-switch">
          New to Campus Customs? <Link to="/create-account">Create an account</Link>
        </p>
      </form>
    </div>
  )
}
