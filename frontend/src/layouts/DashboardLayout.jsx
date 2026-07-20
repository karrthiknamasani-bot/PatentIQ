import React from 'react';
import Sidebar from '../components/dashboard/Sidebar';
import Topbar from '../components/dashboard/Topbar';
import { motion } from 'framer-motion';

const DashboardLayout = ({ children }) => {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#050b14] flex font-sans overflow-x-hidden transition-colors duration-300">
      <Sidebar />
      <div className="flex-1 flex flex-col min-h-screen">
        <Topbar />
        <main className="flex-1 ml-64 p-6 bg-slate-50 dark:bg-[#050b14] relative transition-colors duration-300">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3 }}
            className="w-full h-full"
          >
            {children}
          </motion.div>
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
