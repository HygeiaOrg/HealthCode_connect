import { describe, expect, it } from 'vitest'
import type { Invoice } from '../api/types'
import { TODAY, daysBetween, daysInStage, isOverdue } from './pipeline'
import { BLOCKERS, DEFAULT_SLA, SLA_DAYS, groupTriage, triage } from './triage'

const iso = (d: Date) => d.toISOString().slice(0, 10)
const daysAgo = (n: number) => {
  const d = new Date(TODAY)
  d.setDate(d.getDate() - n)
  return iso(d)
}

function makeInvoice(over: Partial<Invoice> & { stageAgeDays?: number } = {}): Invoice {
  const { stageAgeDays = 0, ...rest } = over
  const status = rest.pipeline_status ?? 'with_insurer'
  const base: Invoice = {
    id: 'inv_test',
    invoice_number: 'INV-2026-9999',
    payer_type: 'private_insurer',
    insurer_name: 'Bupa',
    patient_ref: 'T.T-0001',
    description: 'Initial consultation',
    total: 250,
    amount_due: 250,
    middleman_fee: 7.5,
    currency: 'GBP',
    issued_date: daysAgo(stageAgeDays + 10),
    submitted_date: daysAgo(stageAgeDays + 5),
    expected_payment_date: null,
    paid_date: null,
    pipeline_status: status,
    query_reason: null,
    last_chased_at: null,
    timeline: [
      { stage: 'draft', at: daysAgo(stageAgeDays + 10) },
      { stage: status, at: daysAgo(stageAgeDays) },
    ],
    validation_issues: [],
    source: 'seed',
  }
  return { ...base, ...rest }
}

describe('pipeline helpers', () => {
  it('daysBetween and daysInStage agree with the demo clock', () => {
    expect(daysBetween('2026-06-24', TODAY)).toBe(10)
    expect(daysInStage(makeInvoice({ stageAgeDays: 12 }))).toBe(12)
  })

  it('isOverdue: past expected date and still live', () => {
    expect(isOverdue(makeInvoice({ expected_payment_date: daysAgo(1) }))).toBe(true)
    expect(isOverdue(makeInvoice({ expected_payment_date: daysAgo(-5) }))).toBe(false)
    expect(isOverdue(makeInvoice({ pipeline_status: 'paid', paid_date: daysAgo(1), amount_due: 0, expected_payment_date: daysAgo(9) }))).toBe(false)
  })
})

describe('triage rules, one at a time', () => {
  it('rejected: critical, releases the full amount', () => {
    const t = triage(makeInvoice({ pipeline_status: 'rejected', validation_issues: [{ field: 'F', error: 'E', solution: 'S' }] }))
    expect(t).toMatchObject({ kind: 'rejected', severity: 'critical', releases: 250 })
  })

  it('insurer query: explanation is the insurer question itself', () => {
    const t = triage(makeInvoice({ pipeline_status: 'insurer_query', query_reason: 'Pre-authorisation reference requested.' }))
    expect(t?.kind).toBe('query')
    expect(t?.explanation).toBe('Pre-authorisation reference requested.')
  })

  it('shortfall: paid with a balance releases only the balance', () => {
    const t = triage(makeInvoice({ pipeline_status: 'paid', paid_date: daysAgo(2), amount_due: 60 }))
    expect(t).toMatchObject({ kind: 'shortfall', releases: 60 })
    expect(triage(makeInvoice({ pipeline_status: 'paid', paid_date: daysAgo(2), amount_due: 0 }))).toBeNull()
  })

  it('overdue: strictly past the per-insurer SLA', () => {
    expect(SLA_DAYS['Bupa']).toBe(35)
    expect(triage(makeInvoice({ stageAgeDays: 35 }))).toBeNull()
    const t = triage(makeInvoice({ stageAgeDays: 36 }))
    expect(t).toMatchObject({ kind: 'overdue', chip: '1d over SLA' })
  })

  it('overdue: unknown insurers fall back to the default SLA', () => {
    expect(triage(makeInvoice({ insurer_name: 'Zurich Med', stageAgeDays: DEFAULT_SLA }))).toBeNull()
    expect(triage(makeInvoice({ insurer_name: 'Zurich Med', stageAgeDays: DEFAULT_SLA + 1 }))?.kind).toBe('overdue')
  })

  it('overdue: a chased invoice asks to chase again', () => {
    const t = triage(makeInvoice({ stageAgeDays: 40, last_chased_at: daysAgo(3) }))
    expect(t?.actionLabel).toBe('Chase again')
  })

  it('stalled at Medserv after more than 7 days', () => {
    expect(triage(makeInvoice({ pipeline_status: 'at_medserv', stageAgeDays: 7 }))).toBeNull()
    expect(triage(makeInvoice({ pipeline_status: 'at_medserv', stageAgeDays: 8 }))?.kind).toBe('stalled')
  })

  it('stale draft after more than 7 days', () => {
    expect(triage(makeInvoice({ pipeline_status: 'draft', stageAgeDays: 7 }))).toBeNull()
    expect(triage(makeInvoice({ pipeline_status: 'draft', stageAgeDays: 8 }))?.kind).toBe('stale_draft')
  })

  it('a healthy in-flight invoice matches no rule', () => {
    expect(triage(makeInvoice({ stageAgeDays: 10 }))).toBeNull()
  })

  it('priority: rejection wins over any age signal', () => {
    const t = triage(makeInvoice({
      pipeline_status: 'rejected',
      stageAgeDays: 90,
      expected_payment_date: daysAgo(30),
      validation_issues: [{ field: 'F', error: 'E', solution: 'S' }],
    }))
    expect(t?.kind).toBe('rejected')
  })
})

describe('groupTriage', () => {
  it('groups in rulebook order, rows by money at stake, healthy rows excluded', () => {
    const invoices = [
      makeInvoice({ id: 'a', stageAgeDays: 10 }),                                         // healthy
      makeInvoice({ id: 'b', pipeline_status: 'draft', stageAgeDays: 20, total: 100, amount_due: 100 }),
      makeInvoice({ id: 'c', pipeline_status: 'rejected', total: 300, amount_due: 300 }),
      makeInvoice({ id: 'd', pipeline_status: 'rejected', total: 900, amount_due: 900 }),
      makeInvoice({ id: 'e', stageAgeDays: 50, amount_due: 250 }),                         // overdue
    ]
    const groups = groupTriage(invoices)
    expect(groups.map((g) => g.meta.kind)).toEqual(['rejected', 'overdue', 'stale_draft'])
    const rulebookOrder = BLOCKERS.map((b) => b.kind)
    expect([...groups.map((g) => g.meta.kind)]).toEqual(
      rulebookOrder.filter((k) => groups.some((g) => g.meta.kind === k)),
    )
    const rejected = groups[0]
    expect(rejected.rows.map((r) => r.invoice.id)).toEqual(['d', 'c'])
    expect(rejected.total).toBe(1200)
  })
})
