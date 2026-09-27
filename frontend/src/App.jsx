import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth'
import Layout from './components/Layout'
import Landing from './pages/Landing'
import SignIn from './pages/SignIn'
import Signup from './pages/Signup'
import Dashboard from './pages/Dashboard'
import Simulator from './pages/Simulator'
import Recommendations from './pages/Recommendations'
import Lender from './pages/Lender'

function Guard({ role, children }) {
  const { role: current } = useAuth()
  if (!current) return <Navigate to="/login" replace />
  if (current !== role) return <Navigate to={current === 'lender' ? '/lender' : '/dashboard'} replace />
  return children
}

export default function App() {
  const { role } = useAuth()
  return (
    <Routes>
      <Route path="/" element={role ? <Navigate to={role === 'lender' ? '/lender' : '/dashboard'} replace /> : <Landing />} />
      <Route path="/login" element={role ? <Navigate to={role === 'lender' ? '/lender' : '/dashboard'} replace /> : <SignIn />} />
      <Route path="/signup" element={<Signup />} />
      <Route element={<Guard role="user"><Layout /></Guard>}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/simulator" element={<Simulator />} />
        <Route path="/recommendations" element={<Recommendations />} />
      </Route>
      <Route path="/lender" element={<Guard role="lender"><Lender /></Guard>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
