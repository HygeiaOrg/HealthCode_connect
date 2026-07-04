import type { Invoice, PipelineStatus, PipelineTotal } from '../api/types'
import { daysInStage, isLive, stageMeta } from '../lib/pipeline'
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
