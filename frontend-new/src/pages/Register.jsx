import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../config/api'
import { setAuth } from '../hooks/useAuth'
import { PINCODE_ZONE_MAP, TIER_DISPLAY } from '../config/constants'

const STEPS = ['Phone & OTP', 'Personal Details', 'Location & UPI', 'Confirmation']

export default function Register() {
  const nav = useNavigate()
  const [step, setStep] = useState(0)
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState('')

  // Form state
  const [phone, setPhone] = useState('')
  const [otp, setOtp] = useState('')
  const [aadhaar, setAadhaar] = useState('')
  const [pan, setPan] = useState('')
  const [platform, setPlatform] = useState('zomato')
  const [partnerId, setPartnerId] = useState('')
  const [lang, setLang] = useState('ta')
  const [pincode, setPincode] = useState('')
  const [upi, setUpi] = useState('')
  const [mandateApproved, setMandateApproved] = useState(false)

  // Results
  const [aadhaarHash, setAadhaarHash] = useState('')
  const [panHash, setPanHash] = useState('')
  const [regResult, setRegResult] = useState(null)

  const zoneInfo = PINCODE_ZONE_MAP[parseInt(pincode)] || null

  const fillDemo = () => {
    setPhone('9876543210')
    setOtp('123456')
    setAadhaar('111122223333')
    setPan('ABCDE1234F')
    setPlatform('zomato')
    setPartnerId('ZMT' + Math.floor(Math.random() * 10000))
    setPincode('600042')
    setUpi('demo@upi')
    setLang('en')
    setMandateApproved(true)
  }

  const step1 = () => {
    if (otp.length !== 6) return setErr('Enter any 6-digit OTP (demo mode)')
    setErr(''); setStep(1)
  }

  const step2 = async () => {
    setLoading(true); setErr('')
    try {
      const { data: ad } = await api.post('/api/v1/onboarding/kyc/aadhaar', { aadhaar_number: aadhaar.replace(/\s/g,''), otp: '123456' })
      setAadhaarHash(ad.aadhaar_hash)
      const { data: pd } = await api.post('/api/v1/onboarding/kyc/pan', { pan_number: pan.toUpperCase() })
      setPanHash(pd.pan_hash)
      await api.post('/api/v1/onboarding/platform/verify', { platform, partner_id: partnerId })
      setStep(2)
    } catch(e) { setErr(e.response?.data?.detail || 'Verification failed') }
    finally { setLoading(false) }
  }

  const step3 = async () => {
    setLoading(true); setErr('')
    try {
      await api.post('/api/v1/onboarding/kyc/bank', { upi_vpa: upi })
      setStep(3)
    } catch(e) { setErr(e.response?.data?.detail || 'UPI validation failed') }
    finally { setLoading(false) }
  }

  const register = async () => {
    setLoading(true); setErr('')
    try {
      const { data } = await api.post('/api/v1/onboarding/register', {
        aadhaar_hash: aadhaarHash,
        pan_hash: panHash,
        upi_vpa: upi,
        platform,
        partner_id: partnerId,
        pincode: parseInt(pincode),
        device_fingerprint: `web-${Date.now()}`,
        language_preference: lang,
      })
      if (mandateApproved) {
        try { await api.patch(`/api/v1/onboarding/${data.worker_id}/upi-mandate`, { upi_mandate_active: true }) } catch {}
      }
      setRegResult(data)
      setAuth({ worker_id: data.worker_id, language_preference: lang, platform })
      setStep(4)
    } catch(e) { setErr(e.response?.data?.detail || 'Registration failed') }
    finally { setLoading(false) }
  }

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-lg fade-up">
        <div className="flex items-center justify-between mb-8">
          <Link to="/" className="flex items-center gap-2">
                        <span className="font-heading font-bold text-xl text-primary-900">Giggle</span>
          </Link>
          <button onClick={fillDemo} className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-600 px-3 py-1.5 rounded-lg font-medium transition-colors">
            Fast Demo Fill
          </button>
        </div>

        {/* Progress */}
        {step < 4 && (
          <div className="flex items-center gap-2 mb-8">
            {STEPS.map((s, i) => (
              <div key={s} className="flex items-center gap-2 flex-1">
                <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-colors
                  ${i < step ? 'bg-primary-500 text-white' : i === step ? 'bg-primary-900 text-white' : 'bg-gray-200 text-gray-400'}`}>
                  {i < step ? '✓' : i+1}
                </div>
                <span className={`text-xs hidden sm:block ${i === step ? 'text-primary-900 font-semibold' : 'text-gray-400'}`}>{s}</span>
                {i < STEPS.length-1 && <div className={`flex-1 h-0.5 ${i < step ? 'bg-primary-500' : 'bg-gray-200'}`} />}
              </div>
            ))}
          </div>
        )}

        {/* Step 0 — Phone OTP */}
        {step === 0 && (
          <div className="card">
            <h2 className="font-heading font-bold text-xl text-primary-900 mb-1">Verify Your Phone</h2>
            <p className="text-sm text-gray-400 mb-5">Demo mode: any 6-digit OTP works</p>
            <label className="label">Phone Number</label>
            <input className="input-field mb-3" value={phone} onChange={e => setPhone(e.target.value)} placeholder="9876543210" />
            <label className="label">OTP</label>
            <input className="input-field mb-2" value={otp} onChange={e => setOtp(e.target.value)} placeholder="123456" maxLength={6} />
            <p className="text-xs text-amber-600 bg-amber-50 px-3 py-2 rounded-lg mb-4">🔓 Demo mode — any 6-digit OTP accepted</p>
            {err && <p className="text-red-500 text-sm mb-3">{err}</p>}
            <button className="btn-primary w-full" onClick={step1}>Continue</button>
          </div>
        )}

        {/* Step 1 — KYC */}
        {step === 1 && (
          <div className="card">
            <h2 className="font-heading font-bold text-xl text-primary-900 mb-5">Personal & Platform Details</h2>
            <label className="label">Aadhaar Number</label>
            <input className="input-field mb-3" value={aadhaar} onChange={e => setAadhaar(e.target.value)} placeholder="1234 5678 9012" />
            <label className="label">PAN Number</label>
            <input className="input-field mb-3" value={pan} onChange={e => setPan(e.target.value)} placeholder="ABCDE1234F" />
            <label className="label">Platform</label>
            <select className="input-field mb-3" value={platform} onChange={e => setPlatform(e.target.value)}>
              <option value="zomato">Zomato</option>
              <option value="swiggy">Swiggy</option>
            </select>
            <label className="label">Partner / Delivery ID</label>
            <input className="input-field mb-3" value={partnerId} onChange={e => setPartnerId(e.target.value)} placeholder="ZMT123456" />
            <label className="label">Language Preference</label>
            <select className="input-field mb-5" value={lang} onChange={e => setLang(e.target.value)}>
              <option value="ta">தமிழ் (Tamil)</option>
              <option value="hi">हिंदी (Hindi)</option>
              <option value="en">English</option>
            </select>
            {err && <p className="text-red-500 text-sm mb-3">{err}</p>}
            <div className="flex gap-3">
              <button className="btn-secondary flex-1" onClick={() => setStep(0)}>Back</button>
              <button className="btn-primary flex-1" disabled={loading || !aadhaar || !pan || !partnerId} onClick={step2}>
                {loading ? <span className="spinner" /> : 'Verify'}
              </button>
            </div>
          </div>
        )}

        {/* Step 2 — Location & UPI */}
        {step === 2 && (
          <div className="card">
            <h2 className="font-heading font-bold text-xl text-primary-900 mb-5">Location & UPI Details</h2>
            <label className="label">Pincode</label>
            <input className="input-field mb-2" value={pincode} onChange={e => setPincode(e.target.value)} placeholder="600042" />
            {zoneInfo && (
              <div className="flex gap-2 mb-3">
                <span className="badge badge-active text-xs">📍 {zoneInfo.name}</span>
                <span className={`badge text-xs tier-${zoneInfo.tier}`}>
                  {TIER_DISPLAY[zoneInfo.tier]?.en || zoneInfo.tier}
                </span>
              </div>
            )}
            <label className="label">UPI VPA</label>
            <input className="input-field mb-3" value={upi} onChange={e => setUpi(e.target.value)} placeholder="name@upi" />

            {/* UPI Autopay mandate */}
            <div className="bg-primary-50 border border-primary-200 rounded-xl p-4 mb-5">
              <p className="font-semibold text-primary-900 text-sm mb-1">💳 UPI AutoPay Mandate</p>
              <p className="text-xs text-gray-600 mb-3">Allow Giggle to auto-deduct your weekly premium every Sunday</p>
              <div className="flex gap-2">
                <button onClick={() => setMandateApproved(true)}
                  className={`flex-1 py-2 rounded-lg text-sm font-semibold transition-all ${mandateApproved ? 'bg-primary-900 text-white' : 'bg-white border border-primary-300 text-primary-900 hover:bg-primary-50'}`}>
                  Approve Mandate
                </button>
                <button onClick={() => setMandateApproved(false)}
                  className="text-xs text-gray-400 hover:text-gray-600 px-3">
                  Skip for now
                </button>
              </div>
              {!mandateApproved && <p className="text-xs text-amber-600 mt-2">⚠ Manual payment required without mandate</p>}
            </div>

            {err && <p className="text-red-500 text-sm mb-3">{err}</p>}
            <div className="flex gap-3">
              <button className="btn-secondary flex-1" onClick={() => setStep(1)}>Back</button>
              <button className="btn-primary flex-1" disabled={loading || !upi || !pincode} onClick={step3}>
                {loading ? <span className="spinner" /> : 'Continue'}
              </button>
            </div>
          </div>
        )}

        {/* Step 3 — Review & Register */}
        {step === 3 && (
          <div className="card">
            <h2 className="font-heading font-bold text-xl text-primary-900 mb-5">Review & Enroll</h2>
            <div className="space-y-2 mb-5 text-sm">
              {[['Platform', platform.charAt(0).toUpperCase() + platform.slice(1)],
                ['Partner ID', partnerId], ['UPI', upi], ['Pincode', pincode],
                ['Zone', zoneInfo?.name || '—'], ['Language', lang.toUpperCase()],
                ['UPI Mandate', mandateApproved ? '✓ Active' : '—']
              ].map(([k,v]) => (
                <div key={k} className="flex justify-between py-2 border-b border-gray-100">
                  <span className="text-gray-500">{k}</span>
                  <span className="font-medium text-primary-900">{v}</span>
                </div>
              ))}
            </div>
            {err && <p className="text-red-500 text-sm mb-3">{err}</p>}
            <div className="flex gap-3">
              <button className="btn-secondary flex-1" onClick={() => setStep(2)}>Back</button>
              <button className="btn-primary flex-1" disabled={loading} onClick={register}>
                {loading ? <span className="spinner" /> : 'Enroll Now'}
              </button>
            </div>
          </div>
        )}

        {/* Step 4 — Success */}
        {step === 4 && regResult && (
          <div className="card text-center fade-up">
            <div className="text-5xl mb-4">🎉</div>
            <h2 className="font-heading font-bold text-2xl text-primary-900 mb-2">You're Protected!</h2>
            <p className="text-gray-500 mb-6">Your policy is active. Payouts start after the 28-day waiting period.</p>
            <div className="bg-primary-50 rounded-xl p-4 text-left space-y-2 text-sm mb-6">
              <div className="flex justify-between"><span className="text-gray-500">Weekly Premium</span><span className="font-bold text-primary-900">₹{regResult.weekly_premium_amount?.toFixed(2)}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Waiting Period</span><span className="font-medium">28 days</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Worker ID</span><span className="font-mono text-xs text-gray-700">{String(regResult.worker_id).slice(0,8)}…</span></div>
            </div>
            <button className="btn-primary w-full" onClick={() => nav('/dashboard')}>Go to Dashboard</button>
          </div>
        )}
      </div>
    </div>
  )
}
