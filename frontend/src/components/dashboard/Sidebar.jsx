import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Search, 
  Library, 
  BarChart2, 
  FileText, 
  UploadCloud,
  Settings
} from 'lucide-react';

const Sidebar = () => {
  const navItems = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
    { icon: UploadCloud, label: 'Upload Project', path: '/upload' },
    { icon: Library, label: 'Project Library', path: '/library' },
    { icon: Search, label: 'Patent Search', path: '/search' },
    { icon: BarChart2, label: 'AI Analysis', path: '/analysis' },
    { icon: FileText, label: 'Reports', path: '/reports' },
  ];

  const location = useLocation();
  const isActive = (path) => location.pathname === path;

  return (
    <aside className="w-64 h-screen bg-white dark:bg-[#0a0d14] border-r border-gray-200 dark:border-gray-800 flex flex-col fixed left-0 top-0 z-20 transition-colors duration-300">
      {/* Logo Area */}
      <div className="h-16 flex items-center px-6 border-b border-gray-200 dark:border-gray-800">
        <Link to="/" className="flex items-center gap-1 hover:opacity-80 transition-opacity">
          <span className="text-2xl font-black tracking-tighter text-gray-900 dark:text-white">
            Patent<span className="text-blue-600 dark:text-blue-500">IQ</span>
          </span>
        </Link>
      </div>

      {/* Main Navigation */}
      <div className="flex-1 px-4 py-4 space-y-2 overflow-y-auto">
        {navItems.map((item) => {
          const active = isActive(item.path);
          const Icon = item.icon;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 mx-2 rounded-lg text-sm font-medium transition-all duration-300 relative group overflow-hidden
                ${active 
                  ? 'bg-cyan-50 dark:bg-[#111621] text-cyan-700 dark:text-cyan-400 shadow-[inset_0_1px_1px_rgba(255,255,255,0.1)] dark:shadow-none' 
                  : 'text-gray-600 dark:text-gray-400 hover:text-cyan-600 dark:hover:text-cyan-400 hover:bg-gray-50 dark:hover:bg-[#111621]/50'
                }`}
            >
              {/* Active highlight bar */}
              {active && (
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-cyan-500 shadow-[0_0_10px_rgba(34,211,238,0.8)]"></div>
              )}
              
              <Icon size={18} className={`relative z-10 transition-colors duration-300 ${active ? 'text-cyan-600 dark:text-cyan-400' : 'group-hover:text-cyan-600 dark:group-hover:text-cyan-400'}`} />
              <span className="relative z-10">{item.label}</span>
            </Link>
          );
        })}

        {/* Conditional Filters for Search Page */}
        {location.pathname === '/search' && (
          <div className="mt-8 px-2">
            <h4 className="text-[10px] font-bold text-gray-500 tracking-widest uppercase mb-4">Filters</h4>
            
            <div className="space-y-6">
              <div>
                <label className="text-xs text-gray-400 font-medium mb-2 block">Jurisdictions</label>
                <div className="flex flex-wrap gap-2">
                  <span className="bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-xs px-2 py-1 rounded cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700">USPTO</span>
                  <span className="bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-xs px-2 py-1 rounded cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700">EPO</span>
                  <span className="bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-xs px-2 py-1 rounded cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700">WIPO</span>
                  <span className="bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-xs px-2 py-1 rounded cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700">CNIPA</span>
                </div>
              </div>

              <div>
                <label className="text-xs text-gray-400 font-medium mb-2 block">Tech Cluster</label>
                <select className="w-full bg-gray-50 dark:bg-[#111621] border border-gray-200 dark:border-gray-800 text-gray-700 dark:text-gray-300 text-xs rounded-md px-3 py-2 focus:outline-none focus:border-cyan-500">
                  <option>Artificial Intelligence</option>
                  <option>Quantum Computing</option>
                  <option>Biotechnology</option>
                </select>
              </div>

              <div>
                <label className="text-xs text-gray-400 font-medium mb-2 block">Priority Year</label>
                <div className="flex gap-2">
                  <input type="text" placeholder="From" className="w-1/2 bg-gray-50 dark:bg-[#111621] border border-gray-200 dark:border-gray-800 text-gray-700 dark:text-gray-300 placeholder-gray-400 dark:placeholder-gray-500 text-xs rounded-md px-3 py-2 focus:outline-none focus:border-cyan-500" />
                  <input type="text" placeholder="To" className="w-1/2 bg-gray-50 dark:bg-[#111621] border border-gray-200 dark:border-gray-800 text-gray-700 dark:text-gray-300 placeholder-gray-400 dark:placeholder-gray-500 text-xs rounded-md px-3 py-2 focus:outline-none focus:border-cyan-500" />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Area */}
      {/* Bottom Area */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-800">
        <div className="space-y-1">
          <Link 
            to="/settings" 
            className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-300 relative group overflow-hidden
              ${isActive('/settings') 
                ? 'bg-cyan-50 dark:bg-[#111621] text-cyan-700 dark:text-cyan-400 shadow-[inset_0_1px_1px_rgba(255,255,255,0.1)] dark:shadow-none' 
                : 'text-gray-600 dark:text-gray-400 hover:text-cyan-600 dark:hover:text-cyan-400 hover:bg-gray-50 dark:hover:bg-[#111621]/50'
              }`}
          >
            {isActive('/settings') && (
              <div className="absolute left-0 top-0 bottom-0 w-1 bg-cyan-500 shadow-[0_0_10px_rgba(34,211,238,0.8)]"></div>
            )}
            <Settings size={18} className={`relative z-10 transition-colors duration-300 ${isActive('/settings') ? 'text-cyan-600 dark:text-cyan-400' : 'group-hover:text-cyan-600 dark:group-hover:text-cyan-400'}`} />
            <span className="relative z-10">Settings</span>
          </Link>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
