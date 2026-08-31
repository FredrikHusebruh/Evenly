import { Link } from 'react-router'
import { useAuthForm } from '../hooks/useAuthForm'

export function RegisterPage() {
  const { email, setEmail, password, setPassword, error, submitting, checkEmail, handleSubmit } =
    useAuthForm('register')

  if (checkEmail) {
    return (
      <div className="mx-auto flex min-h-screen max-w-sm flex-col justify-center px-4 text-center">
        <h1 className="mb-2 text-xl font-semibold tracking-tight">Check your email</h1>
        <p className="text-sm text-muted">We sent a confirmation link to {email}. Follow it to finish signing up.</p>
      </div>
    )
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-sm flex-col justify-center px-4">
      <h1 className="mb-8 text-xl font-semibold tracking-tight">Create your account</h1>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <label className="flex flex-col gap-1">
          <span className="text-sm text-muted">Email</span>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="rounded-sm border border-border bg-surface px-3 py-2 text-base outline-none focus:border-accent"
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-sm text-muted">Password</span>
          <input
            type="password"
            required
            minLength={6}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="rounded-sm border border-border bg-surface px-3 py-2 text-base outline-none focus:border-accent"
          />
        </label>
        {error && <p className="text-sm text-owed">{error}</p>}
        <button
          type="submit"
          disabled={submitting}
          className="mt-2 rounded-md bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-accent-hover disabled:opacity-60"
        >
          {submitting ? 'Creating account…' : 'Create account'}
        </button>
      </form>
      <p className="mt-6 text-sm text-muted">
        Already have an account?{' '}
        <Link to="/login" className="text-accent">
          Log in
        </Link>
      </p>
    </div>
  )
}
