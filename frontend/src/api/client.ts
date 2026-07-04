// API client. With VITE_API_URL set it talks to the FastAPI backend;
// without it, mock mode serves identical shapes from the shared seed fixture.
import type { Cashflow, Compare, Invoice, PayerType, PipelineStatus, Summary } from './types'
import { mockCashflow, mockCompare, mockInvoice, mockInvoices, mockSummary } from './mock'

const API = import.meta.env.VITE_API_URL as string | undefined
export const MOCK_MODE = !API

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`)
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
}
