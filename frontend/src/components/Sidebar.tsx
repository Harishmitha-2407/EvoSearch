import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useTheme } from '../contexts/ThemeContext'

const links = [
  { to: '/', label: 'Dashboard', icon: '◈', end: true },
  { to: '/documents', label: 'Documents', icon: '▤' },
  { to: '/search', label: 'Semantic Search', icon: '⌕' },
  { to: '/chat', label: 'AI Assistant', icon: '✦' },
  { to: '/timeline', label: 'Evolution Timeline', icon: '◷' },
  { to: '/comparison', label: 'Comparison', icon: '⇄' },
  { to: '/knowledge-map', label: 'Knowledge Map', icon: '⌘' },
  { to: '/code', label: 'Code Analysis', icon: '</>' },
  { to: '/settings', label: 'Settings', icon: '⚙' },
]

export default function Sidebar() {
  const { userEmail, logout } = useAuth()
  const navigate = useNavigate()
  const { theme, toggleTheme } = useTheme()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <aside className={`w-[276px] shrink-0 border-r h-screen sticky top-0 flex flex-col z-20 ${
      theme === 'dark' ? 'bg-slate-950/90 border-slate-800' : 'bg-white/80 border-slate-200/70'
    } backdrop-blur-2xl`}>
      <div className="px-5 pt-6 pb-5">
        <div className={`relative overflow-hidden rounded-2xl p-4 ${theme === 'dark' ? 'bg-gradient-to-br from-indigo-500/15 via-violet-500/10 to-slate-900' : 'bg-gradient-to-br from-indigo-50 via-violet-50 to-white'} border ${theme === 'dark' ? 'border-indigo-500/15' : 'border-indigo-100'}`}>
          <div className="absolute -right-8 -top-8 h-24 w-24 rounded-full bg-indigo-500/15 blur-2xl" />
          <div className="relative flex items-center gap-3">
            <div className="grid h-11 w-11 place-items-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-lg shadow-indigo-500/25 font-bold text-lg">E</div>
            <div>
              <div className={`text-xl font-extrabold tracking-tight ${theme === 'dark' ? 'text-white' : 'text-slate-950'}`} style={{ fontFamily: 'Space Grotesk, Inter, sans-serif' }}>EVOSearch</div>
              <div className={`text-[11px] font-semibold tracking-wide ${theme === 'dark' ? 'text-slate-400' : 'text-slate-500'}`}>UNDERSTAND · COMPARE · EVOLVE</div>
            </div>
          </div>
        </div>
      </div>

      <nav className={`flex-1 px-4 py-2 space-y-1 overflow-y-auto ${theme === 'dark' ? 'text-slate-300' : ''}`}>
        <div className={`px-3 pb-2 text-[10px] font-bold uppercase tracking-[0.18em] ${theme === 'dark' ? 'text-slate-600' : 'text-slate-400'}`}>Workspace</div>
        {links.map(l => (
          <NavLink
            key={l.to}
            to={l.to}
            end={l.end}
            className={({ isActive }) =>
              `group relative flex items-center gap-3 px-3.5 py-3 rounded-xl text-sm font-semibold transition-all duration-200 ${
                isActive
                  ? theme === 'dark'
                    ? 'bg-indigo-500/12 text-indigo-200 shadow-inner'
                    : 'bg-indigo-50 text-indigo-700 shadow-sm'
                  : theme === 'dark'
                  ? 'text-slate-400 hover:bg-slate-800/70 hover:text-slate-100'
                  : 'text-slate-600 hover:bg-slate-100/80 hover:text-slate-950'
              }`
            }
          >
            {({ isActive }) => <>
              <span className={`grid h-8 w-8 place-items-center rounded-lg text-sm transition ${isActive ? 'bg-indigo-500 text-white shadow-md shadow-indigo-500/25' : theme === 'dark' ? 'bg-slate-900 text-slate-500 group-hover:text-slate-200' : 'bg-slate-100 text-slate-500 group-hover:text-slate-800'}`}>{l.icon}</span>
              <span>{l.label}</span>
              {isActive && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-indigo-500" />}
            </>}
          </NavLink>
        ))}
      </nav>

      <div className={`px-4 py-4 space-y-3 border-t ${theme === 'dark' ? 'border-slate-800' : 'border-slate-200/70'}`}>
        <button
          onClick={toggleTheme}
          className={`w-full flex items-center justify-between gap-3 px-3.5 py-3 rounded-xl text-sm font-semibold transition-all ${theme === 'dark' ? 'bg-slate-900 text-slate-300 hover:bg-slate-800' : 'bg-slate-100/80 text-slate-700 hover:bg-slate-200/80'}`}
        >
          <span className="flex items-center gap-3"><span className="grid h-8 w-8 place-items-center rounded-lg bg-white/10">{theme === 'dark' ? '☀' : '☾'}</span>{theme === 'dark' ? 'Light mode' : 'Dark mode'}</span>
          <span className={`h-5 w-9 rounded-full p-0.5 ${theme === 'dark' ? 'bg-indigo-500' : 'bg-slate-300'}`}><span className={`block h-4 w-4 rounded-full bg-white shadow transition-transform ${theme === 'dark' ? 'translate-x-4' : ''}`} /></span>
        </button>

        {userEmail && (
          <div className={`rounded-xl p-3 ${theme === 'dark' ? 'bg-slate-900/80' : 'bg-slate-100/80'}`}>
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-gradient-to-br from-indigo-500 to-violet-500 text-white text-xs font-bold">{userEmail.charAt(0).toUpperCase()}</div>
              <div className="min-w-0">
                <div className={`text-[10px] uppercase tracking-wider font-bold ${theme === 'dark' ? 'text-slate-500' : 'text-slate-400'}`}>Signed in as</div>
                <div className={`text-xs font-semibold truncate ${theme === 'dark' ? 'text-slate-200' : 'text-slate-700'}`}>{userEmail}</div>
              </div>
            </div>
            <button onClick={handleLogout} className={`w-full mt-3 text-xs font-semibold py-2 rounded-lg transition ${theme === 'dark' ? 'text-red-400 hover:bg-red-500/10' : 'text-red-600 hover:bg-red-50'}`}>Sign out</button>
          </div>
        )}
      </div>
    </aside>
  )
}
