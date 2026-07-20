import React from 'react';
import { Check, Search, Brain, FileText, Star, Shield, Network } from 'lucide-react';
import { motion } from 'framer-motion';

const PatentBlueprintVisual = () => {
  const cards = [
    {
      icon: <Brain size={24} className="text-purple-500" />,
      title: "Innovation Extracted",
      status: "Core Idea Identified",
      statusColor: "text-purple-600 dark:text-purple-400",
      delay: 0,
      bg: "bg-purple-50 dark:bg-purple-900/10",
      borderColor: "border-purple-200 dark:border-purple-500/20"
    },
    {
      icon: <Search size={24} className="text-blue-500" />,
      title: "Similar Patents Retrieved",
      status: "12 Related Patents Found",
      statusColor: "text-blue-600 dark:text-blue-400",
      delay: 0.2,
      bg: "bg-blue-50 dark:bg-blue-900/10",
      borderColor: "border-blue-200 dark:border-blue-500/20"
    },
    {
      icon: <Shield size={24} className="text-teal-500" />,
      title: "Novelty Analyzed",
      status: "Uniqueness Evaluated",
      statusColor: "text-teal-600 dark:text-teal-400",
      delay: 0.4,
      bg: "bg-teal-50 dark:bg-teal-900/10",
      borderColor: "border-teal-200 dark:border-teal-500/20"
    },
    {
      icon: <Star size={24} className="text-amber-500" />,
      title: "Patent Potential",
      status: "87/100",
      statusColor: "text-amber-600 dark:text-amber-400",
      delay: 0.6,
      bg: "bg-amber-50 dark:bg-amber-900/10",
      borderColor: "border-amber-200 dark:border-amber-500/20"
    },
    {
      icon: <FileText size={24} className="text-emerald-500" />,
      title: "AI Report",
      status: "Ready to Download",
      statusColor: "text-emerald-600 dark:text-emerald-400",
      delay: 0.8,
      bg: "bg-emerald-50 dark:bg-emerald-900/10",
      borderColor: "border-emerald-200 dark:border-emerald-500/20"
    }
  ];

  return (
    <div className="relative w-full max-w-[650px] aspect-[4/3] lg:h-[600px] flex items-center justify-center mx-auto">
      
      {/* Background glow */}
      <div className="absolute inset-0 bg-blue-500/5 blur-[100px] rounded-full pointer-events-none"></div>

      <div className="relative w-full h-full flex flex-col items-center justify-center gap-4 z-10 p-4">
        
        {/* Core AI Node */}
        <motion.div 
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="absolute right-0 lg:right-10 top-1/2 -translate-y-1/2 w-48 h-48 hidden md:flex items-center justify-center"
        >
          <div className="absolute inset-0 bg-cyan-500/10 rounded-full animate-pulse blur-2xl"></div>
          <div className="w-24 h-24 bg-white dark:bg-[#111621] border border-cyan-200 dark:border-cyan-800 rounded-full flex items-center justify-center shadow-[0_0_40px_rgba(34,211,238,0.2)] z-10 relative">
            <Network size={40} className="text-cyan-500" />
            <div className="absolute -inset-2 border border-cyan-500/30 rounded-full animate-spin-slow border-t-transparent"></div>
          </div>
        </motion.div>

        {/* Workflow Cards */}
        <div className="w-full max-w-sm flex flex-col gap-4 relative z-20 md:mr-32">
          {cards.map((card, idx) => (
            <motion.div
              key={idx}
              initial={{ x: -50, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: card.delay, duration: 0.6, ease: "easeOut" }}
              className="bg-white/90 dark:bg-[#111621]/90 backdrop-blur-lg border border-gray-100 dark:border-gray-800 rounded-xl p-4 flex items-center gap-4 shadow-xl hover:-translate-y-1 transition-transform duration-300"
            >
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${card.bg} border ${card.borderColor}`}>
                {card.icon}
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-bold text-gray-900 dark:text-white mb-1">{card.title}</h3>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-medium text-gray-500 uppercase tracking-wide">Status:</span>
                  <span className={`text-[11px] font-bold ${card.statusColor} flex items-center gap-1`}>
                    {card.status} <Check size={12} strokeWidth={3} />
                  </span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

      </div>
    </div>
  );
};

export default PatentBlueprintVisual;
