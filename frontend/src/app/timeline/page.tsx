/**
 * @TASK P4-T2 - Timeline Demo Page (Light Theme)
 *
 * Virtual Lab - Pipeline 스타일 Agent Activity 시각화
 */

'use client';

import { useState, useCallback, useEffect, use, useRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useGameSSE } from '@/hooks/useGameSSE';
import RoundProgressBar from '@/components/game/RoundProgressBar';
import ChatLog from '@/components/game/ChatLog';

export default function TimelinePage({
  searchParams,
}: {
  searchParams: Promise<{ topic?: string }>;
}) {
  const router = useRouter();
  const params = use(searchParams);
  const downloadAnchorRef = useRef<HTMLAnchorElement>(null);
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
    <div className="min-h-screen bg-[#f6f8f7] text-[#121714]">
      {/* Sticky Header */}
      <header className="sticky top-0 z-50 bg-white border-b border-[#dde4e0] shadow-sm">
        <div className="max-w-[1800px] mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Left: Logo */}
            <div className="flex items-center gap-3">
              <img src="/logo.png" alt="Virtual Lab" className="h-10" />
              <span className="text-xl font-bold tracking-tight text-[#121714]">VIRTUAL LAB</span>
            </div>

            {/* Center: Nav */}
            <nav className="flex items-center gap-1">
              <Link
                href="/"
                className="px-4 py-2 text-sm text-[#678373] hover:text-[#121714] transition-colors"
              >
                Dashboard
              </Link>
              <div className="px-4 py-2 text-sm font-bold text-[#1b7440] border-b-2 border-[#1b7440]">
                Agents
              </div>
              <Link
                href="/reports"
                className="px-4 py-2 text-sm text-[#678373] hover:text-[#121714] transition-colors"
              >
                Reports
              </Link>
            </nav>

            {/* Right: Back Link */}
            <Link
              href="/"
              className="flex items-center gap-2 px-4 py-2 rounded-lg border border-[#dde4e0] hover:bg-[#e8f5ed] text-sm text-[#121714] transition-colors"
            >
              <span className="material-symbols-outlined text-sm">arrow_back</span>
              <span>Back to Home</span>
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-[1800px] mx-auto px-6 py-8">
        {!isSubmitted ? (
          // Before Submission: Compact input + Workflow Pipeline
          <div className="max-w-3xl mx-auto space-y-6">
            {/* Compact Input Card */}
            <div className="bg-white border border-[#dde4e0] rounded-2xl shadow-sm p-6">
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="material-symbols-outlined text-[#1b7440]">biotech</span>
                  <p className="text-xs font-bold uppercase tracking-wider text-[#1b7440]">
                    EXPERIMENT PARAMETERS
                  </p>
                </div>

                <textarea
                  id="topic"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="연구 주제를 입력하세요 (예: CRISPR-Cas9을 이용한 유전자편집 토마토)"
                  rows={2}
                  className="w-full px-4 py-3 bg-[#f6f8f7] border border-[#dde4e0] rounded-xl text-[#121714] placeholder-[#678373] focus:outline-none focus:ring-2 focus:ring-[#1b7440] focus:border-transparent transition-all resize-none"
                  required
                />

                <div className="flex gap-3">
                  <input
                    type="text"
                    id="constraints"
                    value={constraints}
                    onChange={(e) => setConstraints(e.target.value)}
                    placeholder="Safety Constraints (Optional)"
                    className="flex-1 px-4 py-3 bg-[#f6f8f7] border border-[#dde4e0] rounded-xl text-[#121714] placeholder-[#678373] focus:outline-none focus:ring-2 focus:ring-[#1b7440] focus:border-transparent transition-all"
                  />
                  <button
                    type="submit"
                    disabled={!topic.trim()}
                    className="px-8 py-3 bg-[#1b7440] hover:bg-[#13542e] disabled:bg-[#dde4e0] disabled:text-[#678373] disabled:cursor-not-allowed text-white rounded-xl font-bold uppercase tracking-wide transition-colors flex items-center gap-2"
                  >
                    <span>EXECUTE</span>
                    <span className="material-symbols-outlined text-sm">arrow_forward</span>
                  </button>
                </div>
              </form>
            </div>

            {/* Workflow Pipeline */}
            <div className="bg-white border border-[#dde4e0] rounded-2xl shadow-sm p-6">
              <div className="flex items-center justify-between mb-8">
                <h2 className="text-lg font-bold text-[#121714]">Workflow Pipeline</h2>
                <span className="px-3 py-1 bg-[#e8f5ed] text-[#1b7440] text-xs font-semibold rounded-full">
                  Active
                </span>
              </div>

              <div className="relative">
                <div className="absolute left-8 top-10 bottom-10 w-0.5 bg-gradient-to-b from-[#1b7440]/20 via-[#1b7440]/20 to-[#1b7440]/10" />

                {/* Step 1: PI Agent */}
                <div className="relative flex items-start gap-5 mb-8">
                  <div className="flex-shrink-0 w-16 h-16 rounded-full bg-[#e8f5ed] border-2 border-[#1b7440] flex items-center justify-center z-10">
                    <span className="material-symbols-outlined text-[#1b7440] text-2xl">check_circle</span>
                  </div>
                  <div className="flex-1 bg-[#f6f8f7] rounded-xl p-4 mt-1">
                    <div className="flex items-center gap-3 mb-2">
                      <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center">
                        <span className="material-symbols-outlined text-blue-600 text-sm">psychology</span>
                      </div>
                      <div>
                        <p className="text-sm font-bold text-[#121714]">PI Agent</p>
                        <p className="text-xs text-[#678373]">Principal Investigator</p>
                      </div>
                    </div>
                    <p className="text-xs text-[#678373]">
                      연구팀 구성 및 연구 계획 수립. 전문가를 선별하고 연구 아젠다를 정의합니다.
                    </p>
                  </div>
                </div>

                {/* Step 2: Critic Agent */}
                <div className="relative flex items-start gap-5 mb-8">
                  <div className="flex-shrink-0 w-16 h-16 rounded-full bg-white border-2 border-[#1b7440]/40 flex items-center justify-center z-10 shadow-sm">
                    <span className="w-3 h-3 rounded-full bg-[#1b7440] animate-pulse" />
                  </div>
                  <div className="flex-1 bg-white border border-[#1b7440]/20 rounded-xl p-4 mt-1 shadow-sm">
                    <div className="flex items-center gap-3 mb-2">
                      <div className="w-8 h-8 rounded-lg bg-amber-100 flex items-center justify-center">
                        <span className="material-symbols-outlined text-amber-600 text-sm">gavel</span>
                      </div>
                      <div>
                        <p className="text-sm font-bold text-[#121714]">Critic Agent</p>
                        <p className="text-xs text-[#678373]">Quality Assurance</p>
                      </div>
                    </div>
                    <p className="text-xs text-[#678373]">
                      각 라운드 결과를 평가하고 품질 피드백을 제공합니다. 과학적 엄밀성을 검증합니다.
                    </p>
                  </div>
                </div>

                {/* Step 3: Specialist Agents */}
                <div className="relative flex items-start gap-5 opacity-50">
                  <div className="flex-shrink-0 w-16 h-16 rounded-full bg-[#f6f8f7] border-2 border-[#dde4e0] flex items-center justify-center z-10">
                    <span className="w-3 h-3 rounded-full border-2 border-[#678373]" />
                  </div>
                  <div className="flex-1 bg-[#f6f8f7] rounded-xl p-4 mt-1">
                    <div className="flex items-center gap-3 mb-2">
                      <div className="w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center">
                        <span className="material-symbols-outlined text-gray-500 text-sm">biotech</span>
                      </div>
                      <div>
                        <p className="text-sm font-bold text-[#121714]">Specialist Agents</p>
                        <p className="text-xs text-[#678373]">Domain Experts</p>
                      </div>
                    </div>
                    <p className="text-xs text-[#678373]">
                      분자생물학, 독성학, 규제과학 등 각 전문 분야에서 심층 분석을 수행합니다.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          // After Submission: Pipeline-style Agent Activity
          <>
            {/* Round Progress */}
            <RoundProgressBar
              currentRound={gameState.currentRound}
              maxRounds={gameState.maxRounds}
              phase={gameState.phase}
              isStreaming={gameState.isStreaming}
            />

            {/* Agent Activity Pipeline */}
            <div className="mt-4">
              <ChatLog
                messages={gameState.chatLog}
                isStreaming={gameState.isStreaming}
                phase={gameState.phase}
                currentRound={gameState.currentRound}
              />
            </div>

            {/* Final Report */}
            {finalReport && (
              <div className="mt-8 bg-white border-2 border-[#1b7440]/20 rounded-xl shadow-sm p-8">
                <div className="flex items-center gap-3 mb-6">
                  <span className="material-symbols-outlined text-[#1b7440] text-3xl">task_alt</span>
                  <h2 className="text-2xl font-bold text-[#121714]">최종 보고서</h2>
                </div>

                <div className="mb-6">
                  <div className="whitespace-pre-wrap font-mono text-sm bg-[#f6f8f7] p-6 rounded-lg text-[#121714]">
                    {finalReport}
                  </div>
                </div>

                <div className="flex flex-wrap gap-3">
                  {savedFilename && (
                    <button
                      onClick={() => router.push(`/reports/${encodeURIComponent(savedFilename)}`)}
                      className="px-6 py-3 bg-[#1b7440] hover:bg-[#13542e] text-white rounded-lg font-medium transition-colors flex items-center gap-2"
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
                    className="px-6 py-3 border border-[#dde4e0] hover:bg-[#f6f8f7] text-[#121714] rounded-lg font-medium transition-colors flex items-center gap-2"
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
                      if (downloadAnchorRef.current) {
                        downloadAnchorRef.current.href = url;
                        downloadAnchorRef.current.download = `report_${timestamp}.txt`;
                        downloadAnchorRef.current.click();
                        URL.revokeObjectURL(url);
                      }
                    }}
                    className="px-6 py-3 bg-[#1b7440] hover:bg-[#13542e] text-white rounded-lg font-medium transition-colors flex items-center gap-2"
                  >
                    <span className="material-symbols-outlined text-sm">download</span>
                    <span>TXT Download</span>
                  </button>
                  {/* Hidden anchor used for file download via ref — avoids direct DOM creation */}
                  <a ref={downloadAnchorRef} className="hidden" aria-hidden="true" />
                </div>

                <p className="mt-4 text-sm text-[#678373]">
                  * 보고서는 서버의 reports/ 폴더에도 자동 저장됩니다.
                </p>
              </div>
            )}

            {/* Error Display */}
            {error && (
              <div className="mt-8 bg-white border-2 border-red-200 rounded-xl shadow-sm p-6">
                <div className="flex items-center gap-3 mb-3">
                  <span className="material-symbols-outlined text-red-600 text-2xl">error</span>
                  <h2 className="text-xl font-bold text-red-600">에러 발생</h2>
                </div>
                <p className="text-red-600">{error}</p>
              </div>
            )}

            {/* Reset Button */}
            <div className="mt-8 text-center">
              <button
                onClick={handleReset}
                className="px-8 py-3 border border-[#dde4e0] hover:bg-[#e8f5ed] text-[#121714] rounded-lg font-medium transition-colors flex items-center gap-2 mx-auto"
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
