import React, { useState, useRef, useEffect } from 'react';
import DashboardLayout from '../layouts/DashboardLayout';
import { UploadCloud, FileText, Loader2, CheckCircle2, Clock, Sparkles, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../api/axios';
import toast from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';

const PIPELINE_STAGES = [
  { id: 1, label: 'Document Processing', desc: 'Validating, extracting text, detecting patent sections & chunking' },
  { id: 2, label: 'Feature Extraction', desc: 'Parsing AST and NLP technical features from disclosure' },
  { id: 3, label: 'Hybrid Prior-Art Search', desc: 'Sparse BM25 + Dense BGE vector retrieval across indexed patent corpus' },
  { id: 4, label: 'RRF Candidate Fusion', desc: 'Reciprocal Rank Fusion with rank parameter k=60' },
  { id: 5, label: 'Cross-Encoder Reranking', desc: 'BGE Cross-Encoder scoring deep candidate relevance' },
  { id: 6, label: 'Feature-Evidence Mapping', desc: 'Determining technical relationships (direct, partial, contextual, weak)' },
  { id: 7, label: 'EB-PRE Assessment', desc: 'Deterministic 6-dimension Evidence-Based Patent Readiness calculation' },
  { id: 8, label: 'Grounded Report', desc: 'Compiling auditable 10-section grounded explanation report' },
];

const UploadPage = () => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [currentStageIndex, setCurrentStageIndex] = useState(0);
  const [title, setTitle] = useState('');
  const [domain, setDomain] = useState('General Technology');
  const [recentProjects, setRecentProjects] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(true);

  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchRecentProjects();
  }, []);

  const fetchRecentProjects = async () => {
    try {
      const { data } = await api.get('/projects?limit=5');
      setRecentProjects(data || []);
    } catch (err) {
      console.warn('Could not fetch project history:', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files.length > 0) {
      handleFileUpload(e.target.files[0]);
    }
  };

  const handleFileUpload = async (file) => {
    if (!file) return;

    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!['pdf', 'docx', 'txt'].includes(ext)) {
      return toast.error('Only PDF, DOCX, and TXT files are supported');
    }

    if (file.size > 50 * 1024 * 1024) {
      return toast.error('File size must be under 50MB');
    }

    const baseName = file.name.includes('.') ? file.name.substring(0, file.name.lastIndexOf('.')) : file.name;
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title.trim() || baseName);
    formData.append('domain', domain);

    setIsUploading(true);
    setCurrentStageIndex(0);

    // Realistic progressive stage transition while pipeline executes on backend
    const timer = setInterval(() => {
      setCurrentStageIndex((prev) => {
        if (prev < 6) return prev + 1;
        return prev;
      });
    }, 4500);

    try {
      const { data } = await api.post('/pipeline/analyze', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 300000, // 5 minutes buffer specifically for full AI patent pipeline executions
      });


      clearInterval(timer);
      setCurrentStageIndex(7);

      toast.success('Patent Readiness Assessment completed successfully!');

      // Save to sessionStorage for instant fallback access
      sessionStorage.setItem(`patentiq_analysis_${data.project_id}`, JSON.stringify(data));

      setTimeout(() => {
        navigate(`/analysis?id=${data.project_id}`, { state: { analysisResult: data } });
      }, 800);
    } catch (err) {
      clearInterval(timer);
      console.error(err);
      const msg = err.response?.data?.detail || err.message || 'Analysis pipeline execution failed';
      toast.error(msg);
      setIsUploading(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="w-full pt-4 pb-16">
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2 tracking-tight">
            New Patent Readiness Analysis
          </h1>
          <p className="text-gray-500 dark:text-gray-400">
            Upload your invention disclosure, engineering spec, or research draft for complete EB-PRE assessment.
          </p>
        </motion.div>

        {/* Project Metadata Input */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider mb-2">
              Project Title (Optional)
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              disabled={isUploading}
              placeholder="e.g. Edge LiDAR Autonomous Navigation Unit"
              className="w-full px-4 py-2.5 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-[#0e131f] text-gray-900 dark:text-white text-sm focus:outline-none focus:border-cyan-500"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider mb-2">
              Technology Domain
            </label>
            <select
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              disabled={isUploading}
              className="w-full px-4 py-2.5 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-[#0e131f] text-gray-900 dark:text-white text-sm focus:outline-none focus:border-cyan-500"
            >
              <option value="General Technology">General Technology</option>
              <option value="Artificial Intelligence & ML">Artificial Intelligence & ML</option>
              <option value="Robotics & Autonomous Systems">Robotics & Autonomous Systems</option>
              <option value="Medical Devices & BioTech">Medical Devices & BioTech</option>
              <option value="Wireless Communications">Wireless Communications</option>
              <option value="Semiconductors & Electronics">Semiconductors & Electronics</option>
            </select>
          </div>
        </div>

        {/* Upload Zone */}
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`w-full border-2 border-dashed rounded-3xl p-10 flex flex-col items-center justify-center transition-all duration-300 bg-white/60 dark:bg-[#0b101b]/60 backdrop-blur-sm ${
            isDragging
              ? 'border-cyan-500 bg-cyan-50/50 dark:bg-cyan-900/10 scale-[1.01]'
              : 'border-gray-300 dark:border-gray-800 hover:border-cyan-500/50'
          }`}
        >
          <div className="w-16 h-16 bg-cyan-500/10 rounded-2xl flex items-center justify-center mb-5 text-cyan-500 shadow-inner">
            <UploadCloud size={32} strokeWidth={1.75} />
          </div>
          <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-1">
            Choose an invention document or drag it here
          </h3>
          <p className="text-gray-500 dark:text-gray-400 text-xs mb-6 text-center max-w-sm">
            Supported formats: PDF, DOCX, TXT. Preserves provenance, structure, and claim boundaries.
          </p>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            className="hidden"
            accept=".pdf,.docx,.txt"
          />
          <button
            disabled={isUploading}
            onClick={() => fileInputRef.current?.click()}
            className="bg-cyan-600 hover:bg-cyan-700 dark:bg-cyan-500 dark:hover:bg-cyan-400 text-white dark:text-black px-7 py-3 rounded-xl text-xs font-bold uppercase tracking-wider transition-all duration-300 shadow-lg shadow-cyan-600/20 hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isUploading ? (
              <>
                <Loader2 className="animate-spin" size={16} />
                Executing Pipeline...
              </>
            ) : (
              'Select Invention Document'
            )}
          </button>
        </motion.div>

        {/* Live Multi-Stage Pipeline Stepper */}
        <AnimatePresence>
          {isUploading && (
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mt-8 bg-white dark:bg-[#0e131f] border border-cyan-500/20 rounded-2xl p-6 shadow-xl"
            >
              <div className="flex items-center justify-between mb-5">
                <div className="flex items-center gap-2.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping" />
                  <h3 className="font-bold text-sm text-gray-900 dark:text-white">
                    Executing 18-Step Patent Readiness Pipeline
                  </h3>
                </div>
                <span className="text-xs font-mono text-cyan-500 dark:text-cyan-400 font-semibold">
                  Stage {currentStageIndex + 1} of 8
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                {PIPELINE_STAGES.map((st, idx) => {
                  const isDone = idx < currentStageIndex;
                  const isCurrent = idx === currentStageIndex;
                  return (
                    <div
                      key={st.id}
                      className={`p-3.5 rounded-xl border text-left transition-all ${
                        isCurrent
                          ? 'border-cyan-500 bg-cyan-500/10 text-cyan-400'
                          : isDone
                          ? 'border-emerald-500/30 bg-emerald-500/5 text-emerald-400'
                          : 'border-gray-200 dark:border-gray-800/80 bg-gray-50/50 dark:bg-[#121826]/40 text-gray-400'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-[10px] font-mono font-bold uppercase tracking-wider">
                          Step 0{st.id}
                        </span>
                        {isDone ? (
                          <CheckCircle2 size={14} className="text-emerald-500" />
                        ) : isCurrent ? (
                          <Loader2 size={14} className="animate-spin text-cyan-400" />
                        ) : (
                          <Clock size={12} className="text-gray-500" />
                        )}
                      </div>
                      <div className="text-xs font-bold text-gray-900 dark:text-gray-200 mb-1">{st.label}</div>
                      <div className="text-[10px] text-gray-500 dark:text-gray-400 line-clamp-2 leading-relaxed">
                        {st.desc}
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="mt-5 p-3 rounded-xl bg-gray-100 dark:bg-black/30 text-[11px] text-gray-500 flex items-center justify-between">
                <span>Deterministic EB-PRE evaluates mathematical scoring while Gemini synthesizes grounded reporting.</span>
                <span className="font-mono text-cyan-400">Running BGE & Qdrant</span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Upload History from Real Backend */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mt-12"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-bold text-gray-900 dark:text-white">Recent Analyses</h2>
            <button
              onClick={() => navigate('/library')}
              className="text-xs text-cyan-600 dark:text-cyan-400 hover:underline"
            >
              View All in Library →
            </button>
          </div>

          <div className="bg-white dark:bg-[#0e131f] border border-gray-200 dark:border-gray-800 rounded-2xl overflow-hidden shadow-sm">
            {loadingHistory ? (
              <div className="p-8 text-center text-gray-400 text-xs flex items-center justify-center gap-2">
                <Loader2 size={14} className="animate-spin" /> Loading your workspaces...
              </div>
            ) : recentProjects.length === 0 ? (
              <div className="p-10 flex flex-col items-center justify-center text-center">
                <div className="w-12 h-12 bg-gray-100 dark:bg-gray-800/50 rounded-2xl flex items-center justify-center mb-3 text-gray-400">
                  <FileText size={20} />
                </div>
                <h3 className="text-gray-900 dark:text-white text-sm font-medium mb-1">No prior analyses</h3>
                <p className="text-gray-500 text-xs">Upload your first invention disclosure to begin.</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-100 dark:divide-gray-800/60">
                {recentProjects.map((proj) => (
                  <div
                    key={proj.id}
                    onClick={() => navigate(`/analysis?id=${proj.id}`)}
                    className="p-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-white/5 cursor-pointer transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-xl bg-cyan-500/10 text-cyan-500 flex items-center justify-center">
                        <FileText size={18} />
                      </div>
                      <div>
                        <div className="font-medium text-xs text-gray-900 dark:text-white">{proj.title}</div>
                        <div className="text-[11px] text-gray-400">
                          {proj.original_file_name} • {proj.file_type?.toUpperCase()}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      {proj.readiness_score !== null && proj.readiness_score !== undefined ? (
                        <div className="text-right">
                          <span className="text-xs font-bold text-cyan-600 dark:text-cyan-400 font-mono">
                            {proj.readiness_score}%
                          </span>
                          <div className="text-[10px] text-gray-400 capitalize">{proj.readiness_category}</div>
                        </div>
                      ) : (
                        <span className="text-[11px] text-gray-400">Analyzed</span>
                      )}
                      <button className="text-xs text-gray-400 hover:text-white px-2 py-1">View →</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </DashboardLayout>
  );
};

export default UploadPage;
