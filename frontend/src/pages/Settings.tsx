import { MOCK_MODE } from '../api/client'
import { BLOCKERS, DEFAULT_SLA, SLA_DAYS } from '../lib/triage'

export default function Settings() {
  return (
    <>
      <h1 className="page-title">Settings</h1>
      <p className="page-sub">Connections, insurer SLAs, and the triage rulebook the Fix queue runs on.</p>

      <div className="card">
        <b>Connections</b>
        <div className="queue-item">
          <span className={`queue-count ${MOCK_MODE ? 'warn' : 'info'}`}>{MOCK_MODE ? '○' : '●'}</span>
          <span className="qtext">
            <b>Xero</b> · {MOCK_MODE ? 'demo mode; set VITE_API_URL to use the backend custom connection' : 'connected via backend custom connection'}
          </span>
        </div>
        <div className="queue-item">
          <span className="queue-count warn">○</span>
          <span className="qtext"><b>Medserv</b> · status feed simulated from seed data in the demo</span>
        </div>
      </div>

      <div className="card section-gap">
        <b>Insurer payment SLAs</b>
        <p className="kpi-note" style={{ marginTop: 4 }}>
          Days allowed from reaching the insurer to payment. An invoice past its SLA enters the Fix queue as
          &ldquo;Past insurer SLA&rdquo;. Unlisted insurers get {DEFAULT_SLA} days.
        </p>
        <div className="tbl-wrap">
          <table className="tbl" style={{ minWidth: 320, maxWidth: 480 }}>
            <thead>
              <tr><th>Insurer</th><th className="num">SLA (days)</th></tr>
            </thead>
            <tbody>
              {Object.entries(SLA_DAYS).map(([name, days]) => (
                <tr key={name}>
                  <td>{name}</td>
                  <td className="num"><b>{days}</b></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card section-gap">
        <b>Triage rulebook</b>
        <p className="kpi-note" style={{ marginTop: 4 }}>
          Checked in this order; an invoice matches at most one rule, and every rule prescribes exactly one
          action. No scoring, no guesswork.
        </p>
        {BLOCKERS.map((b, i) => (
          <div className="queue-item" key={b.kind}>
            <span className="queue-count info">{i + 1}</span>
            <span className="qtext">
              <b>{b.title}</b> · {b.rule}
            </span>
            <span className={`chip sev-${b.severity}`}>{b.severity}</span>
          </div>
        ))}
      </div>
    </>
  )
}
