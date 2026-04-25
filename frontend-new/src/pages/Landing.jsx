import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../config/api'

export default function Landing() {
  const [health, setHealth] = useState(null)

  useEffect(() => {
    api.get('/api/v1/health').then(r => setHealth(r.data)).catch(() => setHealth({ status: 'offline' }))
  }, [])

  const ok = health?.database === 'ok' || health?.database === 'connected'

  return (
    <div className="min-h-screen bg-surface">
      {/* Nav */}
      <nav className="sticky top-0 z-50 bg-white/90 border-b border-gray-100 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center gap-3">
          <span className="flex items-center gap-2 font-heading font-bold text-lg text-primary-900">
             Giggle
          </span>
          <div className="ml-auto flex items-center gap-4">
            <span className="flex items-center gap-1.5 text-xs text-gray-500">
              <span className={`w-2 h-2 rounded-full pulse-dot ${health === null ? 'bg-gray-300' : ok ? 'bg-green-500' : 'bg-red-500'}`} />
              {health === null ? 'Connecting...' : ok ? 'All systems operational' : 'API Offline'}
            </span>
            <Link to="/login" className="text-sm font-medium text-gray-600 hover:text-gray-900">Sign in</Link>
            <Link to="/register" className="btn-primary text-sm px-5 py-2">Get Protected</Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden bg-primary-900 text-white pt-24 pb-32">
        <div className="absolute inset-0 opacity-10 bg-[radial-gradient(ellipse_at_top_right,_#22c55e_0%,_transparent_60%)]" />
        <div className="max-w-4xl mx-auto px-6 text-center fade-up">
          <span className="inline-flex items-center gap-2 bg-white/10 border border-white/20 rounded-full px-4 py-1.5 text-sm mb-6">
            <span className="w-2 h-2 rounded-full bg-accent-500" />
            Guidewire DEVTrails 2026 — Team ShadowKernel
          </span>
          <h1 className="font-heading text-5xl font-bold leading-tight mb-5">
            Parametric Income Protection<br />for Gig Workers
          </h1>
          <p className="text-white/70 text-lg max-w-2xl mx-auto mb-10">
            Weather triggers income loss for delivery partners in seconds. 
            Giggle detects disruptions, scores fraud automatically, and sends
            UPI payouts — in under 60 seconds.
          </p>
          <div className="flex items-center justify-center gap-4">
            <Link to="/register" className="bg-accent-500 hover:bg-accent-600 text-white font-semibold px-8 py-4 rounded-xl transition-all hover:-translate-y-0.5 hover:shadow-xl text-base">
              Get Protected Free
            </Link>
            <Link to="/login?role=admin" className="border border-white/30 hover:bg-white/10 text-white font-semibold px-6 py-4 rounded-xl transition-all text-base">
              Admin Dashboard
            </Link>
          </div>
        </div>

        {/* Stats bar */}
        <div className="max-w-3xl mx-auto px-6 mt-16">
          <div className="grid grid-cols-4 gap-4">
            {[
              { val: '15M+', label: 'Gig Workers at Risk' },
              { val: '₹49', label: 'Min Weekly Premium' },
              { val: '60s', label: 'Avg Payout Time' },
              { val: '0', label: 'Forms Required' },
            ].map(s => (
              <div key={s.label} className="text-center bg-white/5 border border-white/10 rounded-2xl p-5">
                <div className="font-heading text-3xl font-bold text-accent-500">{s.val}</div>
                <div className="text-white/60 text-xs mt-1">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="max-w-5xl mx-auto px-6 py-20">
        <h2 className="font-heading text-3xl font-bold text-center text-primary-900 mb-12">How Giggle Works</h2>
        <div className="grid grid-cols-3 gap-6">
          {[
            { icon:'🌧️', title:'Weather Trigger Detected', desc:'3-point Open-Meteo sampling + GIS flood overlay + platform signal confirms disruption with 2-of-3 corroboration.' },
            { icon:'🔍', title:'Fraud Engine Runs', desc:'7-signal ensemble (Isolation Forest + CBLOF) scores every claim in milliseconds. No human bottleneck.' },
            { icon:'💰', title:'UPI Payout in 60s', desc:'Auto-approved claims go straight to Razorpay UPI VPA. Partial and held cases get 48hr review.' },
          ].map(s => (
            <div key={s.title} className="card text-center hover:-translate-y-1 transition-transform duration-200">
              <div className="text-4xl mb-4">{s.icon}</div>
              <h3 className="font-heading font-semibold text-primary-900 mb-2">{s.title}</h3>
              <p className="text-gray-500 text-sm leading-relaxed">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="bg-primary-900 py-16 text-center text-white">
        <h2 className="font-heading text-3xl font-bold mb-4">Ready to protect your income?</h2>
        <p className="text-white/60 mb-8">Takes 2 minutes. No paperwork. Cancel anytime.</p>
        <Link to="/register" className="bg-accent-500 hover:bg-accent-600 text-white font-semibold px-8 py-4 rounded-xl transition-all hover:-translate-y-0.5 inline-block">
          Enroll Now — Free Trial
        </Link>
        <div className="mt-8 text-white/30 text-xs">
          <Link to="/login?role=admin" className="hover:text-white/60 transition-colors">Admin Login</Link>
        </div>
      </section>
    </div>
  )
}
