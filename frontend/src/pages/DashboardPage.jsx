import React, { useState, useEffect } from 'react';
import DashboardLayout from '../layouts/DashboardLayout';
import {
  Upload,
  Search,
  BarChart2,
  PieChart,
  Activity,
  Layers,
  Folder,
  Loader2,
  Award,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
} from 'lucide-react';
import { motion } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import api from '../api/axios';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';

const DashboardPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [latestDetail, setLatestDetail] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const res = await api.get('/projects');
      const projectList = Array.isArray(res.data) ? res.data : res.data?.data || [];
      setProjects(projectList);

      if (projectList.length > 0) {
        const latestId = projectList[0].id || projectList[0]._id;
        try {
          const detailRes = await api.get(`/projects/${latestId}`);
          setLatestDetail(detailRes.data);
        } catch (detailErr) {
          console.warn('Could not fetch detail for latest project:', detailErr);
        }
      }
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      toast.error('Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  const latestProject = projects[0];

  // Calculate live statistics
  const scoredProjects = projects.filter(
    (p) => p.readiness_score !== null && p.readiness_score !== undefined
  );
  const avgReadiness =
    scoredProjects.length > 0
      ? Math.round(
          scoredProjects.reduce((acc, p) => acc + p.readiness_score, 0) / scoredProjects.length
        )
      : null;

  const completedProjects = projects.filter((p) => p.status === 'completed');

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.08 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    show: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 300, damping: 24 } },
  };

  const metrics = [
    {
      label: 'Total Projects',
      value: projects.length.toString(),
      sub: 'Uploaded workspaces',
    },
    {
      label: 'Latest EB-PRE Score',
      value:
        latestProject?.readiness_score !== null && latestProject?.readiness_score !== undefined
          ? `${latestProject.readiness_score}/100`
          : '--',
      sub: latestProject ? latestProject.readiness_category || 'Assessed' : 'Awaiting upload',
    },
    {
      label: 'Latest Confidence',
      value:
        latestProject?.confidence_score !== null && latestProject?.confidence_score !== undefined
          ? `${Math.round(latestProject.confidence_score * 100)}%`
          : '--',
      sub: 'Statistical certainty',
    },
    {
      label: 'Average Readiness',
      value: avgReadiness !== null ? `${avgReadiness}/100` : '--',
      sub: `${scoredProjects.length} evaluated projects`,
    },
    {
      label: 'Features Identified',
      value: latestDetail?.features_count ? latestDetail.features_count.toString() : '--',
      sub: 'In latest invention',
    },
    {
      label: 'Processed Chunks',
      value: latestDetail?.chunks_count ? latestDetail.chunks_count.toString() : '--',
      sub: 'In latest document',
    },
    {
      label: 'System Status',
      value: 'Online',
      sub: 'FastAPI + Qdrant',
    },
  ];

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex flex-col justify-center items-center py-24 min-h-[400px]">
          <Loader2 className="animate-spin text-cyan-500 mb-4" size={40} />
          <p className="text-gray-500 text-sm font-medium">Loading workspace analytics...</p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <motion.div
        className="w-full pt-4 pb-20 max-w-7xl mx-auto"
        variants={containerVariants}
        initial="hidden"
        animate="show"
      >
        {/* Welcome Section */}
        <motion.div variants={itemVariants} className="text-center max-w-3xl mx-auto mb-10">
          <div className="inline-block px-3 py-1 bg-cyan-50 dark:bg-cyan-950/40 text-cyan-600 dark:text-cyan-400 border border-cyan-200 dark:border-cyan-800/60 rounded-full text-xs font-bold uppercase tracking-wider mb-3">
            Evidence-Based AI Patent Readiness Engine
          </div>
          <h1 className="text-4xl md:text-5xl font-black text-gray-900 dark:text-white mb-3 tracking-tight">
            Welcome back,{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-600 to-blue-600 dark:from-cyan-400 dark:to-blue-500">
              {user?.name?.split(' ')[0] || 'Researcher'}
            </span>
          </h1>
          <p className="text-gray-600 dark:text-gray-400 text-base max-w-2xl mx-auto">
            Evaluate invention readiness against the patent corpus using hybrid BM25 lexical + BGE dense retrieval, RRF fusion, and cross-encoder reranking.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mt-6">
            <Link
              to="/upload"
              className="w-full sm:w-auto flex justify-center items-center gap-2 bg-cyan-600 hover:bg-cyan-700 text-white px-8 py-3.5 rounded-xl text-sm font-bold shadow-lg shadow-cyan-600/20 hover:-translate-y-0.5 transition-all"
            >
              <Upload size={18} />
              Upload New Invention
            </Link>
            <Link
              to="/search"
              className="w-full sm:w-auto flex justify-center items-center gap-2 bg-white dark:bg-[#1a2133] hover:bg-gray-50 dark:hover:bg-[#232c45] border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white px-8 py-3.5 rounded-xl text-sm font-bold shadow-sm hover:-translate-y-0.5 transition-all"
            >
              <Search size={18} />
              Corpus Patent Search
            </Link>
          </div>
        </motion.div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3.5 mb-8">
          {metrics.map((m, idx) => (
            <motion.div
              key={idx}
              variants={itemVariants}
              className="bg-white dark:bg-[#141a27] border border-gray-200 dark:border-gray-800 rounded-xl p-4 shadow-sm flex flex-col justify-between"
            >
              <h3 className="text-gray-500 dark:text-gray-400 text-[10px] font-bold uppercase tracking-wider mb-2 leading-tight h-7">
                {m.label}
              </h3>
              <div>
                <div className="text-2xl font-black text-gray-900 dark:text-white">{m.value}</div>
                <p className="text-gray-400 dark:text-gray-500 text-[10px] mt-1 truncate">{m.sub}</p>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Charts / Intelligence Breakdown Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">
          {/* Dimension Score Distribution */}
          <motion.div
            variants={itemVariants}
            className="bg-white dark:bg-[#141a27] border border-gray-200 dark:border-gray-800 rounded-xl p-6 shadow-sm"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <BarChart2 size={18} className="text-cyan-500" />
                <h3 className="text-gray-900 dark:text-white font-bold text-sm">
                  EB-PRE Core Dimensions {latestProject ? `(${latestProject.title})` : ''}
                </h3>
              </div>
              {latestProject && (
                <span className="text-xs font-mono font-bold text-cyan-600 dark:text-cyan-400">
                  {latestProject.readiness_score ?? '--'}/100
                </span>
              )}
            </div>

            {latestDetail?.analysis?.dimension_scores ? (
              <div className="space-y-3 pt-2">
                {Object.entries(latestDetail.analysis.dimension_scores).map(([key, item], i) => {
                  const score = typeof item === 'object' && item.score !== undefined ? item.score : 0.7;
                  const pct = Math.round(score <= 1.0 ? score * 100 : score);
                  return (
                    <div key={i} className="text-xs">
                      <div className="flex justify-between font-medium mb-1">
                        <span className="capitalize text-gray-700 dark:text-gray-300">
                          {key.replace(/_/g, ' ')}
                        </span>
                        <span className="font-bold text-cyan-600 dark:text-cyan-400">{pct}%</span>
                      </div>
                      <div className="w-full bg-gray-100 dark:bg-gray-800 h-1.5 rounded-full overflow-hidden">
                        <div
                          className="bg-cyan-500 h-full rounded-full transition-all"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="h-44 flex flex-col items-center justify-center text-center text-xs text-gray-400">
                <BarChart2 size={32} className="text-gray-300 dark:text-gray-700 mb-2" />
                <p>Run pipeline analysis to visualize 6-dimension EB-PRE scores.</p>
              </div>
            )}
          </motion.div>

          {/* Uncertainty & Grounding Status */}
          <motion.div
            variants={itemVariants}
            className="bg-white dark:bg-[#141a27] border border-gray-200 dark:border-gray-800 rounded-xl p-6 shadow-sm"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Activity size={18} className="text-emerald-500" />
                <h3 className="text-gray-900 dark:text-white font-bold text-sm">
                  Grounding & Uncertainty Tracking
                </h3>
              </div>
              <span className="text-[11px] px-2 py-0.5 rounded bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-400 font-bold">
                Deterministic Engine
              </span>
            </div>

            <div className="space-y-3 text-xs pt-1">
              <div className="p-3 bg-gray-50 dark:bg-[#0f141f] rounded-lg border border-gray-100 dark:border-gray-800">
                <span className="font-bold text-gray-800 dark:text-gray-200 block mb-1">
                  Active Uncertainty Flags
                </span>
                {latestDetail?.analysis?.uncertainty_flags &&
                latestDetail.analysis.uncertainty_flags.length > 0 ? (
                  <ul className="list-disc pl-4 space-y-1 text-amber-600 dark:text-amber-400 font-mono text-[11px]">
                    {latestDetail.analysis.uncertainty_flags.map((flag, idx) => (
                      <li key={idx}>{flag}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-gray-500">No active uncertainty penalties flagged.</p>
                )}
              </div>

              <div className="p-3 bg-gray-50 dark:bg-[#0f141f] rounded-lg border border-gray-100 dark:border-gray-800">
                <span className="font-bold text-gray-800 dark:text-gray-200 block mb-1">
                  Explanation Model & Grounding
                </span>
                <p className="text-gray-600 dark:text-gray-400">
                  Model: <span className="font-mono text-cyan-600 dark:text-cyan-400">{latestDetail?.analysis?.model_used || 'Gemini 3.1 Pro Preview'}</span>
                </p>
                <p className="text-[11px] text-gray-400 mt-1">
                  Strict numerical integrity enforced: explanation layer reproduces deterministic EB-PRE scores without alteration.
                </p>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Recent Projects Table / Cards */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">Recent Inventions</h3>
            <Link
              to="/library"
              className="text-xs font-bold text-cyan-600 dark:text-cyan-400 hover:underline flex items-center gap-1"
            >
              View Full Library <ArrowRight size={13} />
            </Link>
          </div>

          {projects.length === 0 ? (
            <div className="text-center py-12 bg-white dark:bg-[#141a27] border border-gray-200 dark:border-gray-800 rounded-xl text-gray-500 text-sm">
              No projects uploaded yet.{' '}
              <Link to="/upload" className="text-cyan-600 dark:text-cyan-400 underline font-bold">
                Upload your first invention disclosure
              </Link>
              .
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {projects.slice(0, 6).map((proj) => {
                const pId = proj.id || proj._id;
                return (
                  <div
                    key={pId}
                    onClick={() => navigate(`/analysis?id=${pId}`)}
                    className="bg-white dark:bg-[#141a27] border border-gray-200 dark:border-gray-800 rounded-xl p-5 shadow-sm hover:border-cyan-500/50 transition-all cursor-pointer group flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <div className="w-8 h-8 rounded-lg bg-gray-100 dark:bg-gray-800 flex items-center justify-center text-gray-500 group-hover:text-cyan-500 transition-colors">
                          <Folder size={16} />
                        </div>
                        {proj.readiness_score !== null && proj.readiness_score !== undefined ? (
                          <span className="px-2 py-0.5 rounded text-xs font-bold bg-cyan-50 dark:bg-cyan-950/40 text-cyan-700 dark:text-cyan-300 font-mono">
                            {proj.readiness_score}/100
                          </span>
                        ) : (
                          <span className="text-[10px] text-gray-400 italic">Processing</span>
                        )}
                      </div>
                      <h4 className="text-gray-900 dark:text-white font-bold text-sm mb-1 line-clamp-1 group-hover:text-cyan-600 dark:group-hover:text-cyan-400 transition-colors">
                        {proj.title}
                      </h4>
                      <p className="text-gray-500 text-[11px] mb-3 truncate">
                        {proj.original_file_name || 'document'}
                      </p>
                    </div>

                    <div className="flex items-center justify-between pt-3 border-t border-gray-100 dark:border-gray-800/60 text-xs">
                      <span className="text-[10px] uppercase font-bold text-gray-400">
                        {proj.status || 'completed'}
                      </span>
                      <span className="text-cyan-600 dark:text-cyan-400 font-medium group-hover:translate-x-1 transition-transform">
                        View Analysis →
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </motion.div>
    </DashboardLayout>
  );
};

export default DashboardPage;
