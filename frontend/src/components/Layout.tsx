import { ReactNode } from 'react'
import Sidebar from './Sidebar'
import { useTheme } from '../contexts/ThemeContext'

export default function Layout({ children }: { children: ReactNode }) {
  const { theme } = useTheme()

  return (
    <div className={`app-shell flex min-h-screen ${theme === 'dark' ? 'bg-slate-950' : 'bg-transparent'}`}>
      <Sidebar />
      <main className={`app-main flex-1 min-w-0 px-8 py-8 max-w-none ${theme === 'dark' ? 'text-slate-100' : 'text-slate-900'}`}>
        <div className="mx-auto w-full max-w-[1440px]">{children}</div>
      </main>
    </div>
  )
}

export function PageHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  const { theme } = useTheme()

  return (
    <div className={`page-header mb-8 pb-7 border-b ${theme === 'dark' ? 'border-slate-800' : 'border-slate-200/70'}`}>
      <div className="relative z-10">
        <div className="inline-flex items-center gap-2 mb-3 px-3 py-1.5 rounded-full bg-indigo-50 text-indigo-700 dark:bg-indigo-500/10 dark:text-indigo-300 text-xs font-bold uppercase tracking-[0.14em]">
          <span className="h-1.5 w-1.5 rounded-full bg-indigo-500 animate-pulse" /> EVOSearch workspace
        </div>
        <h1 className={`page-header-title text-4xl font-bold tracking-tight mb-2 ${theme === 'dark' ? 'text-white' : 'text-slate-950'}`} style={{ fontFamily: 'Space Grotesk, Inter, sans-serif' }}>{title}</h1>
        {subtitle && <p className={`text-base max-w-3xl leading-7 ${theme === 'dark' ? 'text-slate-400' : 'text-slate-600'}`}>{subtitle}</p>}
      </div>
    </div>
  )
}

export function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    ready: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300',
    processing: 'bg-amber-100 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300',
    pending: 'bg-slate-100 text-slate-600 dark:bg-slate-700/60 dark:text-slate-300',
    failed: 'bg-red-100 text-red-700 dark:bg-red-500/10 dark:text-red-300',
  }
  return <span className={`badge ${colors[status] || colors.pending}`}><span className="h-1.5 w-1.5 rounded-full bg-current opacity-80" />{status}</span>
}
