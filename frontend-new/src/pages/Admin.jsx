import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, CartesianGrid } from 'recharts'
import Layout from '../components/Layout'
import { api, ADMIN_KEY } from '../config/api'
import { ZONE_NAMES, TRIGGER_DISPLAY } from '../config/constants'

function inr(v) { return `₹${parseFloat(v || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` }

function StatCard({ label, value, sub, accent }) {
  return (
    <div className={`rounded-2xl p-5 ${accent ? 'bg-accent-500 text-white' : 'bg-white/10 text-white'}`}>
      <div className="text-xs font-semibold opacity-70 uppercase tracking-wide mb-1">{label}</div>
      <div className="font-heading text-2xl font-bold">{value ?? '—'}</div>
      {sub && <div className="text-xs opacity-60 mt-0.5">{sub}</div>}
    </div>
  )
}

export default function Admin() {
  const { t } = useTranslation()
  const [summary, setSummary] = useState(null)
  const [lossRatio, setLossRatio] = useState([])
  const [forecast, setForecast] = useState([])
  const [modelHealth, setModelHealth] = useState(null)
  const [enrollment, setEnrollment] = useState(null)
  const [triggerHist, setTriggerHist] = useState([])
  const [pendingClaims, setPendingClaims] = useState([])
  const [slabConfig, setSlabConfig] = useState(null)
  const [workersList, setWorkersList] = useState([])
  const [tab, setTab] = useState('overview')
  const [loading, setLoading] = useState(true)
  const [verifying, setVerifying] = useState(false)
  const [resolveLoading, setResolveLoading] = useState(null)
  const [resolveResult, setResolveResult] = useState({})

  useEffect(() => {
    Promise.allSettled([
      api.get('/api/v1/admin/dashboard/summary'),
      api.get('/api/v1/admin/dashboard/loss-ratio'),
      api.get('/api/v1/admin/dashboard/claims-forecast'),
      api.get('/api/v1/admin/model-health'),
      api.get('/api/v1/admin/enrollment-metrics'),
      api.get('/api/v1/trigger/history'),
      api.get('/api/v1/claims/pending'),
      api.get('/api/v1/admin/slab-config/verify'),
      api.get('/api/v1/admin/workers')
    ]).then(([s, lr, fc, mh, en, th, pc, sc, wk]) => {
      if (s.value) setSummary(s.value.data)
      if (lr.value) setLossRatio(lr.value.data.items || lr.value.data || [])
      if (fc.value) {
        const d = fc.value.data
        setForecast(d.weekly_forecast || d.forecast || [])
      }
      if (mh.value) setModelHealth(mh.value.data)
      if (en.value) setEnrollment(en.value.data)
      if (th.value) setTriggerHist((th.value.data.items || []).slice(0, 10))
      if (pc.value) setPendingClaims(pc.value.data.items || pc.value.data || [])
      if (sc.value) setSlabConfig(sc.value.data)
      if (wk.value) setWorkersList(wk.value.data.workers || [])
      setLoading(false)
    })
  }, [])

  const resolveClaim = async (claimId, resolution) => {
    setResolveLoading(claimId + resolution)
    try {
      const { data } = await api.put(`/api/v1/claims/${claimId}/resolve`, { resolution })
      setResolveResult(prev => ({ ...prev, [claimId]: data }))
      setPendingClaims(prev => prev.filter(c => (c.claim_id || c.id) !== claimId))
    } catch (e) {
      alert(e.response?.data?.detail || 'Resolve failed')
    } finally { setResolveLoading(null) }
  }

  const verifySlabs = async () => {
    setVerifying(true)
    try {
      const { data } = await api.put('/api/v1/admin/slab-config/verify')
      setSlabConfig(data)
    } catch {}
    finally { setVerifying(false) }
  }

  const tabs = [
    ['overview', 'Overview'],
    ['workers', 'Workers'],
    ['triggers', 'Triggers'],
    ['claims', `Claims Review (${pendingClaims.length})`],
    ['model', 'Model Health'],
    ['slab', 'Slab Config'],
  ]

  if (loading) return (
    <Layout dark>
      <div className="flex items-center justify-center h-64 gap-3">
        <span className="spinner" style={{ borderTopColor: '#22c55e' }} />
        <span className="text-white/60">Loading Admin...</span>
      </div>
    </Layout>
  )

  return (
    <Layout dark>
      <div className="mb-6">
        <h1 className="font-heading text-2xl font-bold text-white mb-1">Admin Dashboard</h1>
        <p className="text-white/50 text-sm">Giggle platform operations · Real-time view</p>
      </div>

      {/* KPI row */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6 fade-up">
          <StatCard label={t('dashboard.active_policies')} value={summary.active_workers} />
          <StatCard label={t('dashboard.live_disruptions')} value={summary.active_triggers} accent />
          <StatCard label={t('dashboard.claims_this_week')} value={summary.claims_this_week} />
          <StatCard label={t('dashboard.payouts_this_week')} value={inr(summary.payouts_this_week)} />
          <StatCard
            label={t('dashboard.upi_mandate')}
            value={`${summary.upi_mandate_coverage_pct ?? 0}%`}
            sub={summary.avg_fraud_score_this_week != null ? `Avg fraud: ${(summary.avg_fraud_score_this_week * 100).toFixed(0)}%` : undefined}
          />
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-5 bg-white/5 p-1 rounded-xl w-fit">
        {tabs.map(([id, label]) => (
          <button key={id} onClick={() => setTab(id)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${tab === id ? 'bg-white/15 text-white' : 'text-white/40 hover:text-white/70'}`}>
            {label}
          </button>
        ))}
      </div>

      {/* Overview */}
      {tab === 'overview' && (
        <div className="grid md:grid-cols-2 gap-6 fade-up">
          {/* Loss Ratio */}
          <div className="bg-white/10 border border-white/10 rounded-2xl p-5">
            <h2 className="font-heading font-semibold text-white mb-4">Loss Ratio by Zone</h2>
            {lossRatio.length === 0 ? (
              <p className="text-white/40 text-sm py-4">No data</p>
            ) : (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={lossRatio} margin={{ left: -20, right: 0, top: 0, bottom: 0 }}>
                  <XAxis dataKey="zone_cluster_id" tickFormatter={z => ZONE_NAMES[z]?.slice(0,6) || `Z${z}`} tick={{ fill: '#ffffff60', fontSize: 10 }} />
                  <YAxis tick={{ fill: '#ffffff60', fontSize: 10 }} />
                  <Tooltip
                    contentStyle={{ background: '#0D2818', border: '1px solid #ffffff20', color: '#fff', borderRadius: 8 }}
                    formatter={(v, n, p) => [`${(v*100).toFixed(1)}%`, 'Loss Ratio']}
                    labelFormatter={z => ZONE_NAMES[z] || `Zone ${z}`}
                  />
                  <Bar dataKey="loss_ratio" fill="#F5A623" radius={[4,4,0,0]}
                    label={{ position: 'top', fill: '#fff', fontSize: 9, formatter: v => v > 0 ? `${(v*100).toFixed(0)}%` : '' }} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Claims forecast */}
          <div className="bg-white/10 border border-white/10 rounded-2xl p-5">
            <h2 className="font-heading font-semibold text-white mb-4">Claims Forecast (Next 4 Weeks)</h2>
            {forecast.length === 0 ? (
              <p className="text-white/40 text-sm py-4">No forecast data</p>
            ) : (
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={forecast} margin={{ left: -20, right: 0, top: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                  <XAxis dataKey="week" tickFormatter={w => `W${w}`} tick={{ fill: '#ffffff60', fontSize: 10 }} />
                  <YAxis tick={{ fill: '#ffffff60', fontSize: 10 }} />
                  <Tooltip contentStyle={{ background: '#0D2818', border: '1px solid #ffffff20', color: '#fff', borderRadius: 8 }} />
                  <Line type="monotone" dataKey="predicted_claims" stroke="#22c55e" strokeWidth={2} dot={{ fill: '#22c55e', r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Enrollment metrics */}
          {enrollment && (
            <div className="bg-white/10 border border-white/10 rounded-2xl p-5 col-span-2">
              <h2 className="font-heading font-semibold text-white mb-4">Enrollment Metrics</h2>
              <div className="grid grid-cols-4 gap-4">
                {[
                  ['New This Week', enrollment.enrollments_last_7d ?? enrollment.new_this_week ?? '—'],
                  ['Lapse Rate', `${((enrollment.lapse_rate ?? enrollment.lapse_rate_pct ?? 0)*100).toFixed(1)}%`],
                  ['High-Tier Fraction', `${((enrollment.high_tier_fraction ?? enrollment.high_tier_enrollment_pct ?? 0)*100).toFixed(1)}%`],
                  ['Adverse Selection', enrollment.adverse_selection_alert ? '⚠ Alert' : '✓ Normal'],
                ].map(([k, v]) => (
                  <div key={k} className="text-center">
                    <div className={`font-heading text-2xl font-bold ${k === 'Adverse Selection' && enrollment.adverse_selection_alert ? 'text-red-400' : 'text-white'}`}>{v}</div>
                    <div className="text-xs text-white/50 mt-0.5">{k}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Workers List */}
      {tab === 'workers' && (
        <div className="bg-white/10 border border-white/10 rounded-2xl p-5 fade-up">
          <h2 className="font-heading font-semibold text-white mb-4">Enrolled Workers</h2>
          {workersList.length === 0 ? <p className="text-white/40 text-sm py-4">No workers found</p> : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead><tr className="text-left border-b border-white/10">
                  {['Worker ID','Platform','Partner ID','Pincode','Language','Policy Status'].map(h => (
                    <th key={h} className="pb-2 pr-4 text-xs font-semibold text-white/40 uppercase tracking-wide">{h}</th>
                  ))}
                </tr></thead>
                <tbody>
                  {workersList.map(w => (
                    <tr key={w.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                      <td className="py-3 pr-4 font-mono text-xs text-white/60">{String(w.id).slice(0,8)}...</td>
                      <td className="py-3 pr-4 text-white/80 capitalize">{w.platform}</td>
                      <td className="py-3 pr-4 font-mono text-xs text-white/80">{w.partner_id}</td>
                      <td className="py-3 pr-4 text-white/80">{w.pincode}</td>
                      <td className="py-3 pr-4 text-white/80 uppercase">{w.language_preference}</td>
                      <td className="py-3 pr-4">
                        <span className={`badge text-xs ${w.policy_status === 'active' ? 'badge-active' : 'badge-waiting'}`}>
                          {w.policy_status || 'unknown'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Triggers */}
      {tab === 'triggers' && (
        <div className="bg-white/10 border border-white/10 rounded-2xl p-5 fade-up">
          <h2 className="font-heading font-semibold text-white mb-4">Trigger Event History</h2>
          {triggerHist.length === 0 ? <p className="text-white/40 text-sm py-4">No trigger history</p> : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead><tr className="text-left border-b border-white/10">
                  {['Zone','Type','Score','Sources','Payouts','Status','When'].map(h => (
                    <th key={h} className="pb-2 pr-4 text-xs font-semibold text-white/40 uppercase tracking-wide">{h}</th>
                  ))}
                </tr></thead>
                <tbody>
                  {triggerHist.map(t => (
                    <tr key={t.trigger_event_id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                      <td className="py-3 pr-4 text-white/90">{ZONE_NAMES[t.zone_cluster_id] || `Zone ${t.zone_cluster_id}`}</td>
                      <td className="py-3 pr-4">
                        <span className="flex items-center gap-1.5 text-white/80">
                          {TRIGGER_DISPLAY[t.trigger_type]?.icon} {t.trigger_type.replace(/_/g,' ')}
                        </span>
                      </td>
                      <td className="py-3 pr-4 text-accent-400 font-bold">{(parseFloat(t.composite_score||0)*100).toFixed(0)}%</td>
                      <td className="py-3 pr-4 text-white/60">{t.sources_confirmed}</td>
                      <td className="py-3 pr-4 text-white/80">{t.payout_count}</td>
                      <td className="py-3 pr-4"><span className={`badge text-xs ${t.status === 'active' ? 'badge-active' : 'badge-waiting'}`}>{t.status}</span></td>
                      <td className="py-3 text-white/40 text-xs">{t.triggered_at ? new Date(t.triggered_at).toLocaleDateString('en-IN') : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Claims Review */}
      {tab === 'claims' && (
        <div className="bg-white/10 border border-white/10 rounded-2xl p-5 fade-up">
          <h2 className="font-heading font-semibold text-white mb-4">Claims Pending Review</h2>
          {pendingClaims.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-3xl mb-2">✅</p>
              <p className="text-white/50 text-sm">No claims pending review</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead><tr className="text-left border-b border-white/10">
                  {['Claim ID','Worker','Fraud Score','Routing','Zone Match','Action'].map(h => (
                    <th key={h} className="pb-2 pr-4 text-xs font-semibold text-white/40 uppercase tracking-wide">{h}</th>
                  ))}
                </tr></thead>
                <tbody>
                  {pendingClaims.map(c => {
                    const cid = c.claim_id || c.id
                    const sc = parseFloat(c.fraud_score || 0)
                    const done = resolveResult[cid]
                    return (
                      <tr key={cid} className="border-b border-white/5">
                        <td className="py-3 pr-4 font-mono text-xs text-white/60">{String(cid).slice(-8).toUpperCase()}</td>
                        <td className="py-3 pr-4 font-mono text-xs text-white/50">{String(c.worker_id).slice(-6).toUpperCase()}</td>
                        <td className="py-3 pr-4">
                          <span className={`font-bold ${sc < .3 ? 'text-green-400' : sc < .7 ? 'text-amber-400' : 'text-red-400'}`}>{(sc*100).toFixed(0)}%</span>
                        </td>
                        <td className="py-3 pr-4 text-xs text-white/70">{c.fraud_routing}</td>
                        <td className="py-3 pr-4">
                          <span className={`badge text-xs ${c.zone_claim_match ? 'badge-approved' : c.zone_claim_match === false ? 'badge-held' : 'badge-waiting'}`}>
                            {c.zone_claim_match ? '✓' : c.zone_claim_match === false ? '✗' : '?'}
                          </span>
                        </td>
                        <td className="py-3">
                          {done ? <span className="text-green-400 text-xs font-semibold">{done.status === 'approved' ? '✅ Approved' : '❌ Rejected'}</span> : (
                            <div className="flex gap-2">
                              <button onClick={() => resolveClaim(cid, 'approve')} disabled={!!resolveLoading}
                                className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-xs rounded-lg font-semibold transition-colors">
                                {resolveLoading === cid+'approve' ? '...' : 'Approve'}
                              </button>
                              <button onClick={() => resolveClaim(cid, 'reject')} disabled={!!resolveLoading}
                                className="px-3 py-1 bg-red-700/60 hover:bg-red-700 text-white text-xs rounded-lg font-semibold transition-colors">
                                {resolveLoading === cid+'reject' ? '...' : 'Reject'}
                              </button>
                            </div>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Model Health */}
      {tab === 'model' && modelHealth && (
        <div className="grid md:grid-cols-2 gap-6 fade-up">
          <div className="bg-white/10 border border-white/10 rounded-2xl p-5">
            <h2 className="font-heading font-semibold text-white mb-4">Fraud Model</h2>
            {[
              ['Precision', `${((modelHealth.fraud_precision ?? modelHealth.fraud_model_precision ?? 0)*100).toFixed(1)}%`],
              ['Baseline Drift', modelHealth.baseline_drift_alert ? '⚠ Drift Detected' : '✓ Stable'],
              ['Adverse Selection Alert', modelHealth.adverse_selection_alert ? '⚠ Alert' : '✓ Normal'],
            ].map(([k,v]) => (
              <div key={k} className="flex justify-between py-2.5 border-b border-white/10 text-sm">
                <span className="text-white/50">{k}</span>
                <span className={`font-semibold ${v.startsWith('⚠') ? 'text-amber-400' : 'text-white'}`}>{v}</span>
              </div>
            ))}
          </div>
          <div className="bg-white/10 border border-white/10 rounded-2xl p-5">
            <h2 className="font-heading font-semibold text-white mb-4">Slab Config Health</h2>
            {[
              ['Oldest Slab Verified', `${modelHealth.oldest_slab_verified_days ?? modelHealth.slab_config_last_verified_days_ago ?? '—'} days ago`],
              ['Stale Alert', modelHealth.slab_config_stale ? '⚠ Stale' : '✓ Fresh'],
            ].map(([k,v]) => (
              <div key={k} className="flex justify-between py-2.5 border-b border-white/10 text-sm">
                <span className="text-white/50">{k}</span>
                <span className={`font-semibold ${v.startsWith('⚠') ? 'text-red-400' : 'text-white'}`}>{v}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Slab Config */}
      {tab === 'slab' && (
        <div className="bg-white/10 border border-white/10 rounded-2xl p-5 fade-up">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-heading font-semibold text-white">Slab Configuration</h2>
            <button onClick={verifySlabs} disabled={verifying}
              className="bg-accent-500 hover:bg-accent-600 text-white font-semibold px-4 py-2 rounded-xl text-sm transition-all">
              {verifying ? '...' : 'Mark All Verified'}
            </button>
          </div>
          {slabConfig ? (
            <div className="text-sm">
              <p className="text-white/60 mb-3">
                Last verified: <span className={`font-semibold ${slabConfig.slab_config_stale ? 'text-red-400' : 'text-green-400'}`}>
                  {slabConfig.oldest_slab_verified_days ?? '—'} days ago
                </span>
                {slabConfig.slab_config_stale && <span className="text-amber-400 ml-2">⚠ Stale — re-verify recommended</span>}
              </p>
              {slabConfig.slabs && (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead><tr className="text-left border-b border-white/10">
                      {['Zone','Min (₹)','Mid (₹)','Max (₹)','Last Verified'].map(h => (
                        <th key={h} className="pb-2 pr-4 text-xs font-semibold text-white/40 uppercase tracking-wide">{h}</th>
                      ))}
                    </tr></thead>
                    <tbody>
                      {slabConfig.slabs.map((s, i) => (
                        <tr key={i} className="border-b border-white/5 hover:bg-white/5">
                          <td className="py-2 pr-4 text-white/80">{ZONE_NAMES[s.zone_cluster_id] || `Zone ${s.zone_cluster_id}`}</td>
                          <td className="py-2 pr-4 text-white/70">₹{s.zone_rate_min}</td>
                          <td className="py-2 pr-4 text-white/70">₹{s.zone_rate_mid}</td>
                          <td className="py-2 pr-4 text-white/70">₹{s.zone_rate_max}</td>
                          <td className="py-2 text-white/40 text-xs">{s.last_verified_at ? new Date(s.last_verified_at).toLocaleDateString('en-IN') : '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ) : <p className="text-white/40 text-sm py-4">No slab config data available</p>}
        </div>
      )}
    </Layout>
  )
}
