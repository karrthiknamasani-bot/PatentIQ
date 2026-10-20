import React, { useState, useEffect } from 'react';
import DashboardLayout from '../layouts/DashboardLayout';
import {
  Search as SearchIcon,
  Filter,
  FileText,
  Trash2,
  Folder,
  Loader2,
  ExternalLink,
  Award,
  Calendar,
} from 'lucide-react';
import { motion } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import api from '../api/axios';
import toast from 'react-hot-toast';

const LibraryPage = () => {
  const [projects, setProjects] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const res = await api.get('/projects');
      const data = res.data;
      const projectList = Array.isArray(data) ? data : data.data || [];
      setProjects(projectList);
    } catch (err) {
      console.error('Failed to load projects:', err);
      toast.error('Failed to load projects from server');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this project?')) return;
    try {
      await api.delete(`/projects/${id}`);
      setProjects((prev) => prev.filter((p) => (p.id || p._id) !== id));
      toast.success('Project deleted successfully');
    } catch (err) {
      console.error('Failed to delete project:', err);
      toast.error('Failed to delete project');
    }
  };

  const filteredProjects = projects.filter((proj) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      (proj.title && proj.title.toLowerCase().includes(q)) ||
      (proj.original_file_name && proj.original_file_name.toLowerCase().includes(q)) ||
      (proj.readiness_category && proj.readiness_category.toLowerCase().includes(q))
    );
  });

  return (
    <DashboardLayout>
      <div className="w-full pt-4 pb-20 max-w-7xl mx-auto">
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
              <span className="text-cyan-500">Core Projects</span>
            </div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2 tracking-tight">
              Project Library
            </h1>
            <p className="text-gray-600 dark:text-gray-400 text-sm">
              Manage your assessed inventions, trace evidence matrices, and review formal reports.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3 }}
            className="flex items-center gap-3"
          >
            <div className="relative">
              <SearchIcon
                size={16}
                className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
              />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search projects by title..."
                className="pl-9 pr-4 py-2 bg-white dark:bg-[#111621] border border-gray-200 dark:border-gray-800 rounded-lg text-sm focus:outline-none focus:border-cyan-500 text-gray-900 dark:text-white shadow-sm w-64"
              />
            </div>
            <Link
              to="/upload"
              className="bg-cyan-600 hover:bg-cyan-700 text-white px-4 py-2 rounded-lg text-sm font-bold shadow-md transition-colors"
            >
              + New Analysis
            </Link>
          </motion.div>
        </div>

        {/* Content State */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20">
            <Loader2 className="animate-spin text-cyan-500 mb-3" size={40} />
            <p className="text-gray-500 text-sm">Loading project library...</p>
          </div>
        ) : filteredProjects.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.1 }}
            className="w-full bg-white dark:bg-[#111621] border border-gray-200 dark:border-gray-800 rounded-3xl p-16 flex flex-col items-center justify-center text-center min-h-[400px] shadow-sm"
          >
            <div className="w-20 h-20 bg-gray-50 dark:bg-[#161b26] rounded-full flex items-center justify-center mb-6">
              <FileText size={32} className="text-gray-400" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
              {projects.length === 0 ? 'No projects uploaded yet.' : 'No matching projects found.'}
            </h2>
            <p className="text-gray-500 dark:text-gray-400 mb-8 max-w-md text-sm">
              {projects.length === 0
                ? 'Your library is currently empty. Upload a technical invention disclosure to execute the 18-step patent readiness pipeline.'
                : 'Try adjusting your search terms.'}
            </p>
            {projects.length === 0 && (
              <Link
                to="/upload"
                className="bg-cyan-600 hover:bg-cyan-700 text-white px-8 py-3.5 rounded-lg text-sm font-bold shadow-lg transition-all"
              >
                Upload a project to begin
              </Link>
            )}
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
          >
            {filteredProjects.map((proj) => {
              const pId = proj.id || proj._id;
              const dateStr = proj.created_at || proj.createdAt;
              return (
                <div
                  key={pId}
                  onClick={() => navigate(`/analysis?id=${pId}`)}
                  className="bg-white dark:bg-[#141a27] border border-gray-200 dark:border-gray-800 rounded-xl p-5 shadow-sm hover:border-cyan-500/60 transition-all cursor-pointer group flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <div className="w-10 h-10 rounded-lg bg-gray-100 dark:bg-gray-800/60 flex items-center justify-center text-gray-500 group-hover:text-cyan-500 transition-colors">
                        <Folder size={20} />
                      </div>
                      <button
                        onClick={(e) => handleDelete(e, pId)}
                        className="text-gray-400 hover:text-red-500 p-2 rounded-lg hover:bg-red-50 dark:hover:bg-red-950/20 transition-all"
                        title="Delete project"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>

                    <h4 className="text-gray-900 dark:text-white font-bold text-base mb-1 line-clamp-1 group-hover:text-cyan-600 dark:group-hover:text-cyan-400 transition-colors">
                      {proj.title}
                    </h4>
                    <p className="text-gray-500 text-xs mb-3 flex items-center gap-1">
                      <Calendar size={12} />
                      {dateStr ? new Date(dateStr).toLocaleDateString() : 'Recent'} •{' '}
                      <span className="font-mono">{proj.original_file_name || 'document'}</span>
                    </p>

                    {/* Readiness Score Badge */}
                    <div className="flex items-center gap-2 mb-4">
                      {proj.readiness_score !== null && proj.readiness_score !== undefined ? (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold bg-cyan-50 dark:bg-cyan-950/40 text-cyan-700 dark:text-cyan-300 border border-cyan-200 dark:border-cyan-800/60">
                          <Award size={13} />
                          EB-PRE: {proj.readiness_score}/100
                        </span>
                      ) : (
                        <span className="text-xs text-gray-400 italic">Score pending</span>
                      )}
                      <span className="text-[11px] px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 font-medium">
                        {proj.status || 'uploaded'}
                      </span>
                    </div>
                  </div>

                  {/* Actions footer */}
                  <div className="flex items-center justify-between pt-4 border-t border-gray-100 dark:border-gray-800/60">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/reports?id=${pId}`);
                      }}
                      className="text-xs text-cyan-600 dark:text-cyan-400 font-bold hover:underline flex items-center gap-1"
                    >
                      <FileText size={13} /> View Report
                    </button>
                    <span className="text-xs text-gray-500 dark:text-gray-400 group-hover:text-cyan-500 group-hover:translate-x-1 transition-all flex items-center gap-1">
                      Analysis <ExternalLink size={12} />
                    </span>
                  </div>
                </div>
              );
            })}
          </motion.div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default LibraryPage;
