import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import type { PayerType, PipelineStatus } from '../api/types'
import { isOverdue, isStale, STAGES } from '../lib/pipeline'
import { EmptyState, PipelineBar, Skeleton } from '../components/ui'
import { InvoiceTable } from '../components/invoices'

const VALID_STATUS = new Set(STAGES.map((s) => s.key))

export default function Invoices() {
  const [params, setParams] = useSearchParams()
  const [q, setQ] = useState('')

  const statusParam = params.get('status')
  const status = statusParam && VALID_STATUS.has(statusParam as PipelineStatus) ? (statusParam as PipelineStatus) : null
  const payer = params.get('payer') as PayerType | null
  const flag = params.get('flag') // overdue | stale

  const invoices = useQuery({ queryKey: ['invoices', {}], queryFn: () => api.invoices() })
  const summary = useQuery({ queryKey: ['summary'], queryFn: api.summary })

  const filtered = useMemo(() => {
    let rows = invoices.data ?? []
    if (status) rows = rows.filter((i) => i.pipeline_status === status)
    if (payer) rows = rows.filter((i) => i.payer_type === payer)
    if (flag === 'overdue') rows = rows.filter(isOverdue)
    if (flag === 'stale') rows = rows.filter(isStale)
    if (q) {
      const needle = q.toLowerCase()
      rows = rows.filter(
        (i) =>
          i.invoice_number.toLowerCase().includes(needle) ||
          i.patient_ref.toLowerCase().includes(needle) ||
          i.insurer_name.toLowerCase().includes(needle),
      )
    }
    return rows
  }, [invoices.data, status, payer, flag, q])

  const setParam = (key: string, value: string | null) => {
    const next = new URLSearchParams(params)
    if (value == null) next.delete(key)
    else next.set(key, value)
    if (key !== 'flag') next.delete('flag')
    setParams(next, { replace: true })
  }

  return (
    <>
      <h1 className="page-title">Invoices</h1>
      <p className="page-sub">Every invoice with its live pipeline position. Click a row for the full timeline.</p>

      {summary.data && (
        <PipelineBar
          totals={summary.data.pipeline_totals}
          active={status}
          onSelect={(s) => setParam('status', s)}
        />
      )}

      <div className="filters">
        <button className={`fbtn ${!payer ? 'on' : ''}`} onClick={() => setParam('payer', null)}>
          All payers
        </button>
        <button
          className={`fbtn ${payer === 'private_insurer' ? 'on' : ''}`}
          onClick={() => setParam('payer', payer === 'private_insurer' ? null : 'private_insurer')}
        >
          Private insurers
        </button>
        <button
          className={`fbtn ${payer === 'nhs' ? 'on' : ''}`}
          onClick={() => setParam('payer', payer === 'nhs' ? null : 'nhs')}
        >
          NHS
        </button>
        {flag && (
          <button className="fbtn on" onClick={() => setParam('flag', null)}>
            {flag === 'overdue' ? 'Past expected date' : 'Stale 14d+'} ✕
          </button>
        )}
        <span style={{ flex: 1 }} />
        <input
          className="search"
          placeholder="Search number, patient, insurer"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          aria-label="Search invoices"
        />
      </div>

      <div className="card" style={{ padding: 8 }}>
        {invoices.isLoading ? (
          <Skeleton height={300} />
        ) : filtered.length ? (
          <InvoiceTable invoices={filtered} />
        ) : (
          <EmptyState
            icon="🔍"
            title="No invoices match"
            body="Clear a filter above, or change the search. Rejected and overdue work lives under Needs attention on the Overview."
          />
        )}
      </div>
      <p className="footnote">
        {filtered.length} of {invoices.data?.length ?? 0} invoices shown
      </p>
    </>
  )
}
