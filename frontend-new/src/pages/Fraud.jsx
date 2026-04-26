import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import Layout from '../components/Layout'
import { api } from '../config/api'
import { getAuth } from '../hooks/useAuth'

function score_bar(v) {
  const pct = Math.round((v || 0) * 100)
  const col = pct < 30 ? 'bg-green-500' : pct < 70 ? 'bg-amber-500' : 'bg-red-500'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-100 rounded-full h-2">
        <div className={`${col} h-2 rounded-full transition-all duration-700`} style={{ width: `${pct}%` }} />
      </div>
      <span className={`text-xs font-bold w-9 text-right ${pct < 30 ? 'text-green-600' : pct < 70 ? 'text-amber-600' : 'text-red-600'}`}>{pct}%</span>
    </div>
  )
}

function routeLabel(r) {
  const m = { auto_approve:'✅ Auto-Approve', partial_review:'🟡 Partial Review', hold:'🔴 Hold' }
  return m[r] || r
}

export default function Fraud() {
  const { t } = useTranslation()
  const auth = getAuth()
  const wid = auth?.worker_id

  const [signals, setSignals] = useState(null)
  const [queue, setQueue] = useState([])
  const [workerClaims, setWorkerClaims] = useState([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState('signals')

  useEffect(() => {
    Promise.allSettled([
      wid ? api.get(`/api/v1/fraud/worker/${wid}/signals`) : null,
      api.get('/api/v1/fraud/queue'),
      wid ? api.get(`/api/v1/claims/${wid}`) : null,
    ]).then(([s, q, c]) => {
      if (s?.value) setSignals(s.value.data)
      if (q.value) setQueue(Array.isArray(q.value.data) ? q.value.data : q.value.data.queue || [])
      if (c?.value) setWorkerClaims(c.value.data.items || c.value.data.claims || [])
      setLoading(false)
    })
  }, [wid])

  if (loading) return <Layout><div className="flex items-center justify-center h-64 gap-3"><span className="spinner" /><span className="text-gray-500">{t('common.loading')}</span></div></Layout>

  return (
    <Layout>
      <div className="mb-6">
        <h1 className="font-heading text-2xl font-bold text-primary-900 mb-1">{t('nav.fraud')}</h1>
        <p className="text-gray-500 text-sm">7-signal ensemble (Isolation Forest + CBLOF) fraud scoring for your claims</p>
      </div>

      <div className="flex gap-1 mb-5 bg-gray-100 p-1 rounded-xl w-fit">
        {[['signals', 'My Fraud Signals'], ['queue', `Review Queue (${queue.length})`], ['history', 'Claim History']].map(([id, label]) => (
          <button key={id} onClick={() => setTab(id)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${tab === id ? 'bg-white text-primary-900 shadow-sm' : 'text-gray-500 hover:text-gray-800'}`}>
            {label}
          </button>
        ))}
      </div>

      {/* Signals */}
      {tab === 'signals' && (
        <div className="grid md:grid-cols-2 gap-6 fade-up">
          {signals ? (
            <>
              <div className="card">
                <h2 className="font-heading font-semibold text-primary-900 mb-4">{t('fraud.signals')}</h2>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600">Avg Fraud Score (All Claims)</span>
                    </div>
                    {score_bar(signals.avg_fraud_score)}
                  </div>
                  <div className="py-2 border-b border-gray-50">
                    <div className="text-xs text-gray-400 mb-1">Enrollment Recency Score</div>
                    {score_bar(signals.enrollment_recency_score)}
                  </div>
                  <div className="flex justify-between py-2 border-b border-gray-50 text-sm">
                    <span className="text-gray-600">Total Claims</span>
                    <span className="font-bold text-primary-900">{signals.total_claim_count}</span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-gray-50 text-sm">
                    <span className="text-gray-600">Ring Registration Flag</span>
                    <span className={`badge ${signals.ring_registration_flag ? 'badge-held' : 'badge-approved'}`}>
                      {signals.ring_registration_flag ? '⚠ Flagged' : '✓ Clear'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="card">
                <h2 className="font-heading font-semibold text-primary-900 mb-4">Zone GPS History</h2>
                {signals.zone_claim_match_history?.length > 0 ? (
                  <div className="space-y-2">
                    {signals.zone_claim_match_history.map((m, i) => (
                      <div key={i} className="flex items-center gap-3 py-2 border-b border-gray-50 text-sm">
                        <span className="text-gray-400 w-16">Claim #{i+1}</span>
                        <span className={`badge ${m ? 'badge-approved' : m === false ? 'badge-held' : 'badge-waiting'}`}>
                          {m ? '✓ In Zone' : m === false ? '✗ Out of Zone' : '—'}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : <p className="text-gray-400 text-sm py-4">No GPS history yet</p>}

                <div className="mt-4 bg-primary-50 rounded-xl p-3">
                  <p className="text-xs font-semibold text-primary-800 mb-1">How the fraud engine works</p>
                  <p className="text-xs text-gray-600 leading-relaxed">
                    7 signals → Isolation Forest (unsupervised) + CBLOF (cluster-based) → 
                    ensemble score. &lt;30% = Auto-approve, 30–70% = Partial review, &gt;70% = Hold.
                  </p>
                </div>
              </div>
            </>
          ) : <div className="col-span-2 text-center text-gray-400 py-8">Sign in as a worker to see your fraud signals</div>}
        </div>
      )}

      {/* Review queue */}
      {tab === 'queue' && (
        <div className="card fade-up">
          <h2 className="font-heading font-semibold text-primary-900 mb-4">Pending Review Queue</h2>
          {queue.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-4xl mb-3">✅</p>
              <p className="text-gray-500 text-sm">No claims pending review</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead><tr className="text-left border-b border-gray-100">
                  {['Worker','Filed','Fraud Score','Routing','Zone Match','Status'].map(h => (
                    <th key={h} className="pb-2 pr-4 text-xs font-semibold text-gray-400 uppercase tracking-wide">{h}</th>
                  ))}
                </tr></thead>
                <tbody>
                  {queue.map((c, i) => (
                    <tr key={i} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                      <td className="py-3 pr-4 font-mono text-xs">{String(c.worker_id || c.claim_id).slice(-8).toUpperCase()}</td>
                      <td className="py-3 pr-4 text-gray-500 text-xs">
                        {c.claim_date ? new Date(c.claim_date + (c.claim_date.includes('Z') ? '' : 'Z')).toLocaleDateString('en-IN', { timeZone: 'Asia/Kolkata' }) : '—'}
                      </td>
                      <td className="py-3 pr-4">{score_bar(c.fraud_score)}</td>
                      <td className="py-3 pr-4 text-xs">{routeLabel(c.fraud_routing)}</td>
                      <td className="py-3 pr-4">
                        <span className={`badge ${c.zone_claim_match ? 'badge-approved' : c.zone_claim_match === false ? 'badge-held' : 'badge-waiting'}`}>
                          {c.zone_claim_match ? 'Yes' : c.zone_claim_match === false ? 'No' : '—'}
                        </span>
                      </td>
                      <td className="py-3"><span className={`badge badge-${c.status}`}>{c.status}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Claim history */}
      {tab === 'history' && (
        <div className="card fade-up">
          <h2 className="font-heading font-semibold text-primary-900 mb-4">My Claim Fraud Scores</h2>
          {workerClaims.length === 0 ? (
            <p className="text-gray-400 text-sm py-8 text-center">No claims found</p>
          ) : (
            <div className="space-y-3">
              {workerClaims.map(c => {
                const sc = parseFloat(c.fraud_score || 0)
                return (
                  <div key={c.claim_id || c.id} className="flex items-center gap-4 py-3 border-b border-gray-50">
                    <div className="font-mono text-xs text-gray-400 w-16">{String(c.claim_id || c.id).slice(-8).toUpperCase()}</div>
                    <div className="flex-1">{score_bar(sc)}</div>
                    <div className="text-xs">{routeLabel(c.fraud_routing)}</div>
                    <span className={`badge badge-${c.status}`}>{c.status}</span>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}
    </Layout>
  )
}
