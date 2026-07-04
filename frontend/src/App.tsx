import type { ReactNode } from 'react'
import { NavLink, Navigate, Route, Routes } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api, MOCK_MODE } from './api/client'
import { groupTriage } from './lib/triage'
import Overview from './pages/Overview'
import Invoices from './pages/Invoices'
import FixQueue from './pages/FixQueue'
import Compare from './pages/Compare'
import Settings from './pages/Settings'

function SideLink(props: { to: string; end?: boolean; label: string; badge?: ReactNode }) {
  return (
    <NavLink to={props.to} end={props.end} className={({ isActive }) => `side-link${isActive ? ' active' : ''}`}>
      {props.label}
      {props.badge}
    </NavLink>
  )
}

export default function App() {
  const invoices = useQuery({ queryKey: ['invoices', {}], queryFn: () => api.invoices() })
  const stuck = invoices.data ? groupTriage(invoices.data).reduce((s, g) => s + g.rows.length, 0) : null

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="side-brand">
          HealthCode <span className="tick">Connect</span>
          <span className="side-sub">Practice cashflow</span>
        </div>

        <div className="side-group-label">Work</div>
        <SideLink to="/" end label="Overview" />
        <SideLink to="/invoices" label="Invoices" />
        <SideLink
          to="/fix"
          label="Fix queue"
          badge={
            stuck != null ? (
              <span className={`side-badge ${stuck > 0 ? 'crit' : 'ok'}`}>{stuck > 0 ? stuck : '✓'}</span>
            ) : undefined
          }
        />

        <div className="side-group-label">Insight</div>
        <SideLink to="/compare" label="Compare" />

        <div className="side-group-label">System</div>
        <SideLink to="/settings" label="Settings" />

        <div className="side-foot">
          <span>
            <span className="side-dot" style={{ background: MOCK_MODE ? 'var(--overdue)' : 'var(--paid)' }} />
            Xero · {MOCK_MODE ? 'demo data' : 'connected'}
          </span>
          <span>
            <span className="side-dot" style={{ background: 'var(--overdue)' }} />
            Medserv · simulated
          </span>
          <span className="data-badge" style={{ alignSelf: 'flex-start' }}>4 Jul 2026</span>
        </div>
      </aside>

      <div className="content">
        <main className="page-wrap">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/invoices" element={<Invoices />} />
            <Route path="/fix" element={<FixQueue />} />
            <Route path="/compare" element={<Compare />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}
