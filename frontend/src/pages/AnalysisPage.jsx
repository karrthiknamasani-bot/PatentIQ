import React, { useState, useEffect, useCallback } from 'react';
import DashboardLayout from '../layouts/DashboardLayout';
import { Upload, Brain, FileSearch, Search, Activity, CheckCircle2, Loader2, Bot, AlertTriangle, ShieldCheck, FileText, PieChart } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSearchParams, useNavigate } from 'react-router-dom';
import api from '../api/axios';
import toast from 'react-hot-toast';

const AnalysisPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const projectId = searchParams.get('id');

  const [status, setStatus] = useState('empty'); // empty, analyzing, completed
  const [currentStep, setCurrentStep] = useState(0);
  const [analysisData, setAnalysisData] = useState(null);

  const fetchAnalysis = useCallback(async (id) => {
    setStatus('analyzing');
    setCurrentStep(4); // Skip to end of animation conceptually
    try {
      const res = await api.get(`/analyze/${id}`);
      if (res.data && res.data.success) {
        setAnalysisData(res.data.data);
        setStatus('completed');
      }
    } catch (error) {
      console.error(error);
      toast.error('Failed to load analysis. It may still be processing.');
      navigate('/dashboard');
    }
  }, [navigate]);

  useEffect(() => {
    if (projectId) {
      fetchAnalysis(projectId);
    } else {
      setStatus('empty');
    }
  }, [projectId, fetchAnalysis]);

  const steps = [
    { icon: FileText, text: "Reading project document", color: "text-blue-500" },
    { icon: FileSearch, text: "Extracting core innovations", color: "text-purple-500" },
    { icon: Search, text: "Semantic searching global databases", color: "text-emerald-500" },
    { icon: Activity, text: "Comparing technical components", color: "text-amber-500" },
    { icon: Brain, text: "Generating potential score", color: "text-cyan-500" }
  ];

  const handleSimulateUpload = () => {
    navigate('/upload');
  };

  const MetricCard = ({ title, value, subtext, icon: Icon, colorClass, borderClass }) => (
    <div className={`bg-white dark:bg-[#141a27] border ${borderClass} rounded-xl p-5 shadow-sm`}>
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-gray-500 dark:text-gray-400 text-[10px] font-bold uppercase tracking-wider">{title}</h3>
        <Icon size={16} className={colorClass} />
      </div>
      <div className="text-3xl font-black text-gray-900 dark:text-white">{value}</div>
      <p className="text-gray-400 dark:text-gray-500 text-[11px] mt-1 font-medium">{subtext}</p>
    </div>
  );

  return (
    <DashboardLayout>
      <div className="w-full pt-4 pb-20">
        
        {/* Header */}
        <div className="mb-8 flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-[10px] text-gray-500 font-bold uppercase tracking-widest mb-2">
              <span>Intelligence Engine</span>
              <span>/</span>
              <span className="text-cyan-400">Analysis</span>
            </div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Patent Potential Evaluation</h1>
            <p className="text-gray-600 dark:text-gray-400 text-sm">AI-powered project potential assessment</p>
          </div>
          {status === 'completed' && (
            <button 
              onClick={() => navigate('/upload')}
              className="bg-white dark:bg-[#1a2133] hover:bg-gray-50 dark:hover:bg-[#232c45] border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white px-5 py-2.5 rounded-lg text-sm font-bold transition-all shadow-sm"
            >
              Analyze Another Project
            </button>
          )}
        </div>

        <AnimatePresence mode="wait">
          
          {/* EMPTY STATE */}
          {status === 'empty' && (
            <motion.div 
              key="empty"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.3 }}
              className="bg-white dark:bg-[#111621] border border-gray-200 dark:border-gray-800 rounded-2xl p-16 flex flex-col items-center justify-center text-center min-h-[500px] shadow-sm dark:shadow-none"
            >
              <motion.div 
                animate={{ y: [0, -10, 0] }}
                transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }}
                className="w-24 h-24 bg-gray-50 dark:bg-[#141a27] border border-gray-200 dark:border-gray-800/80 rounded-3xl flex items-center justify-center mb-8 shadow-lg dark:shadow-2xl relative"
              >
                <div className="absolute inset-0 bg-cyan-500/10 blur-xl rounded-full"></div>
                <Bot size={36} className="text-gray-400 dark:text-gray-500 relative z-10" strokeWidth={1.5} />
              </motion.div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">Generate your first AI analysis</h2>
              <p className="text-gray-500 max-w-md mb-8">
                Upload a project document to initiate the AI Consultant pipeline. The system will automatically extract innovations and evaluate patent potential.
              </p>
              <button 
                onClick={handleSimulateUpload}
                className="bg-cyan-600 hover:bg-cyan-700 dark:bg-cyan-500 dark:hover:bg-cyan-400 text-white dark:text-black px-8 py-3 rounded-lg font-bold transition-all duration-300 shadow-lg shadow-cyan-600/20 dark:shadow-[0_0_15px_rgba(34,211,238,0.2)] dark:hover:shadow-[0_0_30px_rgba(34,211,238,0.5)] flex items-center gap-2"
              >
                <Upload size={18} />
                Upload a Project
              </button>
            </motion.div>
          )}

          {/* ANALYZING STATE */}
          {status === 'analyzing' && (
            <motion.div 
              key="analyzing"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className="bg-white dark:bg-[#111621] border border-cyan-200 dark:border-cyan-900/50 rounded-2xl p-12 flex flex-col items-center justify-center min-h-[500px] shadow-sm dark:shadow-[0_0_50px_rgba(34,211,238,0.1)] relative overflow-hidden"
            >
              <div className="absolute top-0 inset-x-0 h-1 bg-gray-100 dark:bg-gray-800">
                <motion.div 
                  className="h-full bg-gradient-to-r from-cyan-500 to-purple-500"
                  initial={{ width: '0%' }}
                  animate={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
                  transition={{ duration: 0.3 }}
                />
              </div>

              <div className="relative mb-12">
                <div className="absolute inset-0 bg-cyan-500/10 dark:bg-cyan-500/20 blur-[50px] rounded-full animate-pulse"></div>
                <div className="w-32 h-32 bg-gray-50 dark:bg-[#0a0d14] border border-cyan-200 dark:border-cyan-500/30 rounded-full flex items-center justify-center relative z-10 shadow-lg dark:shadow-[0_0_30px_rgba(34,211,238,0.2)]">
                  <Brain size={48} className="text-cyan-500 dark:text-cyan-400 animate-pulse" />
                </div>
              </div>

              <div className="space-y-6 w-full max-w-md">
                {steps.map((step, idx) => {
                  const Icon = step.icon;
                  const isActive = idx === currentStep;
                  const isPast = idx < currentStep;
                  
                  return (
                    <motion.div 
                      key={idx}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ 
                        opacity: isPast || isActive ? 1 : 0.3,
                        x: 0,
                        scale: isActive ? 1.05 : 1
                      }}
                      className={`flex items-center gap-4 p-3 rounded-lg transition-colors ${isActive ? 'bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700/50' : 'border border-transparent'}`}
                    >
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                        isPast ? 'bg-emerald-100 text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-400' : 
                        isActive ? `bg-gray-100 dark:bg-gray-800 ${step.color}` : 
                        'bg-gray-100 text-gray-400 dark:bg-gray-800/50 dark:text-gray-600'
                      }`}>
                        {isPast ? <CheckCircle2 size={16} /> : 
                         isActive ? <Loader2 size={16} className="animate-spin" /> : 
                         <Icon size={16} />}
                      </div>
                      <span className={`font-medium text-sm ${isActive ? 'text-gray-900 dark:text-white' : isPast ? 'text-gray-500 dark:text-gray-400' : 'text-gray-400 dark:text-gray-600'}`}>
                        {step.text}
                      </span>
                    </motion.div>
                  );
                })}
              </div>
            </motion.div>
          )}

          {/* COMPLETED STATE (AI Consultant Dashboard) */}
          {status === 'completed' && (
            <motion.div 
              key="completed"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex flex-col gap-6"
            >
              
              {/* Top Metrics Row */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <MetricCard 
                  title="Patent Potential" 
                  value={`${analysisData?.scores?.innovationScore || '--'}/100`} 
                  subtext={analysisData?.analysis?.technicalDomain || 'Domain Evaluated'} 
                  icon={ShieldCheck} 
                  colorClass="text-emerald-500" 
                  borderClass="border-emerald-200 dark:border-emerald-900/50"
                />
                <MetricCard 
                  title="Novelty Score" 
                  value={`${analysisData?.scores?.noveltyScore || '--'}%`} 
                  subtext="Originality" 
                  icon={Brain} 
                  colorClass="text-purple-500" 
                  borderClass="border-gray-200 dark:border-gray-800"
                />
                <MetricCard 
                  title="Similarity Score" 
                  value={`${analysisData?.scores?.similarityScore || '--'}%`} 
                  subtext="Overlap with prior art" 
                  icon={PieChart} 
                  colorClass="text-blue-500" 
                  borderClass="border-gray-200 dark:border-gray-800"
                />
                <MetricCard 
                  title="Model Confidence" 
                  value={`${analysisData?.scores?.confidenceScore || '--'}%`} 
                  subtext="Based on retrieved context" 
                  icon={Search} 
                  colorClass="text-cyan-500" 
                  borderClass="border-gray-200 dark:border-gray-800"
                />
              </div>

              {/* Main Two-Column Layout */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                
                {/* Left Column (Details) */}
                <div className="lg:col-span-2 space-y-6">
                  
                  {/* Executive Summary */}
                  <div className="bg-white dark:bg-[#141a27] border border-gray-200 dark:border-gray-800 rounded-xl p-6 shadow-sm">
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                      <Search className="text-blue-500" size={20} />
                      AI Innovation Summary
                    </h3>
                    <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                      {analysisData?.analysis?.innovationSummary || 'No summary available.'}
                    </p>
                  </div>

                  {/* Strengths & Weaknesses */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="bg-white dark:bg-[#141a27] border border-gray-200 dark:border-gray-800 rounded-xl p-6 shadow-sm">
                      <h3 className="text-md font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                        <Activity className="text-purple-500" size={18} />
                        Strengths
                      </h3>
                      <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400 leading-relaxed mb-4 list-disc pl-4">
                        {analysisData?.analysis?.strengths?.map((str, i) => (
                          <li key={i}>{str}</li>
                        )) || <li>No distinct strengths identified.</li>}
                      </ul>
                    </div>

                    <div className="bg-white dark:bg-[#141a27] border border-gray-200 dark:border-gray-800 rounded-xl p-6 shadow-sm">
                      <h3 className="text-md font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                        <AlertTriangle className="text-amber-500" size={18} />
                        Weaknesses & Risks
                      </h3>
                      <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400 leading-relaxed mb-4 list-disc pl-4">
                        {analysisData?.analysis?.weaknesses?.map((risk, i) => (
                          <li key={i}>{risk}</li>
                        )) || <li>No significant risks identified.</li>}
                      </ul>
                    </div>
                  </div>

                </div>

                {/* Right Column (AI Consultant Advice) */}
                <div className="space-y-6">
                  
                  {/* Commercial Applications */}
                  <div className="bg-gradient-to-br from-[#111621] to-[#1a2133] border border-cyan-900/50 rounded-xl p-6 shadow-lg shadow-cyan-900/10">
                    <h3 className="text-md font-bold text-white mb-4 flex items-center gap-2">
                      <Bot className="text-cyan-400" size={20} />
                      Commercial Applications
                    </h3>
                    <div className="space-y-4">
                      {analysisData?.analysis?.commercialApplications?.map((app, i) => (
                        <div key={i} className="bg-white/5 border border-white/10 rounded-lg p-3">
                          <p className="text-[13px] text-gray-300 leading-relaxed">{app}</p>
                        </div>
                      ))}
                      {(!analysisData?.analysis?.commercialApplications || analysisData?.analysis?.commercialApplications?.length === 0) && (
                        <p className="text-[13px] text-gray-300">No applications identified.</p>
                      )}
                    </div>
                  </div>
                  
                  {/* Supporting Context */}
                  <div className="bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700/50 rounded-xl p-6">
                    <h3 className="text-sm font-bold text-gray-900 dark:text-white mb-3">Supporting Context</h3>
                    <p className="text-xs text-gray-500 mb-2">Relevant patents retrieved via Agentic RAG:</p>
                    <ul className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                      {[...new Set(analysisData?.retrievedPatents || [])].map((pid, i) => (
                        <li key={i}>• {pid}</li>
                      ))}
                      {(!analysisData?.retrievedPatents || analysisData.retrievedPatents.length === 0) && (
                        <li>No context chunks utilized.</li>
                      )}
                    </ul>
                  </div>

                  {/* Verdict */}
                  <div className="bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800/50 rounded-xl p-6 text-center">
                    <div className="w-12 h-12 bg-emerald-100 dark:bg-emerald-800/50 rounded-full flex items-center justify-center mx-auto mb-4 text-emerald-600 dark:text-emerald-400">
                      <CheckCircle2 size={24} />
                    </div>
                    <h3 className="text-sm font-bold text-gray-900 dark:text-white uppercase tracking-wider mb-2">Filing Recommendation</h3>
                    <p className="text-2xl font-black text-emerald-600 dark:text-emerald-400 mb-2">{analysisData?.analysis?.recommendation || 'Evaluated'}</p>
                    <p className="text-xs text-gray-600 dark:text-gray-400">Based on global semantic search</p>
                  </div>

                </div>
              </div>
            </motion.div>
          )}

        </AnimatePresence>
      </div>
    </DashboardLayout>
  );
};

export default AnalysisPage;
