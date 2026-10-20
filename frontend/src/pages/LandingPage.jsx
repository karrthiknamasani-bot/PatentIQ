import React from 'react';
import { Link } from 'react-router-dom';
import {
  Brain,
  Search,
  FileText,
  ArrowRight,
  ShieldAlert,
  GitBranch,
  Layers,
  ChevronRight,
  Activity,
  Compass,
  FileCheck2,
  FileSearch2
} from 'lucide-react';
import ThemeToggle from '../components/ThemeToggle';

const LandingPage = () => {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#050b14] text-gray-900 dark:text-gray-100 font-sans antialiased selection:bg-cyan-500/30 transition-colors duration-300">
      
      {/* Header / Nav */}
      <header className="border-b border-gray-200/80 dark:border-gray-800/80 bg-white/70 dark:bg-[#050b14]/70 backdrop-blur-md sticky top-0 z-50 transition-colors duration-300">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-1.5 hover:opacity-90 transition-opacity">
            <span className="text-xl font-black tracking-tighter text-gray-900 dark:text-white">
              Patent<span className="text-cyan-600 dark:text-cyan-400">IQ</span>
            </span>
          </Link>
          
          <div className="flex items-center gap-6">
            <ThemeToggle />
            <Link 
              to="/login" 
              className="text-sm font-semibold text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              Sign In
            </Link>
            <Link 
              to="/register" 
              className="bg-cyan-600 hover:bg-cyan-700 dark:bg-cyan-500 dark:hover:bg-cyan-400 text-white dark:text-black px-4.5 py-2 rounded-lg text-sm font-bold transition-all shadow-md shadow-cyan-600/10 dark:shadow-[0_0_15px_rgba(34,211,238,0.15)]"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      <main className="w-full">
        {/* Banner Disclaimer */}
        <div className="bg-amber-50 dark:bg-amber-950/20 border-b border-amber-200/60 dark:border-amber-900/30 text-amber-800 dark:text-amber-300 text-xs py-3 px-6 text-center font-medium leading-relaxed">
          <span className="inline-flex items-center gap-1.5">
            <ShieldAlert size={14} className="shrink-0" />
            <strong>Disclaimer:</strong> This is an AI-assisted early-stage assessment and does not constitute legal advice or a determination of patentability.
          </span>
        </div>

        {/* Hero Section */}
        <section className="relative pt-20 pb-24 px-6 max-w-5xl mx-auto text-center overflow-hidden">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_var(--tw-gradient-stops))] from-cyan-500/10 via-transparent to-transparent dark:from-cyan-500/5 pointer-events-none blur-3xl -z-10" />

          <span className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-cyan-50 dark:bg-cyan-950/30 text-cyan-700 dark:text-cyan-400 text-[11px] font-bold tracking-wider uppercase mb-8 border border-cyan-200/50 dark:border-cyan-800/30">
            Evidence-Based AI Assistant
          </span>

          <h1 className="text-4xl md:text-6xl font-black text-gray-900 dark:text-white tracking-tight leading-[1.08] mb-6">
            Understand your invention <br className="hidden md:block" />
            before you invest further.
          </h1>

          <p className="text-base md:text-lg text-gray-600 dark:text-gray-400 max-w-3xl mx-auto mb-10 leading-relaxed font-medium">
            An evidence-based AI system that searches prior art, maps technical features, and provides an explainable early-stage patent readiness assessment.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link 
              to="/register" 
              className="w-full sm:w-auto bg-cyan-600 hover:bg-cyan-700 dark:bg-cyan-500 dark:hover:bg-cyan-400 text-white dark:text-black px-8 py-3.5 rounded-xl font-bold transition-all shadow-lg shadow-cyan-600/10 dark:shadow-[0_0_20px_rgba(34,211,238,0.2)] hover:-translate-y-0.5 text-sm flex items-center justify-center gap-1.5"
            >
              Analyze an Invention
              <ArrowRight size={16} />
            </Link>
            <a 
              href="#how-it-works" 
              className="w-full sm:w-auto bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 text-gray-700 dark:text-gray-200 px-8 py-3.5 rounded-xl font-bold transition-all hover:-translate-y-0.5 text-sm flex items-center justify-center"
            >
              Explore How It Works
            </a>
          </div>
        </section>

        {/* Problem & Audience Section */}
        <section className="border-t border-gray-200 dark:border-gray-800 py-20 px-6 max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-12 items-center">
            <div className="lg:col-span-1">
              <h2 className="text-[11px] font-bold text-cyan-600 dark:text-cyan-400 uppercase tracking-widest mb-3">Audience & Focus</h2>
              <h3 className="text-3xl font-extrabold text-gray-900 dark:text-white tracking-tight mb-4">Built for Early-Stage Inventors</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed font-medium">
                PatentIQ helps researchers, students, and early-stage innovators assess their concepts before commissioning expensive legal evaluations. Our goal is to ground every AI insight in actual prior-art database evidence.
              </p>
            </div>
            
            <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white dark:bg-[#0a0f1c] border border-gray-200 dark:border-gray-800 p-6 rounded-2xl">
                <Compass className="text-cyan-500 mb-4" size={24} />
                <h4 className="font-bold text-gray-900 dark:text-white mb-2">Pre-Filing Guidance</h4>
                <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
                  Understand whether your tech has unique components or broad overlap with existing publications before committing capital.
                </p>
              </div>
              <div className="bg-white dark:bg-[#0a0f1c] border border-gray-200 dark:border-gray-800 p-6 rounded-2xl">
                <FileSearch2 className="text-cyan-500 mb-4" size={24} />
                <h4 className="font-bold text-gray-900 dark:text-white mb-2">Research Grounding</h4>
                <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
                  Instead of guessing, evaluate how your technical features correspond directly to database citations.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* How It Works Flow Chart */}
        <section id="how-it-works" className="border-t border-gray-200 dark:border-gray-800 bg-white/30 dark:bg-[#070b13]/40 py-20 px-6">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-[11px] font-bold text-cyan-600 dark:text-cyan-400 uppercase tracking-widest mb-3">Structured RAG Pipeline</h2>
              <h3 className="text-3xl font-extrabold text-gray-900 dark:text-white tracking-tight">The Core Processing Pipeline</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-6 relative">
              {[
                { step: "01", title: "Idea / Doc Upload", desc: "Submit project description or upload PDF/DOCX/TXT files." },
                { step: "02", title: "Structured Feature Parse", desc: "AI decomposes text into traceable key technical features." },
                { step: "03", title: "Hybrid Search & RRF", desc: "BM25 lexical + Qdrant BGE semantic search matches prior art, fused via RRF." },
                { step: "04", title: "Feature-Evidence Mapping", desc: "Verbatim evidence items are programmatically mapped to specific features." },
                { step: "05", title: "Readiness Assessment", desc: "Calculates scores mathematically; Gemini explains the structured findings." }
              ].map((flow, i) => (
                <div key={i} className="bg-white dark:bg-[#0a0f1c] border border-gray-200 dark:border-gray-800 rounded-2xl p-6 flex flex-col relative">
                  <span className="text-3xl font-black text-gray-200 dark:text-gray-800/80 mb-4 font-mono">{flow.step}</span>
                  <h4 className="font-bold text-gray-900 dark:text-white mb-2 text-sm">{flow.title}</h4>
                  <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed flex-1">{flow.desc}</p>
                  {i < 4 && (
                    <div className="hidden lg:block absolute top-1/2 -right-3 transform -translate-y-1/2 z-10 text-gray-300 dark:text-gray-700">
                      <ChevronRight size={20} />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Feature-Evidence Mapping (Core Contribution) */}
        <section className="border-t border-gray-200 dark:border-gray-800 py-20 px-6 max-w-7xl mx-auto">
          <div className="flex flex-col lg:flex-row items-center gap-12">
            <div className="lg:w-1/2 space-y-6">
              <span className="text-[11px] font-bold text-cyan-600 dark:text-cyan-400 uppercase tracking-widest">Research Contribution</span>
              <h3 className="text-3xl font-extrabold text-gray-900 dark:text-white tracking-tight leading-tight">Feature-to-Evidence Mapping</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed font-medium">
                PatentIQ breaks away from simple black-box LLM analysis. Our system isolates individual claims/features, matches them to specific sentences inside retrieved patents, and calculates evidence strength independently of retrieval similarity.
              </p>
              
              <div className="space-y-4">
                <div className="flex gap-4">
                  <div className="w-8 h-8 rounded-lg bg-cyan-100 dark:bg-cyan-950/50 flex items-center justify-center shrink-0 text-cyan-600 dark:text-cyan-400">
                    <GitBranch size={16} />
                  </div>
                  <div>
                    <h4 className="font-bold text-gray-900 dark:text-white text-sm">Fine-Grained Mapping</h4>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      See exactly which claims have strong, weak, or zero matching prior art.
                    </p>
                  </div>
                </div>
                <div className="flex gap-4">
                  <div className="w-8 h-8 rounded-lg bg-cyan-100 dark:bg-cyan-950/50 flex items-center justify-center shrink-0 text-cyan-600 dark:text-cyan-400">
                    <FileCheck2 size={16} />
                  </div>
                  <div>
                    <h4 className="font-bold text-gray-900 dark:text-white text-sm">Negative Evidence Tracking</h4>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      Highlights contradicting prior art or conflicting disclosures to pinpoint risks.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Simulated Mapping Visualization */}
            <div className="lg:w-1/2 w-full bg-white dark:bg-[#0a0f1c] border border-gray-200 dark:border-gray-800 rounded-3xl p-6 font-mono text-xs shadow-sm">
              <div className="border-b border-gray-150 dark:border-gray-800 pb-3 mb-4 flex justify-between items-center text-gray-400">
                <span>FEATURE_EVIDENCE_MAPPER</span>
                <span className="text-emerald-500 font-bold">STATUS: RUNNING</span>
              </div>
              <div className="space-y-4">
                <div className="p-3 bg-slate-50 dark:bg-[#111624] border border-gray-200 dark:border-gray-800 rounded-lg">
                  <div className="font-bold text-cyan-600 dark:text-cyan-400 mb-1">FEAT-001: Distributed Torque Balancer</div>
                  <div className="text-gray-400 dark:text-gray-500 mb-2">Category: Propulsion  |  Weight: High</div>
                  <div className="pl-3 border-l-2 border-emerald-500 text-gray-600 dark:text-gray-300">
                    → Matched US-10492-B2 "Rotor Control System"
                    <br/>
                    <span className="text-[10px] text-gray-400 font-medium">Similarity: 0.88  |  Strength: 0.82 (Supporting)</span>
                  </div>
                </div>

                <div className="p-3 bg-slate-50 dark:bg-[#111624] border border-gray-200 dark:border-gray-800 rounded-lg">
                  <div className="font-bold text-cyan-600 dark:text-cyan-400 mb-1">FEAT-002: Optoelectronic feedback loop</div>
                  <div className="text-gray-400 dark:text-gray-500 mb-2">Category: Sensing  |  Weight: Med</div>
                  <div className="pl-3 border-l-2 border-gray-300 dark:border-gray-700 text-gray-400 dark:text-gray-500">
                    → No strong prior art matches found.
                    <br/>
                    <span className="text-[10px] font-bold text-cyan-600 dark:text-cyan-400 uppercase">High Differentiation Signal</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Readiness Dashboard Engine (6 Dimensions) */}
        <section className="border-t border-gray-200 dark:border-gray-800 bg-white/30 dark:bg-[#070b13]/40 py-20 px-6">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-[11px] font-bold text-cyan-600 dark:text-cyan-400 uppercase tracking-widest mb-3">Six Multi-Dimensional Metrics</h2>
              <h3 className="text-3xl font-extrabold text-gray-900 dark:text-white tracking-tight">Level-2 Patent Readiness Assessment</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[
                { title: "Novelty", type: "Algorithmic", desc: "Calculated based on feature-level coverage and collective prior art overlaps, avoiding simple max similarity loops." },
                { title: "Prior-Art Overlap", type: "Algorithmic", desc: "Calculates the overall density and strength of patent chunks directly related to your claim statements." },
                { title: "Technical Differentiation", type: "Algorithmic", desc: "Tracks the ratio of high-importance technical features which remain entirely unaddressed by existing patents." },
                { title: "Documentation Quality", type: "Algorithmic", desc: "Evaluates the completeness, technical category specificity, and structural density of your source write-up." },
                { title: "Innovation Characteristics", type: "Qualitative", desc: "Qualitative evidence-supported assessment highlighting structural differences and design categories." },
                { title: "Commercial Potential", type: "Qualitative", desc: "Qualitative analysis outlining technical domains and market readiness with local confidence ratings." }
              ].map((dim, i) => (
                <div key={i} className="bg-white dark:bg-[#0a0f1c] border border-gray-200 dark:border-gray-800 p-6 rounded-2xl relative flex flex-col">
                  <div className="flex justify-between items-center mb-4">
                    <h4 className="font-bold text-gray-900 dark:text-white">{dim.title}</h4>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${dim.type === 'Algorithmic' ? 'bg-cyan-50 dark:bg-cyan-950/50 text-cyan-600 dark:text-cyan-400' : 'bg-purple-50 dark:bg-purple-950/50 text-purple-600 dark:text-purple-400'}`}>
                      {dim.type}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed flex-1">{dim.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Disclaimer CTA Section */}
        <section className="border-t border-gray-200 dark:border-gray-800 py-20 px-6 max-w-4xl mx-auto text-center">
          <div className="bg-red-50/50 dark:bg-red-950/10 border border-red-200/50 dark:border-red-900/20 p-8 rounded-3xl mb-12 text-left flex flex-col md:flex-row gap-6 items-start">
            <ShieldAlert className="text-red-500 shrink-0 mt-1" size={24} />
            <div>
              <h4 className="font-bold text-red-950 dark:text-red-400 text-sm mb-2">Important Legal Notice</h4>
              <p className="text-xs text-red-800/80 dark:text-red-400/80 leading-relaxed font-medium">
                PatentIQ is designed solely as an early-stage planning and research tool to help innovators evaluate their technical developments. It does not search exhaustive legal indexes, guarantees nothing regarding patent grant success, and must not replace professional analysis by licensed patent attorneys.
              </p>
            </div>
          </div>

          <h3 className="text-3xl font-extrabold text-gray-900 dark:text-white mb-6 tracking-tight">Evaluate your technology with evidence</h3>
          <Link 
            to="/register" 
            className="inline-flex bg-cyan-600 hover:bg-cyan-700 dark:bg-cyan-500 dark:hover:bg-cyan-400 text-white dark:text-black px-8 py-3.5 rounded-xl font-bold transition-all shadow-lg shadow-cyan-600/10 dark:shadow-[0_0_20px_rgba(34,211,238,0.2)] hover:-translate-y-0.5 text-sm"
          >
            Start Assessing
          </Link>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 dark:border-gray-800 py-12 px-6 bg-white dark:bg-[#040810] transition-colors duration-300">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-1.5">
            <span className="text-md font-black tracking-tighter text-gray-900 dark:text-white">
              Patent<span className="text-cyan-600 dark:text-cyan-400">IQ</span>
            </span>
          </div>
          <div className="text-xs text-gray-400 dark:text-gray-500">
            &copy; 2026 PatentIQ. Built for explainable, evidence-based early assessment.
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;

