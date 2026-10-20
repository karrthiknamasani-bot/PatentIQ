import React, { useState } from 'react';
import DashboardLayout from '../layouts/DashboardLayout';
import {
  Search,
  History,
  Sparkles,
  Loader2,
  FileText,
  Layers,
  Award,
  ExternalLink,
  Sliders,
  CheckCircle2,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../api/axios';
import toast from 'react-hot-toast';

const SearchPage = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [useRerank, setUseRerank] = useState(false);
  const [activeTab, setActiveTab] = useState('all');

  const handleSearch = async (e, searchQuery = query) => {
    e?.preventDefault();
    if (!searchQuery.trim()) return;

    setQuery(searchQuery);
    setLoading(true);

    try {
      // First attempt hybrid search with both sparse and dense
      let res;
      try {
        res = await api.post('/retrieval/search', {
          query: searchQuery,
          top_k: 10,
          methods: ['sparse', 'dense'],
          rerank: useRerank,
        });
      } catch (denseErr) {
        // If dense retrieval/Qdrant is unconfigured or unreachable, gracefully fallback to BM25 sparse
        console.warn('Dense retrieval failed, attempting sparse BM25 retrieval:', denseErr);
        res = await api.post('/retrieval/search', {
          query: searchQuery,
          top_k: 10,
          methods: ['sparse'],
          rerank: false,
        });
      }

      const data = res.data;
      setResults(data);
      toast.success('Prior-art retrieval completed');
    } catch (err) {
      console.error('Search failed:', err);
      toast.error('Search failed: ' + (err.response?.data?.detail || err.message));
      setResults(null);
    } finally {
      setLoading(false);
    }
  };

  // Compile combined candidate list
  const getCandidateList = () => {
    if (!results) return [];
    if (activeTab === 'reranked' && results.reranked_results) return results.reranked_results;
    if (activeTab === 'hybrid' && results.hybrid_results) return results.hybrid_results;
    if (activeTab === 'dense' && results.dense_results) return results.dense_results;
    if (activeTab === 'sparse' && results.sparse_results) return results.sparse_results;

    // 'all' tab: prioritize reranked, then hybrid, then sparse + dense combined
    if (results.reranked_results && results.reranked_results.length > 0) {
      return results.reranked_results;
    }
    if (results.hybrid_results && results.hybrid_results.length > 0) {
      return results.hybrid_results;
    }
    const combined = [
      ...(results.sparse_results || []),
      ...(results.dense_results || []),
    ];
    return combined;
  };

  const candidateList = getCandidateList();

  return (
    <DashboardLayout>
      <div className="w-full pt-6 pb-20 max-w-5xl mx-auto">
        {/* Search Header */}
        <motion.div
          initial={{ opacity: 0, y: -15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="text-center mb-8"
        >
          <div className="inline-block px-3 py-1 bg-cyan-50 dark:bg-cyan-950/40 text-cyan-600 dark:text-cyan-400 border border-cyan-200 dark:border-cyan-800/60 rounded-full text-xs font-bold uppercase tracking-wider mb-3">
            BM25 + BGE Dense + Cross-Encoder Reranking
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold text-gray-900 dark:text-white tracking-tight mb-2">
            Prior-Art Corpus Search
          </h1>
          <p className="text-gray-600 dark:text-gray-400 text-sm max-w-xl mx-auto">
            Search verified patent disclosures and claim text using dense semantic vectors and lexical BM25.
          </p>
        </motion.div>

        {/* Big Search Bar */}
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3, delay: 0.1 }}
          className="relative z-10 w-full mb-8"
        >
          <form
            onSubmit={handleSearch}
            className="bg-white dark:bg-[#111621] border-2 border-gray-200 dark:border-gray-800 hover:border-gray-300 dark:hover:border-gray-700 rounded-2xl p-2 pl-5 flex items-center shadow-md focus-within:border-cyan-500/50 transition-all group"
          >
            <Search
              className="text-gray-400 dark:text-gray-500 group-focus-within:text-cyan-600 dark:group-focus-within:text-cyan-400 transition-colors mr-3 shrink-0"
              size={22}
            />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Describe a technical invention, architectural feature, or claim..."
              className="bg-transparent border-none w-full text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-600 focus:outline-none text-base font-medium"
            />
            <button
              type="submit"
              disabled={loading}
              className="bg-cyan-600 hover:bg-cyan-700 text-white px-6 py-3 rounded-xl text-sm font-bold transition-all shadow-md flex items-center gap-2 shrink-0 disabled:opacity-50"
            >
              {loading ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
              {loading ? 'Searching...' : 'Search'}
            </button>
          </form>

          {/* Quick options & presets */}
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-2">
              <span className="text-gray-500 font-medium flex items-center gap-1">
                <History size={14} /> Examples:
              </span>
              <button
                onClick={(e) => handleSearch(e, 'quantum error correction surface codes')}
                className="bg-gray-100 dark:bg-[#1a2133] hover:bg-gray-200 dark:hover:bg-[#232c45] border border-gray-200 dark:border-gray-800 text-gray-700 dark:text-gray-300 px-3 py-1 rounded-full text-xs transition-colors"
              >
                Quantum error correction
              </button>
              <button
                onClick={(e) => handleSearch(e, 'distributed consensus ledger synchronization')}
                className="bg-gray-100 dark:bg-[#1a2133] hover:bg-gray-200 dark:hover:bg-[#232c45] border border-gray-200 dark:border-gray-800 text-gray-700 dark:text-gray-300 px-3 py-1 rounded-full text-xs transition-colors"
              >
                Consensus ledger
              </button>
              <button
                onClick={(e) => handleSearch(e, 'transformer self-attention hardware accelerator')}
                className="bg-gray-100 dark:bg-[#1a2133] hover:bg-gray-200 dark:hover:bg-[#232c45] border border-gray-200 dark:border-gray-800 text-gray-700 dark:text-gray-300 px-3 py-1 rounded-full text-xs transition-colors"
              >
                Attention accelerator
              </button>
            </div>

            <label className="flex items-center gap-2 cursor-pointer select-none text-gray-600 dark:text-gray-400">
              <input
                type="checkbox"
                checked={useRerank}
                onChange={(e) => setUseRerank(e.target.checked)}
                className="w-4 h-4 rounded text-cyan-600 focus:ring-cyan-500"
              />
              <span className="font-semibold text-xs">Apply BGE Cross-Encoder Reranker</span>
            </label>
          </div>
        </motion.div>

        {/* Results Container */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 bg-white dark:bg-[#111621] rounded-2xl border border-gray-200 dark:border-gray-800">
            <Loader2 className="animate-spin text-cyan-500 mb-3" size={36} />
            <p className="text-gray-500 text-sm">Querying patent corpus indices...</p>
          </div>
        ) : results ? (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            {/* Results Filter Tabs */}
            <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-800 pb-3">
              <div className="flex gap-2">
                {[
                  { id: 'all', label: 'All Results' },
                  { id: 'sparse', label: `BM25 (${results.sparse_results?.length || 0})` },
                  { id: 'dense', label: `BGE Dense (${results.dense_results?.length || 0})` },
                  { id: 'hybrid', label: `RRF Hybrid (${results.hybrid_results?.length || 0})` },
                  { id: 'reranked', label: `Reranked (${results.reranked_results?.length || 0})` },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                      activeTab === tab.id
                        ? 'bg-cyan-50 dark:bg-cyan-950/40 text-cyan-700 dark:text-cyan-400 border border-cyan-200 dark:border-cyan-800'
                        : 'text-gray-500 hover:text-gray-900 dark:hover:text-white'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
              <span className="text-xs text-gray-400">
                Top {candidateList.length} passage hits
              </span>
            </div>

            {/* Hit Cards */}
            {candidateList.length === 0 ? (
              <div className="text-center py-12 bg-white dark:bg-[#111621] rounded-2xl border border-gray-200 dark:border-gray-800 text-gray-500 text-sm">
                No results retrieved for this category.
              </div>
            ) : (
              <div className="space-y-4">
                {candidateList.map((item, idx) => {
                  const patNum = item.patent_number || item.metadata?.patent_number || `Citation ${idx + 1}`;
                  const score =
                    item.reranker_score !== undefined
                      ? `Reranker: ${item.reranker_score.toFixed(3)}`
                      : item.rrf_score !== undefined
                      ? `RRF: ${item.rrf_score.toFixed(4)}`
                      : item.retrieval_score !== undefined
                      ? `Score: ${item.retrieval_score.toFixed(3)}`
                      : 'Candidate';

                  const method = item.retrieval_method || 'hybrid_rrf';

                  return (
                    <div
                      key={idx}
                      className="bg-white dark:bg-[#111621] border border-gray-200 dark:border-gray-800 rounded-xl p-5 shadow-sm hover:border-cyan-500/40 transition-all text-xs"
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3 pb-2 border-b border-gray-100 dark:border-gray-800/60">
                        <div className="flex items-center gap-2 font-mono">
                          <span className="font-bold text-sm text-cyan-600 dark:text-cyan-400">
                            {patNum}
                          </span>
                          <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-[10px] text-gray-600 dark:text-gray-300 uppercase">
                            Section: {item.section || 'description'}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded font-mono font-bold bg-cyan-50 dark:bg-cyan-950/40 text-cyan-700 dark:text-cyan-300 text-[11px]">
                            {score}
                          </span>
                          <span className="px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-500 text-[10px]">
                            {method}
                          </span>
                        </div>
                      </div>

                      {item.metadata?.title && (
                        <h4 className="font-bold text-sm text-gray-900 dark:text-white mb-2">
                          {item.metadata.title}
                        </h4>
                      )}

                      <p className="text-gray-700 dark:text-gray-300 leading-relaxed font-sans line-clamp-4 hover:line-clamp-none transition-all">
                        {item.text}
                      </p>

                      {item.metadata && Object.keys(item.metadata).length > 0 && (
                        <div className="mt-3 pt-2 flex flex-wrap items-center gap-3 text-[10px] text-gray-400 font-mono">
                          {item.metadata.assignee && <span>Assignee: {item.metadata.assignee}</span>}
                          {item.metadata.date && <span>Pub Date: {item.metadata.date}</span>}
                          {item.metadata.cpc && <span>CPC: {item.metadata.cpc}</span>}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </motion.div>
        ) : null}
      </div>
    </DashboardLayout>
  );
};

export default SearchPage;
