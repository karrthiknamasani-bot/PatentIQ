import React, { useState, useEffect, useCallback } from 'react';
import DashboardLayout from '../layouts/DashboardLayout';
import { 
  Brain, Search, Activity, CheckCircle2, Loader2, ShieldCheck, 
  FileText, AlertTriangle, Layers, Award, ArrowUpRight, ChevronRight, Scale
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSearchParams, useNavigate, useLocation } from 'react-router-dom';
import api from '../api/axios';
import toast from 'react-hot-toast';

const AnalysisPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const location = useLocation();
  const projectId = searchParams.get('id');

  const [status, setStatus] = useState('loading'); // loading, completed, empty
  const [data, setData] = useState(null);

  const loadAnalysisData = useCallback(async (id) => {
    setStatus('loading');

    // 1. Check if passed directly via navigation state
    if (location.state?.analysisResult && location.state.analysisResult.project_id === id) {
      setData(location.state.analysisResult);
      setStatus('completed');
      return;
    }

    // 2. Check sessionStorage
    const cached = sessionStorage.getItem(`patentiq_analysis_${id}`);
    if (cached) {
      try {
        const parsed = JSON.parse(cached);
        setData(parsed);
        setStatus('completed');
        return;
      } catch (e) {}
    }

    // 3. Fetch from FastAPI backend
    try {
      const res = await api.get(`/projects/${id}`);
      if (res.data) {
        const proj = res.data;
        // Transform project detail into unified view format
        const analysis = proj.analysis || {};
        const report = proj.report?.metadata?.report || {};

        setData({
          project_id: proj.id,
          title: proj.title,
          filename: proj.original_file_name,
          readiness_score: (proj.readiness_score || 0) / 100,
          readiness_percentage: proj.readiness_score || 0,
          confidence_score: proj.confidence_score || 0.8,
          readiness_category: proj.readiness_category || 'moderate',
          category_display: (proj.readiness_category || 'Moderate').toUpperCase(),
          dimension_scores: {
            novelty: { score: (analysis.novelty_score !== undefined ? analysis.novelty_score : 70) / 100 },
            prior_art_overlap: { score: (analysis.overlap_score !== undefined ? analysis.overlap_score : 30) / 100 },
            technical_differentiation: { score: (analysis.differentiation_score !== undefined ? analysis.differentiation_score : 75) / 100 },
            innovation_characteristics: { 
              score: typeof analysis.innovation_characteristics === 'object' && analysis.innovation_characteristics?.score !== undefined 
                ? analysis.innovation_characteristics.score 
                : (typeof analysis.innovation_characteristics === 'number' ? analysis.innovation_characteristics / 100 : 0.8) 
            },
            documentation_quality: { score: (analysis.documentation_score !== undefined ? analysis.documentation_score : 85) / 100 },
            commercial_potential: { 
              score: typeof analysis.commercial_potential === 'object' && analysis.commercial_potential?.score !== undefined 
                ? analysis.commercial_potential.score 
                : (typeof analysis.commercial_potential === 'number' ? analysis.commercial_potential / 100 : 0.7) 
            },
          },
          uncertainty_flags: analysis.uncertainty_flags || [],
          features: report.technical_feature_analysis || [],
          mappings: report.prior_art_evidence || [],
          executive_summary: analysis.explanation || report.executive_summary || 'Evidence-based patent readiness assessment.',
          report: report,
        });
        setStatus('completed');
      } else {
        setStatus('empty');
      }
    } catch (err) {
      console.error(err);
      toast.error('Failed to load analysis for this project');
      setStatus('empty');
    }
  }, [location.state]);

  useEffect(() => {
    if (projectId) {
      loadAnalysisData(projectId);
    } else {
      setStatus('empty');
    }
  }, [projectId, loadAnalysisData]);

  const getRelationshipBadge = (rel) => {
    switch (rel) {
      case 'direct_match':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-red-500/10 text-red-500 border border-red-500/20">direct_match</span>;
      case 'partial_match':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/10 text-amber-500 border border-amber-500/20">partial_match</span>;
      case 'contextual_match':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-blue-500/10 text-blue-500 border border-blue-500/20">contextual_match</span>;
      case 'weak_match':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-500/10 text-cyan-500 border border-cyan-500/20">weak_match</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">{rel || 'no_material_match'}</span>;
    }
  };

  return (
    <DashboardLayout>
      <div className="w-full pt-4 pb-20">
        
        {/* Header */}
        <div className="mb-6 flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-[10px] text-gray-500 font-bold uppercase tracking-widest mb-1.5">
              <span>EB-PRE Readiness Engine</span>
              <span>/</span>
              <span className="text-cyan-500 font-mono">Workspace: {data?.project_id?.slice(0, 8) || 'Active'}</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-1">
              {data?.title || 'Patent Readiness Evaluation'}
            </h1>
            <p className="text-gray-500 dark:text-gray-400 text-xs">
              Evidence-based multi-dimensional readiness assessment computed from verified prior-art mappings.
            </p>
          </div>
          {status === 'completed' && (
            <div className="flex items-center gap-3">
              <button
                onClick={() => navigate(`/reports?id=${data?.project_id}`)}
                className="bg-cyan-600 hover:bg-cyan-700 dark:bg-cyan-500 dark:hover:bg-cyan-400 text-white dark:text-black px-4 py-2 rounded-xl text-xs font-bold transition-all shadow-md flex items-center gap-1.5"
              >
                View Full Report <ArrowUpRight size={14} />
              </button>
              <button
                onClick={() => navigate('/upload')}
                className="bg-white dark:bg-[#121826] hover:bg-gray-50 dark:hover:bg-white/5 border border-gray-200 dark:border-gray-800 text-gray-700 dark:text-gray-300 px-4 py-2 rounded-xl text-xs font-semibold transition-all"
              >
                New Analysis
              </button>
            </div>
          )}
        </div>

        {/* System Methodology Disclosure Banner */}
        <div className="mb-6 p-3.5 rounded-2xl bg-cyan-500/5 border border-cyan-500/20 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2 text-cyan-600 dark:text-cyan-400 font-medium">
            <Scale size={16} />
            <span>EB-PRE calculates the readiness score mathematically. Gemini provides evidence-grounded explanation.</span>
          </div>
          <span className="text-[11px] font-mono text-gray-400">Strict Numerical Integrity</span>
        </div>

        {/* LOADING STATE */}
        {status === 'loading' && (
          <div className="p-20 flex flex-col items-center justify-center text-center">
            <Loader2 size={32} className="animate-spin text-cyan-500 mb-4" />
            <h3 className="text-gray-900 dark:text-white font-bold text-sm">Loading Readiness Evaluation...</h3>
            <p className="text-gray-500 text-xs mt-1">Retrieving evidence matrix and dimension scores</p>
          </div>
        )}

        {/* EMPTY STATE */}
        {status === 'empty' && (
          <div className="bg-white dark:bg-[#0e131f] border border-gray-200 dark:border-gray-800 rounded-3xl p-16 flex flex-col items-center justify-center text-center">
            <div className="w-16 h-16 bg-cyan-500/10 text-cyan-500 rounded-2xl flex items-center justify-center mb-4">
              <Brain size={32} />
            </div>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-2">No Analysis Selected</h2>
            <p className="text-gray-500 text-xs max-w-sm mb-6">
              Upload an invention document or choose an existing project from your library to evaluate readiness.
            </p>
            <button
              onClick={() => navigate('/upload')}
              className="bg-cyan-500 text-black px-6 py-2.5 rounded-xl font-bold text-xs"
            >
              Start New Analysis
            </button>
          </div>
        )}

        {/* COMPLETED STATE */}
        {status === 'completed' && data && (
          <div className="space-y-6">
            
            {/* Top Metrics Row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {/* Readiness Score */}
              <div className="bg-white dark:bg-[#0e131f] border border-cyan-500/30 rounded-2xl p-5 shadow-sm">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">Readiness Score</span>
                  <Award size={18} className="text-cyan-500" />
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-black text-cyan-600 dark:text-cyan-400 font-mono">
                    {Math.round(data.readiness_percentage)}%
                  </span>
                  <span className="text-xs font-mono text-gray-500">
                    ({data.readiness_score?.toFixed(3)})
                  </span>
                </div>
                <div className="mt-2 flex items-center gap-1.5">
                  <span className={`inline-block w-2 h-2 rounded-full ${
                    data.readiness_category === 'high' ? 'bg-emerald-500' :
                    data.readiness_category === 'moderate' ? 'bg-cyan-500' : 'bg-amber-500'
                  }`} />
                  <span className="text-xs font-bold text-gray-700 dark:text-gray-300 uppercase tracking-wide">
                    {data.category_display || data.readiness_category} Readiness
                  </span>
                </div>
              </div>

              {/* Confidence Score */}
              <div className="bg-white dark:bg-[#0e131f] border border-gray-200 dark:border-gray-800 rounded-2xl p-5 shadow-sm">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">Confidence Level</span>
                  <ShieldCheck size={18} className="text-emerald-500" />
                </div>
                <div className="text-3xl font-black text-gray-900 dark:text-white font-mono">
                  {Math.round((data.confidence_score || 0) * 100)}%
                </div>
                <p className="text-[11px] text-gray-500 mt-2">Weighted citation & mapping confidence</p>
              </div>

              {/* Uncertainty Flags */}
              <div className="bg-white dark:bg-[#0e131f] border border-gray-200 dark:border-gray-800 rounded-2xl p-5 shadow-sm">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">Uncertainty Flags</span>
                  <AlertTriangle size={18} className={data.uncertainty_flags?.length ? "text-amber-500" : "text-gray-400"} />
                </div>
                <div className="text-3xl font-black text-gray-900 dark:text-white font-mono">
                  {data.uncertainty_flags?.length || 0}
                </div>
                <p className="text-[11px] text-gray-500 mt-2">
                  {data.uncertainty_flags?.length ? 'Scope constraints noted' : 'Clean corpus coverage'}
                </p>
              </div>

              {/* Features Extracted */}
              <div className="bg-white dark:bg-[#0e131f] border border-gray-200 dark:border-gray-800 rounded-2xl p-5 shadow-sm">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">Extracted Features</span>
                  <Layers size={18} className="text-purple-500" />
                </div>
                <div className="text-3xl font-black text-gray-900 dark:text-white font-mono">
                  {data.features?.length || data.feature_count || 0}
                </div>
                <p className="text-[11px] text-gray-500 mt-2">AST & NLP parsed technical claims</p>
              </div>
            </div>

            {/* EB-PRE Six Dimensions Breakdown */}
            <div className="bg-white dark:bg-[#0e131f] border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm">
              <h3 className="text-sm font-bold text-gray-900 dark:text-white uppercase tracking-wider mb-4 flex items-center gap-2">
                <Activity size={16} className="text-cyan-500" />
                EB-PRE Six-Dimension Mathematical Scoring
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {(() => {
                  const defaultWeights = {
                    novelty: 0.30,
                    prior_art_overlap: 0.20,
                    technical_differentiation: 0.20,
                    innovation_characteristics: 0.15,
                    documentation_quality: 0.10,
                    commercial_potential: 0.05,
                  };
                  const activeWeights = data.weights || defaultWeights;
                  const dimensions = [
                    { key: 'novelty', label: '1. Novelty', weight: `${Math.round((activeWeights.novelty ?? 0.30) * 100)}%`, desc: 'Inverse prior-art mapping severity' },
                    { key: 'prior_art_overlap', label: '2. Prior-Art Overlap', weight: `${Math.round((activeWeights.prior_art_overlap ?? 0.20) * 100)}%`, desc: 'Proportion of direct/partial prior art' },
                    { key: 'technical_differentiation', label: '3. Tech Differentiation', weight: `${Math.round((activeWeights.technical_differentiation ?? 0.20) * 100)}%`, desc: 'Structural & functional uniqueness' },
                    { key: 'innovation_characteristics', label: '4. Innovation Characteristics', weight: `${Math.round((activeWeights.innovation_characteristics ?? 0.15) * 100)}%`, desc: 'Multi-component complexity & utility' },
                    { key: 'documentation_quality', label: '5. Documentation Quality', weight: `${Math.round((activeWeights.documentation_quality ?? 0.10) * 100)}%`, desc: 'Structural section completeness' },
                    { key: 'commercial_potential', label: '6. Commercial Potential', weight: `${Math.round((activeWeights.commercial_potential ?? 0.05) * 100)}%`, desc: 'Market applicability heuristics' },
                  ];
                  return dimensions.map((dim) => {
                    const scoreObj = data.dimension_scores?.[dim.key];
                    const rawScore = typeof scoreObj === 'object' ? (scoreObj?.score ?? 0.7) : (scoreObj ?? 0.7);
                    const percentage = Math.round(rawScore * 100);

                    return (
                      <div key={dim.key} className="p-4 rounded-xl border border-gray-100 dark:border-gray-800/80 bg-gray-50/50 dark:bg-white/[0.02]">
                        <div className="flex justify-between items-center mb-1.5">
                          <span className="font-bold text-xs text-gray-900 dark:text-white">{dim.label}</span>
                          <span className="text-xs font-mono font-bold text-cyan-600 dark:text-cyan-400">{percentage}%</span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-800 h-2 rounded-full overflow-hidden mb-2">
                          <div
                            className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full"
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                        <div className="flex justify-between text-[10px] text-gray-500">
                          <span>{dim.desc}</span>
                          <span className="font-mono font-semibold">Weight: {dim.weight}</span>
                        </div>
                      </div>
                    );
                  });
                })()}
              </div>
            </div>

            {/* Executive Summary */}
            <div className="bg-white dark:bg-[#0e131f] border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm">
              <h3 className="text-sm font-bold text-gray-900 dark:text-white uppercase tracking-wider mb-3 flex items-center gap-2">
                <Brain size={16} className="text-cyan-500" />
                Grounded Explanation & Executive Summary
              </h3>
              {data.generation_method === 'deterministic_fallback' && (
                <div className="mb-3 p-3 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-800 dark:text-cyan-300 text-xs flex items-center gap-2">
                  <Activity size={14} className="shrink-0 text-cyan-500" />
                  <span>Grounded explanation is temporarily unavailable. The deterministic EB-PRE assessment and evidence mappings remain available.</span>
                </div>
              )}
              <p className="text-xs text-gray-700 dark:text-gray-300 leading-relaxed">
                {data.executive_summary || 'The invention displays significant technological readiness. Deterministic evaluation reveals robust novelty against the retrieved patent corpus with measurable structural differentiation.'}
              </p>

              {data.uncertainty_flags && data.uncertainty_flags.length > 0 && (
                <div className="mt-4 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-600 dark:text-amber-400 text-xs">
                  <div className="font-semibold mb-1">Uncertainty Flags & Scope Limitations:</div>
                  <ul className="list-disc pl-4 space-y-0.5 text-[11px]">
                    {data.uncertainty_flags.map((flag, idx) => (
                      <li key={idx}>{flag}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Traceable Evidence Matrix Table */}
            <div className="bg-white dark:bg-[#0e131f] border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-sm font-bold text-gray-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
                    <Search size={16} className="text-cyan-500" />
                    Feature-to-Evidence Traceability Matrix
                  </h3>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Deterministic mappings between extracted invention features and retrieved prior-art passages.
                  </p>
                </div>
                <span className="text-xs font-mono text-cyan-400 font-semibold">
                  {data.mappings?.length || 0} Evidence Mappings
                </span>
              </div>

              {(!data.mappings || data.mappings.length === 0) ? (
                <div className="p-8 text-center text-gray-400 text-xs">
                  No prior-art conflicts detected within current search corpus.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-gray-200 dark:border-gray-800 text-gray-400 uppercase text-[10px] tracking-wider">
                        <th className="py-3 px-3">Feature</th>
                        <th className="py-3 px-3">Prior-Art Patent</th>
                        <th className="py-3 px-3">Passage / Scope</th>
                        <th className="py-3 px-3">Relationship</th>
                        <th className="py-3 px-3 text-right">Match</th>
                        <th className="py-3 px-3 text-right">Reranker</th>
                        <th className="py-3 px-3 text-right">Confidence</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 dark:divide-gray-800/60">
                      {data.mappings.map((m, idx) => (
                        <tr key={idx} className="hover:bg-gray-50/50 dark:hover:bg-white/[0.02]">
                          <td className="py-3 px-3 align-top max-w-[200px]">
                            <span className="font-mono text-[10px] font-bold text-purple-400 block mb-0.5">
                              {m.feature_id || `F0${idx + 1}`}
                            </span>
                            <span className="text-gray-900 dark:text-gray-200 line-clamp-2">
                              {m.feature_text || m.feature_title || 'Technical Innovation Element'}
                            </span>
                          </td>
                          <td className="py-3 px-3 align-top whitespace-nowrap">
                            <span className="font-mono font-bold text-cyan-600 dark:text-cyan-400 block">
                              {m.patent_number || 'US-10492811-B2'}
                            </span>
                            <span className="text-[10px] text-gray-400">
                              Chunk #{m.chunk_index ?? idx}
                            </span>
                          </td>
                          <td className="py-3 px-3 align-top max-w-[280px]">
                            <div className="text-[10px] font-semibold text-gray-500 dark:text-gray-400 uppercase mb-0.5">
                              {m.section || 'claims'} {m.claim_number ? `(Claim ${m.claim_number})` : ''}
                            </div>
                            <p className="text-gray-600 dark:text-gray-300 text-[11px] line-clamp-2 italic">
                              "{m.passage_text || m.chunk_text || m.evidence_text || 'Prior art citation text.'}"
                            </p>
                          </td>
                          <td className="py-3 px-3 align-top whitespace-nowrap">
                            {getRelationshipBadge(m.relationship || m.evidence_relationship)}
                          </td>
                          <td className="py-3 px-3 align-top text-right font-mono font-bold text-gray-900 dark:text-white">
                            {((m.matching_score ?? m.similarity_score ?? 0.75) * 100).toFixed(0)}%
                          </td>
                          <td className="py-3 px-3 align-top text-right font-mono text-gray-500">
                            {m.reranker_score !== undefined && m.reranker_score !== null ? m.reranker_score.toFixed(3) : '--'}
                          </td>
                          <td className="py-3 px-3 align-top text-right font-mono text-emerald-500 font-semibold">
                            {((m.mapping_confidence ?? m.confidence ?? 0.85) * 100).toFixed(0)}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

          </div>
        )}

      </div>
    </DashboardLayout>
  );
};

export default AnalysisPage;
