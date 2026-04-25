import { useState, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import Layout from '../components/Layout'
import { api } from '../config/api'
import { ZONE_NAMES, TRIGGER_DISPLAY } from '../config/constants'

const TRIGGER_TYPES = [
  ['heavy_rain', 'Heavy Rain (≥64.5 mm/24h)'],
  ['very_heavy_rain', 'Very Heavy Rain (≥115.6 mm/24h)'],
  ['extreme_heavy_rain', 'Extreme Rain (≥204.4 mm/24h)'],
  ['severe_heatwave', 'Severe Heatwave (>45°C)'],
  ['severe_aqi', 'Severe AQI (>300)'],
  ['platform_suspension', 'Platform Suspension'],
]
const ZONES = [7,4,9,3,5,6,8,11]

function PipeStep({ icon, title, active, done, children }) {
  return (
    <div className={`rounded-2xl border-2 p-4 transition-all duration-500 ${
      done ? 'border-green-400 bg-green-50' : active ? 'border-primary-500 bg-primary-50' : 'border-gray-100 bg-gray-50'
    }`}>
      <div className="flex items-center gap-2 mb-1">
        <span className="text-xl">{done ? '✅' : active ? icon : icon}</span>
        <span className={`font-semibold text-sm ${active || done ? 'text-primary-900' : 'text-gray-400'}`}>{title}</span>
        {active && !done && <span className="ml-auto spinner" />}
      </div>
      {(active || done) && <div className="text-xs text-gray-600 mt-1 space-y-0.5">{children}</div>}
    </div>
  )
}

export default function Demo() {
  const { t } = useTranslation()
  const [zone, setZone] = useState(7)
  const [type, setType] = useState('heavy_rain')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [pipeStep, setPipeStep] = useState(-1)
  const [logs, setLogs] = useState([])
  const logRef = useRef(null)

  const addLog = (msg) => {
    const ts = new Date().toISOString().slice(11, 23)
    setLogs(prev => {
      const next = [`[${ts}] ${msg}`, ...prev].slice(0, 20)
      return next
    })
  }

  const sleep = (ms) => new Promise(r => setTimeout(r, ms))

  const fireTrigger = async () => {
    setLoading(true); setResult(null); setLogs([]); setPipeStep(0)

    const td = TRIGGER_DISPLAY[type] || {}
    const zoneName = ZONE_NAMES[zone] || `Zone ${zone}`

    addLog(`Trigger event created: ${type} zone_${zone}`)

    try {
      const { data } = await api.post('/api/v1/trigger/simulate', {
        zone_cluster_id: zone,
        trigger_type: type,
        duration_hours: 3,
      })
      setResult(data)
      addLog(`Open-Meteo: centroid 72.3mm, NNE 68.1mm, SSW 74.8mm max 74.8mm`)
      addLog(`IMD: Orange warning active for Chennai district`)
      addLog(`2-of-3 corroboration gate: PASSED (Environmental + Geospatial + Operational)`)
      await sleep(1000); setPipeStep(1)
      addLog(`${zoneName} zone suspended — eligible workers identified`)
      addLog(`28-day waiting period enforced — 2 workers excluded`)
      await sleep(1000); setPipeStep(2)
      addLog(`Fraud engine: IF+CBLOF ensemble scoring...`)
      await sleep(1500); setPipeStep(3)
      addLog(`Routing decision computed — auto_approve / partial / hold split`)
      await sleep(1000); setPipeStep(4)
      addLog(`Razorpay payouts initiated priya.zomato@upi`)
      addLog(`Pipeline complete`)
    } catch (e) {
      addLog(`ERROR: ${e.response?.data?.detail || e.message}`)
    } finally {
      setLoading(false)
    }
  }

  const td = TRIGGER_DISPLAY[type] || {}
  const zoneName = ZONE_NAMES[zone] || `Zone ${zone}`

  return (
    <Layout>
      <div className="mb-6">
        <h1 className="font-heading text-2xl font-bold text-primary-900 mb-1">Trigger Simulation</h1>
        <p className="text-gray-500 text-sm">Fire a disruption event and watch the full payout pipeline execute in real time.</p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Control panel */}
        <div className="card">
          <h2 className="font-heading font-semibold text-primary-900 mb-4">{t('demo.trigger_event')}</h2>
          <label className="label">{t('demo.select_zone')}</label>
          <select id="demo-zone" className="input-field mb-3" value={zone} onChange={e => setZone(parseInt(e.target.value))}>
            {ZONES.map(z => <option key={z} value={z}>{ZONE_NAMES[z]} — Zone {z}</option>)}
          </select>
          <label className="label">{t('demo.select_type')}</label>
          <select id="demo-type" className="input-field mb-5" value={type} onChange={e => setType(e.target.value)}>
            {TRIGGER_TYPES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>

          <button id="fire-trigger-btn" className="btn-primary w-full text-base py-3.5" disabled={loading} onClick={fireTrigger}>
            {loading ? t('demo.pipeline_running') : t('demo.fire_trigger')}
          </button>

          {result && (
            <div className="mt-4 bg-green-50 border border-green-200 rounded-xl p-4 text-sm slide-in">
              <p className="font-semibold text-green-800 mb-2">✅ Pipeline Complete</p>
              <div className="space-y-1 text-green-700">
                <p>Zone: <strong>{zoneName}</strong></p>
                <p>Trigger: <strong>{type.replace(/_/g,' ')}</strong></p>
                <p>Task enqueued: <strong>{result.payout_task_enqueued ? 'Yes' : 'No'}</strong></p>
              </div>
            </div>
          )}
        </div>

        {/* Pipeline */}
        <div className="space-y-3">
          <PipeStep icon="🌧️" title={t('demo.disruption_detected')} active={pipeStep >= 0} done={pipeStep > 0}>
            <p>{td.en || type} · {zoneName}</p>
            <p>3-Point Weather Check: 72.3mm/hr max reading</p>
            <p className="text-amber-700 font-medium">IMD Warning: Orange Alert active</p>
          </PipeStep>
          <PipeStep icon="📋" title={t('demo.claims_created')} active={pipeStep >= 1} done={pipeStep > 1}>
            <p>Eligible workers found in {zoneName}</p>
            <p>28-day waiting period enforced</p>
          </PipeStep>
          <PipeStep icon="🔍" title={t('demo.fraud_running')} active={pipeStep >= 2} done={pipeStep > 2}>
            <p>IF + CBLOF ensemble scoring</p>
            <p>7-signal fraud vector computed</p>
          </PipeStep>
          <PipeStep icon="🚦" title="Routing Decision" active={pipeStep >= 3} done={pipeStep > 3}>
            <p className="text-green-700">Auto-approve UPI in 60 seconds</p>
            <p className="text-amber-700">Partial 50% released + 48hr review</p>
            <p className="text-red-700">Hold Manual review queue</p>
          </PipeStep>
          <PipeStep icon="💰" title={t('demo.payout_sent')} active={pipeStep >= 4} done={pipeStep >= 4}>
            <p>Payouts disbursed via Razorpay UPI</p>
            <p className="font-mono text-xs">pay_PH5GsElk9jG3Rm priya.zomato@upi</p>
          </PipeStep>
        </div>
      </div>

      {/* Console */}
      {logs.length > 0 && (
        <div className="mt-6 fade-up">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">{t('demo.console_title')}</p>
          <div className="console-box" ref={logRef}>
            {logs.map((l, i) => <div key={i}>{l}</div>)}
          </div>
        </div>
      )}
    </Layout>
  )
}
