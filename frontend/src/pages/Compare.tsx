import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import { gbp, pct } from '../lib/format'
import { AgingBars, CompareBars } from '../components/charts'
import { Skeleton } from '../components/ui'

export default function Compare() {
  const compare = useQuery({ queryKey: ['compare'], queryFn: api.compare })

  if (compare.isLoading) return <><Skeleton height={120} /><div className="grid-kpi"><Skeleton /><Skeleton /></div></>
  if (compare.isError || !compare.data)
    return <div className="card empty"><b>Could not load the comparison</b>Check the backend connection, or unset VITE_API_URL for demo data.</div>

  const priv = compare.data.by_payer.find((p) => p.payer_type === 'private_insurer')!
  const nhs = compare.data.by_payer.find((p) => p.payer_type === 'nhs')!

  const facts = [
    { label: 'Invoices', p: String(priv.invoice_count), n: String(nhs.invoice_count) },
    { label: 'Billed (6 months)', p: gbp(priv.total_billed), n: gbp(nhs.total_billed) },
    { label: 'Outstanding', p: gbp(priv.outstanding), n: gbp(nhs.outstanding) },
    {
      label: 'Median days to payment',
      p: priv.median_days_to_payment != null ? `${priv.median_days_to_payment} days` : '–',
      n: nhs.median_days_to_payment != null ? `${nhs.median_days_to_payment} days` : '–',
    },
    { label: 'Rejection rate', p: pct(priv.rejection_rate), n: pct(nhs.rejection_rate) },
    { label: 'Clearing fees paid', p: gbp(priv.fees_paid), n: gbp(nhs.fees_paid) },
  ]

  const gap =
    priv.median_days_to_payment != null && nhs.median_days_to_payment != null
      ? priv.median_days_to_payment - nhs.median_days_to_payment
      : null

  return (
    <>
      <h1 className="page-title">Private vs NHS</h1>
      <p className="page-sub">
        The two income streams side by side, January to July 2026.
        {gap != null && gap > 0 && (
          <> Private insurer money arrives a median <b>{gap} days later</b> than NHS money, and it is the only stream paying clearing fees.</>
        )}
      </p>

      <div className="card">
        <b>Monthly billed by payer</b>
        <div className="section-gap" style={{ marginTop: 10 }}>
          <CompareBars payers={compare.data.by_payer} />
        </div>
      </div>

      <div className="card section-gap" style={{ padding: 0 }}>
        <div className="tbl-wrap">
          <table className="tbl" style={{ minWidth: 560 }}>
            <thead>
              <tr>
                <th>Metric</th>
                <th className="num" style={{ color: 'var(--good-text)' }}>Private insurers</th>
                <th className="num" style={{ color: 'var(--nhs)' }}>NHS</th>
              </tr>
            </thead>
            <tbody>
              {facts.map((f) => (
                <tr key={f.label}>
                  <td style={{ color: 'var(--ink2)' }}>{f.label}</td>
                  <td className="num"><b>{f.p}</b></td>
                  <td className="num"><b>{f.n}</b></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid-kpi section-gap" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))' }}>
        <div className="card">
          <b>Private outstanding by age</b>
          <div style={{ marginTop: 10 }}>
            <AgingBars payer={priv} color="var(--private)" />
          </div>
        </div>
        <div className="card">
          <b>NHS outstanding by age</b>
          <div style={{ marginTop: 10 }}>
            <AgingBars payer={nhs} color="var(--nhs)" />
          </div>
        </div>
      </div>
    </>
  )
}
