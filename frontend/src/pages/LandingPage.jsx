import React from 'react';
import { Link } from 'react-router-dom';
import { 
  Brain, 
  Search, 
  BarChart2, 
  FileText,
  Rocket,
  ArrowRight,
  Sun,
  Moon,
  Check,
  FileSearch,
  Database,
  CheckCircle2,
  Sparkles
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import PatentBlueprintVisual from '../components/PatentBlueprintVisual';

const LandingPage = () => {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="min-h-screen bg-white dark:bg-[#0b0914] text-gray-900 dark:text-white font-sans selection:bg-blue-500/30 transition-colors duration-300 overflow-x-hidden">
      
      {/* Navbar */}
      <nav className="flex items-center justify-between py-6 px-8 max-w-7xl mx-auto w-full relative z-50">
        <Link to="/" className="flex items-center hover:opacity-80 transition-opacity">
          <span className="text-[20px] font-black tracking-tighter text-gray-900 dark:text-white">
            Patent<span className="text-blue-600 dark:text-blue-500">IQ</span>
          </span>
        </Link>
        <div className="hidden lg:flex items-center gap-12 text-[13px] font-medium text-gray-700 dark:text-gray-300">
          <a href="#features" className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">Features</a>
          <a href="#solutions" className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">Solutions</a>
          <a href="#technology" className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">Technology</a>
          <a href="#demo" className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">Book Demo</a>
        </div>
        <div className="flex items-center gap-6 text-[13px] font-medium">
          <button 
            onClick={toggleTheme}
            aria-label="Toggle theme"
            className="text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors p-2"
          >
            {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
          </button>
          <Link to="/register" className="text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors hidden sm:block">Get Started</Link>
          <Link to="/login" className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-lg font-bold transition-colors flex items-center gap-2 shadow-sm text-[13px]">
            Analyze Now <ArrowRight size={14} />
          </Link>
        </div>
      </nav>

      <main className="w-full flex flex-col items-center">
        
        {/* Hero Section */}
        <section className="flex flex-col lg:flex-row items-center justify-between gap-12 pt-8 lg:pt-12 pb-16 lg:pb-24 w-full max-w-7xl mx-auto px-8 relative overflow-hidden">
          {/* Left Content */}
          <div className="w-full lg:w-[45%] flex flex-col items-start text-left relative z-10">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-[10px] font-bold tracking-wider uppercase mb-8 border border-blue-100 dark:border-blue-800/50">
              <span className="text-blue-600 dark:text-blue-400">✨</span>
              AI-Powered Patent Potential Analysis
            </div>
            
            <h1 className="text-4xl lg:text-[3.5rem] font-extrabold text-gray-900 dark:text-white leading-[1.12] tracking-[-0.02em] mb-6">
              Evaluate Your Project's <br className="hidden lg:block"/>
              <span className="text-blue-600 dark:text-blue-500">Patent Potential</span> <br className="hidden lg:block"/>
              with AI
            </h1>
            
            <p className="text-[14px] text-gray-600 dark:text-gray-400 mb-10 max-w-[540px] leading-[1.8] font-medium tracking-tight">
              Upload your project report, research paper, or technical documentation. PatentIQ uses Agentic RAG to retrieve relevant patents, compare innovations, estimate novelty, and provide intelligent recommendations before patent filing.
            </p>
            
            <div className="flex flex-wrap items-center gap-4">
              <Link to="/login" className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3.5 rounded-lg font-bold transition-colors shadow-lg shadow-blue-600/30 flex items-center gap-2 text-[14px]">
                Assess My Project <ArrowRight size={16} />
              </Link>
              <button className="bg-white dark:bg-[#151a28] border-2 border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 text-gray-900 dark:text-white px-8 py-3.5 rounded-lg font-bold transition-colors flex items-center gap-2 shadow-sm text-[14px]">
                <FileText size={16} className="text-blue-600 dark:text-blue-400" /> View Demo Report
              </button>
            </div>
          </div>

          {/* Right Content - Visual Elements */}
          <div className="w-full lg:w-[55%] relative h-[500px] lg:h-[600px] flex items-center justify-center mt-12 lg:mt-0">
            <PatentBlueprintVisual />
          </div>
        </section>

        {/* How It Works Section */}
        <section id="solutions" className="w-full max-w-7xl mx-auto px-8 py-16 lg:py-20 border-t border-gray-100 dark:border-gray-800/50">
          <div className="text-center mb-16">
            <h2 className="text-[28px] lg:text-[36px] font-extrabold text-gray-900 dark:text-white mb-4 tracking-[-0.02em] leading-tight">How PatentIQ Works</h2>
          </div>
          
          <div className="relative flex flex-col md:flex-row items-center justify-between gap-6 md:gap-2">
            {/* Connecting Line (hidden on mobile) */}
            <div className="hidden md:block absolute top-[24px] left-8 right-8 h-[2px] bg-gradient-to-r from-blue-100 via-blue-500 to-blue-100 dark:from-blue-900/30 dark:via-blue-500/50 dark:to-blue-900/30 z-0"></div>
            
            {[
              { icon: <FileText size={20} />, label: "Upload Project" },
              { icon: <Brain size={20} />, label: "AI Understands Project" },
              { icon: <FileSearch size={20} />, label: "Extract Innovation" },
              { icon: <Database size={20} />, label: "Agentic RAG retrieves relevant patents" },
              { icon: <Search size={20} />, label: "Semantic Comparison" },
              { icon: <BarChart2 size={20} />, label: "Novelty Evaluation" },
              { icon: <Check size={20} />, label: "Patent Potential Score" },
              { icon: <Sparkles size={20} />, label: "AI Recommendations" },
              { icon: <CheckCircle2 size={20} />, label: "Download Patent Potential Report" }
            ].map((step, index) => (
              <div key={index} className="relative z-10 flex flex-col items-center gap-4 w-full md:w-auto group">
                <div className="w-12 h-12 bg-white dark:bg-[#111522] border-2 border-blue-100 dark:border-blue-900/50 rounded-full flex items-center justify-center text-blue-600 dark:text-blue-400 shadow-md shadow-blue-500/10 group-hover:scale-110 group-hover:border-blue-500 group-hover:text-blue-500 transition-all duration-300">
                  {step.icon}
                </div>
                <div className="text-[11px] font-bold text-gray-700 dark:text-gray-300 text-center w-24 leading-snug">
                  {step.label}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="w-full max-w-7xl mx-auto px-8 py-16 lg:py-20">
          <div className="text-center mb-16 lg:mb-20">
            <h2 className="text-[28px] lg:text-[36px] font-extrabold text-gray-900 dark:text-white mb-4 tracking-[-0.02em] leading-tight">Powerful Features for Patent Excellence</h2>
            <p className="text-[14px] text-gray-600 dark:text-gray-400 font-medium leading-[1.8] max-w-2xl mx-auto">Built for innovators, researchers, and IP professionals who demand precision.</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 lg:gap-8">
            
            <div className="bg-white dark:bg-[#111522] border border-gray-100 dark:border-gray-800/60 p-8 rounded-[2rem] shadow-sm relative overflow-hidden group hover:shadow-xl transition-all duration-300 flex flex-col h-full">
              <div className="w-12 h-12 bg-blue-600 rounded-2xl flex items-center justify-center text-white mb-6 shadow-lg shadow-blue-600/20 group-hover:scale-110 transition-transform duration-300">
                <FileText size={24} />
              </div>
              <h3 className="text-[18px] font-bold text-blue-600 dark:text-blue-500 mb-3 leading-[1.3] tracking-tight">Upload Project</h3>
              <p className="text-[13px] text-gray-600 dark:text-gray-400 leading-[1.8] relative z-10 flex-1 pr-2">Securely upload your project report, research paper, or technical documentation in multiple formats.</p>
              <div className="absolute -bottom-8 -right-4 text-[100px] font-black text-gray-50 dark:text-gray-800/20 select-none z-0 group-hover:text-blue-50 dark:group-hover:text-blue-900/10 transition-colors duration-300">01</div>
            </div>

            <div className="bg-white dark:bg-[#111522] border border-gray-100 dark:border-gray-800/60 p-8 rounded-[2rem] shadow-sm relative overflow-hidden group hover:shadow-xl transition-all duration-300 flex flex-col h-full">
              <div className="w-12 h-12 bg-cyan-600 rounded-2xl flex items-center justify-center text-white mb-6 shadow-lg shadow-cyan-600/20 group-hover:scale-110 transition-transform duration-300">
                <Brain size={24} />
              </div>
              <h3 className="text-[18px] font-bold text-cyan-600 dark:text-cyan-500 mb-3 leading-[1.3] tracking-tight">AI Project<br/>Understanding</h3>
              <p className="text-[13px] text-gray-600 dark:text-gray-400 leading-[1.8] relative z-10 flex-1 pr-2">Advanced LLMs read and comprehend your complex technical documents just like an expert consultant.</p>
              <div className="absolute -bottom-8 -right-4 text-[100px] font-black text-gray-50 dark:text-gray-800/20 select-none z-0 group-hover:text-cyan-50 dark:group-hover:text-cyan-900/10 transition-colors duration-300">02</div>
            </div>

            <div className="bg-white dark:bg-[#111522] border border-gray-100 dark:border-gray-800/60 p-8 rounded-[2rem] shadow-sm relative overflow-hidden group hover:shadow-xl transition-all duration-300 flex flex-col h-full">
              <div className="w-12 h-12 bg-indigo-600 rounded-2xl flex items-center justify-center text-white mb-6 shadow-lg shadow-indigo-600/20 group-hover:scale-110 transition-transform duration-300">
                <FileSearch size={24} />
              </div>
              <h3 className="text-[18px] font-bold text-indigo-600 dark:text-indigo-400 mb-3 leading-[1.3] tracking-tight">Innovation<br/>Extraction</h3>
              <p className="text-[13px] text-gray-600 dark:text-gray-400 leading-[1.8] relative z-10 flex-1 pr-2">Automatically identifies and isolates the core novel ideas and technical methodologies within your work.</p>
              <div className="absolute -bottom-8 -right-4 text-[100px] font-black text-gray-50 dark:text-gray-800/20 select-none z-0 group-hover:text-indigo-50 dark:group-hover:text-indigo-900/10 transition-colors duration-300">03</div>
            </div>
            
            <div className="bg-white dark:bg-[#111522] border border-gray-100 dark:border-gray-800/60 p-8 rounded-[2rem] shadow-sm relative overflow-hidden group hover:shadow-xl transition-all duration-300 flex flex-col h-full">
              <div className="w-12 h-12 bg-emerald-600 rounded-2xl flex items-center justify-center text-white mb-6 shadow-lg shadow-emerald-600/20 group-hover:scale-110 transition-transform duration-300">
                <Database size={24} />
              </div>
              <h3 className="text-[18px] font-bold text-emerald-600 dark:text-emerald-500 mb-3 leading-[1.3] tracking-tight">Agentic RAG<br/>Retrieval</h3>
              <p className="text-[13px] text-gray-600 dark:text-gray-400 leading-[1.8] relative z-10 flex-1 pr-2">Autonomous agents retrieve the most relevant existing patents from global databases based on your innovation.</p>
              <div className="absolute -bottom-8 -right-4 text-[100px] font-black text-gray-50 dark:text-gray-800/20 select-none z-0 group-hover:text-emerald-50 dark:group-hover:text-emerald-900/10 transition-colors duration-300">04</div>
            </div>
            
            <div className="bg-white dark:bg-[#111522] border border-gray-100 dark:border-gray-800/60 p-8 rounded-[2rem] shadow-sm relative overflow-hidden group hover:shadow-xl transition-all duration-300 flex flex-col h-full">
              <div className="w-12 h-12 bg-teal-500 rounded-2xl flex items-center justify-center text-white mb-6 shadow-lg shadow-teal-500/20 group-hover:scale-110 transition-transform duration-300">
                <Search size={24} />
              </div>
              <h3 className="text-[18px] font-bold text-teal-600 dark:text-teal-400 mb-3 leading-[1.3] tracking-tight">Semantic Patent<br/>Comparison</h3>
              <p className="text-[13px] text-gray-600 dark:text-gray-400 leading-[1.8] relative z-10 flex-1 pr-2">Deep semantic comparison between your project features and existing patents to uncover true similarities.</p>
              <div className="absolute -bottom-8 -right-4 text-[100px] font-black text-gray-50 dark:text-gray-800/20 select-none z-0 group-hover:text-teal-50 dark:group-hover:text-teal-900/10 transition-colors duration-300">05</div>
            </div>
            
            <div className="bg-white dark:bg-[#111522] border border-gray-100 dark:border-gray-800/60 p-8 rounded-[2rem] shadow-sm relative overflow-hidden group hover:shadow-xl transition-all duration-300 flex flex-col h-full">
              <div className="w-12 h-12 bg-purple-500 rounded-2xl flex items-center justify-center text-white mb-6 shadow-lg shadow-purple-500/20 group-hover:scale-110 transition-transform duration-300">
                <BarChart2 size={24} />
              </div>
              <h3 className="text-[18px] font-bold text-purple-600 dark:text-purple-400 mb-3 leading-[1.3] tracking-tight">Patent Potential<br/>Analysis</h3>
              <p className="text-[13px] text-gray-600 dark:text-gray-400 leading-[1.8] relative z-10 flex-1 pr-2">Quantify your project's patent potential with our proprietary scoring algorithm and understand exactly what makes it unique.</p>
              <div className="absolute -bottom-8 -right-4 text-[100px] font-black text-gray-50 dark:text-gray-800/20 select-none z-0 group-hover:text-purple-50 dark:group-hover:text-purple-900/10 transition-colors duration-300">06</div>
            </div>

            <div className="bg-white dark:bg-[#111522] border border-gray-100 dark:border-gray-800/60 p-8 rounded-[2rem] shadow-sm relative overflow-hidden group hover:shadow-xl transition-all duration-300 flex flex-col h-full">
              <div className="w-12 h-12 bg-rose-500 rounded-2xl flex items-center justify-center text-white mb-6 shadow-lg shadow-rose-500/20 group-hover:scale-110 transition-transform duration-300">
                <Sparkles size={24} />
              </div>
              <h3 className="text-[18px] font-bold text-rose-500 dark:text-rose-400 mb-3 leading-[1.3] tracking-tight">AI Improvement<br/>Recommendations</h3>
              <p className="text-[13px] text-gray-600 dark:text-gray-400 leading-[1.8] relative z-10 flex-1 pr-2">Receive actionable advice on how to tweak your project to increase its likelihood of patent success.</p>
              <div className="absolute -bottom-8 -right-4 text-[100px] font-black text-gray-50 dark:text-gray-800/20 select-none z-0 group-hover:text-rose-50 dark:group-hover:text-rose-900/10 transition-colors duration-300">07</div>
            </div>
            
            <div className="bg-white dark:bg-[#111522] border border-gray-100 dark:border-gray-800/60 p-8 rounded-[2rem] shadow-sm relative overflow-hidden group hover:shadow-xl transition-all duration-300 flex flex-col h-full">
              <div className="w-12 h-12 bg-orange-500 rounded-2xl flex items-center justify-center text-white mb-6 shadow-lg shadow-orange-500/20 group-hover:scale-110 transition-transform duration-300">
                <CheckCircle2 size={24} />
              </div>
              <h3 className="text-[18px] font-bold text-orange-500 dark:text-orange-400 mb-3 leading-[1.3] tracking-tight">Professional Report<br/>Generation</h3>
              <p className="text-[13px] text-gray-600 dark:text-gray-400 leading-[1.8] relative z-10 flex-1 pr-2">Generate comprehensive Patent Potential Reports to share with stakeholders or IP attorneys before filing.</p>
              <div className="absolute -bottom-8 -right-4 text-[100px] font-black text-gray-50 dark:text-gray-800/20 select-none z-0 group-hover:text-orange-50 dark:group-hover:text-orange-900/10 transition-colors duration-300">08</div>
            </div>

          </div>
        </section>

        {/* CTA Section */}
        <section id="technology" className="w-full max-w-7xl mx-auto px-8 py-10 mb-20">
          <div className="bg-[#f4f7ff] dark:bg-[#111624] border border-blue-100/50 dark:border-blue-900/30 rounded-[2rem] p-10 md:p-14 flex flex-col lg:flex-row items-center justify-between gap-10 relative overflow-hidden">
            <div className="absolute inset-0 opacity-[0.03] dark:opacity-[0.02] pointer-events-none" style={{backgroundImage: 'radial-gradient(#000 2px, transparent 2px)', backgroundSize: '30px 30px'}}></div>
            
            <div className="flex items-center gap-8 relative z-10 w-full lg:w-auto">
              <div className="hidden md:flex shrink-0 transform -rotate-12">
                <Rocket size={64} strokeWidth={1.5} className="text-blue-600 dark:text-blue-500 drop-shadow-xl" />
              </div>
              <div className="text-center md:text-left">
                <h2 className="text-[28px] lg:text-[32px] font-extrabold text-gray-900 dark:text-white mb-4 tracking-[-0.02em] leading-tight">Ready to evaluate your project's patent potential?</h2>
                <p className="text-[14px] text-gray-600 dark:text-gray-400 leading-[1.8] font-medium max-w-lg">Upload your project report and receive AI-powered novelty analysis, semantic patent comparisons, and a professional patent potential report within minutes.</p>
              </div>
            </div>
            
            <div className="flex flex-col sm:flex-row items-center gap-4 relative z-10 shrink-0 w-full lg:w-auto">
              <Link to="/register" className="w-full sm:w-auto text-center bg-blue-600 hover:bg-blue-700 text-white px-8 py-3.5 rounded-xl font-bold transition-colors shadow-lg shadow-blue-600/20 text-[14px]">
                Get Started Free
              </Link>
              <button id="demo" className="w-full sm:w-auto text-center bg-white dark:bg-[#151a28] border-2 border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 text-gray-900 dark:text-white px-8 py-3.5 rounded-xl font-bold transition-colors shadow-sm text-[14px]">
                Request a Demo
              </button>
            </div>
          </div>
        </section>

      </main>
      
      {/* Footer */}
      <footer id="resources" className="border-t border-gray-100 dark:border-gray-800/50 py-12 w-full">
        <div className="max-w-7xl mx-auto px-8 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center">
            <span className="text-[16px] font-black tracking-tighter text-gray-900 dark:text-white">
              Patent<span className="text-blue-600 dark:text-blue-500">IQ</span>
            </span>
          </div>
          
          <div className="flex flex-wrap items-center justify-center gap-8 text-[13px] font-medium text-gray-500 dark:text-gray-400">
            <a href="#" className="hover:text-gray-900 dark:hover:text-white transition-colors">About</a>
            <a href="#" className="hover:text-gray-900 dark:hover:text-white transition-colors">Documentation</a>
            <a href="#" className="hover:text-gray-900 dark:hover:text-white transition-colors">Privacy Policy</a>
            <a href="#" className="hover:text-gray-900 dark:hover:text-white transition-colors">Contact</a>
          </div>

          <div className="text-[12px] text-gray-400 dark:text-gray-500 font-medium">
            &copy; 2026 PatentIQ
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
