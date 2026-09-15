import { NavLink, Route, Routes } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import RouteExplorer from './pages/RouteExplorer'
import LeadTimeElasticity from './pages/LeadTimeElasticity'
import DataQuality from './pages/DataQuality'
import Validation from './pages/Validation'

const NAV_ITEMS = [
  { to: '/', label: 'APIx Overview', end: true },
  { to: '/routes', label: 'Route Explorer' },
  { to: '/lead-time', label: 'Lead-Time Elasticity' },
  { to: '/data-quality', label: 'Data Quality' },
  { to: '/validation', label: 'Backtest / Validation' },
]

export default function App() {
  return (
    <div className="min-h-screen">
      <header className="bg-gov-600 text-white shadow-md">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-1">
            <h1 className="text-xl font-bold tracking-tight">
              AirIndex India — APIx Dashboard
            </h1>
            <p className="text-sm text-gov-200">
              Airfare Price Index for Indian domestic routes · DEMO / PROTOTYPE — synthetic data
            </p>
          </div>
          <nav className="mt-4 flex flex-wrap gap-1">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-white text-gov-700 shadow-sm'
                      : 'text-gov-100 hover:bg-gov-500 hover:text-white'
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/routes" element={<RouteExplorer />} />
          <Route path="/lead-time" element={<LeadTimeElasticity />} />
          <Route path="/data-quality" element={<DataQuality />} />
          <Route path="/validation" element={<Validation />} />
        </Routes>
      </main>

      <footer className="border-t border-gov-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-4 text-xs text-gov-500 sm:px-6 lg:px-8">
          AirIndex India prototype · All fare data is synthetic (MOCK source) ·
          Not official MoSPI/PSD/DGCA methodology · Index levels are anchored
          to the first observation of each series (base period unresolved).
        </div>
      </footer>
    </div>
  )
}
