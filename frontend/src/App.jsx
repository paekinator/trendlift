import { Routes, Route, useLocation } from 'react-router-dom'
import Navbar from './components/Navbar.jsx'
import ParticlesBackdrop from './components/ParticlesBackdrop.jsx'
import Landing from './pages/Landing.jsx'
import Validator from './pages/Validator.jsx'
import Breakout from './pages/Breakout.jsx'
import TitlePatterns from './pages/TitlePatterns.jsx'

export default function App() {
  const { pathname } = useLocation()
  const isHome = pathname === '/'

  return (
    <div className="relative min-h-screen bg-[#070708] text-[#f1f5f9]">
      {!isHome ? <ParticlesBackdrop /> : null}
      <div className="relative z-10 flex min-h-screen flex-col">
        <Navbar />
        <div className="flex flex-1 flex-col">
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/validate" element={<Validator />} />
            <Route path="/breakout" element={<Breakout />} />
            <Route path="/title-patterns" element={<TitlePatterns />} />
          </Routes>
        </div>
      </div>
    </div>
  )
}
