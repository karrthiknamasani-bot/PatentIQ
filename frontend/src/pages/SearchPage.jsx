import React, { useState } from 'react';
import DashboardLayout from '../layouts/DashboardLayout';
import { Search, History, Sparkles, Loader2, FileText } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../api/axios';
import toast from 'react-hot-toast';

const SearchPage = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (e, searchQuery = query) => {
    e?.preventDefault();
    if (!searchQuery.trim()) return;
    
    setQuery(searchQuery);
    setLoading(true);
    
    try {
      const { data } = await api.post('/search/similar', { query: searchQuery, topK: 5 });
      if (data.success) {
        // Chroma returns results usually nested inside arrays.
        // Assuming data.data looks like standard Chroma results, we'll format it.
        // If data.data is already an array of formatted results from the backend, we use it.
        const resData = data.data;
        let formatted = [];
        
        if (Array.isArray(resData)) {
          formatted = resData;
        } else if (resData.ids && resData.ids[0]) {
           // Chroma format: { ids: [[]], documents: [[]], metadatas: [[]], distances: [[]] }
           formatted = resData.ids[0].map((id, index) => ({
             id,
             document: resData.documents[0][index],
             metadata: resData.metadatas[0][index],
             distance: resData.distances[0][index]
           }));
        }
        setResults(formatted);
      }
    } catch (err) {
      console.error(err);
      toast.error('Search failed');
      setResults([]);
    } finally {
      setLoading(false);
    }
  };
  return (
    <DashboardLayout>
      {/* Removed absolutely positioned Recent Searches button, moving it to the content area */}

      <div className="w-full pt-8 pb-12">
        {/* Search Header */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="text-center mb-10"
        >
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2 tracking-tight">
            Discover the <span className="text-cyan-600 dark:text-cyan-400 drop-shadow-[0_0_15px_rgba(34,211,238,0.2)] dark:drop-shadow-[0_0_15px_rgba(34,211,238,0.5)]">Next Horizon</span>
          </h1>
        </motion.div>

        {/* Big Search Bar */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3, delay: 0.1 }}
          className="relative z-10 w-full mb-12"
        >
          <form onSubmit={handleSearch} className="bg-white/80 dark:bg-[#111621]/80 backdrop-blur-md border-2 border-gray-200 dark:border-gray-800 hover:border-gray-300 dark:hover:border-gray-700 rounded-2xl p-2 pl-6 flex items-center shadow-[0_10px_40px_rgba(0,0,0,0.05)] dark:shadow-[0_10px_40px_rgba(0,0,0,0.3)] focus-within:shadow-[0_10px_50px_rgba(34,211,238,0.15)] focus-within:border-cyan-500/50 transition-all duration-500 group">
            <Search className="text-gray-400 dark:text-gray-500 group-focus-within:text-cyan-600 dark:group-focus-within:text-cyan-400 transition-colors duration-300 mr-4 shrink-0" size={24} />
            <input 
              type="text" 
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Describe a technology or problem in natural language..." 
              className="bg-transparent border-none w-full text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-600 focus:outline-none text-lg font-medium"
            />
            <div className="flex items-center gap-3 shrink-0">
              <div className="hidden sm:flex border border-gray-200 dark:border-gray-700 rounded px-2 py-1 text-gray-500 text-xs font-mono bg-gray-50 dark:bg-[#141a27] font-medium tracking-wide">
                ↵
              </div>
              <button 
                type="submit"
                disabled={loading}
                className="bg-cyan-600 hover:bg-cyan-700 dark:bg-cyan-500 dark:hover:bg-cyan-400 text-white dark:text-black px-8 py-3.5 rounded-lg text-[14px] font-bold transition-all duration-300 shadow-[0_0_15px_rgba(34,211,238,0.15)] dark:shadow-[0_0_15px_rgba(34,211,238,0.3)] hover:-translate-y-0.5 flex items-center gap-2 disabled:opacity-50"
              >
                {loading ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
                {loading ? 'Searching...' : 'Discover'}
              </button>
            </div>
          </form>
          
          <div className="mt-6 flex flex-wrap items-center justify-center gap-3 text-sm">
            <span className="text-gray-500 font-medium mr-2 flex items-center gap-2"><History size={16}/> Recent:</span>
            <button onClick={(e) => handleSearch(e, 'Quantum error correction')} className="bg-white dark:bg-[#1a2133] hover:bg-gray-50 dark:hover:bg-[#232c45] border border-gray-200 dark:border-gray-800 hover:border-gray-300 dark:hover:border-gray-600 text-gray-600 dark:text-gray-300 px-4 py-1.5 rounded-full text-xs font-medium transition-colors shadow-sm dark:shadow-none">Quantum error correction</button>
            <button onClick={(e) => handleSearch(e, 'Solid-state battery cooling')} className="bg-white dark:bg-[#1a2133] hover:bg-gray-50 dark:hover:bg-[#232c45] border border-gray-200 dark:border-gray-800 hover:border-gray-300 dark:hover:border-gray-600 text-gray-600 dark:text-gray-300 px-4 py-1.5 rounded-full text-xs font-medium transition-colors shadow-sm dark:shadow-none">Solid-state battery cooling</button>
            <button onClick={(e) => handleSearch(e, 'Non-invasive glucose monitoring')} className="bg-white dark:bg-[#1a2133] hover:bg-gray-50 dark:hover:bg-[#232c45] border border-gray-200 dark:border-gray-800 hover:border-gray-300 dark:hover:border-gray-600 text-gray-600 dark:text-gray-300 px-4 py-1.5 rounded-full text-xs font-medium transition-colors shadow-sm dark:shadow-none">Non-invasive glucose</button>
          </div>
        </motion.div>

        {/* Empty State */}
        <AnimatePresence mode="wait">
          {loading ? (
            <motion.div 
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex justify-center py-20"
            >
              <Loader2 className="animate-spin text-cyan-500" size={40} />
            </motion.div>
          ) : results === null ? (
            <motion.div 
              key="empty"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className="flex flex-col items-center justify-center py-20 text-center"
            >
              <div className="relative mb-6">
                <div className="absolute inset-0 bg-cyan-500/10 dark:bg-cyan-500/20 blur-2xl rounded-full"></div>
                <div className="w-24 h-24 bg-white dark:bg-[#141a27] border border-gray-200 dark:border-gray-800/80 rounded-3xl flex items-center justify-center relative z-10 shadow-lg dark:shadow-2xl">
                  <Search size={36} className="text-gray-400 dark:text-gray-500" strokeWidth={1.5} />
                </div>
              </div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Discover Innovations</h2>
              <p className="text-gray-500 max-w-md">
                Enter a natural language query above to search through millions of global patents using our advanced AI semantic engine.
              </p>
            </motion.div>
          ) : results.length === 0 ? (
            <motion.div 
              key="no-results"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-20 text-gray-500"
            >
              No results found for your query. Try different keywords.
            </motion.div>
          ) : (
            <motion.div
              key="results"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6 max-w-4xl mx-auto"
            >
              <h3 className="text-gray-900 dark:text-white font-bold mb-4">{results.length} results found</h3>
              {results.map((res, index) => (
                <div key={res.id || index} className="bg-white dark:bg-[#141a27] border border-gray-200 dark:border-gray-800 rounded-xl p-6 shadow-sm hover:border-cyan-500/50 transition-colors">
                  <div className="flex justify-between items-start mb-3">
                    <h4 className="text-lg font-bold text-gray-900 dark:text-white">
                      {res.metadata?.title || 'Untitled Document chunk'}
                    </h4>
                    <span className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 rounded font-medium shrink-0">
                      Score: {((1 - (res.distance || 0)) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed mb-4">
                    {res.document?.substring(0, 300)}...
                  </p>
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    <span className="flex items-center gap-1"><FileText size={14}/> {res.metadata?.sourceType || 'Patent'}</span>
                    {res.metadata?.patentId && <span>ID: {res.metadata.patentId}</span>}
                  </div>
                </div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>

      </div>
    </DashboardLayout>
  );
};

export default SearchPage;
