import { Fragment, useState } from 'react'
import type { Invoice, PipelineStatus } from '../api/types'
import { TODAY, daysBetween, stageMeta } from '../lib/pipeline'
import { gbp, gbpExact, longDate, shortDate } from '../lib/format'
import { PayerChip, StatusChip } from './ui'

const MAIN_PATH: PipelineStatus[] = ['draft', 'at_semble', 'at_healthcode', 'with_insurer', 'paid']

function Timeline({ invoice }: { invoice: Invoice }) {
  const reached = new Map(invoice.timeline.map((e) => [e.stage, e.at]))
  const rejected = invoice.pipeline_status === 'rejected'
  const lastStage = invoice.timeline[invoice.timeline.length - 1]?.stage

  // On rejection the path stops where it broke; show the rejected node instead of the remainder.
  const rejectedAfter = rejected ? invoice.timeline[invoice.timeline.length - 2]?.stage : null
  const path: PipelineStatus[] = rejected
    ? [...MAIN_PATH.slice(0, MAIN_PATH.indexOf(rejectedAfter ?? 'at_healthcode') + 1), 'rejected']
    : MAIN_PATH

  return (
    <div className="timeline">
      {path.map((stage, idx) => {
        const at = reached.get(stage)
        const meta = stageMeta(stage)
        const done = !!at && stage !== lastStage
        const current = stage === lastStage && stage !== 'paid' && stage !== 'rejected'
        const terminal = stage === 'paid' ? 'terminal-paid' : stage === 'rejected' ? 'terminal-rejected' : ''
        const cls = [
          'tl-step',
          done ? 'done' : '',
          current ? 'current' : '',
          at && terminal ? terminal : '',
        ].join(' ')
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

function ValidationPanel({ invoice }: { invoice: Invoice }) {
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
  const fee = invoice.middleman_fee
  return (
    <td colSpan={7} className="expand-cell">
      <Timeline invoice={invoice} />
      <ValidationPanel invoice={invoice} />
      <div className="tl-meta">
        {invoice.description} for {invoice.patient_ref} · issued {longDate(invoice.issued_date)}
        {invoice.submitted_date && <> · submitted {longDate(invoice.submitted_date)}</>}
        {invoice.paid_date ? (
          <> · paid {longDate(invoice.paid_date)} ({daysBetween(invoice.issued_date, invoice.paid_date)} days)</>
        ) : invoice.expected_payment_date ? (
          <> · expected {longDate(invoice.expected_payment_date)}</>
        ) : null}
        {fee > 0 && <> · clearing fee {gbpExact(fee)}</>}
      </div>
    </td>
  )
}

function actionFor(invoice: Invoice): string {
  if (invoice.pipeline_status === 'rejected') return 'Fix'
  if (invoice.pipeline_status === 'draft') return 'Submit'
  if (invoice.amount_due > 0 && invoice.expected_payment_date && new Date(invoice.expected_payment_date) < TODAY)
    return 'Chase'
  return 'View'
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
          {invoices.map((inv) => (
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
                <td><StatusChip invoice={inv} /></td>
                <td className="mono">
                  {inv.pipeline_status === 'paid' ? `paid ${shortDate(inv.paid_date)}` : shortDate(inv.expected_payment_date)}
                </td>
                <td>
                  <button
                    className="rowaction"
                    onClick={(e) => {
                      e.stopPropagation()
                      setOpen(open === inv.id ? null : inv.id)
                    }}
                  >
                    {actionFor(inv)}
                  </button>
                </td>
              </tr>
              {open === inv.id && <tr><ExpandedRow invoice={inv} /></tr>}
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  )
}
