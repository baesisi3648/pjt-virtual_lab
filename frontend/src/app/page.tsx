'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function HomePage() {
  const router = useRouter();
  const [backendStatus, setBackendStatus] = useState<'online' | 'offline' | 'checking'>('checking');
  const [topic, setTopic] = useState('');

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then(res => res.ok ? setBackendStatus('online') : setBackendStatus('offline'))
      .catch(() => setBackendStatus('offline'));
  }, []);

  const handleExecute = (e: React.FormEvent) => {
    e.preventDefault();
    if (topic.trim()) {
      router.push(`/timeline?topic=${encodeURIComponent(topic.trim())}`);
    }
  };

  return (
    <div className="min-h-screen bg-[#101922] text-white">
      {/* Header */}
      <header className="sticky top-0 z-50 glass-panel border-b border-white/10">
        <div className="max-w-[1800px] mx-auto px-6 py-4 flex items-center justify-between">
          {/* Left: Logo */}
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-[#137fec]/10 flex items-center justify-center">
              <span className="material-symbols-outlined text-[#137fec] text-3xl">biotech</span>
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight">BIO-CORE AI LAB</h1>
              <div className="flex items-center gap-1.5 text-xs text-[#0bda5b]">
                <span className="w-2 h-2 rounded-full bg-[#0bda5b] animate-pulse"></span>
                System Online
              </div>
            </div>
          </div>

          {/* Center: Nav */}
          <nav className="flex items-center gap-2 bg-white/5 rounded-full p-1.5">
            <div className="px-6 py-2 bg-[#137fec] rounded-full text-sm font-medium">
              Dashboard
            </div>
            <Link href="/timeline" className="px-6 py-2 hover:bg-white/5 rounded-full text-sm font-medium transition-colors">
              Agents
            </Link>
            <Link href="/reports" className="px-6 py-2 hover:bg-white/5 rounded-full text-sm font-medium transition-colors">
              Reports
            </Link>
          </nav>

          {/* Right: Backend Status */}
          <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/5">
            <span className={`w-2 h-2 rounded-full ${backendStatus === 'online' ? 'bg-[#0bda5b]' : backendStatus === 'offline' ? 'bg-red-500' : 'bg-yellow-500'} ${backendStatus === 'checking' ? 'animate-pulse' : ''}`}></span>
            <span className="text-sm">
              {backendStatus === 'online' ? 'Backend Online' : backendStatus === 'offline' ? 'Backend Offline' : 'Checking...'}
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-[1800px] mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

          {/* Left Sidebar */}
          <aside className="lg:col-span-3 space-y-6">
            {/* Laboratory Status */}
            <div className="glass-panel p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <span className="material-symbols-outlined text-[#137fec]">analytics</span>
                Laboratory Status
              </h3>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-white/60">Compute Load</span>
                    <span className="text-[#137fec] font-mono">87%</span>
                  </div>
                  <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-[#137fec] to-[#00f0ff] w-[87%] rounded-full"></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-white/60">Core Temp</span>
                    <span className="text-[#0bda5b] font-mono">42°C</span>
                  </div>
                  <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-[#0bda5b] to-[#00f0ff] w-[42%] rounded-full"></div>
                  </div>
                </div>
              </div>
            </div>

            {/* Active Agents */}
            <div className="glass-panel p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <span className="material-symbols-outlined text-[#0bda5b]">group</span>
                Active Agents
              </h3>
              <div className="space-y-3">
                <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors">
                  <div className="w-10 h-10 rounded-full bg-[#8b5cf6]/20 flex items-center justify-center">
                    <span className="material-symbols-outlined text-[#8b5cf6]">psychology</span>
                  </div>
                  <div className="flex-1">
                    <div className="font-medium">PI Agent</div>
                    <div className="text-xs text-white/40">Principal Investigator</div>
                  </div>
                  <span className="w-2 h-2 rounded-full bg-[#8b5cf6] animate-pulse"></span>
                </div>
                <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors">
                  <div className="w-10 h-10 rounded-full bg-[#00f0ff]/20 flex items-center justify-center">
                    <span className="material-symbols-outlined text-[#00f0ff]">fact_check</span>
                  </div>
                  <div className="flex-1">
                    <div className="font-medium">Critic</div>
                    <div className="text-xs text-white/40">Quality Assurance</div>
                  </div>
                  <span className="w-2 h-2 rounded-full bg-[#00f0ff] animate-pulse"></span>
                </div>
                <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors">
                  <div className="w-10 h-10 rounded-full bg-[#137fec]/20 flex items-center justify-center">
                    <span className="material-symbols-outlined text-[#137fec]">biotech</span>
                  </div>
                  <div className="flex-1">
                    <div className="font-medium">Specialist</div>
                    <div className="text-xs text-white/40">Domain Expert</div>
                  </div>
                  <span className="w-2 h-2 rounded-full bg-[#137fec] animate-pulse"></span>
                </div>
              </div>
            </div>
          </aside>

          {/* Center */}
          <section className="lg:col-span-6 space-y-6">
            {/* PI Agent Visualization */}
            <div className="glass-panel p-12 flex flex-col items-center justify-center">
              <div className="relative w-48 h-48 mb-6">
                <div className="absolute inset-0 rounded-full bg-gradient-to-r from-[#137fec] via-[#00f0ff] to-[#8b5cf6] opacity-20 blur-xl animate-pulse"></div>
                <div className="absolute inset-0 rounded-full border-4 border-transparent bg-gradient-to-r from-[#137fec] via-[#00f0ff] to-[#8b5cf6] bg-clip-border animate-spin-slow"></div>
                <div className="absolute inset-2 rounded-full bg-[#101922] flex items-center justify-center">
                  <span className="material-symbols-outlined text-[#137fec]" style={{ fontSize: '80px' }}>psychology</span>
                </div>
              </div>
              <h2 className="text-3xl font-bold mb-2 bg-gradient-to-r from-[#137fec] to-[#00f0ff] bg-clip-text text-transparent">
                PI AGENT
              </h2>
              <div className="flex items-center gap-2 text-[#0bda5b]">
                <span className="w-2 h-2 rounded-full bg-[#0bda5b] animate-pulse"></span>
                Status: Active
              </div>
            </div>

            {/* Input Console */}
            <form onSubmit={handleExecute} className="glass-panel p-6">
              <div className="flex items-center gap-3 mb-4">
                <span className="material-symbols-outlined text-[#137fec]">terminal</span>
                <h3 className="text-lg font-semibold">Research Console</h3>
              </div>
              <div className="flex gap-3">
                <input
                  type="text"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="연구 주제를 입력하세요..."
                  className="flex-1 px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:border-[#137fec] transition-colors"
                />
                <button
                  type="submit"
                  disabled={!topic.trim()}
                  className="px-8 py-3 bg-[#137fec] hover:bg-[#137fec]/80 disabled:bg-white/10 disabled:cursor-not-allowed rounded-lg font-medium transition-colors flex items-center gap-2"
                >
                  <span className="material-symbols-outlined">play_arrow</span>
                  EXECUTE
                </button>
              </div>
            </form>

            {/* Terminal Log */}
            <div className="glass-panel p-6 bg-black/40">
              <div className="flex items-center gap-3 mb-4">
                <span className="material-symbols-outlined text-[#0bda5b]">code</span>
                <h3 className="text-lg font-semibold">System Log</h3>
              </div>
              <div className="font-mono text-sm space-y-1">
                <div className="text-white/40">
                  <span className="text-[#00f0ff]">[23:42:15]</span> System initialized...
                </div>
                <div className="text-white/40">
                  <span className="text-[#0bda5b]">[23:42:16]</span> PI Agent ready
                </div>
                <div className="text-white/40">
                  <span className="text-[#8b5cf6]">[23:42:17]</span> RAG system connected (316 documents)
                </div>
                <div className="text-white/40">
                  <span className="text-[#137fec]">[23:42:18]</span> Backend: http://localhost:8000
                </div>
                <div className="text-white/60">
                  <span className="text-[#0bda5b]">[23:42:19]</span> <span className="text-[#0bda5b]">Ready for input</span>
                </div>
              </div>
            </div>
          </section>

          {/* Right Sidebar */}
          <aside className="lg:col-span-3 space-y-6">
            {/* Research Progress */}
            <div className="glass-panel p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <span className="material-symbols-outlined text-[#8b5cf6]">bar_chart</span>
                Research Progress
              </h3>
              <div className="space-y-3">
                <div className="h-32 flex items-end gap-2">
                  <div className="flex-1 bg-gradient-to-t from-[#137fec] to-[#00f0ff] rounded-t-lg" style={{ height: '80%' }}></div>
                  <div className="flex-1 bg-gradient-to-t from-[#0bda5b] to-[#00f0ff] rounded-t-lg" style={{ height: '60%' }}></div>
                  <div className="flex-1 bg-gradient-to-t from-[#8b5cf6] to-[#00f0ff] rounded-t-lg" style={{ height: '90%' }}></div>
                  <div className="flex-1 bg-gradient-to-t from-[#137fec] to-[#8b5cf6] rounded-t-lg" style={{ height: '45%' }}></div>
                </div>
                <div className="grid grid-cols-4 gap-2 text-xs text-center text-white/40">
                  <div>W1</div>
                  <div>W2</div>
                  <div>W3</div>
                  <div>W4</div>
                </div>
              </div>
            </div>

            {/* Tech Stack */}
            <div className="glass-panel p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <span className="material-symbols-outlined text-[#00f0ff]">extension</span>
                Tech Stack
              </h3>
              <div className="space-y-3 text-sm">
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-white/60">FastAPI</span>
                    <span className="text-[#0bda5b] font-mono">100%</span>
                  </div>
                  <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full bg-[#0bda5b] w-full rounded-full"></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-white/60">LangGraph</span>
                    <span className="text-[#137fec] font-mono">95%</span>
                  </div>
                  <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full bg-[#137fec] w-[95%] rounded-full"></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-white/60">Pinecone</span>
                    <span className="text-[#8b5cf6] font-mono">92%</span>
                  </div>
                  <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full bg-[#8b5cf6] w-[92%] rounded-full"></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-white/60">Next.js</span>
                    <span className="text-[#00f0ff] font-mono">88%</span>
                  </div>
                  <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full bg-[#00f0ff] w-[88%] rounded-full"></div>
                  </div>
                </div>
              </div>
            </div>
          </aside>
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
          <Link href="/timeline" className="glass-panel-hover p-8 group">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-full bg-[#137fec]/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                <span className="material-symbols-outlined text-[#137fec] text-2xl">timeline</span>
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-2">Agent Timeline</h3>
                <p className="text-white/60 text-sm">실시간으로 에이전트 간 협업 과정을 모니터링하고 각 단계의 의사결정을 추적합니다.</p>
              </div>
            </div>
          </Link>

          <Link href="/timeline" className="glass-panel-hover p-8 group">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-full bg-[#8b5cf6]/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                <span className="material-symbols-outlined text-[#8b5cf6] text-2xl">sports_esports</span>
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-2">Game Board</h3>
                <p className="text-white/60 text-sm">픽셀아트 캐릭터로 에이전트 팀 회의를 시각화합니다. 연구실/회의실 씬 전환 포함.</p>
              </div>
            </div>
          </Link>

          <Link href="/reports" className="glass-panel-hover p-8 group">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-full bg-[#0bda5b]/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                <span className="material-symbols-outlined text-[#0bda5b] text-2xl">description</span>
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-2">Research Reports</h3>
                <p className="text-white/60 text-sm">AI가 생성한 연구 보고서를 확인하고 Markdown 형식으로 다운로드할 수 있습니다.</p>
              </div>
            </div>
          </Link>
        </div>
      </main>

      <style jsx>{`
        @keyframes spin-slow {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }
        .animate-spin-slow {
          animation: spin-slow 3s linear infinite;
        }
      `}</style>
    </div>
  );
}
