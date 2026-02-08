/**
 * @TASK P4-T2 - Timeline Demo Page
 * @SPEC TASKS.md#P4-T2
 *
 * ProcessTimeline 컴포넌트를 테스트하는 데모 페이지
 */

'use client';

import { useState } from 'react';
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

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold text-center mb-8 text-gray-900">
          Virtual Lab - Process Timeline
        </h1>

        {/* 입력 폼 */}
        {!isSubmitted ? (
          <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-lg p-8">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label
                  htmlFor="topic"
                  className="block text-sm font-medium text-gray-700 mb-2"
                >
                  연구 주제 *
                </label>
                <input
                  type="text"
                  id="topic"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="예: CRISPR-Cas9을 이용한 유전자편집 토마토"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label
                  htmlFor="constraints"
                  className="block text-sm font-medium text-gray-700 mb-2"
                >
                  제약 조건 (선택)
                </label>
                <textarea
                  id="constraints"
                  value={constraints}
                  onChange={(e) => setConstraints(e.target.value)}
                  placeholder="예: EU 규제 기준을 중심으로"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
              onComplete={(report) => {
                setFinalReport(report);
              }}
              onError={(err) => {
                setError(err);
              }}
            />

            {/* 최종 보고서 */}
            {finalReport && (
              <div className="mt-8 max-w-4xl mx-auto bg-white rounded-lg shadow-lg p-8">
                <h2 className="text-2xl font-bold mb-4 text-gray-900">최종 보고서</h2>
                <div className="prose max-w-none">
                  <div className="whitespace-pre-wrap text-gray-700">{finalReport}</div>
                </div>
                <div className="mt-6 flex gap-4">
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(finalReport);
                      alert('보고서가 클립보드에 복사되었습니다.');
                    }}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                  >
                    📋 복사
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
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    💾 다운로드
                  </button>
                </div>
              </div>
            )}

            {/* 에러 */}
            {error && (
              <div className="mt-8 max-w-4xl mx-auto bg-red-50 border border-red-200 rounded-lg p-6">
                <h2 className="text-xl font-bold text-red-800 mb-2">에러 발생</h2>
                <p className="text-red-700">{error}</p>
              </div>
            )}

            {/* 리셋 버튼 */}
            <div className="mt-8 text-center">
              <button
                onClick={handleReset}
                className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
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
