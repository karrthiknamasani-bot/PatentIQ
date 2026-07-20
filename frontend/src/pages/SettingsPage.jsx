import React, { useState } from 'react';
import DashboardLayout from '../layouts/DashboardLayout';
import { Camera, Shield, Palette, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';

const SettingsPage = () => {
  const [activeTab, setActiveTab] = useState('profile');
  const { theme, setTheme } = useTheme();
  const { user } = useAuth();

  const handleSaveProfile = () => toast.success('Profile updated successfully');
  const handleUpdatePassword = () => toast.success('Password updated successfully');
  const handleDeleteAccount = () => toast.success('Account deletion requested. Check your email to confirm.');

  const tabs = [
    { id: 'profile', label: 'Profile' },
    { id: 'account', label: 'Account Settings' },
    { id: 'security', label: 'Change Password' },
    { id: 'theme', label: 'Theme Settings' }
  ];

  return (
    <DashboardLayout>
      <div className="w-full pt-2 pb-20">
        
        {/* Header */}
        <div className="mb-8">
          <motion.h1 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="text-3xl font-bold text-gray-900 dark:text-white mb-2"
          >
            Settings
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="text-gray-600 dark:text-gray-400 text-sm"
          >
            Manage your account, security preferences, and integration workflows.
          </motion.p>
        </div>

        {/* Tabs - Segmented Control */}
        <div className="flex bg-gray-100 dark:bg-[#111621] p-1.5 rounded-xl border border-gray-200 dark:border-gray-800 mb-10 overflow-x-auto max-w-fit shadow-sm dark:shadow-lg">
          {tabs.map(tab => (
            <button 
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-6 py-2.5 rounded-lg text-sm font-medium transition-all duration-300 whitespace-nowrap ${
                activeTab === tab.id 
                  ? 'bg-white dark:bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 shadow-sm dark:shadow-[0_0_15px_rgba(34,211,238,0.15)] font-bold' 
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-200 dark:hover:bg-gray-800/50'
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
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="w-full md:w-1/3"
          >
            {activeTab === 'profile' && (
              <div className="bg-white dark:bg-[#111621] border border-gray-200 dark:border-gray-800 rounded-xl p-8 flex flex-col items-center text-center shadow-sm dark:shadow-lg transition-all">
                <div className="relative mb-6 group cursor-pointer">
                  <div className="w-32 h-32 rounded-2xl overflow-hidden border-2 border-dashed border-gray-300 dark:border-gray-700 p-1 group-hover:border-cyan-600 dark:group-hover:border-cyan-400 transition-colors">
                    <div className="w-full h-full rounded-xl bg-gray-50 dark:bg-gray-800/50 flex flex-col items-center justify-center text-gray-400 dark:text-gray-500 overflow-hidden group-hover:bg-gray-100 dark:group-hover:bg-gray-800 transition-colors">
                      <Camera size={32} className="mb-2 opacity-50 group-hover:opacity-100 group-hover:text-cyan-600 dark:group-hover:text-cyan-400 transition-all" />
                      <span className="text-[10px] font-bold uppercase tracking-widest text-gray-500 dark:text-gray-400">Upload Photo</span>
                    </div>
                  </div>
                </div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-gray-400 mb-1">Set up your profile</h2>
                <p className="text-gray-500 text-sm mb-8">Add your details to get started</p>
              </div>
            )}

            {activeTab === 'security' && (
              <div className="bg-white dark:bg-[#111621] border border-gray-200 dark:border-gray-800 rounded-xl p-6 shadow-sm dark:shadow-lg">
                <div className="w-12 h-12 rounded-full bg-cyan-50 dark:bg-cyan-900/20 text-cyan-600 dark:text-cyan-400 flex items-center justify-center mb-4"><Shield size={24} /></div>
                <h3 className="text-gray-900 dark:text-white font-bold mb-2">Account Security</h3>
                <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">Protect your intellectual property assets with two-factor authentication and strict password requirements.</p>
              </div>
            )}

            {activeTab === 'account' && (
              <div className="bg-white dark:bg-[#111621] border border-gray-200 dark:border-gray-800 rounded-xl p-6 shadow-sm dark:shadow-lg">
                <div className="w-12 h-12 rounded-full bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 flex items-center justify-center mb-4"><AlertCircle size={24} /></div>
                <h3 className="text-gray-900 dark:text-white font-bold mb-2">Account Management</h3>
                <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">Manage your account data and permanent deletion options.</p>
              </div>
            )}

            {activeTab === 'theme' && (
              <div className="bg-white dark:bg-[#111621] border border-gray-200 dark:border-gray-800 rounded-xl p-6 shadow-sm dark:shadow-lg">
                <div className="w-12 h-12 rounded-full bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 flex items-center justify-center mb-4"><Palette size={24} /></div>
                <h3 className="text-gray-900 dark:text-white font-bold mb-2">Appearance</h3>
                <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">Customize your dashboard experience to suit your working environment.</p>
              </div>
            )}
          </motion.div>

          {/* Right Column: Dynamic Form Content */}
          <motion.div 
            key={activeTab}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4 }}
            className="w-full md:w-2/3"
          >
            <div className="bg-white dark:bg-[#111621] border border-gray-200 dark:border-gray-800 rounded-xl p-8 shadow-sm dark:shadow-lg min-h-[400px]">
              
              {activeTab === 'profile' && (
                <>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-8">Personal Information</h3>
                  <div className="space-y-6">
                    <div className="flex flex-col sm:flex-row gap-6">
                      <div className="flex-1">
                        <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-2 uppercase tracking-wide">First Name</label>
                        <input type="text" defaultValue={user?.name?.split(' ')[0] || ''} placeholder="Enter first name" className="w-full bg-gray-50 dark:bg-[#0a0d14] border border-gray-200 dark:border-gray-800 rounded-lg py-3.5 px-4 text-sm text-gray-900 dark:text-gray-200 placeholder-gray-400 dark:placeholder-gray-600 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/50 transition-all shadow-inner dark:shadow-[inset_0_2px_4px_rgba(0,0,0,0.2)]" />
                      </div>
                      <div className="flex-1">
                        <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-2 uppercase tracking-wide">Last Name</label>
                        <input type="text" defaultValue={user?.name?.split(' ')[1] || ''} placeholder="Enter last name" className="w-full bg-gray-50 dark:bg-[#0a0d14] border border-gray-200 dark:border-gray-800 rounded-lg py-3.5 px-4 text-sm text-gray-900 dark:text-gray-200 placeholder-gray-400 dark:placeholder-gray-600 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/50 transition-all shadow-inner dark:shadow-[inset_0_2px_4px_rgba(0,0,0,0.2)]" />
                      </div>
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-2 uppercase tracking-wide">Email Address</label>
                      <input type="email" defaultValue={user?.email || ''} readOnly className="w-full bg-gray-100 dark:bg-[#0a0d14] border border-gray-200 dark:border-gray-800 rounded-lg py-3.5 px-4 text-sm text-gray-500 dark:text-gray-400 cursor-not-allowed transition-all shadow-inner dark:shadow-[inset_0_2px_4px_rgba(0,0,0,0.2)]" />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-2 uppercase tracking-wide">Organization</label>
                      <input type="text" placeholder="Company or Institution name" className="w-full bg-gray-50 dark:bg-[#0a0d14] border border-gray-200 dark:border-gray-800 rounded-lg py-3.5 px-4 text-sm text-gray-900 dark:text-gray-200 placeholder-gray-400 dark:placeholder-gray-600 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/50 transition-all shadow-inner dark:shadow-[inset_0_2px_4px_rgba(0,0,0,0.2)]" />
                    </div>
                  </div>
                  <div className="flex justify-end gap-4 mt-10">
                    <button className="bg-transparent border border-gray-300 dark:border-gray-700 hover:bg-gray-50 dark:hover:border-gray-500 text-gray-700 dark:text-gray-300 px-6 py-2.5 rounded-lg text-[14px] font-medium transition-colors">Cancel</button>
                    <button onClick={handleSaveProfile} className="bg-cyan-600 hover:bg-cyan-700 dark:bg-cyan-500 dark:hover:bg-cyan-400 text-white dark:text-black px-6 py-2.5 rounded-lg text-[14px] font-bold transition-all shadow-md shadow-cyan-600/20 dark:shadow-[0_0_15px_rgba(34,211,238,0.2)] hover:-translate-y-0.5">Save Profile</button>
                  </div>
                </>
              )}

              {activeTab === 'security' && (
                <>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-8">Password & Authentication</h3>
                  <div className="space-y-6">
                    <div className="flex flex-col sm:flex-row gap-6">
                      <div className="flex-1">
                        <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-2 uppercase tracking-wide">New Password</label>
                        <input type="password" placeholder="Min 12 characters" className="w-full bg-gray-50 dark:bg-[#0a0d14] border border-gray-200 dark:border-gray-800 rounded-lg py-3.5 px-4 text-sm text-gray-900 dark:text-gray-200 placeholder-gray-400 dark:placeholder-gray-600 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/50 transition-all shadow-inner dark:shadow-[inset_0_2px_4px_rgba(0,0,0,0.2)]" />
                      </div>
                      <div className="flex-1">
                        <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-2 uppercase tracking-wide">Confirm New Password</label>
                        <input type="password" placeholder="Min 12 characters" className="w-full bg-gray-50 dark:bg-[#0a0d14] border border-gray-200 dark:border-gray-800 rounded-lg py-3.5 px-4 text-sm text-gray-900 dark:text-gray-200 placeholder-gray-400 dark:placeholder-gray-600 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/50 transition-all shadow-inner dark:shadow-[inset_0_2px_4px_rgba(0,0,0,0.2)]" />
                      </div>
                    </div>
                    <div className="pt-4 border-t border-gray-200 dark:border-gray-800">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="text-gray-900 dark:text-white font-medium mb-1">Two-Factor Authentication (2FA)</h4>
                          <p className="text-gray-500 text-xs">Add an extra layer of security to your account.</p>
                        </div>
                        <button className="bg-white dark:bg-[#1a2133] hover:bg-gray-50 dark:hover:bg-[#232c45] border border-gray-300 dark:border-gray-700 text-cyan-600 dark:text-cyan-400 px-4 py-2 rounded-md text-xs font-bold transition-colors">Enable 2FA</button>
                      </div>
                    </div>
                  </div>
                  <div className="flex justify-end gap-4 mt-10">
                    <button onClick={handleUpdatePassword} className="bg-cyan-600 hover:bg-cyan-700 dark:bg-cyan-500 dark:hover:bg-cyan-400 text-white dark:text-black px-6 py-2.5 rounded-lg text-[14px] font-bold transition-all shadow-md shadow-cyan-600/20 dark:shadow-[0_0_15px_rgba(34,211,238,0.2)] hover:-translate-y-0.5">Update Password</button>
                  </div>
                </>
              )}

              {activeTab === 'account' && (
                <>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-8">Danger Zone</h3>
                  <div className="space-y-6">
                    <div className="border border-red-200 dark:border-red-900/50 rounded-xl p-6 bg-red-50/50 dark:bg-red-900/10">
                      <h4 className="text-red-800 dark:text-red-400 font-bold mb-2">Delete Account</h4>
                      <p className="text-red-600/80 dark:text-red-400/80 text-sm mb-6 max-w-xl">
                        Once you delete your account, there is no going back. All of your uploaded patents, generated reports, and profile data will be permanently wiped.
                      </p>
                      <button onClick={handleDeleteAccount} className="bg-red-600 hover:bg-red-700 text-white px-6 py-2.5 rounded-lg text-[14px] font-bold transition-all shadow-md shadow-red-600/20 hover:-translate-y-0.5">
                        Delete Account
                      </button>
                    </div>
                  </div>
                </>
              )}



              {activeTab === 'theme' && (
                <>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-8">Interface Settings</h3>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div 
                      onClick={() => setTheme('light')}
                      className={`border-2 rounded-xl p-1 cursor-pointer transition-all ${theme === 'light' ? 'border-cyan-500 dark:border-cyan-400 opacity-100' : 'border-gray-200 dark:border-gray-800 opacity-50 hover:opacity-100'}`}
                    >
                      <div className="bg-white h-24 rounded-lg flex items-center justify-center border border-gray-200 shadow-sm">
                        <span className="text-gray-900 font-medium text-sm">Light (Default)</span>
                      </div>
                    </div>
                    <div 
                      onClick={() => setTheme('dark')}
                      className={`border-2 rounded-xl p-1 cursor-pointer transition-all ${theme === 'dark' ? 'border-cyan-500 dark:border-cyan-400 opacity-100' : 'border-gray-200 dark:border-gray-800 opacity-50 hover:opacity-100'}`}
                    >
                      <div className="bg-[#050b14] h-24 rounded-lg flex items-center justify-center shadow-sm">
                        <span className="text-white font-medium text-sm">Dark</span>
                      </div>
                    </div>
                    <div 
                      onClick={() => setTheme('system')}
                      className={`border-2 rounded-xl p-1 cursor-pointer transition-all ${theme === 'system' ? 'border-cyan-500 dark:border-cyan-400 opacity-100' : 'border-gray-200 dark:border-gray-800 opacity-50 hover:opacity-100'}`}
                    >
                      <div className="bg-gradient-to-r from-gray-100 to-[#050b14] h-24 rounded-lg flex items-center justify-center shadow-sm">
                        <span className="text-gray-900 font-medium text-sm mix-blend-difference bg-white/50 px-2 py-1 rounded">System</span>
                      </div>
                    </div>
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
