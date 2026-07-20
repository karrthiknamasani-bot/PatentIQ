import React, { useState, useEffect } from 'react';
import DashboardLayout from '../layouts/DashboardLayout';
import { FileText, Download, CheckCircle2, ShieldAlert, Sparkles, Brain, Search, Loader2, FileCheck } from 'lucide-react';
import { motion } from 'framer-motion';
import { useSearchParams, useNavigate } from 'react-router-dom';
import api from '../api/axios';
import toast from 'react-hot-toast';

const ReportsPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const projectId = searchParams.get('id');

  const [analysisData, setAnalysisData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    if (projectId) {
      fetchAnalysis(projectId);
    } else {
      setLoading(false);
    }
  }, [projectId]);

  const fetchAnalysis = async (id) => {
    try {
      const { data } = await api.get(`/analyze/${id}`);
      if (data.success) {
        setAnalysisData(data.data);
      }
    } catch (err) {
      console.error(err);
      toast.error('Failed to load report data');
    } finally {
      setLoading(false);
    }
  };

  const handleExportPDF = async () => {
    if (!projectId) return;
    setExporting(true);
    try {
      const { data } = await api.post(`/report/${projectId}`, { type: 'pdf' });
      if (data.success && data.data?._id) {
        toast.success('Report generated successfully, starting download...');
        // Need auth token for downloading if it's protected, but res.download requires browser handling.
        // Easiest is to trigger a fetch as blob and then save it.
        const token = localStorage.getItem('token');
        const response = await fetch(`http://localhost:5001/api/report/${data.data._id}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (!response.ok) throw new Error('Download failed');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `PatentIQ_Report_${projectId}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
      }
    } catch (err) {
      console.error(err);
      toast.error('Failed to export PDF');
    } finally {
      setExporting(false);
    }
  };
  const handleExportJSON = async () => {
    if (!projectId) return;
    setExporting(true);
    try {
      const { data } = await api.post(`/report/${projectId}`, { type: 'json' });
      if (data.success && data.data?._id) {
        toast.success('JSON generated successfully, starting download...');
        const token = localStorage.getItem('token');
        const response = await fetch(`http://localhost:5001/api/report/${data.data._id}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (!response.ok) throw new Error('Download failed');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `PatentIQ_Report_${projectId}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
      }
    } catch (err) {
      console.error(err);
      toast.error('Failed to export JSON');
    } finally {
      setExporting(false);
    }
  };

  const ReportSection = ({ title, icon: Icon, children }) => (
    <div className="mb-10 last:mb-0">
      <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2 border-b border-gray-200 dark:border-gray-800 pb-2">
        <Icon size={18} className="text-cyan-600 dark:text-cyan-400" />
        {title}
      </h3>
      <div className="text-gray-600 dark:text-gray-400 text-[14px] leading-relaxed">
        {children}
      </div>
    </div>
  );

  return (
    <DashboardLayout>
      <div className="w-full pt-4 pb-20 max-w-4xl mx-auto">
        
        {/* Header Action */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
          <div>
            <div className="flex items-center gap-2 text-[10px] text-gray-500 font-bold uppercase tracking-widest mb-2">
              <span>Intelligence Engine</span>
              <span>/</span>
              <span className="text-cyan-400">Reports</span>
            </div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Patent Potential Report</h1>
            <p className="text-gray-600 dark:text-gray-400 text-sm">Project ID: {projectId || 'None'} • Generated: {new Date().toLocaleDateString()}</p>
          </div>
          {analysisData && (
            <div className="flex items-center gap-3">
              <button 
                onClick={handleExportJSON}
                disabled={exporting}
                className="flex items-center gap-2 bg-white dark:bg-[#1a2133] hover:bg-gray-50 dark:hover:bg-[#232c45] border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white px-4 py-2.5 rounded-lg font-bold transition-all shadow-sm text-sm disabled:opacity-50"
              >
                {exporting ? <Loader2 size={16} className="animate-spin" /> : <FileText size={16} />} 
                JSON
              </button>
              <button 
                onClick={handleExportPDF}
                disabled={exporting}
                className="flex items-center gap-2 bg-cyan-600 hover:bg-cyan-700 text-white px-5 py-2.5 rounded-lg font-bold transition-all shadow-md text-sm disabled:opacity-50"
              >
                {exporting ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />} 
                {exporting ? 'Generating...' : 'Export as PDF'}
              </button>
            </div>
          )}
        </div>

        {loading ? (
          <div className="flex justify-center py-20">
            <Loader2 className="animate-spin text-cyan-500" size={40} />
          </div>
        ) : !analysisData ? (
          <div className="text-center py-20 bg-white dark:bg-[#111621] rounded-2xl border border-gray-200 dark:border-gray-800">
            <FileText size={48} className="mx-auto text-gray-400 mb-4" />
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">No Report Available</h2>
            <p className="text-gray-500 mb-6">Upload a project and complete analysis to view reports.</p>
            <button onClick={() => navigate('/upload')} className="bg-cyan-600 text-white px-6 py-2 rounded-lg font-bold">
              Upload Project
            </button>
          </div>
        ) : (
          /* The Report Document View */
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white dark:bg-[#111621] border border-gray-200 dark:border-gray-800 rounded-2xl p-8 md:p-12 shadow-xl dark:shadow-none"
          >
          {/* Document Header */}
          <div className="text-center mb-12">
            <h2 className="text-2xl font-black text-gray-900 dark:text-white uppercase tracking-tight">AI Patent Potential Assessment</h2>
            <div className="w-16 h-1 bg-cyan-500 mx-auto mt-4 rounded-full"></div>
          </div>

          <ReportSection title="Executive Summary" icon={FileText}>
            <p>{analysisData?.analysis?.executiveSummary || 'Executive summary not available.'}</p>
          </ReportSection>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-10">
            <ReportSection title="Project Summary" icon={FileCheck}>
              <p><strong>Status:</strong> {analysisData?.status}</p>
              <p><strong>Model:</strong> {analysisData?.modelUsed}</p>
              <p><strong>Processed in:</strong> {(analysisData?.processingTimeMs / 1000).toFixed(1)}s</p>
            </ReportSection>
            
            <ReportSection title="Final Verdict" icon={CheckCircle2}>
              <div className="bg-emerald-50 dark:bg-emerald-900/10 border border-emerald-200 dark:border-emerald-800/50 rounded-lg p-4 text-center">
                <h4 className="font-bold text-emerald-700 dark:text-emerald-400 mb-1 text-lg uppercase">{analysisData?.analysis?.recommendation || 'Assessment Complete'}</h4>
                <p className="text-emerald-600 dark:text-emerald-500 text-xs font-medium">Patent Potential Score: {analysisData?.scores?.noveltyScore || '--'}/100</p>
              </div>
            </ReportSection>
          </div>

          <ReportSection title="Innovation Analysis & Novel Features" icon={Brain}>
            <ul className="list-disc pl-5 space-y-2">
              {analysisData?.analysis?.innovationScore?.keyInnovations?.map((inn, i) => (
                <li key={i}><strong>Innovation {i + 1}:</strong> {inn}</li>
              )) || <li>No distinct innovations identified.</li>}
            </ul>
          </ReportSection>

          <ReportSection title="Similar Patent Analysis & Similarity Breakdown" icon={Search}>
            <p className="mb-4">{analysisData?.retrievedPatents?.length || 0} related patents were retrieved via semantic search. Similarity score is {analysisData?.scores?.similarityScore || '--'}%.</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
              <div className="p-3 border border-gray-200 dark:border-gray-800 rounded bg-gray-50 dark:bg-gray-800/30">
                <span className="text-xs font-bold uppercase text-gray-500 block mb-1">Matched (Prior Art)</span>
                {analysisData?.analysis?.similarityAnalysis?.keyOverlaps?.map((overlap, i) => <div key={i}>• {overlap}</div>) || 'No major overlaps'}
              </div>
              <div className="p-3 border border-emerald-200 dark:border-emerald-800/50 rounded bg-emerald-50 dark:bg-emerald-900/10">
                <span className="text-xs font-bold uppercase text-emerald-600 dark:text-emerald-400 block mb-1">Unique (Your Project)</span>
                {analysisData?.analysis?.similarityAnalysis?.keyDifferences?.map((diff, i) => <div key={i}>• {diff}</div>) || 'Highly unique'}
              </div>
            </div>
          </ReportSection>

          <ReportSection title="AI Recommendations & Improvement Roadmap" icon={Sparkles}>
            <div className="space-y-4">
              {analysisData?.analysis?.improvementSuggestions?.map((sug, i) => (
                <div key={i} className="flex gap-3">
                  <div className="w-6 h-6 rounded-full bg-cyan-100 dark:bg-cyan-900/50 text-cyan-600 dark:text-cyan-400 flex items-center justify-center shrink-0 font-bold text-xs mt-0.5">{i + 1}</div>
                  <div>
                    <h4 className="font-bold text-gray-800 dark:text-gray-200 text-sm">Suggested Improvement</h4>
                    <p className="text-xs mt-1">{sug}</p>
                  </div>
                </div>
              ))}
              {(!analysisData?.analysis?.improvementSuggestions || analysisData.analysis.improvementSuggestions.length === 0) && (
                <p>No further improvements suggested.</p>
              )}
            </div>
          </ReportSection>

          <ReportSection title="Technical & Risk Analysis" icon={ShieldAlert}>
            <p className="mb-2"><strong>Technical Analysis:</strong> {analysisData?.analysis?.technicalAnalysis || 'N/A'}</p>
            <p><strong>Identified Risks:</strong></p>
            <ul className="list-disc pl-5 mt-1">
              {analysisData?.analysis?.risks?.map((risk, i) => (
                <li key={i}>{risk}</li>
              )) || <li>No risks identified.</li>}
            </ul>
          </ReportSection>

        </motion.div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default ReportsPage;
