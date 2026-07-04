import { Fragment, useState } from 'react'
import { Link } from 'react-router-dom'
import type { Invoice, PipelineStatus } from '../api/types'
import { daysBetween, stageMeta } from '../lib/pipeline'
import { triage } from '../lib/triage'
import { gbp, gbpExact, longDate, shortDate } from '../lib/format'
import { PayerChip, StatusChip } from './ui'

const MAIN_PATH: PipelineStatus[] = ['draft', 'at_medserv', 'with_insurer', 'paid']

function Timeline({ invoice }: { invoice: Invoice }) {
  const reached = new Map(invoice.timeline.map((e) => [e.stage, e.at]))
  const lastStage = invoice.timeline[invoice.timeline.length - 1]?.stage

  let path: PipelineStatus[]
  if (invoice.pipeline_status === 'rejected') {
    // The path stops where it broke; the rejected node replaces the remainder.
    const brokeAfter = invoice.timeline[invoice.timeline.length - 2]?.stage ?? 'at_medserv'
    const idx = MAIN_PATH.indexOf(brokeAfter)
    path = [...MAIN_PATH.slice(0, (idx === -1 ? 1 : idx) + 1), 'rejected']
  } else if (reached.has('insurer_query')) {
    path = ['draft', 'at_medserv', 'with_insurer', 'insurer_query', 'paid']
  } else {
    path = MAIN_PATH
  }

  return (
    <div className="timeline">
      {path.map((stage, idx) => {
        const at = reached.get(stage)
        const meta = stageMeta(stage)
        const done = !!at && stage !== lastStage
        const current = stage === lastStage && stage !== 'paid' && stage !== 'rejected'
        const terminal = stage === 'paid' ? 'terminal-paid' : stage === 'rejected' ? 'terminal-rejected' : ''
        const cls = ['tl-step', done ? 'done' : '', current ? 'current' : '', at && terminal ? terminal : ''].join(' ')
        const dateLabel = at
          ? shortDate(at)
          : stage === 'paid' && invoice.expected_payment_date
            ? `exp. ${shortDate(invoice.expected_payment_date)}`
            : 'pending'
        return (
          <div className={cls} key={stage}>
            <div className="tl-node">
              <span className="tl-dot" aria-hidden />
              <span className="tl-lbl">{meta.label}</span>
              <span className="tl-date">{dateLabel}</span>
            </div>
            {idx < path.length - 1 && <span className="tl-bar" aria-hidden />}
          </div>
        )
      })}
    </div>
  )
}

export function ValidationPanel({ invoice }: { invoice: Invoice }) {
  if (!invoice.validation_issues.length) return null
  return (
    <div className="vpanel">
      <div className="vpanel-head">
        {invoice.validation_issues.length} issue{invoice.validation_issues.length > 1 ? 's' : ''} blocking this
        invoice
      </div>
      {invoice.validation_issues.map((v, i) => (
        <div className="vrow" key={i}>
          <span className="f"><span className="vlbl">Field</span>{v.field}</span>
          <span><span className="vlbl">Error</span>{v.error}</span>
          <span className="s"><span className="vlbl">Solution</span>{v.solution}</span>
        </div>
      ))}
    </div>
  )
}

function ExpandedRow({ invoice }: { invoice: Invoice }) {
  const shortfall = invoice.pipeline_status === 'paid' && invoice.amount_due > 0
  return (
    <td colSpan={7} className="expand-cell">
      <Timeline invoice={invoice} />
      <ValidationPanel invoice={invoice} />
      {invoice.query_reason && <div className="tl-meta"><b>Insurer query:</b> {invoice.query_reason}</div>}
      <div className="tl-meta">
        {invoice.description} for {invoice.patient_ref} · issued {longDate(invoice.issued_date)}
        {invoice.submitted_date && <> · submitted {longDate(invoice.submitted_date)}</>}
        {invoice.paid_date ? (
          <>
            {' '}· paid {longDate(invoice.paid_date)} ({daysBetween(invoice.issued_date, invoice.paid_date)} days)
            {shortfall && <> · {gbpExact(invoice.amount_due)} short</>}
          </>
        ) : invoice.expected_payment_date ? (
          <> · expected {longDate(invoice.expected_payment_date)}</>
        ) : null}
        {invoice.middleman_fee > 0 && <> · clearing fee {gbpExact(invoice.middleman_fee)}</>}
        {invoice.last_chased_at && <> · chased {longDate(invoice.last_chased_at)}</>}
      </div>
    </td>
  )
}

export function InvoiceTable({ invoices }: { invoices: Invoice[] }) {
  const [open, setOpen] = useState<string | null>(null)
  return (
    <div className="tbl-wrap">
      <table className="tbl">
        <thead>
          <tr>
            <th>Invoice</th>
            <th>Patient</th>
            <th>Payer</th>
            <th className="num">Amount</th>
            <th>Status</th>
            <th>Expected</th>
            <th aria-label="Actions" />
          </tr>
        </thead>
        <tbody>
          {invoices.map((inv) => {
            const t = triage(inv)
            return (
              <Fragment key={inv.id}>
                <tr
                  className="rowbtn"
                  onClick={() => setOpen(open === inv.id ? null : inv.id)}
                  aria-expanded={open === inv.id}
                >
                  <td className="mono">{inv.invoice_number}</td>
                  <td>{inv.patient_ref}</td>
                  <td><PayerChip invoice={inv} /></td>
                  <td className="num">{gbp(inv.total)}</td>
                  <td>
                    <span className="row" style={{ gap: 6 }}>
                      <StatusChip invoice={inv} />
                      {t && <span className={`chip sev-${t.severity}`}>{t.chip}</span>}
                    </span>
                  </td>
                  <td className="mono">
                    {inv.pipeline_status === 'paid'
                      ? `paid ${shortDate(inv.paid_date)}`
                      : shortDate(inv.expected_payment_date)}
                  </td>
                  <td>
                    {t ? (
                      <Link
                        to="/fix"
                        className="rowaction"
                        style={{ textDecoration: 'none' }}
                        onClick={(e) => e.stopPropagation()}
                      >
                        Fix
                      </Link>
                    ) : (
                      <button
                        className="rowaction"
                        onClick={(e) => {
                          e.stopPropagation()
                          setOpen(open === inv.id ? null : inv.id)
                        }}
                      >
                        View
                      </button>
                    )}
                  </td>
                </tr>
                {open === inv.id && <tr><ExpandedRow invoice={inv} /></tr>}
              </Fragment>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
