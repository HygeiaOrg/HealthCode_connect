// Mirrors ../../shared-api-contract.json. Keep the two in sync.

export type PipelineStatus =
  | 'draft'
  | 'at_medserv'
  | 'with_insurer'
  | 'insurer_query'
  | 'paid'
  | 'rejected'

export type PayerType = 'private_insurer' | 'nhs'

export interface ValidationIssue {
  field: string
  error: string
  solution: string
}

export interface TimelineEvent {
  stage: PipelineStatus
  at: string
}

export interface Invoice {
  id: string
  invoice_number: string
  payer_type: PayerType
  insurer_name: string
  patient_ref: string
  description: string
  total: number
  amount_due: number
  middleman_fee: number
  currency: 'GBP'
  issued_date: string
  submitted_date: string | null
  expected_payment_date: string | null
  paid_date: string | null
  pipeline_status: PipelineStatus
  query_reason: string | null
  last_chased_at: string | null
  timeline: TimelineEvent[]
  validation_issues: ValidationIssue[]
  source: 'xero' | 'seed'
}

export interface PipelineTotal {
  status: PipelineStatus
  amount: number
  count: number
}

export interface Summary {
  outstanding_total: number
  expected_this_month: number
  expected_this_month_by: string | null
  overdue_total: number
  median_days_to_payment: { private_insurer: number | null; nhs: number | null }
  fees_paid_ytd: number
  rejected_count: number
  stale_count: number
  pipeline_totals: PipelineTotal[]
}

export interface CashflowMonth {
  month: string
  received: number
  expected: number
}

export interface Cashflow {
  months: CashflowMonth[]
}

export interface PayerRollup {
  payer_type: PayerType
  invoice_count: number
  total_billed: number
  total_received: number
  outstanding: number
  median_days_to_payment: number | null
  rejection_rate: number
  fees_paid: number
  aging: { b0_30: number; b31_60: number; b61_90: number; b91_plus: number }
  monthly_billed: { month: string; amount: number }[]
}

export interface Compare {
  by_payer: PayerRollup[]
}
