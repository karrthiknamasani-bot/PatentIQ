import React, { useState, useRef } from 'react';
import DashboardLayout from '../layouts/DashboardLayout';
import { UploadCloud, FileText, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../api/axios';
import toast from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';

const UploadPage = () => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingStatus, setProcessingStatus] = useState(null);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

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

  const pollStatus = async (projectId) => {
    try {
      const { data } = await api.get(`/process/${projectId}/status`);
      if (data.success) {
        setProcessingStatus(data.data.processingStage);
        setUploadProgress(data.data.progress || 0);

        if (data.data.status === 'completed' || data.data.status === 'failed') {
          setIsUploading(false);
          setUploadProgress(100);
          if (data.data.status === 'completed') {
            toast.success('Document imported and parsed successfully!');
            navigate(`/analysis?id=${projectId}`);
          } else {
            toast.error(data.data.processingError || data.data.errorMessage || 'Document processing failed');
          }
        } else {
          setTimeout(() => pollStatus(projectId), 2000);
        }
      }
    } catch (err) {
      console.error(err);
      toast.error('Failed to get status');
      setIsUploading(false);
    }
  };

  const handleFileUpload = async (file) => {
    if (!file) return;
    
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    if (!allowedTypes.includes(file.type)) {
      return toast.error('Only PDF, DOCX, and TXT files are supported');
    }

    if (file.size > 50 * 1024 * 1024) {
      return toast.error('File size must be under 50MB');
    }

    const formData = new FormData();
    formData.append('document', file);
    formData.append('title', file.name.split('.')[0]);

    setIsUploading(true);
    setUploadProgress(0);
    setProcessingStatus('uploading');

    try {
      const { data } = await api.post('/projects/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percentCompleted);
        }
      });
      
      if (data.success) {
        setProcessingStatus('queued');
        setUploadProgress(5);
        pollStatus(data.data._id);
      }
    } catch (err) {
      toast.error(err.response?.data?.message || 'Upload failed');
      setIsUploading(false);
      setProcessingStatus(null);
    }
  };

  return (
    <DashboardLayout>
      <div className="w-full pt-4 pb-12">
        <motion.div 
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2 tracking-tight">Upload Project</h1>
          <p className="text-gray-500 dark:text-gray-400">Upload your project report, research paper, or technical documentation for AI-powered Patent Potential Analysis.</p>
        </motion.div>

        {/* Upload Zone */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`w-full border-2 border-dashed rounded-2xl p-12 flex flex-col items-center justify-center transition-all duration-300 bg-white/50 dark:bg-[#111621]/50 backdrop-blur-sm
            ${isDragging 
              ? 'border-cyan-500 bg-cyan-50/50 dark:bg-cyan-900/10 scale-[1.01]' 
              : 'border-gray-300 dark:border-gray-800 hover:border-cyan-400 dark:hover:border-gray-700'
            }`}
        >
          <div className="w-20 h-20 bg-gray-100 dark:bg-[#161b26] rounded-full flex items-center justify-center mb-6 shadow-inner">
            <UploadCloud size={36} className={isDragging ? "text-cyan-500" : "text-gray-400 dark:text-gray-500"} strokeWidth={1.5} />
          </div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
            Click to upload or drag and drop
          </h3>
          <p className="text-gray-500 dark:text-gray-400 text-sm mb-6 text-center max-w-sm">
            Supported formats: PDF, DOCX, TXT. Maximum file size: 50MB.
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
            className="bg-cyan-600 hover:bg-cyan-700 dark:bg-cyan-500 dark:hover:bg-cyan-400 text-white dark:text-black px-8 py-3.5 rounded-lg text-[14px] font-bold transition-all duration-300 shadow-md shadow-cyan-600/20 dark:shadow-[0_0_15px_rgba(34,211,238,0.2)] hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isUploading ? 'Uploading...' : 'Browse Files'}
          </button>
        </motion.div>

        {/* Processing Indicator */}
        <AnimatePresence>
          {isUploading && (
            <motion.div 
              initial={{ opacity: 0, y: 10, height: 0 }}
              animate={{ opacity: 1, y: 0, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-8 bg-white dark:bg-[#111621] border border-gray-200 dark:border-gray-800 rounded-xl p-6 shadow-sm"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <Loader2 className="animate-spin text-cyan-500" size={20} />
                  <h3 className="font-bold text-gray-900 dark:text-white">
                    {processingStatus === 'uploading' && `Uploading... ${uploadProgress}%`}
                    {processingStatus === 'queued' && 'Queued for processing...'}
                    {processingStatus === 'parsing' && 'Parsing Document...'}
                    {processingStatus === 'cleaning' && 'Cleaning Text...'}
                    {processingStatus === 'chunking' && 'Chunking Text...'}
                    {processingStatus === 'embedding' && 'Generating Embeddings...'}
                    {processingStatus === 'analyzing' && 'Running AI Analysis...'}
                    {processingStatus === 'completed' && 'Analysis Complete!'}
                  </h3>
                </div>
              </div>
              <div className="w-full bg-gray-100 dark:bg-gray-800 rounded-full h-2 mb-2 overflow-hidden">
                <div 
                  className="bg-cyan-500 h-2 rounded-full transition-all duration-500 ease-out" 
                  style={{ width: `${uploadProgress}%` }}
                >
                  {processingStatus !== 'uploading' && (
                    <div className="w-full h-full bg-cyan-400/30 animate-pulse"></div>
                  )}
                </div>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                This process involves OCR, NLP chunking, semantic embedding, and vector storage. It may take a minute.
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Upload History */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mt-12"
        >
          <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-6">Recent Uploads</h2>
          
          <div className="bg-white dark:bg-[#111621] border border-gray-200 dark:border-gray-800 rounded-xl overflow-hidden shadow-sm dark:shadow-none">
            {/* Empty State for History */}
            <div className="p-12 flex flex-col items-center justify-center text-center">
              <div className="w-16 h-16 bg-gray-50 dark:bg-[#161b26] rounded-full flex items-center justify-center mb-4">
                <FileText size={24} className="text-gray-400" />
              </div>
              <h3 className="text-gray-900 dark:text-white font-medium mb-1">No uploads yet</h3>
              <p className="text-gray-500 dark:text-gray-400 text-sm">Your recently uploaded projects will appear here.</p>
            </div>
          </div>
        </motion.div>

      </div>
    </DashboardLayout>
  );
};

export default UploadPage;
