import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { CashflowMonth, PayerRollup } from '../api/types'
import { gbp, monthLabel } from '../lib/format'
import { TODAY } from '../lib/pipeline'

const compact = new Intl.NumberFormat('en-GB', {
  style: 'currency',
  currency: 'GBP',
  notation: 'compact',
  maximumFractionDigits: 1,
})

const axis = { fontSize: 11.5, fill: 'var(--ink3)' }

function MoneyTip({ active, payload, label }: { active?: boolean; payload?: any[]; label?: string }) {
  if (!active || !payload?.length) return null
  return (
    <div
      className="card"
      style={{ padding: '8px 12px', fontSize: 12.5, boxShadow: '0 4px 14px rgba(11,11,11,.14)' }}
    >
      <div style={{ color: 'var(--ink3)', marginBottom: 4 }}>{label}</div>
      {payload
        .filter((p) => p.value > 0)
        .map((p) => (
          <div key={p.dataKey} className="row" style={{ gap: 6 }}>
            <i style={{ width: 9, height: 9, borderRadius: 3, background: p.color ?? p.stroke, display: 'inline-block' }} />
            <span style={{ color: 'var(--ink2)' }}>{p.name}</span>
            <b style={{ fontVariantNumeric: 'tabular-nums' }}>{gbp(p.value)}</b>
          </div>
        ))}
    </div>
  )
}

export function CashflowChart({ months }: { months: CashflowMonth[] }) {
  const nowYM = TODAY.toISOString().slice(0, 7)
  // Actuals stop at the current month; the projection starts there. Zeros beyond
  // those edges would read as a collapse, so they become gaps instead.
  const data = months.map((m) => ({
    label: monthLabel(m.month),
    received: m.month <= nowYM ? m.received : null,
    expected: m.month >= nowYM ? m.expected : null,
  }))
  return (
    <div>
      <div className="chart-legend">
        <span><i style={{ background: 'var(--brand)' }} />Received (after fees)</span>
        <span><i style={{ background: 'var(--ink3)' }} />Expected from outstanding</span>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data} margin={{ top: 8, right: 12, left: 4, bottom: 0 }}>
          <CartesianGrid stroke="var(--line)" vertical={false} />
          <XAxis dataKey="label" tick={axis} tickLine={false} axisLine={{ stroke: 'var(--line)' }} />
          <YAxis
            tick={axis}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v: number) => compact.format(v)}
            width={52}
          />
          <Tooltip content={<MoneyTip />} cursor={{ stroke: 'var(--line)' }} />
          <ReferenceLine x="Jul" stroke="var(--ink3)" strokeDasharray="3 3" label={{ value: 'today', fontSize: 11, fill: 'var(--ink3)', position: 'top' }} />
          <Line isAnimationActive={false} type="monotone" dataKey="received" name="Received" stroke="var(--brand)" strokeWidth={2} dot={{ r: 2.5 }} activeDot={{ r: 4 }} />
          <Line isAnimationActive={false} type="monotone" dataKey="expected" name="Expected" stroke="var(--ink3)" strokeWidth={2} strokeDasharray="5 4" dot={{ r: 2.5 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export function CompareBars({ payers }: { payers: PayerRollup[] }) {
  const priv = payers.find((p) => p.payer_type === 'private_insurer')
  const nhs = payers.find((p) => p.payer_type === 'nhs')
  if (!priv || !nhs) return null
  const data = priv.monthly_billed.map((m, idx) => ({
    label: monthLabel(m.month),
    Private: m.amount,
    NHS: nhs.monthly_billed[idx]?.amount ?? 0,
  }))
  return (
    <div>
      <div className="chart-legend">
        <span><i style={{ background: 'var(--private)' }} />Private insurers</span>
        <span><i style={{ background: 'var(--nhs)' }} />NHS</span>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 8, right: 12, left: 4, bottom: 0 }} barGap={2}>
          <CartesianGrid stroke="var(--line)" vertical={false} />
          <XAxis dataKey="label" tick={axis} tickLine={false} axisLine={{ stroke: 'var(--line)' }} />
          <YAxis tick={axis} tickLine={false} axisLine={false} tickFormatter={(v: number) => compact.format(v)} width={52} />
          <Tooltip content={<MoneyTip />} cursor={{ fill: 'var(--brandsoft)' }} />
          <Bar isAnimationActive={false} dataKey="Private" fill="var(--private)" radius={[4, 4, 0, 0]} maxBarSize={26} />
          <Bar isAnimationActive={false} dataKey="NHS" fill="var(--nhs)" radius={[4, 4, 0, 0]} maxBarSize={26} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export function AgingBars({ payer, color }: { payer: PayerRollup; color: string }) {
  const rows = [
    { label: '0–30 days', v: payer.aging.b0_30 },
    { label: '31–60 days', v: payer.aging.b31_60 },
    { label: '61–90 days', v: payer.aging.b61_90 },
    { label: '91+ days', v: payer.aging.b91_plus },
  ]
  const max = Math.max(...rows.map((r) => r.v), 1)
  return (
    <div>
      {rows.map((r) => (
        <div className="aging-row" key={r.label}>
          <span style={{ color: 'var(--ink2)' }}>{r.label}</span>
          <div className="aging-track">
            <div className="aging-fill" style={{ width: `${(r.v / max) * 100}%`, background: color }} />
          </div>
          <span className="aging-val">{r.v ? gbp(r.v) : '–'}</span>
        </div>
      ))}
    </div>
  )
}
