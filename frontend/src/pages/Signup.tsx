import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useAuth } from '../contexts/AuthContext'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function SignupPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [showPassword, setShowPassword] = useState(false)

  // Fetch password requirements
  const requirementsQuery = useQuery({
    queryKey: ['password-requirements'],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/auth/password-requirements`)
      return res.json()
    },
  })

  // Password validation state
  const [validation, setValidation] = useState({
    minLength: false,
    maxBytes: false,
    uppercase: false,
    lowercase: false,
    number: false,
    special: false,
  })

  // Check password strength in real-time
  useEffect(() => {
    // Calculate UTF-8 byte length
    const encoder = new TextEncoder()
    const byteLength = encoder.encode(password).length
    
    setValidation({
      minLength: password.length >= 8,
      maxBytes: byteLength <= 72,
      uppercase: /[A-Z]/.test(password),
      lowercase: /[a-z]/.test(password),
      number: /[0-9]/.test(password),
      special: /[!@#$%^&*(),.?":{}|<>]/.test(password),
    })
  }, [password])

  const signupMutation = useMutation({
    mutationFn: async () => {
      const normalizedEmail = email.toLowerCase().trim()
      const res = await fetch(`${API_URL}/api/auth/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: normalizedEmail, password }),
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Signup failed')
      }
      return res.json()
    },
    onSuccess: (data) => {
      login(data.token, data.user.id, data.user.email)
      navigate('/')
    },
    onError: (err: any) => {
      setError(err.message || 'Signup failed')
    },
  })

  const isPasswordValid = Object.values(validation).every(v => v === true)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!email || !password || !confirmPassword) {
      setError('Please fill in all fields')
      return
    }

    if (email.toLowerCase() !== email) {
      setError('Email must be lowercase')
      return
    }

    if (!isPasswordValid) {
      setError('Password does not meet all requirements')
      return
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    signupMutation.mutate()
  }

  const isFormValid = isPasswordValid && password === confirmPassword

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-emerald-500 via-emerald-400 to-teal-500 p-4">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-white/10 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-white/10 rounded-full blur-3xl"></div>
      </div>

      <div className="w-full max-w-md z-10">
        {/* Logo/Brand */}
        <div className="text-center mb-8">
          <div className="text-5xl mb-4">🚀</div>
          <h1 className="text-4xl font-bold text-white mb-2">EVOSearch</h1>
          <p className="text-emerald-100">Join to track knowledge evolution</p>
        </div>

        {/* Signup Card */}
        <div className="bg-white/95 backdrop-blur-xl rounded-2xl shadow-2xl p-8 border border-white/20">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-slate-900 mb-1">Create Account</h2>
            <p className="text-slate-600 text-sm">Manage documents and code effortlessly</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Email */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">📧 Email Address</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 border-2 border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-slate-50 hover:bg-slate-100 transition"
                placeholder="your@email.com"
              />
              <p className="text-xs text-slate-500 mt-1">Email will be stored in lowercase</p>
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">🔑 Password</label>
              <div className="relative mb-3">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 border-2 border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-slate-50 hover:bg-slate-100 transition"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-3 text-slate-500 hover:text-slate-700 text-lg"
                >
                  {showPassword ? '👁️' : '👁️‍🗨️'}
                </button>
              </div>

              {/* Password Requirements Checklist */}
              <div className="bg-slate-50 border border-slate-200 p-3 rounded-xl">
                <p className="text-xs font-semibold text-slate-700 mb-2">✓ Requirements:</p>
                <div className="text-xs space-y-1.5">
                  <div className={`flex items-center gap-2 ${validation.minLength ? 'text-emerald-600' : 'text-slate-500'}`}>
                    <span className="text-base">{validation.minLength ? '✅' : '○'}</span>
                    <span>At least 8 characters</span>
                  </div>
                  <div className={`flex items-center gap-2 ${validation.maxBytes ? 'text-emerald-600' : 'text-red-600'}`}>
                    <span className="text-base">{validation.maxBytes ? '✅' : '○'}</span>
                    <span>Maximum 72 bytes (UTF-8)</span>
                  </div>
                  <div className={`flex items-center gap-2 ${validation.uppercase ? 'text-emerald-600' : 'text-slate-500'}`}>
                    <span className="text-base">{validation.uppercase ? '✅' : '○'}</span>
                    <span>Uppercase letter (A-Z)</span>
                  </div>
                  <div className={`flex items-center gap-2 ${validation.lowercase ? 'text-emerald-600' : 'text-slate-500'}`}>
                    <span className="text-base">{validation.lowercase ? '✅' : '○'}</span>
                    <span>Lowercase letter (a-z)</span>
                  </div>
                  <div className={`flex items-center gap-2 ${validation.number ? 'text-emerald-600' : 'text-slate-500'}`}>
                    <span className="text-base">{validation.number ? '✅' : '○'}</span>
                    <span>Number (0-9)</span>
                  </div>
                  <div className={`flex items-center gap-2 ${validation.special ? 'text-emerald-600' : 'text-slate-500'}`}>
                    <span className="text-base">{validation.special ? '✅' : '○'}</span>
                    <span>Special character (!@#$%^&*)</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Confirm Password */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">🔐 Confirm Password</label>
              <input
                type={showPassword ? 'text' : 'password'}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full px-4 py-3 border-2 border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-slate-50 hover:bg-slate-100 transition"
                placeholder="••••••••"
              />
              {confirmPassword && password !== confirmPassword && (
                <p className="text-xs text-red-600 mt-2 font-medium">❌ Passwords do not match</p>
              )}
              {confirmPassword && password === confirmPassword && (
                <p className="text-xs text-emerald-600 mt-2 font-medium">✅ Passwords match</p>
              )}
            </div>

            {error && (
              <div className="p-4 bg-red-50 border-2 border-red-200 rounded-xl text-red-700 text-sm font-medium">
                ❌ {error}
              </div>
            )}

            <button
              type="submit"
              disabled={!isFormValid || signupMutation.isPending}
              className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 disabled:from-emerald-400 disabled:to-teal-400 text-white font-bold py-3 rounded-xl transition transform hover:scale-105 shadow-lg"
            >
              {signupMutation.isPending ? '⏳ Creating Account...' : '✓ Create Account'}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-slate-200">
            <p className="text-slate-600 text-center text-sm">
              Already have an account?{' '}
              <Link to="/login" className="text-emerald-600 hover:text-emerald-700 font-bold">
                Login here
              </Link>
            </p>
          </div>
        </div>

        {/* Footer info */}
        <div className="mt-8 text-center text-white/80 text-xs">
          <p>🛡️ Your data is encrypted and secure</p>
        </div>
      </div>
    </div>
  )
}
