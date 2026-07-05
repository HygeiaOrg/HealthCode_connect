// API client. With VITE_API_URL set it talks to the FastAPI backend;
// without it, mock mode serves identical shapes from the shared seed fixture.
import type { Cashflow, Compare, Invoice, PayerType, PipelineStatus, Summary } from './types'
import {
  mockCashflow,
  mockChase,
  mockCompare,
  mockInvoice,
  mockInvoices,
  mockReply,
  mockResolve,
  mockResubmit,
  mockSubmitDraft,
  mockSummary,
} from './mock'

const API = import.meta.env.VITE_API_URL as string | undefined
export const MOCK_MODE = !API

// The PDF check always talks to the Python engine; in mock mode it targets the
// local backend (override with VITE_VALIDATION_URL if port 8000 is taken).
const VALIDATION_BASE =
  API ?? (import.meta.env.VITE_VALIDATION_URL as string | undefined) ?? 'http://localhost:8000'

export interface UploadIssue {
  field: string
  error: string
  solution: string
  severity: 'error' | 'warning'
  rule: string
  path: string
}

export interface UploadResult {
  filename: string
  valid: boolean
  parsed: {
    patient?: { first_name?: string; surname?: string }
    policy?: { insurer_id?: string }
    totals?: { net?: number }
  } | null
  issues: UploadIssue[]
}

export async function uploadInvoicePdf(file: File): Promise<UploadResult> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${VALIDATION_BASE}/invoices/upload`, { method: 'POST', body: form })
  if (!res.ok) throw new Error(`upload failed: ${res.status}`)
  return res.json() as Promise<UploadResult>
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`)
  if (!res.ok) throw new Error(`${path} failed: ${res.status}`)
  return res.json() as Promise<T>
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body == null ? undefined : JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`${path} failed: ${res.status}`)
  return res.json() as Promise<T>
}

export interface InvoiceFilters {
  payer_type?: PayerType
  status?: PipelineStatus
  q?: string
}

export const api = {
  invoices(filters: InvoiceFilters = {}): Promise<Invoice[]> {
    if (MOCK_MODE) return mockInvoices(filters)
    const qs = new URLSearchParams(
      Object.entries(filters).filter(([, v]) => v != null && v !== '') as [string, string][],
    ).toString()
    return get(`/invoices${qs ? `?${qs}` : ''}`)
  },
  invoice(id: string): Promise<Invoice> {
    return MOCK_MODE ? mockInvoice(id) : get(`/invoices/${id}`)
  },
  summary(): Promise<Summary> {
    return MOCK_MODE ? mockSummary() : get('/analytics/summary')
  },
  cashflow(): Promise<Cashflow> {
    return MOCK_MODE ? mockCashflow() : get('/analytics/cashflow')
  },
  compare(): Promise<Compare> {
    return MOCK_MODE ? mockCompare() : get('/analytics/compare')
  },
  // fix-queue actions
  resubmit(id: string): Promise<Invoice> {
    return MOCK_MODE ? mockResubmit(id) : post(`/invoices/${id}/resubmit`)
  },
  reply(id: string, message: string): Promise<Invoice> {
    return MOCK_MODE ? mockReply(id) : post(`/invoices/${id}/reply`, { message })
  },
  submitDraft(id: string): Promise<Invoice> {
    return MOCK_MODE ? mockSubmitDraft(id) : post(`/invoices/${id}/submit`)
  },
  chase(id: string): Promise<Invoice> {
    return MOCK_MODE ? mockChase(id) : post(`/invoices/${id}/chase`)
  },
  resolve(id: string): Promise<Invoice> {
    return MOCK_MODE ? mockResolve(id) : post(`/invoices/${id}/resolve`)
  },
}
