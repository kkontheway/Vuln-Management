import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { SidebarProvider } from './context/SidebarContext';
import Dashboard from './pages/Dashboard';
import Vulnerabilities from './pages/Vulnerabilities';
import ThreatIntelligence from './pages/ThreatIntelligence';
import ServiceNow from './pages/ServiceNow';
import ServiceNowConfig from './pages/ServiceNowConfig';
import ChatConfig from './pages/ChatConfig';
import AIChat from './pages/AIChat';
import Tools from './pages/Tools';
import ReportView from './pages/ReportView';
import { Toaster } from './components/ui/toaster';
import DashboardShell from './components/layout/DashboardShell';
import './styles/globals.css';

function App() {
  return (
    <SidebarProvider>
      <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <DashboardShell>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/vulnerabilities" element={<Vulnerabilities />} />
            <Route path="/threat-intelligence" element={<ThreatIntelligence />} />
            <Route path="/servicenow" element={<ServiceNow />} />
            <Route path="/servicenow-config" element={<ServiceNowConfig />} />
            <Route path="/chat-config" element={<ChatConfig />} />
            <Route path="/ai-chat" element={<AIChat />} />
            <Route path="/tools" element={<Tools />} />
            <Route path="/report/:cveId" element={<ReportView />} />
          </Routes>
        </DashboardShell>
        <Toaster />
      </Router>
    </SidebarProvider>
  );
}

export default App;
