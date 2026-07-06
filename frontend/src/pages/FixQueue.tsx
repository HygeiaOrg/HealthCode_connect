import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'
import type { Invoice } from '../api/types'
import type { Triage, TriageGroup } from '../lib/triage'
import { BLOCKERS, DEFAULT_SLA, SLA_DAYS, groupTriage } from '../lib/triage'
import { gbp } from '../lib/format'
import { EmptyState, PayerChip, Skeleton } from '../components/ui'
import { ValidationPanel } from '../components/invoices'
import { UploadCard } from '../components/upload'

function useFixAction() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (job: { invoice: Invoice; t: Triage; message?: string }) => {
      const { invoice, t } = job
      switch (t.kind) {
        case 'rejected':
          return api.resubmit(invoice.id)
        case 'query':
          return api.reply(invoice.id, job.message ?? 'Details attached.')
        case 'shortfall':
          return api.resolve(invoice.id)
        case 'overdue':
        case 'stalled':
          return api.chase(invoice.id)
        case 'stale_draft':
          return api.submitDraft(invoice.id)
      }
    },
    onSuccess: () => qc.invalidateQueries(),
  })
}

function FixRow({ invoice, t }: { invoice: Invoice; t: Triage }) {
  const action = useFixAction()
  const [message, setMessage] = useState('')
  return (
    <div className="fixq-row">
      <div className="fixq-main">
        <div className="who row" style={{ gap: 8 }}>
          {invoice.invoice_number} · {invoice.patient_ref}
          <PayerChip invoice={invoice} />
          <span className={`chip sev-${t.severity}`}>{t.chip}</span>
        </div>
        <div className="why">{t.explanation}</div>
        {t.kind === 'rejected' && <ValidationPanel invoice={invoice} />}
        {t.kind === 'query' && (
          <textarea
            className="reply-box"
            placeholder="Reply to the insurer (attachments arrive via Medserv)…"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            aria-label={`Reply for ${invoice.invoice_number}`}
          />
        )}
      </div>
      <span className="fixq-amt">{gbp(t.releases)}</span>
      <button
        className="fix-btn"
        disabled={action.isPending}
        onClick={() => action.mutate({ invoice, t, message })}
      >
        {action.isPending ? 'Working…' : t.actionLabel}
      </button>
    </div>
  )
}

function Group({ group }: { group: TriageGroup }) {
  return (
    <div className={`card fixq-group sev-${group.meta.severity} section-gap`}>
      <div className="fixq-head">
        <b>{group.meta.title}</b>
        <span className="chip muted">{group.rows.length}</span>
        <span className="fixq-amt" style={{ marginLeft: 'auto' }}>{gbp(group.total)}</span>
        <span className="rule">{group.meta.rule}</span>
      </div>
      {group.rows.map((r) => (
        <FixRow key={r.invoice.id} invoice={r.invoice} t={r.t} />
      ))}
    </div>
  )
}

export default function FixQueue() {
  const invoices = useQuery({ queryKey: ['invoices', {}], queryFn: () => api.invoices() })

  if (invoices.isLoading) return <><Skeleton height={90} /><div className="section-gap" /><Skeleton height={240} /></>
  if (invoices.isError || !invoices.data)
    return <div className="card empty"><b>Could not load the queue</b>Check the backend connection, or unset VITE_API_URL for demo data.</div>

  const groups = groupTriage(invoices.data)
  const count = groups.reduce((s, g) => s + g.rows.length, 0)
  const releases = groups.reduce((s, g) => s + g.total, 0)

  return (
    <>
      <h1 className="page-title">Fix queue</h1>
      <p className="page-sub">
        Every stuck invoice, matched to one rule and one next action. Check new invoices here before they leave
        the practice; the rulebook below shows exactly how decisions are made.
      </p>

      <UploadCard />
      <div className="section-gap" />

      {count === 0 ? (
        <div className="card">
          <EmptyState
            icon="✓"
            title="Nothing is stuck"
            body="Every invoice is either moving inside its SLA or paid in full. Check back after the next Medserv sync."
          />
        </div>
      ) : (
        <>
          <div className="card">
            <div className="row" style={{ gap: 24 }}>
              <div>
                <div className="kpi-num">{count}</div>
                <div className="kpi-label">invoices stuck</div>
              </div>
              <div>
                <div className="kpi-num">{gbp(releases)}</div>
                <div className="kpi-label">released by clearing this queue</div>
              </div>
              <div style={{ flex: 1 }} />
              <div className="kpi-note" style={{ maxWidth: 380 }}>
                Groups are ordered by severity, rows by money at stake. Working top to bottom is always the
                highest-value order.
              </div>
            </div>
          </div>
          {groups.map((g) => (
            <Group key={g.meta.kind} group={g} />
          ))}
        </>
      )}

      <details className="rulebook card section-gap">
        <summary>How triage decides: the rulebook and insurer SLAs</summary>
        <div className="section-gap" style={{ marginTop: 10 }}>
          {BLOCKERS.map((b, i) => (
            <div className="queue-item" key={b.kind}>
              <span className="queue-count info">{i + 1}</span>
              <span className="qtext"><b>{b.title}</b> · {b.rule}</span>
              <span className={`chip sev-${b.severity}`}>{b.severity}</span>
            </div>
          ))}
          <p className="footnote" style={{ marginTop: 14 }}>
            Payment SLAs, in days from reaching the insurer (unlisted insurers get {DEFAULT_SLA}):{' '}
            {Object.entries(SLA_DAYS).map(([name, days]) => `${name} ${days}`).join(' · ')}. Rules are checked
            top to bottom; an invoice matches at most one.
          </p>
        </div>
      </details>
    </>
  )
}
