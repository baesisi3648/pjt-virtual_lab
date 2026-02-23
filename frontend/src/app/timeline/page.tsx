/**
 * @TASK P4-T2 - Timeline Demo Page (Redesigned)
 *
 * BIO-CORE AI LAB - GameBoard 통합 버전
 * ProcessTimeline 대신 GameBoard 캐릭터 시각화 사용
 */

'use client';

import { useState, useCallback, useEffect, use } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useGameSSE } from '@/hooks/useGameSSE';
import GameBoard from '@/components/game/GameBoard';

export default function TimelinePage({
  searchParams,
}: {
  searchParams: Promise<{ topic?: string }>;
}) {
  const router = useRouter();
  const params = use(searchParams);
  const [topic, setTopic] = useState('');
  const [constraints, setConstraints] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [finalReport, setFinalReport] = useState('');
  const [savedFilename, setSavedFilename] = useState('');
  const [error, setError] = useState('');

  // Auto-populate and submit if topic parameter exists
  useEffect(() => {
    if (params.topic) {
      setTopic(decodeURIComponent(params.topic));
      setIsSubmitted(true);
      setFinalReport('');
      setError('');
    }
  }, [params.topic]);

  const handleComplete = useCallback((report: string, filename?: string) => {
    setFinalReport(report);
    if (filename) setSavedFilename(filename);
  }, []);

  const handleError = useCallback((err: string) => {
    setError(err);
  }, []);

  // useGameSSE: topic이 비어있으면 idle, isSubmitted일 때만 실제 topic 전달
  const activeTopic = isSubmitted ? topic : '';
  const activeConstraints = isSubmitted ? constraints : '';

  const { state: gameState, reset: resetGame } = useGameSSE({
    topic: activeTopic,
    constraints: activeConstraints,
    onComplete: handleComplete,
    onError: handleError,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) {
      alert('연구 주제를 입력하세요.');
      return;
    }
    setIsSubmitted(true);
    setFinalReport('');
    setError('');
  };

  const handleReset = () => {
    resetGame();
    setIsSubmitted(false);
    setTopic('');
    setConstraints('');
    setFinalReport('');
    setSavedFilename('');
    setError('');
  };

  return (
    <div className="min-h-screen bg-[#101922] text-white">
      {/* Sticky Header */}
      <header className="sticky top-0 z-50 glass-panel border-b border-white/10">
        <div className="max-w-[1800px] mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
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
            <nav className="flex items-center gap-2 bg-white/5 rounded-full p-1">
              <Link href="/" className="px-4 py-1.5 hover:bg-white/5 rounded-full text-sm transition-colors">
                Dashboard
              </Link>
              <div className="px-4 py-1.5 bg-[#137fec] rounded-full text-sm font-medium">
                Agents
              </div>
              <Link href="/reports" className="px-4 py-1.5 hover:bg-white/5 rounded-full text-sm transition-colors">
                Reports
              </Link>
            </nav>

            {/* Right: Back Link */}
            <Link
              href="/"
              className="flex items-center gap-2 px-4 py-2 rounded-lg glass-panel-hover transition-all"
            >
              <span className="material-symbols-outlined text-sm">arrow_back</span>
              <span className="text-sm">Back to Home</span>
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-[1800px] mx-auto px-6 py-8">
        {!isSubmitted ? (
          // Before Submission: Two-column layout
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Side: Input Form */}
            <div className="lg:col-span-4 space-y-6">
              <div className="glass-panel p-6">
                <div className="flex items-center gap-3 mb-6">
                  <span className="material-symbols-outlined text-[#137fec]">terminal</span>
                  <h2 className="text-xl font-semibold">Research Console</h2>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                  {/* Topic Input */}
                  <div className="relative">
                    <label
                      htmlFor="topic"
                      className="absolute -top-2.5 left-3 px-2 bg-[#1a232e] text-xs text-white/60"
                    >
                      Research Topic *
                    </label>
                    <input
                      type="text"
                      id="topic"
                      value={topic}
                      onChange={(e) => setTopic(e.target.value)}
                      placeholder="예: CRISPR-Cas9을 이용한 유전자편집 토마토"
                      className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-white/30 focus:outline-none focus:border-[#137fec] transition-colors"
                      required
                    />
                  </div>

                  {/* Constraints Textarea */}
                  <div className="relative">
                    <label
                      htmlFor="constraints"
                      className="absolute -top-2.5 left-3 px-2 bg-[#1a232e] text-xs text-white/60"
                    >
                      Constraints (Optional)
                    </label>
                    <textarea
                      id="constraints"
                      value={constraints}
                      onChange={(e) => setConstraints(e.target.value)}
                      placeholder="예: EU 규제 기준을 중심으로"
                      className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-white/30 focus:outline-none focus:border-[#137fec] transition-colors resize-none"
                      rows={4}
                    />
                  </div>

                  {/* Submit Button */}
                  <button
                    type="submit"
                    disabled={!topic.trim()}
                    className="w-full px-6 py-4 bg-[#137fec] hover:bg-[#137fec]/80 disabled:bg-white/10 disabled:cursor-not-allowed rounded-lg font-semibold transition-all flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(19,127,236,0.3)] hover:shadow-[0_0_30px_rgba(19,127,236,0.5)]"
                  >
                    <span>EXECUTE</span>
                    <span className="material-symbols-outlined">arrow_forward</span>
                  </button>
                </form>
              </div>
            </div>

            {/* Right Side: Workflow Visualization */}
            <div className="lg:col-span-8">
              <div className="glass-panel p-8">
                {/* Title */}
                <div className="flex justify-center mb-8">
                  <div className="px-6 py-2 glass-panel-light rounded-full text-sm font-medium text-[#137fec]">
                    Active Neural Pathway
                  </div>
                </div>

                {/* SVG Workflow Diagram */}
                <div className="relative w-full h-[500px]">
                  <svg className="w-full h-full" viewBox="0 0 800 500">
                    {/* Flow Paths */}
                    <path
                      d="M 400 100 L 400 200"
                      stroke="rgba(139, 92, 246, 0.4)"
                      strokeWidth="2"
                      fill="none"
                      className="flow-path"
                    />
                    <path
                      d="M 400 250 L 200 350"
                      stroke="rgba(6, 182, 212, 0.4)"
                      strokeWidth="2"
                      fill="none"
                      className="flow-path"
                    />
                    <path
                      d="M 400 250 L 400 350"
                      stroke="rgba(6, 182, 212, 0.4)"
                      strokeWidth="2"
                      fill="none"
                      className="flow-path"
                    />
                    <path
                      d="M 400 250 L 600 350"
                      stroke="rgba(6, 182, 212, 0.4)"
                      strokeWidth="2"
                      fill="none"
                      className="flow-path"
                    />
                  </svg>

                  {/* PI Agent - Top Center */}
                  <div className="absolute top-0 left-1/2 -translate-x-1/2 flex flex-col items-center">
                    <div className="w-20 h-20 rounded-full bg-[#8b5cf6]/20 flex items-center justify-center border-2 border-[#8b5cf6] animate-pulse-glow-purple">
                      <span className="material-symbols-outlined text-[#8b5cf6] text-4xl">psychology</span>
                    </div>
                    <div className="mt-3 px-4 py-2 glass-panel rounded-lg">
                      <div className="text-sm font-semibold text-center">PI Agent</div>
                      <div className="text-xs text-white/40 text-center">Principal Investigator</div>
                    </div>
                  </div>

                  {/* Critic - Middle Center */}
                  <div className="absolute top-[200px] left-1/2 -translate-x-1/2 flex flex-col items-center">
                    <div className="w-20 h-20 rounded-full bg-[#00f0ff]/20 flex items-center justify-center border-2 border-[#00f0ff] animate-pulse-glow-cyan">
                      <span className="material-symbols-outlined text-[#00f0ff] text-4xl">fact_check</span>
                    </div>
                    <div className="mt-3 px-4 py-2 glass-panel rounded-lg">
                      <div className="text-sm font-semibold text-center">Critic</div>
                      <div className="text-xs text-white/40 text-center">Quality Assurance</div>
                    </div>
                  </div>

                  {/* Specialist 1 - Bottom Left */}
                  <div className="absolute top-[350px] left-[100px] flex flex-col items-center">
                    <div className="w-16 h-16 rounded-full bg-[#137fec]/20 flex items-center justify-center border-2 border-[#137fec] animate-pulse-glow">
                      <span className="material-symbols-outlined text-[#137fec] text-3xl">biotech</span>
                    </div>
                    <div className="mt-3 px-3 py-1.5 glass-panel rounded-lg">
                      <div className="text-xs font-semibold text-center">Biotech</div>
                    </div>
                  </div>

                  {/* Specialist 2 - Bottom Center */}
                  <div className="absolute top-[350px] left-1/2 -translate-x-1/2 flex flex-col items-center">
                    <div className="w-16 h-16 rounded-full bg-[#137fec]/20 flex items-center justify-center border-2 border-[#137fec] animate-pulse-glow">
                      <span className="material-symbols-outlined text-[#137fec] text-3xl">science</span>
                    </div>
                    <div className="mt-3 px-3 py-1.5 glass-panel rounded-lg">
                      <div className="text-xs font-semibold text-center">Science</div>
                    </div>
                  </div>

                  {/* Specialist 3 - Bottom Right */}
                  <div className="absolute top-[350px] right-[100px] flex flex-col items-center">
                    <div className="w-16 h-16 rounded-full bg-[#137fec]/20 flex items-center justify-center border-2 border-[#137fec] animate-pulse-glow">
                      <span className="material-symbols-outlined text-[#137fec] text-3xl">medication_liquid</span>
                    </div>
                    <div className="mt-3 px-3 py-1.5 glass-panel rounded-lg">
                      <div className="text-xs font-semibold text-center">Laboratory</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          // After Submission: GameBoard visualization
          <>
            {/* GameBoard - Character visualization */}
            <GameBoard state={gameState} />

            {/* Final Report */}
            {finalReport && (
              <div className="mt-8 glass-panel border-2 border-[#0bda5b]/30 p-8">
                <div className="flex items-center gap-3 mb-6">
                  <span className="material-symbols-outlined text-[#0bda5b] text-3xl">task_alt</span>
                  <h2 className="text-2xl font-bold text-[#0bda5b]">최종 보고서</h2>
                </div>

                <div className="prose prose-invert max-w-none mb-6">
                  <div className="whitespace-pre-wrap text-gray-200 font-mono text-sm bg-black/20 p-6 rounded-lg border border-white/5">
                    {finalReport}
                  </div>
                </div>

                <div className="flex gap-4">
                  {savedFilename && (
                    <button
                      onClick={() => router.push(`/reports/${encodeURIComponent(savedFilename)}`)}
                      className="px-6 py-3 bg-[#0bda5b] hover:bg-[#0bda5b]/80 rounded-lg font-medium transition-all flex items-center gap-2 shadow-[0_0_20px_rgba(11,218,91,0.3)]"
                    >
                      <span className="material-symbols-outlined text-sm">description</span>
                      <span>보고서 보기</span>
                    </button>
                  )}

                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(finalReport);
                      alert('보고서가 클립보드에 복사되었습니다.');
                    }}
                    className="px-6 py-3 glass-panel-hover rounded-lg font-medium transition-all flex items-center gap-2"
                  >
                    <span className="material-symbols-outlined text-sm">content_copy</span>
                    <span>Copy</span>
                  </button>

                  <button
                    onClick={() => {
                      const now = new Date();
                      const timestamp = now.toISOString().slice(0, 19).replace(/[T:]/g, '_').replace(/-/g, '');
                      const header = `${'='.repeat(80)}\n  Virtual Lab - 최종 연구 보고서\n  연구 주제: ${topic}\n  생성 일시: ${now.toLocaleString('ko-KR')}\n${'='.repeat(80)}\n\n`;
                      const blob = new Blob([header + finalReport], { type: 'text/plain; charset=utf-8' });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `report_${timestamp}.txt`;
                      a.click();
                      URL.revokeObjectURL(url);
                    }}
                    className="px-6 py-3 bg-[#137fec] hover:bg-[#137fec]/80 rounded-lg font-medium transition-all flex items-center gap-2 shadow-[0_0_20px_rgba(19,127,236,0.3)]"
                  >
                    <span className="material-symbols-outlined text-sm">download</span>
                    <span>TXT Download</span>
                  </button>
                </div>

                <p className="mt-4 text-sm text-white/40">
                  * 보고서는 서버의 reports/ 폴더에도 자동 저장됩니다.
                </p>
              </div>
            )}

            {/* Error Display */}
            {error && (
              <div className="mt-8 glass-panel border-2 border-red-500/30 p-6">
                <div className="flex items-center gap-3 mb-3">
                  <span className="material-symbols-outlined text-red-400 text-2xl">error</span>
                  <h2 className="text-xl font-bold text-red-400">에러 발생</h2>
                </div>
                <p className="text-red-300">{error}</p>
              </div>
            )}

            {/* Reset Button */}
            <div className="mt-8 text-center">
              <button
                onClick={handleReset}
                className="px-8 py-3 glass-panel-hover rounded-lg font-medium transition-all flex items-center gap-2 mx-auto"
              >
                <span className="material-symbols-outlined">restart_alt</span>
                <span>New Research</span>
              </button>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
