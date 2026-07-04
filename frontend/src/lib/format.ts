const gbpFmt = new Intl.NumberFormat('en-GB', {
  style: 'currency',
  currency: 'GBP',
  maximumFractionDigits: 0,
})
const gbpFmtP = new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP' })

export const gbp = (n: number): string => gbpFmt.format(n)
export const gbpExact = (n: number): string => gbpFmtP.format(n)

const dFmt = new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short' })
const dFmtY = new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })

export const shortDate = (iso: string | null): string => (iso ? dFmt.format(new Date(iso)) : '–')
export const longDate = (iso: string | null): string => (iso ? dFmtY.format(new Date(iso)) : '–')

export const monthLabel = (ym: string): string => {
  const [y, m] = ym.split('-').map(Number)
  return new Intl.DateTimeFormat('en-GB', { month: 'short' }).format(new Date(y, m - 1, 1))
}

export const pct = (x: number): string => `${Math.round(x * 100)}%`
