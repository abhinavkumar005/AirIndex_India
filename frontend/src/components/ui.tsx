/**
 * Shared dashboard UI primitives.
 */

import type { ReactNode } from 'react'

export function PageHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-6">
      <h2 className="text-2xl font-bold text-gov-700">{title}</h2>
      {subtitle && <p className="mt-1 text-sm text-gov-500">{subtitle}</p>}
    </div>
  )
}

export function Card({ title, children, className = '' }: { title?: string; children: ReactNode; className?: string }) {
  return (
    <section className={`rounded-lg border border-gov-200 bg-white p-4 shadow-sm ${className}`}>
      {title && <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gov-500">{title}</h3>}
      {children}
    </section>
  )
}

export function StatTile({
  label,
  value,
  hint,
  tone = 'default',
}: {
  label: string
  value: string
  hint?: string
  tone?: 'default' | 'up' | 'down' | 'flat'
}) {
  const toneClass =
    tone === 'up'
      ? 'text-emerald-700'
      : tone === 'down'
        ? 'text-red-700'
        : tone === 'flat'
          ? 'text-gov-600'
          : 'text-gov-800'

  return (
    <div className="rounded-lg border border-gov-200 bg-white p-4 shadow-sm">
      <div className="text-xs font-medium uppercase tracking-wide text-gov-500">{label}</div>
      <div className={`mt-1 text-2xl font-bold tabular-nums ${toneClass}`}>{value}</div>
      {hint && <div className="mt-1 text-xs text-gov-400">{hint}</div>}
    </div>
  )
}

export function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-red-300 bg-red-50 p-4 text-sm text-red-800">
      <strong className="font-semibold">Failed to load data:</strong> {message}
      <div className="mt-1 text-xs text-red-600">
        Is the backend running at http://localhost:8000? Start it with{' '}
        <code className="rounded bg-red-100 px-1">uvicorn app.main:app --reload</code> from the backend directory.
      </div>
    </div>
  )
}

export function Loading() {
  return (
    <div className="flex items-center justify-center rounded-lg border border-gov-200 bg-white p-12 text-gov-400 shadow-sm">
      <div className="flex items-center gap-3">
        <svg className="h-5 w-5 animate-spin" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
        </svg>
        <span className="text-sm font-medium">Loading…</span>
      </div>
    </div>
  )
}
