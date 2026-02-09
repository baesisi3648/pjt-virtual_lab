/**
 * @TASK P4-T2 - Timeline Demo Page
 * @SPEC TASKS.md#P4-T2
 *
 * ProcessTimeline 컴포넌트를 테스트하는 데모 페이지
 */

'use client';

import { useState, useCallback } from 'react';
import Link from 'next/link';
import ProcessTimeline from '@/components/ProcessTimeline';

export default function TimelinePage() {
  const [topic, setTopic] = useState('');
  const [constraints, setConstraints] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [finalReport, setFinalReport] = useState('');
  const [error, setError] = useState('');

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
    setIsSubmitted(false);
    setTopic('');
    setConstraints('');
    setFinalReport('');
    setError('');
  };

  const handleComplete = useCallback((report: string) => {
    setFinalReport(report);
  }, []);

  const handleError = useCallback((err: string) => {
    setError(err);
  }, []);

  return (
    <div className="min-h-screen bg-gray-950 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-4xl font-bold text-white">
            Virtual Lab - Process Timeline
          </h1>
          <Link
            href="/"
            className="px-4 py-2 text-sm bg-gray-800 text-gray-300 rounded-lg hover:bg-gray-700 transition-colors"
          >
            Home
          </Link>
        </div>

        {/* 입력 폼 */}
        {!isSubmitted ? (
          <div className="max-w-2xl mx-auto bg-gray-900 rounded-lg shadow-lg p-8 border border-gray-800">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label
                  htmlFor="topic"
                  className="block text-sm font-medium text-gray-300 mb-2"
                >
                  연구 주제 *
                </label>
                <input
                  type="text"
                  id="topic"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="예: CRISPR-Cas9을 이용한 유전자편집 토마토"
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label
                  htmlFor="constraints"
                  className="block text-sm font-medium text-gray-300 mb-2"
                >
                  제약 조건 (선택)
                </label>
                <textarea
                  id="constraints"
                  value={constraints}
                  onChange={(e) => setConstraints(e.target.value)}
                  placeholder="예: EU 규제 기준을 중심으로"
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={3}
                />
              </div>

              <button
                type="submit"
                className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
              >
                연구 시작
              </button>
            </form>
          </div>
        ) : (
          <>
            {/* 타임라인 */}
            <ProcessTimeline
              topic={topic}
              constraints={constraints}
              onComplete={handleComplete}
              onError={handleError}
            />

            {/* 최종 보고서 */}
            {finalReport && (
              <div className="mt-8 max-w-4xl mx-auto bg-gray-900 rounded-lg shadow-lg p-8 border border-green-800">
                <h2 className="text-2xl font-bold mb-4 text-green-400">최종 보고서</h2>
                <div className="prose prose-invert max-w-none">
                  <div className="whitespace-pre-wrap text-gray-200">{finalReport}</div>
                </div>
                <div className="mt-6 flex gap-4">
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(finalReport);
                      alert('보고서가 클립보드에 복사되었습니다.');
                    }}
                    className="px-4 py-2 bg-green-700 text-white rounded-lg hover:bg-green-600 transition-colors"
                  >
                    복사
                  </button>
                  <button
                    onClick={() => {
                      const blob = new Blob([finalReport], { type: 'text/plain' });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `research-report-${Date.now()}.txt`;
                      a.click();
                      URL.revokeObjectURL(url);
                    }}
                    className="px-4 py-2 bg-blue-700 text-white rounded-lg hover:bg-blue-600 transition-colors"
                  >
                    다운로드
                  </button>
                </div>
              </div>
            )}

            {/* 에러 */}
            {error && (
              <div className="mt-8 max-w-4xl mx-auto bg-red-950 border border-red-800 rounded-lg p-6">
                <h2 className="text-xl font-bold text-red-400 mb-2">에러 발생</h2>
                <p className="text-red-300">{error}</p>
              </div>
            )}

            {/* 리셋 버튼 */}
            <div className="mt-8 text-center">
              <button
                onClick={handleReset}
                className="px-6 py-3 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors"
              >
                새 연구 시작
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
