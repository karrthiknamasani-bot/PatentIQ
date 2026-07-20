import React, { useState, useRef, useEffect } from 'react';
import { Search, Bell, Grid, User, Settings as SettingsIcon, LogOut, FileText, CheckCircle2, Sun, Moon } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useTheme } from '../../contexts/ThemeContext';
import { useAuth } from '../../contexts/AuthContext';

const Topbar = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  
  const handleLogout = () => {
    logout();
    navigate('/login');
  };
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const [isAppsOpen, setIsAppsOpen] = useState(false);
  
  const { theme, toggleTheme } = useTheme();

  const profileRef = useRef(null);
  const notificationsRef = useRef(null);
  const appsRef = useRef(null);

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (profileRef.current && !profileRef.current.contains(event.target)) {
        setIsProfileOpen(false);
      }
      if (notificationsRef.current && !notificationsRef.current.contains(event.target)) {
        setIsNotificationsOpen(false);
      }
      if (appsRef.current && !appsRef.current.contains(event.target)) {
        setIsAppsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="h-16 bg-white dark:bg-[#0c1017] border-b border-gray-200 dark:border-gray-800 flex items-center justify-between px-6 sticky top-0 z-50 w-full ml-64 transition-colors duration-300" style={{ width: 'calc(100% - 16rem)' }}>
      {/* Search Bar */}
      <div className="flex-1 max-w-xl">
        <div className="relative group">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search size={16} className="text-gray-500 group-focus-within:text-cyan-400 transition-colors" />
          </div>
          <input
            type="text"
            placeholder="Search within analysis..."
            className="block w-full bg-gray-100 dark:bg-[#111621] border border-transparent dark:border-gray-800/80 rounded-lg py-2 pl-10 pr-12 text-sm text-gray-900 dark:text-gray-200 placeholder-gray-500 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 focus:bg-white dark:focus:bg-[#141a27] transition-all duration-300 shadow-sm dark:shadow-[inset_0_2px_4px_rgba(0,0,0,0.2)]"
          />
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
            <div className="border border-gray-200 dark:border-gray-700 bg-white dark:bg-[#1a2133] rounded px-1.5 py-0.5 text-[10px] text-gray-500 font-mono font-medium">⌘K</div>
          </div>
        </div>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-4 text-gray-500 dark:text-gray-400">
          
          {/* Theme Toggle */}
          <button 
            onClick={toggleTheme}
            className="transition-colors hover:text-gray-900 dark:hover:text-white"
          >
            {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
          </button>

          {/* Notifications Dropdown */}
          <div className="relative" ref={notificationsRef}>
            <button 
              onClick={() => {
                setIsNotificationsOpen(!isNotificationsOpen);
                setIsProfileOpen(false);
                setIsAppsOpen(false);
              }}
              className={`transition-colors relative ${isNotificationsOpen ? 'text-cyan-400' : 'hover:text-white'}`}
            >
              <Bell size={20} />
            </button>

            {isNotificationsOpen && (
              <div className="absolute right-0 mt-4 w-80 bg-white/95 dark:bg-[#111621]/95 backdrop-blur-xl border border-gray-200 dark:border-gray-800 rounded-xl shadow-[0_10px_40px_rgba(0,0,0,0.1)] dark:shadow-[0_10px_40px_rgba(0,0,0,0.5)] py-2 z-50 overflow-hidden transform origin-top-right transition-all">
                <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-800 flex justify-between items-center bg-gray-50/50 dark:bg-[#0c1017]/50">
                  <span className="font-bold text-gray-900 dark:text-white text-sm">Notifications</span>
                  <button className="text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">Settings</button>
                </div>
                
                <div className="flex flex-col items-center justify-center py-10 px-4 text-center">
                  <CheckCircle2 size={32} className="text-emerald-500/50 mb-3" />
                  <p className="text-sm font-medium text-gray-900 dark:text-white mb-1">You're all caught up</p>
                  <p className="text-xs text-gray-500">We'll notify you when an analysis completes or team members share files.</p>
                </div>
                
                <div className="px-4 py-2 text-center border-t border-gray-200 dark:border-gray-800">
                  <button className="text-xs font-bold text-gray-500 hover:text-gray-900 dark:hover:text-white">View All Notifications</button>
                </div>
              </div>
            )}
          </div>

          {/* Apps Dropdown */}
          <div className="relative" ref={appsRef}>
            <button 
              onClick={() => {
                setIsAppsOpen(!isAppsOpen);
                setIsProfileOpen(false);
                setIsNotificationsOpen(false);
              }}
              className={`transition-colors ${isAppsOpen ? 'text-cyan-400' : 'hover:text-white'}`}
            >
              <Grid size={20} />
            </button>

            {isAppsOpen && (
              <div className="absolute right-0 mt-4 w-64 bg-white/95 dark:bg-[#111621]/95 backdrop-blur-xl border border-gray-200 dark:border-gray-800 rounded-xl shadow-[0_10px_40px_rgba(0,0,0,0.1)] dark:shadow-[0_10px_40px_rgba(0,0,0,0.5)] p-4 z-50 grid grid-cols-3 gap-4 transform origin-top-right transition-all">
                <Link to="/analysis" className="flex flex-col items-center gap-2 text-gray-500 dark:text-gray-400 hover:text-cyan-600 dark:hover:text-cyan-400 group">
                  <div className="w-10 h-10 rounded-lg bg-gray-100 dark:bg-gray-800/50 group-hover:bg-cyan-50 dark:group-hover:bg-cyan-900/30 flex items-center justify-center border border-gray-200 dark:border-gray-700 group-hover:border-cyan-200 dark:group-hover:border-cyan-500/50 transition-all">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 20V10"/><path d="M18 20V4"/><path d="M6 20v-4"/></svg>
                  </div>
                  <span className="text-[10px] font-medium text-center">Analysis</span>
                </Link>
                <Link to="/reports" className="flex flex-col items-center gap-2 text-gray-500 dark:text-gray-400 hover:text-cyan-600 dark:hover:text-cyan-400 group">
                  <div className="w-10 h-10 rounded-lg bg-gray-100 dark:bg-gray-800/50 group-hover:bg-cyan-50 dark:group-hover:bg-cyan-900/30 flex items-center justify-center border border-gray-200 dark:border-gray-700 group-hover:border-cyan-200 dark:group-hover:border-cyan-500/50 transition-all">
                    <FileText size={18} />
                  </div>
                  <span className="text-[10px] font-medium text-center">Reports</span>
                </Link>
                <Link to="/library" className="flex flex-col items-center gap-2 text-gray-500 dark:text-gray-400 hover:text-cyan-600 dark:hover:text-cyan-400 group">
                  <div className="w-10 h-10 rounded-lg bg-gray-100 dark:bg-gray-800/50 group-hover:bg-cyan-50 dark:group-hover:bg-cyan-900/30 flex items-center justify-center border border-gray-200 dark:border-gray-700 group-hover:border-cyan-200 dark:group-hover:border-cyan-500/50 transition-all">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>
                  </div>
                  <span className="text-[10px] font-medium text-center">Library</span>
                </Link>
              </div>
            )}
          </div>
        </div>
        
        {/* User Profile Dropdown */}
        <div className="relative" ref={profileRef}>
          <div 
            onClick={() => {
              setIsProfileOpen(!isProfileOpen);
              setIsNotificationsOpen(false);
              setIsAppsOpen(false);
            }}
            className="flex items-center gap-3 border-l border-gray-200 dark:border-gray-800 pl-6 cursor-pointer hover:opacity-80 transition-opacity"
          >
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-500 to-purple-500 p-0.5">
              <div className="w-full h-full rounded-full bg-white dark:bg-gray-900 border border-white dark:border-gray-800 overflow-hidden">
                 {user?.avatar ? (
                   <img src={user.avatar} alt={user.name || 'User avatar'} className="w-full h-full object-cover" referrerPolicy="no-referrer" />
                 ) : (
                   <div className="w-full h-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center text-xs font-bold text-gray-700 dark:text-white">
                     {user?.name ? user.name.substring(0, 2).toUpperCase() : 'U'}
                   </div>
                 )}
              </div>
            </div>
            <span className="text-sm font-medium text-gray-900 dark:text-white select-none">{user?.name || 'User'}</span>
          </div>

          {isProfileOpen && (
            <div className="absolute right-0 mt-4 w-56 bg-white/95 dark:bg-[#111621]/95 backdrop-blur-xl border border-gray-200 dark:border-gray-800 rounded-xl shadow-[0_10px_40px_rgba(0,0,0,0.1)] dark:shadow-[0_10px_40px_rgba(0,0,0,0.5)] py-2 z-50 overflow-hidden transform origin-top-right transition-all">
              <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-800/50 mb-2 bg-gray-50/50 dark:bg-[#0c1017]/50">
                <p className="text-sm text-gray-900 dark:text-white font-bold">{user?.name || 'User'}</p>
                <p className="text-xs text-gray-500 truncate">{user?.email || ''}</p>
              </div>
              <Link to="/settings" className="flex items-center gap-3 px-4 py-2 text-sm text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                <User size={14} /> My Profile
              </Link>
              <Link to="/settings" className="flex items-center gap-3 px-4 py-2 text-sm text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                <SettingsIcon size={14} /> Settings
              </Link>
              <div className="h-px bg-gray-200 dark:bg-gray-800/50 my-2"></div>
              <button onClick={handleLogout} className="w-full flex items-center gap-3 px-4 py-2 text-sm text-red-500 dark:text-red-400 hover:text-red-600 dark:hover:text-red-300 hover:bg-red-50 dark:hover:bg-gray-800/50 transition-colors">
                <LogOut size={14} /> Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Topbar;
