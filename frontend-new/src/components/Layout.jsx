import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useState, useEffect } from 'react'
import { api } from '../config/api'
import { getAuth, clearAuth, clearAdmin, setAuth } from '../hooks/useAuth'
import i18n from 'i18next'

export default function Layout({ children, dark = false }) {
  const { t } = useTranslation()
  const nav = useNavigate()
  const loc = useLocation()
  const auth = getAuth()
  const [health, setHealth] = useState(null)
  const [lang, setLang] = useState(i18n.language || 'ta')

  useEffect(() => {
    api.get('/api/v1/health').then(r => setHealth(r.data)).catch(() => setHealth(null))
  }, [])

  const onLogout = () => { clearAuth(); clearAdmin(); nav('/') }

  const changeLang = async (l) => {
    setLang(l)
    i18n.changeLanguage(l)
    if (auth?.worker_id) {
      try {
        await api.patch(`/api/v1/onboarding/${auth.worker_id}/language`, { language_preference: l })
        setAuth({ ...auth, language_preference: l })
      } catch {}
    }
  }

  const navLink = (to, label) => {
    const active = loc.pathname === to
    return (
      <Link key={to} to={to}
        className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-150 ${
          active
            ? 'bg-white/20 text-white'
            : 'text-white/60 hover:text-white hover:bg-white/10'
        }`}>
        {label}
      </Link>
    )
  }

  const isOk = health?.database === 'ok' || health?.database === 'connected'

  return (
    <div className={`min-h-screen ${dark ? 'bg-primary-900' : 'bg-surface'}`}>
      {/* Nav */}
      <nav className={`sticky top-0 z-50 border-b backdrop-blur-xl ${
        dark ? 'bg-primary-900/95 border-white/10' : 'bg-primary-900 shadow-md border-primary-800'
      }`}>
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center gap-3">
          {/* Logo */}
          <Link to={auth ? '/dashboard' : '/'} className="flex items-center gap-2 mr-4">
            <span className="font-heading font-bold text-xl text-white tracking-wide">
              Giggle
            </span>
          </Link>

          {loc.pathname !== '/' && loc.pathname !== '/dashboard' && (
            <button onClick={() => nav(-1)} className="text-xs font-medium px-3 py-1.5 rounded-lg border border-white/20 text-white/80 hover:bg-white/10 hover:text-white transition-colors">
              ← Back
            </button>
          )}

          {/* Nav links */}
          <div className="flex items-center gap-1">
            {auth && navLink('/dashboard', t('nav.coverage'))}
          </div>

          <div className="ml-auto flex items-center gap-4">
            {/* Health dot */}
            <span className="flex items-center gap-1.5 text-xs text-white/70 font-medium bg-white/5 px-2.5 py-1 rounded-full">
              <span className={`w-2 h-2 rounded-full pulse-dot ${isOk ? 'bg-green-400' : health ? 'bg-red-400' : 'bg-gray-400'}`} />
              {isOk ? 'Live' : health ? 'Degraded' : '...'}
            </span>

            {/* Lang switcher */}
            <div className="flex gap-0.5 text-xs font-semibold rounded-lg overflow-hidden border border-white/20 bg-black/20">
              {['ta','hi','en'].map(l => (
                <button key={l} onClick={() => changeLang(l)}
                  className={`px-2 py-1 transition-colors ${lang === l
                    ? 'bg-white/20 text-white'
                    : 'text-white/50 hover:text-white hover:bg-white/10'
                  }`}>
                  {l === 'ta' ? 'த' : l === 'hi' ? 'हि' : 'En'}
                </button>
              ))}
            </div>

            {/* Admin link */}
            <Link to="/admin" className="text-xs text-white/50 hover:text-white font-medium transition-colors">
              {t('nav.admin', 'Admin')}
            </Link>

            {auth && (
              <button onClick={onLogout}
                className="text-xs font-bold px-3 py-1.5 rounded-lg bg-white text-primary-900 hover:bg-gray-100 transition-colors ml-2 shadow-sm">
                {t('nav.logout', 'Sign Out')}
              </button>
            )}
          </div>
        </div>
      </nav>

      {/* Page content */}
      <main className={`max-w-7xl mx-auto px-6 py-8 ${dark ? 'text-white' : ''}`}>
        {children}
      </main>
    </div>
  )
}
