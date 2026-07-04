import { Link } from 'react-router-dom'
import type { Invoice, PipelineStatus, PipelineTotal } from '../api/types'
import { daysInStage, isOverdue, isStale, stageMeta } from '../lib/pipeline'
import { gbp } from '../lib/format'

export function StatusChip({ invoice }: { invoice: Invoice }) {
  const meta = stageMeta(invoice.pipeline_status)
  const days = daysInStage(invoice)
  const suffix = invoice.pipeline_status !== 'paid' && invoice.pipeline_status !== 'rejected' && days > 7 ? ` · ${days}d` : ''
  const cls =
    invoice.pipeline_status === 'paid' ? 'paid' : invoice.pipeline_status === 'rejected' ? 'rejected' : 'stage'
  return (
    <span className="row" style={{ gap: 6 }}>
      <span className={`chip ${cls}`}>
        <span className="ico" aria-hidden>{meta.icon}</span>
        {meta.label}
        {suffix}
      </span>
      {isOverdue(invoice) && (
        <span className="chip overdue">
          <span className="ico" aria-hidden>!</span>Overdue
        </span>
      )}
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

export function ActionQueue({ invoices }: { invoices: Invoice[] }) {
  const rejected = invoices.filter((i) => i.pipeline_status === 'rejected')
  const stale = invoices.filter(isStale)
  const overdue = invoices.filter(isOverdue)
  const drafts = invoices.filter((i) => i.pipeline_status === 'draft')

  const rows: { count: number; cls: string; text: JSX.Element; to: string }[] = []
  if (rejected.length)
    rows.push({
      count: rejected.length,
      cls: 'crit',
      text: (
        <>
          <b>Rejected</b> with validation issues to fix: {gbp(rejected.reduce((s, i) => s + i.total, 0))} held up
        </>
      ),
      to: '/invoices?status=rejected',
    })
  if (overdue.length)
    rows.push({
      count: overdue.length,
      cls: 'warn',
      text: (
        <>
          <b>Past expected payment date</b>: {gbp(overdue.reduce((s, i) => s + i.amount_due, 0))} to chase
        </>
      ),
      to: '/invoices?flag=overdue',
    })
  if (stale.length)
    rows.push({
      count: stale.length,
      cls: 'warn',
      text: <><b>No movement for 14+ days</b> at their current stage</>,
      to: '/invoices?flag=stale',
    })
  if (drafts.length)
    rows.push({
      count: drafts.length,
      cls: 'info',
      text: <><b>Drafts</b> never submitted to Healthcode</>,
      to: '/invoices?status=draft',
    })

  if (!rows.length)
    return (
      <div className="empty">
        <div className="big" aria-hidden>✓</div>
        <b>No invoices need attention</b>
        Everything in flight is moving and nothing is overdue.
      </div>
    )

  return (
    <div>
      {rows.map((r, i) => (
        <div className="queue-item" key={i}>
          <span className={`queue-count ${r.cls}`}>{r.count}</span>
          <span className="qtext">{r.text}</span>
          <Link to={r.to} className="rowaction" style={{ textDecoration: 'none' }}>
            View
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
