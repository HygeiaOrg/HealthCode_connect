import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { gbp } from '../lib/format'
import { longDate } from '../lib/format'
import { CashflowChart } from '../components/charts'
import { ActionQueue, KpiCard, PipelineBar, Skeleton } from '../components/ui'

export default function Overview() {
  const navigate = useNavigate()
  const summary = useQuery({ queryKey: ['summary'], queryFn: api.summary })
  const cashflow = useQuery({ queryKey: ['cashflow'], queryFn: api.cashflow })
  const invoices = useQuery({ queryKey: ['invoices', {}], queryFn: () => api.invoices() })

  if (summary.isLoading || cashflow.isLoading)
    return (
      <>
        <Skeleton height={220} />
        <div className="grid-kpi">
          <Skeleton /><Skeleton /><Skeleton />
        </div>
      </>
    )
  if (summary.isError || !summary.data)
    return <div className="card empty"><b>Could not load the dashboard</b>Check that the backend is running, or unset VITE_API_URL to use demo data.</div>

  const s = summary.data
  const mdPriv = s.median_days_to_payment.private_insurer
  const mdNhs = s.median_days_to_payment.nhs

  return (
    <>
      <div className="card">
        <span className="hero-label">Expected this month</span>
        <div className="hero-figure">{gbp(s.expected_this_month)}</div>
        <div className="hero-when">
          {s.expected_this_month_by ? (
            <>all of it due by <b>{longDate(s.expected_this_month_by)}</b> · </>
          ) : null}
          {gbp(s.outstanding_total)} outstanding in total, {gbp(s.overdue_total)} of it past its expected date
        </div>
        <div className="section-gap">{cashflow.data && <CashflowChart months={cashflow.data.months} />}</div>
      </div>

      <div className="grid-kpi">
        <KpiCard
          label="Outstanding"
          value={gbp(s.outstanding_total)}
          note="Billed, unpaid, not rejected. Click a pipeline stage below to see where it sits."
        />
        <KpiCard
          label="Payment velocity (median days to get paid)"
          value={mdPriv != null ? `${mdPriv} days` : '–'}
          note={`Private insurers ${mdPriv ?? '–'}d vs NHS ${mdNhs ?? '–'}d, from issue to money received.`}
          delta={mdPriv != null && mdNhs != null ? { text: `+${mdPriv - mdNhs}d vs NHS`, good: false } : undefined}
        />
        <KpiCard
          label="Clearing fees paid in 2026"
          value={gbp(s.fees_paid_ytd)}
          note="3% per private insurer invoice. This is the middleman cost the practice absorbs."
        />
      </div>

      <div className="card">
        <div className="row spread">
          <b>Where the money sits</b>
          <span className="footnote">Click a stage to open the filtered invoice list</span>
        </div>
        <PipelineBar
          totals={s.pipeline_totals}
          onSelect={(stage) => navigate(stage ? `/invoices?status=${stage}` : '/invoices')}
        />
      </div>

      <div className="card section-gap">
        <b>Needs attention</b>
        <div className="section-gap" style={{ marginTop: 8 }}>
          {invoices.data ? <ActionQueue invoices={invoices.data} /> : <Skeleton height={60} />}
        </div>
      </div>
    </>
  )
}
