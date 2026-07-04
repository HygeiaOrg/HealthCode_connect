import type { Invoice, PipelineStatus } from '../api/types'

// Demo clock: seed data is generated against this date so the story stays stable.
export const TODAY = new Date('2026-07-04')

export interface StageMeta {
  key: PipelineStatus
  label: string
  cssVar: string
  lightText: boolean
  icon: string
}

// In-flight stages ride the ordinal blue ramp: money darkens as it moves toward
// the doctor (design.md). Query, paid, and rejected are exception/terminal colors.
export const STAGES: StageMeta[] = [
  { key: 'draft', label: 'Draft', cssVar: 'var(--stage-draft)', lightText: false, icon: '✎' },
  { key: 'at_medserv', label: 'At Medserv', cssVar: 'var(--stage-medserv)', lightText: true, icon: '●' },
  { key: 'with_insurer', label: 'With insurer', cssVar: 'var(--stage-insurer)', lightText: true, icon: '●' },
  { key: 'insurer_query', label: 'Insurer query', cssVar: 'var(--stuck)', lightText: true, icon: '?' },
  { key: 'paid', label: 'Paid', cssVar: 'var(--paid)', lightText: true, icon: '✓' },
  { key: 'rejected', label: 'Rejected', cssVar: 'var(--rejected)', lightText: true, icon: '✕' },
]

export const stageMeta = (key: PipelineStatus): StageMeta =>
  STAGES.find((s) => s.key === key) ?? STAGES[0]

export const daysBetween = (a: string | Date, b: string | Date): number => {
  const da = typeof a === 'string' ? new Date(a) : a
  const db = typeof b === 'string' ? new Date(b) : b
  return Math.round((db.getTime() - da.getTime()) / 86_400_000)
}

/** Days the invoice has sat in its current stage. */
export const daysInStage = (inv: Invoice): number => {
  const last = inv.timeline[inv.timeline.length - 1]
  return last ? daysBetween(last.at, TODAY) : 0
}

export const isLive = (inv: Invoice): boolean =>
  inv.pipeline_status !== 'paid' && inv.pipeline_status !== 'rejected'

export const isOverdue = (inv: Invoice): boolean =>
  isLive(inv) && !!inv.expected_payment_date && new Date(inv.expected_payment_date) < TODAY
