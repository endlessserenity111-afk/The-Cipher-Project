import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, FolderSearch } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

import Dashboard from './pages/Dashboard';
import ProjectsExplorer from './pages/ProjectsExplorer';
import ProjectDetail from './pages/ProjectDetail';

// Utility for merging tailwind classes safely
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

function Navigation() {
  const location = useLocation();
  
  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Projects Explorer', path: '/projects', icon: FolderSearch },
  ];

  return (
    <nav className="bg-white border-b border-slate-200 sticky top-0 z-50 mb-8">
      <div className="max-w-[1440px] mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-slate-900 flex items-center justify-center text-white font-bold text-lg">
            M
          </div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            MPLADS Transparency & Risk Intelligence
          </h1>
        </div>
      
      <div className="flex items-center gap-1">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path || 
                          (item.path !== '/' && location.pathname.startsWith(item.path));
          return (
            <Link
              key={item.name}
              to={item.path}
              className={cn(
                "flex items-center gap-2 px-4 py-2 rounded text-sm font-semibold transition-colors",
                isActive 
                  ? "bg-slate-100 text-slate-900" 
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              )}
            >
              <item.icon className={cn("w-4 h-4", isActive ? "text-blue-600" : "text-slate-400")} />
              {item.name}
            </Link>
          );
        })}
        </div>
      </div>
    </nav>
  );
}

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-slate-50 font-sans text-slate-900">
        <Navigation />
        <main className="max-w-[1440px] mx-auto px-6 pb-12">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/projects" element={<ProjectsExplorer />} />
            <Route path="/projects/:id" element={<ProjectDetail />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
