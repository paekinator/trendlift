import { NavLink } from 'react-router-dom'

const LINKS = [
  { to: '/validate',      label: 'Idea Validator' },
  { to: '/breakout',      label: 'Breakout Finder' },
  { to: '/title-patterns', label: 'Title Patterns' },
]

export default function Navbar() {
  return (
    <nav className="sticky top-0 z-50 border-b border-white/[0.06] bg-[#070708]/75 backdrop-blur-xl backdrop-saturate-150">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-5 sm:px-8">
        {/* Logo */}
        <NavLink
          to="/"
          className="select-none text-[15px] font-semibold tracking-tight text-white/95 hover:text-white"
        >
          TrendLift
        </NavLink>

        {/* Nav links */}
        <div className="flex items-center gap-0.5">
          {LINKS.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                [
                  'rounded-full px-3 py-1.5 text-[13px] font-medium transition-colors',
                  isActive
                    ? 'bg-white/[0.1] text-white'
                    : 'text-white/45 hover:text-white/85',
                ].join(' ')
              }
            >
              {label}
            </NavLink>
          ))}
        </div>
      </div>
    </nav>
  )
}
