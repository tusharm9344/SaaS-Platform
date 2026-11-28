import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'

import Incidents from './pages/Incidents'
import Dashboard from './pages/Dashboard'
import IncidentDetail from './pages/IncidentDetail'
import Containers from './pages/Containers'
import Applications from './pages/Applications'
import Settings from './pages/Settings'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/applications" element={<Applications />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/incidents/:incidentId" element={<IncidentDetail />} />
        <Route path="/incidents" element={<Incidents />} />
        <Route path="/containers" element={<Containers />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App