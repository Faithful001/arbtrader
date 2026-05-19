import { useState } from 'react'
import { authApi } from '../api/auth.api'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [otp, setOtp] = useState('')
  const [step, setStep] = useState<1 | 2>(1)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleRequestOtp = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email) return
    setLoading(true)
    setError('')
    try {
      await authApi.requestOtp(email)
      setStep(2)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to request OTP')
    } finally {
      setLoading(false)
    }
  }

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!otp) return
    setLoading(true)
    setError('')
    try {
      const { access_token } = await authApi.verifyOtp(email, otp)
      login(access_token)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid OTP')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      background: 'var(--bg-base)'
    }}>
      <div style={{
        width: '100%',
        maxWidth: 400,
        padding: 40,
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border-dim)',
        borderRadius: 8
      }}>
        <div style={{ marginBottom: 30, textAlign: 'center' }}>
          <h1 className="view-title" style={{ marginBottom: 8 }}>ARBTRADER TERMINAL</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Authentication Required</p>
        </div>

        {error && (
          <div style={{ padding: 12, background: 'rgba(255, 68, 68, 0.1)', color: 'var(--warn)', border: '1px solid var(--warn)', borderRadius: 4, marginBottom: 20, fontSize: 13 }}>
            {error}
          </div>
        )}

        {step === 1 ? (
          <form onSubmit={handleRequestOtp}>
            <div style={{ marginBottom: 20 }}>
              <label style={{ display: 'block', fontSize: 11, color: 'var(--text-muted)', marginBottom: 8, fontFamily: 'var(--font-mono)' }}>EMAIL ADDRESS</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="operator@arbtrader.com"
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  background: 'var(--bg-base)',
                  border: '1px solid var(--border-dim)',
                  color: 'var(--text-primary)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: 14,
                  borderRadius: 4,
                  outline: 'none'
                }}
                required
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              style={{
                width: '100%',
                padding: '14px',
                background: 'var(--text-primary)',
                color: 'var(--bg-base)',
                border: 'none',
                borderRadius: 4,
                fontFamily: 'var(--font-mono)',
                fontWeight: 600,
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading ? 0.7 : 1
              }}
            >
              {loading ? 'REQUESTING...' : 'REQUEST ACCESS CODE'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleVerifyOtp}>
            <div style={{ marginBottom: 20 }}>
              <label style={{ display: 'block', fontSize: 11, color: 'var(--text-muted)', marginBottom: 8, fontFamily: 'var(--font-mono)' }}>ONE-TIME PASSWORD (OTP)</label>
              <input
                type="text"
                value={otp}
                onChange={e => setOtp(e.target.value)}
                placeholder="123456"
                maxLength={6}
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  background: 'var(--bg-base)',
                  border: '1px solid var(--border-dim)',
                  color: 'var(--profit)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: 24,
                  textAlign: 'center',
                  letterSpacing: 4,
                  borderRadius: 4,
                  outline: 'none'
                }}
                required
              />
              <p style={{ marginTop: 8, fontSize: 11, color: 'var(--text-muted)', textAlign: 'center' }}>
                Check the backend terminal console for your OTP code.
              </p>
            </div>
            <button
              type="submit"
              disabled={loading}
              style={{
                width: '100%',
                padding: '14px',
                background: 'var(--profit)',
                color: 'var(--bg-base)',
                border: 'none',
                borderRadius: 4,
                fontFamily: 'var(--font-mono)',
                fontWeight: 600,
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading ? 0.7 : 1
              }}
            >
              {loading ? 'VERIFYING...' : 'VERIFY & ENTER'}
            </button>
            <button
              type="button"
              onClick={() => setStep(1)}
              style={{
                width: '100%',
                padding: '14px',
                background: 'transparent',
                color: 'var(--text-muted)',
                border: 'none',
                fontFamily: 'var(--font-mono)',
                fontSize: 12,
                cursor: 'pointer',
                marginTop: 10
              }}
            >
              BACK TO EMAIL
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
