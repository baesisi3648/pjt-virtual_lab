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
  const [downloadHref, setDownloadHref] = useState('');
  const [downloadName, setDownloadName] = useState('');

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
    const suffix = lang === 'en' ? '_EN' : '';
    setDownloadName(`${decodedFilename.replace('.txt', '')}${suffix}.txt`);
    setDownloadHref(url);
  };

  const handleDownloadMounted = (node: HTMLAnchorElement | null) => {
    if (node) {
      node.click();
      URL.revokeObjectURL(downloadHref);
      setDownloadHref('');
      setDownloadName('');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-3"></div>
          <p className="text-slate-500 text-sm">Loading report...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="bg-white border-2 border-red-200 p-8 rounded-xl max-w-md text-center shadow-sm">
          <span className="material-icons text-red-400 text-4xl mb-4 block">error</span>
          <h2 className="text-xl font-bold text-red-600 mb-2">보고서를 불러올 수 없습니다</h2>
          <p className="text-red-500 text-sm mb-6">{error}</p>
          <Link
            href="/reports"
            className="inline-flex items-center gap-2 px-6 py-3 bg-slate-100 hover:bg-slate-200 rounded-lg font-medium text-slate-700 transition-all"
          >
            <span className="material-icons text-sm">arrow_back</span>
            보고서 목록으로
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {downloadHref && (
        <a
          ref={handleDownloadMounted}
          href={downloadHref}
          download={downloadName}
          className="sr-only"
          aria-hidden="true"
        />
      )}

      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/90 backdrop-blur-md border-b border-slate-200">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6">
              <div className="flex items-center">
                <img src="/logo.png" alt="Virtual Lab" className="h-8" />
              </div>
              <nav className="hidden md:flex items-center gap-1 text-sm">
                <Link
                  href="/"
                  className="px-3 py-1.5 rounded-md text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors"
                >
                  Dashboard
                </Link>
                <Link
                  href="/reports"
                  className="px-3 py-1.5 rounded-md text-white bg-primary font-medium transition-colors"
                >
                  Reports
                </Link>
              </nav>
            </div>

            <Link
              href="/reports"
              className="flex items-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 rounded-lg text-sm text-slate-700 font-medium transition-all"
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
          {/* Breadcrumb bar */}
          <nav className="mb-6 flex items-center gap-1.5 text-sm text-slate-500">
            <Link href="/" className="hover:text-slate-900 transition-colors">Dashboard</Link>
            <span className="material-icons text-xs">chevron_right</span>
            <Link href="/reports" className="hover:text-slate-900 transition-colors">Reports</Link>
            <span className="material-icons text-xs">chevron_right</span>
            <span className="text-slate-900 font-semibold truncate max-w-[300px]">
              {topic || decodedFilename}
            </span>
          </nav>

          {/* Status Message */}
          {message && (
            <div
              className={`mb-6 rounded-lg px-6 py-4 border-l-4 ${
                message.includes('실패')
                  ? 'bg-red-50 border-red-500'
                  : 'bg-green-50 border-primary'
              }`}
            >
              <div className="flex items-center gap-3">
                <span
                  className={`material-icons ${
                    message.includes('실패') ? 'text-red-500' : 'text-primary'
                  }`}
                >
                  {message.includes('실패') ? 'error' : 'check_circle'}
                </span>
                <span
                  className={
                    message.includes('실패') ? 'text-red-700' : 'text-primary'
                  }
                >
                  {message}
                </span>
              </div>
            </div>
          )}

          {/* Paper Document Container */}
          <article className="relative bg-white rounded-xl border border-slate-100 shadow-paper min-h-[800px] overflow-hidden">
            <div className="corner-accent absolute top-0 left-0 w-16 h-16 rounded-tl-xl pointer-events-none"></div>

            <div className="min-h-[800px]">
              <ReportEditor
                report={lang === 'en' && translatedReport ? translatedReport : report}
                onRegenerate={handleRegenerate}
                isLoading={isRegenerating}
              />
            </div>
          </article>

          {/* In-progress indicator */}
          {(isRegenerating || isTranslating) && (
            <div className="mt-6 bg-white rounded-xl border border-slate-100 shadow-sm px-6 py-4">
              <div className="flex items-center gap-3">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary"></div>
                <span className="text-slate-600 text-sm">
                  {isTranslating ? 'Translating to English...' : '재생성 중...'}
                </span>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* Floating Toolbar */}
      <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50">
        <div className="bg-slate-900 text-white rounded-full shadow-floating p-2 flex items-center gap-3 px-4">
          <div className="flex items-center gap-2.5">
            <span className="flex items-center gap-1.5 text-xs font-semibold text-red-400">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-red-500"></span>
              CONFIDENTIAL
            </span>
            {createdAt && (
              <span className="text-xs text-slate-400 hidden sm:inline">
                {createdAt}
              </span>
            )}
          </div>

          <div className="w-px h-5 bg-slate-700"></div>

          <div className="flex items-center gap-2">
            {translatedReport ? (
              <div className="flex items-center rounded-full overflow-hidden border border-slate-700">
                <button
                  onClick={() => setLang('ko')}
                  className={`px-3 py-1.5 text-xs font-medium transition-colors rounded-full ${
                    lang === 'ko'
                      ? 'bg-white text-slate-900'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  한국어
                </button>
                <button
                  onClick={() => setLang('en')}
                  className={`px-3 py-1.5 text-xs font-medium transition-colors rounded-full ${
                    lang === 'en'
                      ? 'bg-white text-slate-900'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  English
                </button>
              </div>
            ) : (
              <button
                onClick={handleTranslate}
                disabled={isTranslating}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-slate-300 hover:text-white rounded-full hover:bg-slate-800 transition-colors disabled:opacity-50"
              >
                {isTranslating ? (
                  <>
                    <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-primary"></div>
                    Translating...
                  </>
                ) : (
                  <>Translate to English</>
                )}
              </button>
            )}

            <button
              onClick={handleDownloadTxt}
              className="btn-primary flex items-center gap-1.5 px-4 py-1.5 text-xs text-white bg-primary rounded-full transition-colors font-medium"
            >
              <span className="material-icons text-sm">download</span>
              Export TXT{lang === 'en' ? ' (EN)' : ''}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
