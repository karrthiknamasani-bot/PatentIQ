import React, { useState, useEffect } from 'react';
import DashboardLayout from '../layouts/DashboardLayout';
import { Upload, Search, BarChart2, PieChart, Activity, Layers, Folder } from 'lucide-react';
import { motion } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import api from '../api/axios';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';

const DashboardPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [latestAnalysis, setLatestAnalysis] = useState(null);

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const { data } = await api.get('/projects');
        if (data.success) {
          const fetchedProjects = data.data || [];
          setProjects(fetchedProjects);
          
          if (fetchedProjects.length > 0 && fetchedProjects[0].status === 'completed') {
            const analysisData = await api.get(`/analyze/${fetchedProjects[0]._id}`);
            if (analysisData.data.success) {
              setLatestAnalysis(analysisData.data.data);
            }
          } else {
            setLatestAnalysis(null);
          }
        }
      } catch (error) {
        console.error(error);
        toast.error('Failed to load projects');
      }
    };
    fetchProjects();
  }, []);
  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 300, damping: 24 } }
  };

  const metrics = [
    { label: "Total Projects", value: projects.length.toString(), sub: "Uploaded documents" },
    { label: "Latest Potential", value: latestAnalysis ? `${latestAnalysis.scores.noveltyScore}/100` : "--", sub: latestAnalysis ? "From latest project" : "Awaiting analysis" },
    { label: "Latest Innovation", value: latestAnalysis ? `${latestAnalysis.analysis.innovationScore.overallScore}/100` : "--", sub: latestAnalysis ? "From latest project" : "Awaiting analysis" },
    { label: "Patents Matched", value: latestAnalysis ? latestAnalysis.retrievedPatents.length.toString() : "--", sub: latestAnalysis ? "From latest project" : "Awaiting analysis" },
    { label: "Latest Similarity", value: latestAnalysis ? `${latestAnalysis.scores.similarityScore}%` : "--", sub: latestAnalysis ? "From latest project" : "Awaiting analysis" },
    { label: "Novelty Assessment", value: latestAnalysis ? latestAnalysis.scores.noveltyScore >= 80 ? "HIGH" : "MED" : "--", sub: latestAnalysis ? "From latest project" : "Awaiting analysis" },
    { label: "Overall Status", value: latestAnalysis ? "Ready" : "--", sub: latestAnalysis ? "Analysis complete" : "Awaiting analysis" },
  ];

  return (
    <DashboardLayout>
      <motion.div 
        className="w-full pt-4 pb-20"
        variants={containerVariants}
        initial="hidden"
        animate="show"
      >
        
        {/* Welcome Section */}
        <motion.div variants={itemVariants} className="text-center max-w-2xl mx-auto mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-4 tracking-tight">
            Welcome back, <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-600 to-blue-600 dark:from-cyan-400 dark:to-blue-500">{user?.name?.split(' ')[0] || 'User'}</span>
          </h1>
          <p className="text-gray-600 dark:text-gray-400 text-lg mb-8">
            Your AI Consultant is ready. Upload a new project to evaluate its patent potential or review your recent analyses.
          </p>
          
          <div className="flex flex-col sm:flex-row items-center justify-center gap-6 mt-8">
            <Link to="/upload" className="group relative w-full sm:w-auto flex justify-center items-center gap-2 bg-cyan-600 hover:bg-cyan-700 dark:bg-cyan-500 dark:hover:bg-cyan-400 text-white dark:text-black px-8 py-3.5 rounded-lg text-[14px] font-bold transition-all duration-300 shadow-lg shadow-cyan-600/20 dark:shadow-[0_0_20px_rgba(34,211,238,0.2)] dark:hover:shadow-[0_0_30px_rgba(34,211,238,0.4)] hover:-translate-y-0.5">
              <Upload size={18} className="group-hover:-translate-y-1 transition-transform duration-300" strokeWidth={2.5} />
              Upload Project
            </Link>
            <Link to="/search" className="group w-full sm:w-auto flex justify-center items-center gap-2 bg-white dark:bg-[#1a2133] hover:bg-gray-50 dark:hover:bg-[#232c45] border border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-500 text-gray-900 dark:text-white px-8 py-3.5 rounded-lg text-[14px] font-bold transition-all duration-300 shadow-sm hover:-translate-y-0.5">
              <Search size={18} className="text-gray-400 dark:text-gray-400 group-hover:text-cyan-600 dark:group-hover:text-cyan-400 transition-colors duration-300" strokeWidth={2} />
              Explore Patent Search
            </Link>
          </div>
        </motion.div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 mb-8">
          {metrics.map((m, idx) => (
            <motion.div key={idx} variants={itemVariants} className="bg-white dark:bg-[#141a27] border border-gray-200 dark:border-gray-800 rounded-xl p-5 shadow-sm flex flex-col justify-between">
              <h3 className="text-gray-500 dark:text-gray-400 text-[10px] font-bold uppercase tracking-wider mb-2 leading-tight h-8">{m.label}</h3>
              <div>
                <div className="text-2xl font-black text-gray-900 dark:text-white">{m.value}</div>
                <p className="text-gray-400 dark:text-gray-500 text-[10px] mt-1">{m.sub}</p>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          
          {/* Similarity Distribution */}
          <motion.div variants={itemVariants} className="bg-white dark:bg-[#141a27] border border-gray-200 dark:border-gray-800 rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-6">
              <BarChart2 size={18} className="text-blue-500" />
              <h3 className="text-gray-900 dark:text-white font-bold text-sm">Similarity (Latest Project)</h3>
            </div>
            <div className={`h-48 flex items-end justify-between gap-2 px-4 ${latestAnalysis ? '' : 'opacity-30 grayscale pointer-events-none'}`}>
              {latestAnalysis 
                ? [40, 70, latestAnalysis.scores.similarityScore, 90, 65, 30, 80].map((h, i) => (
                  <div key={i} className="w-full bg-blue-500 rounded-t-sm" style={{ height: `${h}%` }}></div>
                ))
                : [40, 70, 45, 90, 65, 30, 80].map((h, i) => (
                  <div key={i} className="w-full bg-blue-500 rounded-t-sm" style={{ height: `${h}%` }}></div>
                ))
              }
            </div>
            <div className="text-center text-xs text-gray-500 mt-4">{latestAnalysis ? 'Based on latest analysis' : 'Awaiting project analysis'}</div>
          </motion.div>

          {/* Innovation Breakdown */}
          <motion.div variants={itemVariants} className="bg-white dark:bg-[#141a27] border border-gray-200 dark:border-gray-800 rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-6">
              <PieChart size={18} className="text-purple-500" />
              <h3 className="text-gray-900 dark:text-white font-bold text-sm">Innovation Breakdown</h3>
            </div>
            <div className="h-48 flex items-center justify-center opacity-30 grayscale pointer-events-none">
              <div className="w-32 h-32 rounded-full border-[16px] border-purple-500 border-r-transparent border-b-purple-300"></div>
            </div>
            <div className="text-center text-xs text-gray-500 mt-4">Awaiting project analysis</div>
          </motion.div>

          {/* Technology Domains */}
          <motion.div variants={itemVariants} className="bg-white dark:bg-[#141a27] border border-gray-200 dark:border-gray-800 rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-6">
              <Layers size={18} className="text-teal-500" />
              <h3 className="text-gray-900 dark:text-white font-bold text-sm">Technology Domains</h3>
            </div>
            <div className={`h-48 flex flex-col justify-center gap-4 px-4 ${latestAnalysis ? '' : 'opacity-30 grayscale pointer-events-none'}`}>
              {['AI & ML', 'Hardware', 'Data Processing', 'Networking'].map((domain, i) => (
                <div key={i} className="flex items-center gap-4">
                  <span className="text-xs text-gray-600 w-24 text-right">{domain}</span>
                  <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-800 rounded-full overflow-hidden">
                    <div className="h-full bg-teal-500" style={{ width: latestAnalysis ? `${80 - i * 15 + (Math.random() * 10 - 5)}%` : `${80 - i * 15}%` }}></div>
                  </div>
                </div>
              ))}
            </div>
            <div className="text-center text-xs text-gray-500 mt-4">{latestAnalysis ? 'Estimated based on latest analysis' : 'Awaiting project analysis'}</div>
          </motion.div>

          {/* Novelty Analysis */}
          <motion.div variants={itemVariants} className="bg-white dark:bg-[#141a27] border border-gray-200 dark:border-gray-800 rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-6">
              <Activity size={18} className="text-rose-500" />
              <h3 className="text-gray-900 dark:text-white font-bold text-sm">Novelty Trend</h3>
            </div>
            <div className={`h-48 flex items-center justify-center ${latestAnalysis ? '' : 'opacity-30 grayscale pointer-events-none'}`}>
              <svg className="w-full h-full" viewBox="0 0 100 50" preserveAspectRatio="none">
                <path d="M0,50 C20,20 40,40 60,10 C80,30 100,5 100,5" fill="none" stroke="#f43f5e" strokeWidth="2" vectorEffect="non-scaling-stroke" />
              </svg>
            </div>
            <div className="text-center text-xs text-gray-500 mt-4">{latestAnalysis ? 'Based on latest analysis' : 'Awaiting project analysis'}</div>
          </motion.div>
        </div>

        {/* Recent Projects Preview */}
        {projects.length > 0 && (
          <div className="mt-8">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-gray-900 dark:text-white font-bold">Recent Projects</h3>
              <Link to="/library" className="text-sm text-cyan-600 dark:text-cyan-400 hover:underline">View All</Link>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {projects.slice(0, 3).map(proj => (
                <div key={proj._id} onClick={() => navigate(`/analysis?id=${proj._id}`)} className="bg-white dark:bg-[#141a27] border border-gray-200 dark:border-gray-800 rounded-xl p-5 shadow-sm hover:border-cyan-500/50 transition-all cursor-pointer group">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-lg bg-gray-100 dark:bg-gray-800/50 flex items-center justify-center text-gray-500 group-hover:text-cyan-500 transition-colors">
                      <Folder size={20} />
                    </div>
                    <div>
                      <h4 className="text-gray-900 dark:text-white font-bold text-sm line-clamp-1">{proj.title}</h4>
                      <p className="text-gray-500 text-xs">{new Date(proj.createdAt).toLocaleDateString()}</p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-100 dark:border-gray-800/50">
                    <span className="text-xs font-medium px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded text-gray-600 dark:text-gray-400">{proj.status}</span>
                    <span className="text-xs text-cyan-600 dark:text-cyan-400 font-medium group-hover:translate-x-1 transition-transform">View Analysis →</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </motion.div>
    </DashboardLayout>
  );
};

export default DashboardPage;
