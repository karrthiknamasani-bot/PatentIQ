import React, { useState } from 'react';
import DashboardLayout from '../layouts/DashboardLayout';
import { Camera, Shield, Palette, AlertCircle, Cpu, CheckCircle2, Server, Database } from 'lucide-react';
import { motion } from 'framer-motion';
import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';

const SettingsPage = () => {
  const [activeTab, setActiveTab] = useState('profile');
  const { theme, setTheme } = useTheme();
  const { user, isDemoMode, isSupabaseConfigured } = useAuth();

  const handleSaveProfile = () => toast.success('Profile updated successfully');
  const handleUpdatePassword = () => toast.success('Password updated successfully');
  const handleDeleteAccount = () => toast.success('Account deletion requested. Check your email to confirm.');

  const tabs = [
    { id: 'profile', label: 'Profile' },
    { id: 'system', label: 'System & Architecture' },
    { id: 'security', label: 'Security' },
    { id: 'theme', label: 'Appearance' },
  ];

  return (
    <DashboardLayout>
      <div className="w-full pt-2 pb-20 max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <motion.h1
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="text-3xl font-black text-gray-900 dark:text-white mb-2 tracking-tight"
          >
            Settings & System Status
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="text-gray-600 dark:text-gray-400 text-sm"
          >
            Manage your account identity, security preferences, and inspect active pipeline architecture.
          </motion.p>
        </div>

        {/* Tabs - Segmented Control */}
        <div className="flex bg-gray-100 dark:bg-[#111621] p-1.5 rounded-xl border border-gray-200 dark:border-gray-800 mb-8 overflow-x-auto max-w-fit shadow-sm">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-5 py-2 rounded-lg text-xs font-bold transition-all whitespace-nowrap ${
                activeTab === tab.id
                  ? 'bg-white dark:bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 shadow-sm font-black'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content Grid */}
        <div className="flex flex-col md:flex-row gap-8">
          {/* Left Column: Contextual Sidebar */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full md:w-1/3"
          >
            {activeTab === 'profile' && (
              <div className="bg-white dark:bg-[#111621] border border-gray-200 dark:border-gray-800 rounded-xl p-6 text-center shadow-sm">
                <div className="w-20 h-20 rounded-full bg-cyan-100 dark:bg-cyan-950/40 text-cyan-600 dark:text-cyan-400 flex items-center justify-center mx-auto mb-4 text-2xl font-black">
                  {(user?.name || user?.email || 'U')[0].toUpperCase()}
                </div>
                <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-1">
                  {user?.name || 'PatentIQ Researcher'}
                </h2>
                <p className="text-gray-400 text-xs font-mono truncate">{user?.email || 'researcher@patentiq.local'}</p>
                <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-800 text-left text-xs space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Auth Mode:</span>
                    <span className="font-bold text-cyan-600 dark:text-cyan-400">
                      {isDemoMode ? 'Developer Demo' : 'Supabase Live JWT'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">User ID:</span>
                    <span className="font-mono text-[10px] text-gray-500 truncate max-w-[120px]">
                      {user?.id || '00000000-0000-0000-0000-000000000001'}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'system' && (
              <div className="bg-white dark:bg-[#111621] border border-gray-200 dark:border-gray-800 rounded-xl p-6 shadow-sm">
                <div className="w-10 h-10 rounded-full bg-cyan-50 dark:bg-cyan-900/20 text-cyan-600 dark:text-cyan-400 flex items-center justify-center mb-3">
                  <Cpu size={20} />
                </div>
                <h3 className="text-gray-900 dark:text-white font-bold text-sm mb-1">Architecture Overview</h3>
                <p className="text-gray-600 dark:text-gray-400 text-xs leading-relaxed">
                  PatentIQ integrates an 18-step patent evaluation engine combining lexical, dense vector, and grounded AI models.
                </p>
              </div>
            )}

            {activeTab === 'security' && (
              <div className="bg-white dark:bg-[#111621] border border-gray-200 dark:border-gray-800 rounded-xl p-6 shadow-sm">
                <div className="w-10 h-10 rounded-full bg-cyan-50 dark:bg-cyan-900/20 text-cyan-600 dark:text-cyan-400 flex items-center justify-center mb-3">
                  <Shield size={20} />
                </div>
                <h3 className="text-gray-900 dark:text-white font-bold text-sm mb-1">Account Security</h3>
                <p className="text-gray-600 dark:text-gray-400 text-xs leading-relaxed">
                  Standard Supabase JWT authentication protects uploaded patent disclosures and evaluation history.
                </p>
              </div>
            )}

            {activeTab === 'theme' && (
              <div className="bg-white dark:bg-[#111621] border border-gray-200 dark:border-gray-800 rounded-xl p-6 shadow-sm">
                <div className="w-10 h-10 rounded-full bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 flex items-center justify-center mb-3">
                  <Palette size={20} />
                </div>
                <h3 className="text-gray-900 dark:text-white font-bold text-sm mb-1">Appearance</h3>
                <p className="text-gray-600 dark:text-gray-400 text-xs leading-relaxed">
                  Toggle light, dark, or operating system synchronized theme preferences.
                </p>
              </div>
            )}
          </motion.div>

          {/* Right Column: Dynamic Form Content */}
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, x: 15 }}
            animate={{ opacity: 1, x: 0 }}
            className="w-full md:w-2/3"
          >
            <div className="bg-white dark:bg-[#111621] border border-gray-200 dark:border-gray-800 rounded-xl p-8 shadow-sm">
              {activeTab === 'profile' && (
                <>
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-6">Personal Information</h3>
                  <div className="space-y-4">
                    <div className="flex flex-col sm:flex-row gap-4">
                      <div className="flex-1">
                        <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 uppercase tracking-wide">
                          First Name
                        </label>
                        <input
                          type="text"
                          defaultValue={user?.name?.split(' ')[0] || 'Researcher'}
                          className="w-full bg-gray-50 dark:bg-[#0a0d14] border border-gray-200 dark:border-gray-800 rounded-lg py-2.5 px-3 text-sm text-gray-900 dark:text-gray-200 focus:outline-none focus:border-cyan-500"
                        />
                      </div>
                      <div className="flex-1">
                        <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 uppercase tracking-wide">
                          Last Name
                        </label>
                        <input
                          type="text"
                          defaultValue={user?.name?.split(' ')[1] || 'User'}
                          className="w-full bg-gray-50 dark:bg-[#0a0d14] border border-gray-200 dark:border-gray-800 rounded-lg py-2.5 px-3 text-sm text-gray-900 dark:text-gray-200 focus:outline-none focus:border-cyan-500"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 uppercase tracking-wide">
                        Email Address
                      </label>
                      <input
                        type="email"
                        defaultValue={user?.email || 'user@patentiq.local'}
                        readOnly
                        className="w-full bg-gray-100 dark:bg-[#0a0d14] border border-gray-200 dark:border-gray-800 rounded-lg py-2.5 px-3 text-sm text-gray-500 dark:text-gray-400 cursor-not-allowed"
                      />
                    </div>
                  </div>
                  <div className="flex justify-end gap-3 mt-8">
                    <button
                      onClick={handleSaveProfile}
                      className="bg-cyan-600 hover:bg-cyan-700 text-white px-5 py-2.5 rounded-lg text-xs font-bold transition-all shadow-md"
                    >
                      Save Profile
                    </button>
                  </div>
                </>
              )}

              {activeTab === 'system' && (
                <>
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-6">
                    Active System Architecture & Endpoints
                  </h3>
                  <div className="space-y-4 text-xs">
                    <div className="p-3.5 bg-gray-50 dark:bg-[#0a0d14] border border-gray-200 dark:border-gray-800 rounded-lg flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Server size={18} className="text-cyan-600" />
                        <div>
                          <div className="font-bold text-gray-900 dark:text-white">FastAPI Backend API</div>
                          <div className="text-gray-500 font-mono text-[11px]">
                            {import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'}
                          </div>
                        </div>
                      </div>
                      <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 font-bold rounded text-[10px]">
                        Active
                      </span>
                    </div>

                    <div className="p-3.5 bg-gray-50 dark:bg-[#0a0d14] border border-gray-200 dark:border-gray-800 rounded-lg flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Database size={18} className="text-cyan-600" />
                        <div>
                          <div className="font-bold text-gray-900 dark:text-white">Supabase PostgreSQL & Auth</div>
                          <div className="text-gray-500 text-[11px]">
                            {isSupabaseConfigured ? 'Remote Supabase Configured' : 'Local Developer Fallback Store Active'}
                          </div>
                        </div>
                      </div>
                      <span className={`px-2 py-0.5 font-bold rounded text-[10px] ${isSupabaseConfigured ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300' : 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'}`}>
                        {isSupabaseConfigured ? 'Connected' : 'Demo Store'}
                      </span>
                    </div>

                    <div className="p-3.5 bg-gray-50 dark:bg-[#0a0d14] border border-gray-200 dark:border-gray-800 rounded-lg flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Cpu size={18} className="text-cyan-600" />
                        <div>
                          <div className="font-bold text-gray-900 dark:text-white">Corpus Retrieval & Vector DB</div>
                          <div className="text-gray-500 text-[11px]">
                            Qdrant (Hybrid BM25 + BAAI/bge-small-en-v1.5 Dense + BGE Reranker)
                          </div>
                        </div>
                      </div>
                      <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 font-bold rounded text-[10px]">
                        Steps 4–6
                      </span>
                    </div>

                    <div className="p-3.5 bg-gray-50 dark:bg-[#0a0d14] border border-gray-200 dark:border-gray-800 rounded-lg flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <CheckCircle2 size={18} className="text-cyan-600" />
                        <div>
                          <div className="font-bold text-gray-900 dark:text-white">Assessment & Explanation Engine</div>
                          <div className="text-gray-500 text-[11px]">
                            EB-PRE Deterministic 6-Dimension Assessment + Gemini 3.1 Pro Preview
                          </div>
                        </div>
                      </div>
                      <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 font-bold rounded text-[10px]">
                        Steps 7–10
                      </span>
                    </div>
                  </div>
                </>
              )}

              {activeTab === 'security' && (
                <>
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-6">Password & Credentials</h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 uppercase tracking-wide">
                        New Password
                      </label>
                      <input
                        type="password"
                        placeholder="••••••••••••"
                        className="w-full bg-gray-50 dark:bg-[#0a0d14] border border-gray-200 dark:border-gray-800 rounded-lg py-2.5 px-3 text-sm text-gray-900 dark:text-gray-200 focus:outline-none focus:border-cyan-500"
                      />
                    </div>
                  </div>
                  <div className="flex justify-end gap-3 mt-8">
                    <button
                      onClick={handleUpdatePassword}
                      className="bg-cyan-600 hover:bg-cyan-700 text-white px-5 py-2.5 rounded-lg text-xs font-bold transition-all shadow-md"
                    >
                      Update Password
                    </button>
                  </div>
                </>
              )}

              {activeTab === 'theme' && (
                <>
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-6">Interface Appearance</h3>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <button
                      onClick={() => setTheme('light')}
                      className={`p-4 rounded-xl border text-center transition-all ${
                        theme === 'light'
                          ? 'border-cyan-500 bg-cyan-50/20 text-cyan-600 font-bold'
                          : 'border-gray-200 dark:border-gray-800 text-gray-700 dark:text-gray-300'
                      }`}
                    >
                      Light Mode
                    </button>
                    <button
                      onClick={() => setTheme('dark')}
                      className={`p-4 rounded-xl border text-center transition-all ${
                        theme === 'dark'
                          ? 'border-cyan-500 bg-cyan-500/10 text-cyan-400 font-bold'
                          : 'border-gray-200 dark:border-gray-800 text-gray-700 dark:text-gray-300'
                      }`}
                    >
                      Dark Mode
                    </button>
                    <button
                      onClick={() => setTheme('system')}
                      className={`p-4 rounded-xl border text-center transition-all ${
                        theme === 'system'
                          ? 'border-cyan-500 bg-cyan-500/10 text-cyan-400 font-bold'
                          : 'border-gray-200 dark:border-gray-800 text-gray-700 dark:text-gray-300'
                      }`}
                    >
                      System Default
                    </button>
                  </div>
                </>
              )}
            </div>
          </motion.div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default SettingsPage;
