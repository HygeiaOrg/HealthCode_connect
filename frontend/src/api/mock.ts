// Mock mode: serves the exact contract shapes from the shared seed fixture,
// so the app runs with no backend. client.ts switches here when VITE_API_URL is unset.
import seedsRaw from './seeds.json'
import type { Cashflow, Compare, Invoice, PayerRollup, PayerType, PipelineStatus, Summary } from './types'
import { STAGES, TODAY, daysBetween, isOverdue, isStale } from '../lib/pipeline'

const seeds = seedsRaw as Invoice[]
const delay = <T,>(v: T, ms = 180): Promise<T> => new Promise((r) => setTimeout(() => r(v), ms))

const median = (xs: number[]): number | null => {
  if (!xs.length) return null
  const s = [...xs].sort((a, b) => a - b)
  const m = Math.floor(s.length / 2)
  return s.length % 2 ? s[m] : Math.round((s[m - 1] + s[m]) / 2)
}

const daysToPay = (inv: Invoice): number | null =>
  inv.paid_date ? daysBetween(inv.issued_date, inv.paid_date) : null

const ym = (iso: string): string => iso.slice(0, 7)

export function mockInvoices(params: {
  payer_type?: PayerType
  status?: PipelineStatus
  q?: string
}): Promise<Invoice[]> {
  let out = seeds
  if (params.payer_type) out = out.filter((i) => i.payer_type === params.payer_type)
  if (params.status) out = out.filter((i) => i.pipeline_status === params.status)
  if (params.q) {
    const q = params.q.toLowerCase()
    out = out.filter(
      (i) =>
        i.invoice_number.toLowerCase().includes(q) ||
        i.patient_ref.toLowerCase().includes(q) ||
        i.insurer_name.toLowerCase().includes(q),
    )
  }
  out = [...out].sort((a, b) => b.issued_date.localeCompare(a.issued_date))
  return delay(out)
}

export function mockInvoice(id: string): Promise<Invoice> {
  const inv = seeds.find((i) => i.id === id)
  if (!inv) return Promise.reject(new Error(`Invoice ${id} not found`))
  return delay(inv)
}

export function mockSummary(): Promise<Summary> {
  const open = seeds.filter((i) => i.pipeline_status !== 'paid' && i.pipeline_status !== 'rejected')
  const outstanding = open.reduce((s, i) => s + i.amount_due, 0)
  const thisMonth = TODAY.toISOString().slice(0, 7)
  const dueThisMonth = open.filter(
    (i) => i.expected_payment_date && ym(i.expected_payment_date) === thisMonth,
  )
  const expectedThisMonth = dueThisMonth.reduce((s, i) => s + i.amount_due, 0)
  const lastExpected = dueThisMonth
    .map((i) => i.expected_payment_date!)
    .sort()
    .pop()
  const overdue = open.filter(isOverdue).reduce((s, i) => s + i.amount_due, 0)

  const paid = seeds.filter((i) => i.pipeline_status === 'paid')
  const mdays = (p: PayerType) =>
    median(paid.filter((i) => i.payer_type === p).map((i) => daysToPay(i)!).filter((n) => n != null))

  const fees = paid
    .filter((i) => i.paid_date && i.paid_date.startsWith('2026'))
    .reduce((s, i) => s + i.middleman_fee, 0)

  const pipeline_totals = STAGES.map((st) => {
    const rows = seeds.filter((i) => i.pipeline_status === st.key)
    return {
      status: st.key,
      amount: rows.reduce((s, i) => s + i.total, 0),
      count: rows.length,
    }
  })

  return delay({
    outstanding_total: outstanding,
    expected_this_month: expectedThisMonth,
    expected_this_month_by: lastExpected ?? null,
    overdue_total: overdue,
    median_days_to_payment: { private_insurer: mdays('private_insurer'), nhs: mdays('nhs') },
    fees_paid_ytd: Math.round(fees * 100) / 100,
    rejected_count: seeds.filter((i) => i.pipeline_status === 'rejected').length,
    stale_count: seeds.filter(isStale).length,
    pipeline_totals,
  })
}

export function mockCashflow(): Promise<Cashflow> {
  const months = ['2026-01', '2026-02', '2026-03', '2026-04', '2026-05', '2026-06', '2026-07', '2026-08', '2026-09']
  const out = months.map((m) => {
    const received = seeds
      .filter((i) => i.paid_date && ym(i.paid_date) === m)
      .reduce((s, i) => s + i.total - i.middleman_fee, 0)
    const expected = seeds
      .filter(
        (i) =>
          i.pipeline_status !== 'paid' &&
          i.pipeline_status !== 'rejected' &&
          i.expected_payment_date &&
          ym(i.expected_payment_date) === m,
      )
      .reduce((s, i) => s + i.amount_due, 0)
    return { month: m, received: Math.round(received), expected: Math.round(expected) }
  })
  return delay({ months: out })
}

export function mockCompare(): Promise<Compare> {
  const rollup = (p: PayerType): PayerRollup => {
    const rows = seeds.filter((i) => i.payer_type === p)
    const paid = rows.filter((i) => i.pipeline_status === 'paid')
    const open = rows.filter((i) => i.pipeline_status !== 'paid' && i.pipeline_status !== 'rejected')
    const aging = { b0_30: 0, b31_60: 0, b61_90: 0, b91_plus: 0 }
    for (const i of open) {
      const age = daysBetween(i.issued_date, TODAY)
      if (age <= 30) aging.b0_30 += i.amount_due
      else if (age <= 60) aging.b31_60 += i.amount_due
      else if (age <= 90) aging.b61_90 += i.amount_due
      else aging.b91_plus += i.amount_due
    }
    const months = ['2026-01', '2026-02', '2026-03', '2026-04', '2026-05', '2026-06', '2026-07']
    return {
      payer_type: p,
      invoice_count: rows.length,
      total_billed: rows.reduce((s, i) => s + i.total, 0),
      total_received: paid.reduce((s, i) => s + i.total, 0),
      outstanding: open.reduce((s, i) => s + i.amount_due, 0),
      median_days_to_payment: median(paid.map((i) => daysToPay(i)!).filter((n) => n != null)),
      rejection_rate: rows.length ? rows.filter((i) => i.pipeline_status === 'rejected').length / rows.length : 0,
      fees_paid: Math.round(paid.reduce((s, i) => s + i.middleman_fee, 0) * 100) / 100,
      aging,
      monthly_billed: months.map((m) => ({
        month: m,
        amount: rows.filter((i) => ym(i.issued_date) === m).reduce((s, i) => s + i.total, 0),
      })),
    }
  }
  return delay({ by_payer: [rollup('private_insurer'), rollup('nhs')] })
}
