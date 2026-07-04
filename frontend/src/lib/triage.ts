// Deterministic triage: every stuck invoice matches exactly one rule, and every
// rule prescribes exactly one next action. No scoring, no heuristics; the rules
// are inspectable on the Settings page. Order below is priority order.
import type { Invoice } from '../api/types'
import { daysInStage } from './pipeline'
import { gbpExact } from './format'

/** Payment SLA per insurer, in days from reaching the insurer. Editable ruleset. */
export const SLA_DAYS: Record<string, number> = {
  Bupa: 35,
  'AXA Health': 40,
  Aviva: 45,
  Vitality: 40,
  WPA: 30,
  'NHS England': 30,
}
export const DEFAULT_SLA = 40
export const STALLED_AFTER_DAYS = 7
export const DRAFT_STALE_AFTER_DAYS = 7

export type BlockerKind = 'rejected' | 'query' | 'shortfall' | 'overdue' | 'stalled' | 'stale_draft'
export type Severity = 'critical' | 'serious' | 'warning' | 'info'

export interface Triage {
  kind: BlockerKind
  severity: Severity
  chip: string
  explanation: string
  actionLabel: string
  releases: number
}

export interface BlockerMeta {
  kind: BlockerKind
  severity: Severity
  title: string
  rule: string
}

export const BLOCKERS: BlockerMeta[] = [
  { kind: 'rejected', severity: 'critical', title: 'Failed Medserv validation', rule: 'Status is rejected. Fix the named fields and resubmit; nothing moves until then.' },
  { kind: 'query', severity: 'serious', title: 'Insurer asked a question', rule: 'Status is insurer_query. The claim is frozen until the practice replies.' },
  { kind: 'shortfall', severity: 'serious', title: 'Paid short', rule: 'Insurer paid, but less than billed. Bill the patient for the balance or write it off.' },
  { kind: 'overdue', severity: 'warning', title: 'Past insurer SLA', rule: 'With insurer longer than that insurer’s SLA (see table below). Send a chaser.' },
  { kind: 'stalled', severity: 'warning', title: 'Stalled at Medserv', rule: `At Medserv more than ${STALLED_AFTER_DAYS} days with no acknowledgement. Query Medserv with the invoice reference.` },
  { kind: 'stale_draft', severity: 'info', title: 'Never submitted', rule: `Draft older than ${DRAFT_STALE_AFTER_DAYS} days. Submit it; unsubmitted work is invisible money.` },
]

export const blockerMeta = (kind: BlockerKind): BlockerMeta => BLOCKERS.find((b) => b.kind === kind)!

export function triage(inv: Invoice): Triage | null {
  const days = daysInStage(inv)

  if (inv.pipeline_status === 'rejected') {
    const n = inv.validation_issues.length
    return {
      kind: 'rejected',
      severity: 'critical',
      chip: 'Fix fields',
      explanation: `Rejected ${days}d ago with ${n} field issue${n === 1 ? '' : 's'}. ${gbpExact(inv.total)} is going nowhere until they are corrected.`,
      actionLabel: 'Fix & resubmit',
      releases: inv.total,
    }
  }

  if (inv.pipeline_status === 'insurer_query') {
    return {
      kind: 'query',
      severity: 'serious',
      chip: 'Needs reply',
      explanation: inv.query_reason ?? 'The insurer returned this claim asking for more information.',
      actionLabel: 'Send reply',
      releases: inv.total,
    }
  }

  if (inv.pipeline_status === 'paid' && inv.amount_due > 0) {
    return {
      kind: 'shortfall',
      severity: 'serious',
      chip: 'Shortfall',
      explanation: `${inv.insurer_name} paid ${gbpExact(inv.total - inv.amount_due)} of ${gbpExact(inv.total)}; ${gbpExact(inv.amount_due)} is unaccounted for.`,
      actionLabel: 'Bill patient balance',
      releases: inv.amount_due,
    }
  }

  if (inv.pipeline_status === 'with_insurer') {
    const sla = SLA_DAYS[inv.insurer_name] ?? DEFAULT_SLA
    if (days > sla) {
      const chased = inv.last_chased_at ? ' Chased once already.' : ''
      return {
        kind: 'overdue',
        severity: 'warning',
        chip: `${days - sla}d over SLA`,
        explanation: `${days} days at ${inv.insurer_name}; their SLA is ${sla}. Silence past SLA is how invoices get lost.${chased}`,
        actionLabel: inv.last_chased_at ? 'Chase again' : 'Send chaser',
        releases: inv.amount_due,
      }
    }
  }

  if (inv.pipeline_status === 'at_medserv' && days > STALLED_AFTER_DAYS) {
    return {
      kind: 'stalled',
      severity: 'warning',
      chip: 'No acknowledgement',
      explanation: `Sent to Medserv ${days} days ago and never acknowledged. It may not be in their system at all.`,
      actionLabel: 'Query Medserv',
      releases: inv.total,
    }
  }

  if (inv.pipeline_status === 'draft' && days > DRAFT_STALE_AFTER_DAYS) {
    return {
      kind: 'stale_draft',
      severity: 'info',
      chip: 'Unsubmitted',
      explanation: `Drafted ${days} days ago and never sent. The payment clock has not even started.`,
      actionLabel: 'Submit to Medserv',
      releases: inv.total,
    }
  }

  return null
}

export interface TriageGroup {
  meta: BlockerMeta
  rows: { invoice: Invoice; t: Triage }[]
  total: number
}

export function groupTriage(invoices: Invoice[]): TriageGroup[] {
  const groups = new Map<BlockerKind, TriageGroup>()
  for (const invoice of invoices) {
    const t = triage(invoice)
    if (!t) continue
    let g = groups.get(t.kind)
    if (!g) {
      g = { meta: blockerMeta(t.kind), rows: [], total: 0 }
      groups.set(t.kind, g)
    }
    g.rows.push({ invoice, t })
    g.total += t.releases
  }
  for (const g of groups.values()) g.rows.sort((a, b) => b.t.releases - a.t.releases)
  return BLOCKERS.filter((b) => groups.has(b.kind)).map((b) => groups.get(b.kind)!)
}
