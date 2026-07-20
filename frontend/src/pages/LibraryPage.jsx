import React, { useState, useEffect } from 'react';
import DashboardLayout from '../layouts/DashboardLayout';
import { Search as SearchIcon, Filter, FileText, Trash2, Folder, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import api from '../api/axios';
import toast from 'react-hot-toast';

const LibraryPage = () => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      const { data } = await api.get('/projects');
      if (data.data) {
        setProjects(data.data);
      }
    } catch (err) {
      console.error(err);
      toast.error('Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this project?')) return;
    try {
      await api.delete(`/projects/${id}`);
      setProjects(projects.filter(p => p._id !== id));
      toast.success('Project deleted');
    } catch (err) {
      console.error(err);
      toast.error('Failed to delete project');
    }
  };
  return (
    <DashboardLayout>
      <div className="w-full pt-4 pb-20">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-10">
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div className="flex items-center gap-2 text-[11px] text-gray-500 font-bold uppercase tracking-[0.2em] mb-2">
              <span>Knowledge Base</span>
              <span className="text-gray-700">/</span>
              <span className="text-cyan-400">Core Projects</span>
            </div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2 tracking-tight">Project Library</h1>
            <p className="text-gray-600 dark:text-gray-400 text-sm">Manage your project reports and technical specifications.</p>
          </motion.div>
          
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3 }}
            className="flex items-center gap-3"
          >
            <div className="relative">
              <SearchIcon size={16} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input type="text" placeholder="Search patents..." className="pl-9 pr-4 py-2 bg-white dark:bg-[#111621] border border-gray-200 dark:border-gray-800 rounded-lg text-sm focus:outline-none focus:border-cyan-500 text-gray-900 dark:text-white shadow-sm" />
            </div>
            <button className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-[#111621] border border-gray-200 dark:border-gray-800 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-[#161b26] transition-colors shadow-sm">
              <Filter size={16} /> Filter
            </button>
          </motion.div>
        </div>

        {/* Content State */}
        {loading ? (
          <div className="flex justify-center py-20">
            <Loader2 className="animate-spin text-cyan-500" size={40} />
          </div>
        ) : projects.length === 0 ? (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.1 }}
            className="w-full bg-white dark:bg-[#111621] border border-gray-200 dark:border-gray-800 rounded-3xl p-16 flex flex-col items-center justify-center text-center transition-all duration-500 min-h-[400px] shadow-sm"
          >
            <div className="w-20 h-20 bg-gray-50 dark:bg-[#161b26] rounded-full flex items-center justify-center mb-6">
              <FileText size={32} className="text-gray-400" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">No projects uploaded yet.</h2>
            <p className="text-gray-500 dark:text-gray-400 mb-8 max-w-md">
              Your library is currently empty. Upload a project to begin your AI novelty assessment and build your knowledge base.
            </p>
            <Link to="/upload" className="bg-cyan-600 hover:bg-cyan-700 dark:bg-cyan-500 dark:hover:bg-cyan-400 text-white dark:text-black px-8 py-3.5 rounded-lg text-[14px] font-bold transition-all duration-300 shadow-lg shadow-cyan-600/20 dark:shadow-[0_0_20px_rgba(34,211,238,0.2)] dark:hover:shadow-[0_0_30px_rgba(34,211,238,0.4)] hover:-translate-y-0.5">
              Upload a project to begin
            </Link>
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
          >
            {projects.map(proj => (
              <div 
                key={proj._id} 
                onClick={() => navigate(`/analysis?id=${proj._id}`)} 
                className="bg-white dark:bg-[#141a27] border border-gray-200 dark:border-gray-800 rounded-xl p-5 shadow-sm hover:border-cyan-500/50 transition-all cursor-pointer group"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="w-10 h-10 rounded-lg bg-gray-100 dark:bg-gray-800/50 flex items-center justify-center text-gray-500 group-hover:text-cyan-500 transition-colors">
                    <Folder size={20} />
                  </div>
                  <button 
                    onClick={(e) => handleDelete(e, proj._id)}
                    className="text-gray-400 hover:text-red-500 p-2 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
                <div>
                  <h4 className="text-gray-900 dark:text-white font-bold text-sm mb-1 line-clamp-1">{proj.title}</h4>
                  <p className="text-gray-500 text-xs mb-4">{new Date(proj.createdAt).toLocaleDateString()}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-medium px-2 py-1 rounded ${proj.status === 'completed' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'}`}>
                    {proj.status}
                  </span>
                </div>
                <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-100 dark:border-gray-800/50">
                  <button 
                    onClick={(e) => { e.stopPropagation(); navigate(`/reports?id=${proj._id}`); }}
                    className="text-xs text-cyan-600 dark:text-cyan-400 font-medium hover:underline"
                  >
                    View Report
                  </button>
                  <span className="text-xs text-cyan-600 dark:text-cyan-400 font-medium group-hover:translate-x-1 transition-transform">
                    View Analysis →
                  </span>
                </div>
              </div>
            ))}
          </motion.div>
        )}

      </div>
    </DashboardLayout>
  );
};

export default LibraryPage;
