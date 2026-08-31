import { useState, type FormEvent } from 'react'
import { useNavigate, useSearchParams } from 'react-router'
import { supabase } from '../lib/supabaseClient'

export function useAuthForm(mode: 'login' | 'register') {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [checkEmail, setCheckEmail] = useState(false)
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setSubmitting(true)
    setError(null)

    const result =
      mode === 'login'
        ? await supabase.auth.signInWithPassword({ email, password })
        : await supabase.auth.signUp({ email, password })

    setSubmitting(false)

    if (result.error) {
      setError(result.error.message)
      return
    }

    if (mode === 'register' && !result.data.session) {
      // Email confirmation required before a session exists.
      setCheckEmail(true)
      return
    }

    navigate(searchParams.get('next') || '/groups', { replace: true })
  }

  return { email, setEmail, password, setPassword, error, submitting, checkEmail, handleSubmit }
}
