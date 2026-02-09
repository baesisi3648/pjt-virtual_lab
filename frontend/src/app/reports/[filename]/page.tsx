'use client';

import { useState, useEffect, use } from 'react';
import Link from 'next/link';
import ReportEditor from '@/components/ReportEditor';
import { fetchReportContent, regenerateSection, translateReport } from '@/lib/api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function ReportViewerPage({
  params,
}: {
  params: Promise<{ filename: string }>;
}) {
  const { filename } = use(params);
  const decodedFilename = decodeURIComponent(filename);

  const [report, setReport] = useState('');
  const [topic, setTopic] = useState('');
  const [createdAt, setCreatedAt] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [message, setMessage] = useState('');
  const [translatedReport, setTranslatedReport] = useState('');
  const [isTranslating, setIsTranslating] = useState(false);
  const [lang, setLang] = useState<'ko' | 'en'>('ko');

  useEffect(() => {
    fetchReportContent(decodedFilename)
      .then((data) => {
        setReport(data.content);
        setTopic(data.topic);
        setCreatedAt(data.created_at);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [decodedFilename]);

  const handleRegenerate = async (request: { section: string; feedback: string }) => {
    setIsRegenerating(true);
    setMessage('');
    try {
      const response = await regenerateSection({
        section: request.section,
        feedback: request.feedback,
        current_report: report,
      });
      setReport(response.updated_report);
      setMessage(response.message);
    } catch (err) {
      setMessage(`재생성 실패: ${err instanceof Error ? err.message : '알 수 없는 오류'}`);
    } finally {
      setIsRegenerating(false);
    }
  };

  const handleTranslate = async () => {
    setIsTranslating(true);
    setMessage('');
    try {
      const response = await translateReport(report);
      setTranslatedReport(response.translated);
      setLang('en');
      setMessage('Translation completed successfully.');
    } catch (err) {
      setMessage(`번역 실패: ${err instanceof Error ? err.message : '알 수 없는 오류'}`);
    } finally {
      setIsTranslating(false);
    }
  };

  const handleDownloadTxt = () => {
    const content = lang === 'en' && translatedReport ? translatedReport : report;
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const suffix = lang === 'en' ? '_EN' : '';
    a.download = `${decodedFilename.replace('.txt', '')}${suffix}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0f1216] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#137fec] mx-auto mb-3"></div>
          <p className="text-gray-400 font-mono text-sm">Loading report...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#0f1216] flex items-center justify-center">
        <div className="glass-panel border-2 border-red-500/30 p-8 rounded-lg max-w-md text-center">
          <span className="material-icons text-red-400 text-4xl mb-4">error</span>
          <h2 className="text-xl font-bold text-red-400 mb-2">보고서를 불러올 수 없습니다</h2>
          <p className="text-red-300 text-sm mb-6">{error}</p>
          <Link
            href="/reports"
            className="inline-flex items-center gap-2 px-6 py-3 glass-panel-hover rounded-lg font-medium transition-all"
          >
            <span className="material-icons text-sm">arrow_back</span>
            보고서 목록으로
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0f1216]">
      {/* Header */}
      <header className="sticky top-0 z-50 glass-panel">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-3">
                <span className="material-icons text-[#137fec] text-2xl">biotech</span>
                <span className="text-lg font-bold">BioLab AI</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <Link href="/" className="hover:text-white transition-colors">Dashboard</Link>
                <span className="material-icons text-xs">chevron_right</span>
                <Link href="/reports" className="hover:text-white transition-colors">Reports</Link>
                <span className="material-icons text-xs">chevron_right</span>
                <span className="text-white truncate max-w-[300px]">{topic || decodedFilename}</span>
              </div>
            </div>

            <Link
              href="/reports"
              className="flex items-center gap-2 px-4 py-2 glass-panel-light rounded-lg hover:bg-white/10 transition-all text-sm text-gray-300"
            >
              <span className="material-icons text-base">arrow_back</span>
              목록
            </Link>
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="container mx-auto px-6 py-8">
        <main>
          <div className="bg-grid min-h-screen">
            {/* Floating Toolbar */}
            <div className="sticky top-24 z-10 mb-6">
              <div className="glass-panel rounded-lg px-6 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="px-3 py-1 bg-red-500/20 text-red-400 text-xs rounded-full font-semibold border border-red-500/30">
                    CONFIDENTIAL
                  </span>
                  {createdAt && (
                    <span className="text-sm text-gray-400">Last updated: {createdAt}</span>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  {/* Language toggle / Translate button */}
                  {translatedReport ? (
                    <div className="flex items-center rounded-lg overflow-hidden border border-gray-600">
                      <button
                        onClick={() => setLang('ko')}
                        className={`px-3 py-2 text-sm font-medium transition-colors ${
                          lang === 'ko'
                            ? 'bg-[#137fec] text-white'
                            : 'bg-transparent text-gray-400 hover:text-white'
                        }`}
                      >
                        한국어
                      </button>
                      <button
                        onClick={() => setLang('en')}
                        className={`px-3 py-2 text-sm font-medium transition-colors ${
                          lang === 'en'
                            ? 'bg-[#137fec] text-white'
                            : 'bg-transparent text-gray-400 hover:text-white'
                        }`}
                      >
                        English
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={handleTranslate}
                      disabled={isTranslating}
                      className="flex items-center gap-2 px-4 py-2 text-sm text-gray-300 glass-panel-light rounded-lg hover:bg-white/10 transition-colors disabled:opacity-50"
                    >
                      {isTranslating ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-[#137fec]"></div>
                          Translating...
                        </>
                      ) : (
                        <>Translate to English</>
                      )}
                    </button>
                  )}

                  <button
                    onClick={handleDownloadTxt}
                    className="flex items-center gap-2 px-4 py-2 text-sm text-white bg-[#137fec] rounded-lg hover:bg-[#0e6bc9] transition-colors"
                  >
                    <span className="material-icons text-base">download</span>
                    Export TXT{lang === 'en' ? ' (EN)' : ''}
                  </button>
                </div>
              </div>
            </div>

            {/* Status Message */}
            {message && (
              <div
                className={`mb-6 glass-panel rounded-lg px-6 py-4 border-l-4 ${
                  message.includes('실패')
                    ? 'border-red-500 bg-red-500/10'
                    : 'border-green-500 bg-green-500/10'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className={`material-icons ${message.includes('실패') ? 'text-red-400' : 'text-green-400'}`}>
                    {message.includes('실패') ? 'error' : 'check_circle'}
                  </span>
                  <span className={message.includes('실패') ? 'text-red-300' : 'text-green-300'}>
                    {message}
                  </span>
                </div>
              </div>
            )}

            {/* Paper Document Container */}
            <div className="relative">
              <div className="report-paper rounded-lg shadow-2xl overflow-hidden relative">
                {/* Corner borders */}
                <div className="absolute top-0 left-0 w-12 h-12 border-t-4 border-l-4 border-[#137fec]/30"></div>
                <div className="absolute top-0 right-0 w-12 h-12 border-t-4 border-r-4 border-[#137fec]/30"></div>
                <div className="absolute bottom-0 left-0 w-12 h-12 border-b-4 border-l-4 border-[#137fec]/30"></div>
                <div className="absolute bottom-0 right-0 w-12 h-12 border-b-4 border-r-4 border-[#137fec]/30"></div>

                <div className="min-h-[800px]">
                  <ReportEditor
                    report={lang === 'en' && translatedReport ? translatedReport : report}
                    onRegenerate={handleRegenerate}
                    isLoading={isRegenerating}
                  />
                </div>
              </div>
            </div>

            {/* Loading indicator */}
            {(isRegenerating || isTranslating) && (
              <div className="mt-6 glass-panel rounded-lg px-6 py-4">
                <div className="flex items-center gap-3">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-[#137fec]"></div>
                  <span className="text-gray-400">
                    {isTranslating ? 'Translating to English...' : '재생성 중...'}
                  </span>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
