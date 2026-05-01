'use client';

import { useState, useEffect, use } from 'react';
import Link from 'next/link';
import AppHeader from '@/components/AppHeader';
import ReportEditor from '@/components/ReportEditor';
import { fetchReportContent, regenerateSection, translateReport } from '@/lib/api';
import { useLocale } from '@/lib/i18n';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function ReportViewerPage({
  params,
}: {
  params: Promise<{ filename: string }>;
}) {
  const { filename } = use(params);
  const decodedFilename = decodeURIComponent(filename);

  // English is now the primary language (the workflow generates EN first,
  // then auto-translates to KO as a sidecar). The toggle swaps between the
  // two precomputed renderings; an on-demand fallback via translateReport()
  // is kept for legacy reports that lack a sidecar.
  const [reportEn, setReportEn] = useState('');
  const [reportKo, setReportKo] = useState('');
  const [koAvailable, setKoAvailable] = useState(false);
  const [topic, setTopic] = useState('');
  const [createdAt, setCreatedAt] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [message, setMessage] = useState('');
  const [isTranslating, setIsTranslating] = useState(false);
  const [lang, setLang] = useState<'ko' | 'en'>('en');
  const [downloadHref, setDownloadHref] = useState('');
  const [downloadName, setDownloadName] = useState('');
  const { t } = useLocale();

  useEffect(() => {
    fetchReportContent(decodedFilename, 'en')
      .then((data) => {
        setReportEn(data.content);
        setTopic(data.topic);
        setCreatedAt(data.created_at);
        setKoAvailable(Boolean(data.ko_available));
        if (data.ko_available) {
          // Pre-fetch the Korean sidecar so the toggle is instantaneous.
          fetchReportContent(decodedFilename, 'ko')
            .then((ko) => setReportKo(ko.content))
            .catch(() => {
              // sidecar missing or other error — fall back to on-demand translation
            });
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [decodedFilename]);

  const currentReport = lang === 'ko' ? reportKo || reportEn : reportEn;

  const handleRegenerate = async (request: { section: string; feedback: string }) => {
    setIsRegenerating(true);
    setMessage('');
    try {
      const response = await regenerateSection({
        section: request.section,
        feedback: request.feedback,
        current_report: currentReport,
      });
      // Update whichever language is currently displayed.
      if (lang === 'ko') {
        setReportKo(response.updated_report);
      } else {
        setReportEn(response.updated_report);
      }
      setMessage(response.message);
    } catch (err) {
      setMessage(`Regeneration failed: ${err instanceof Error ? err.message : 'unknown error'}`);
    } finally {
      setIsRegenerating(false);
    }
  };

  const handleTranslate = async () => {
    // On-demand fallback for legacy reports without a Korean sidecar.
    setIsTranslating(true);
    setMessage('');
    try {
      const response = await translateReport(reportEn);
      setReportKo(response.translated);
      setKoAvailable(true);
      setLang('ko');
      setMessage('Translation completed successfully.');
    } catch (err) {
      setMessage(`Translation failed: ${err instanceof Error ? err.message : 'unknown error'}`);
    } finally {
      setIsTranslating(false);
    }
  };

  const handleDownloadTxt = () => {
    const content = currentReport;
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const suffix = lang === 'ko' ? '_KO' : '_EN';
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
          <p className="text-slate-500 text-sm">{t('reportDetail.loading')}</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="bg-white border-2 border-red-200 p-8 rounded-xl max-w-md text-center shadow-sm">
          <span className="material-icons text-red-400 text-4xl mb-4 block">error</span>
          <h2 className="text-xl font-bold text-red-600 mb-2">{t('reportDetail.errorTitle')}</h2>
          <p className="text-red-500 text-sm mb-6">{error}</p>
          <Link
            href="/reports"
            className="inline-flex items-center gap-2 px-6 py-3 bg-slate-100 hover:bg-slate-200 rounded-lg font-medium text-slate-700 transition-all"
          >
            <span className="material-icons text-sm">arrow_back</span>
            {t('reportDetail.errorBack')}
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

      <AppHeader current="reports" />

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
                report={currentReport}
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
                  {isTranslating ? t('reportDetail.translating') : t('reportDetail.regenerating')}
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
            {koAvailable || reportKo ? (
              <div className="flex items-center rounded-full overflow-hidden border border-slate-700">
                <button
                  onClick={() => setLang('en')}
                  className={`px-3 py-1.5 text-xs font-medium transition-colors rounded-full ${
                    lang === 'en'
                      ? 'bg-white text-slate-900'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {t('reportDetail.lang.en')}
                </button>
                <button
                  onClick={() => setLang('ko')}
                  className={`px-3 py-1.5 text-xs font-medium transition-colors rounded-full ${
                    lang === 'ko'
                      ? 'bg-white text-slate-900'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {t('reportDetail.lang.ko')}
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
                    {t('reportDetail.translating')}
                  </>
                ) : (
                  <>{t('reportDetail.translate')}</>
                )}
              </button>
            )}

            <button
              onClick={handleDownloadTxt}
              className="btn-primary flex items-center gap-1.5 px-4 py-1.5 text-xs text-white bg-primary rounded-full transition-colors font-medium"
            >
              <span className="material-icons text-sm">download</span>
              Export TXT ({lang.toUpperCase()})
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
