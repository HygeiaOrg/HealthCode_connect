import { Link } from 'react-router-dom'
import type { Invoice, PipelineStatus, PipelineTotal } from '../api/types'
import { daysInStage, isLive, stageMeta } from '../lib/pipeline'
import { groupTriage } from '../lib/triage'
import { gbp } from '../lib/format'

export function StatusChip({ invoice }: { invoice: Invoice }) {
  const meta = stageMeta(invoice.pipeline_status)
  const days = daysInStage(invoice)
  const suffix = isLive(invoice) && days > 7 ? ` · ${days}d` : ''
  const cls =
    invoice.pipeline_status === 'paid'
      ? 'paid'
      : invoice.pipeline_status === 'rejected'
        ? 'rejected'
        : invoice.pipeline_status === 'insurer_query'
          ? 'query'
          : 'stage'
  return (
    <span className={`chip ${cls}`}>
      <span className="ico" aria-hidden>{meta.icon}</span>
      {meta.label}
      {suffix}
    </span>
  )
}

export function PayerChip({ invoice }: { invoice: Invoice }) {
  const nhs = invoice.payer_type === 'nhs'
  return <span className={`chip ${nhs ? 'payer-nhs' : 'payer-private'}`}>{invoice.insurer_name}</span>
}

export function KpiCard(props: {
  label: string
  value: string
  note?: string
  delta?: { text: string; good: boolean }
}) {
  return (
    <div className="card">
      <div className="row spread">
        <div className="kpi-num">{props.value}</div>
        {props.delta && <span className={`delta ${props.delta.good ? 'good' : 'bad'}`}>{props.delta.text}</span>}
      </div>
      <div className="kpi-label">{props.label}</div>
      {props.note && <div className="kpi-note">{props.note}</div>}
    </div>
  )
}

export function PipelineBar(props: {
  totals: PipelineTotal[]
  active?: PipelineStatus | null
  onSelect?: (s: PipelineStatus | null) => void
}) {
  const segs = props.totals.filter((t) => t.count > 0)
  return (
    <div className="money-bar" role="group" aria-label="Invoice pipeline by stage">
      {segs.map((t) => {
        const meta = stageMeta(t.status)
        const active = props.active === t.status
        const dim = props.active != null && !active
        return (
          <button
            key={t.status}
            className={`money-seg${meta.lightText ? '' : ' seg-light'}${dim ? ' dim' : ''}`}
            style={{ background: meta.cssVar, flexGrow: Math.max(t.amount, 200) }}
            onClick={() => props.onSelect?.(active ? null : t.status)}
            title={`${meta.label}: ${gbp(t.amount)} across ${t.count} invoice${t.count === 1 ? '' : 's'}`}
          >
            <span className="amt">{gbp(t.amount)}</span>
            <span className="lbl">
              {meta.label} · {t.count}
            </span>
          </button>
        )
      })}
    </div>
  )
}

const SEV_CLS = { critical: 'crit', serious: 'serious', warning: 'warn', info: 'info' } as const

/** Triage summary for the Overview: one row per blocker group, linking into the Fix queue. */
export function ActionQueue({ invoices }: { invoices: Invoice[] }) {
  const groups = groupTriage(invoices)
  if (!groups.length)
    return (
      <div className="empty">
        <div className="big" aria-hidden>✓</div>
        <b>No invoices need attention</b>
        Everything in flight is inside its SLA and nothing came back with errors.
      </div>
    )
  return (
    <div>
      {groups.map((g) => (
        <div className="queue-item" key={g.meta.kind}>
          <span className={`queue-count ${SEV_CLS[g.meta.severity]}`}>{g.rows.length}</span>
          <span className="qtext">
            <b>{g.meta.title}</b> · {gbp(g.total)} held up
          </span>
          <Link to="/fix" className="rowaction" style={{ textDecoration: 'none' }}>
            Fix
          </Link>
        </div>
      ))}
    </div>
  )
}

export function Skeleton({ height = 90 }: { height?: number }) {
  return <div className="skeleton" style={{ minHeight: height }} aria-hidden />
}

export function EmptyState(props: { icon: string; title: string; body: string }) {
  return (
    <div className="empty">
      <div className="big" aria-hidden>{props.icon}</div>
      <b>{props.title}</b>
      {props.body}
    </div>
  )
}
