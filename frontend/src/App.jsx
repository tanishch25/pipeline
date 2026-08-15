import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Rocket, Users, FlaskConical, BarChart3 } from 'lucide-react';
import PipelineRunner from './pages/PipelineRunner';
import LeadCRM from './pages/LeadCRM';
import PromptLab from './pages/PromptLab';
import Analytics from './pages/Analytics';

function Navbar() {
  const location = useLocation();
  
  const navItems = [
    { path: '/', label: 'Pipeline', icon: Rocket },
    { path: '/crm', label: 'Lead CRM', icon: Users },
    { path: '/lab', label: 'Prompt Lab', icon: FlaskConical },
    { path: '/analytics', label: 'Analytics', icon: BarChart3 },
  ];

  return (
    <nav className="bg-slate-800 border-b border-slate-700 p-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Rocket className="text-purple-500 w-6 h-6" />
          <span className="text-xl font-bold text-white tracking-wide">OutboundAI</span>
        </div>
        <div className="flex space-x-4">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  active ? 'bg-slate-700 text-purple-400' : 'text-slate-300 hover:bg-slate-700 hover:text-white'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}

function MainContent() {
  const location = useLocation();
  
  return (
    <div className="min-h-screen bg-slate-900 text-slate-50 flex flex-col">
      <Navbar />
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 overflow-y-auto">
        <div style={{ display: location.pathname === '/' ? 'block' : 'none' }}>
          <PipelineRunner />
        </div>
        {location.pathname === '/crm' && <LeadCRM />}
        {location.pathname === '/lab' && <PromptLab />}
        {location.pathname === '/analytics' && <Analytics />}
      </main>
    </div>
  );
}

function App() {
  return (
    <Router>
      <MainContent />
    </Router>
  );
}

export default App;
