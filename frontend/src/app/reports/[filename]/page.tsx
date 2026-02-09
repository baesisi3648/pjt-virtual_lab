'use client';

import { useState, useEffect, use } from 'react';
import Link from 'next/link';
import ReportEditor from '@/components/ReportEditor';
import { fetchReportContent, regenerateSection } from '@/lib/api';

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
  const [activeSection, setActiveSection] = useState('executive-summary');

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

  const navSections = [
    { id: 'executive-summary', label: 'Executive Summary', icon: 'dashboard' },
    { id: 'risk-analysis', label: 'Risk Analysis', icon: 'analytics' },
    { id: 'guideline-assessment', label: 'Guideline Assessment', icon: 'science' },
    { id: 'update-items', label: 'Update Items', icon: 'genetics' },
    { id: 'conclusion', label: 'Conclusion', icon: 'verified_user' },
  ];

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

      {/* Two-column layout */}
      <div className="container mx-auto px-6 py-8 flex gap-8">
        {/* Left Sidebar */}
        <aside className="w-64 hidden lg:block flex-shrink-0">
          <div className="sticky top-24 space-y-6">
            {/* Navigation */}
            <div className="glass-panel-light rounded-lg p-4">
              <h2 className="text-xs uppercase tracking-wider text-gray-500 mb-4">Report Sections</h2>
              <nav className="space-y-2">
                {navSections.map((section) => (
                  <button
                    key={section.id}
                    onClick={() => setActiveSection(section.id)}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                      activeSection === section.id
                        ? 'bg-[#137fec]/10 text-[#137fec] border-l-2 border-[#137fec]'
                        : 'text-gray-400 hover:text-white hover:bg-white/5'
                    }`}
                  >
                    <span className="material-icons text-base">{section.icon}</span>
                    <span>{section.label}</span>
                  </button>
                ))}
              </nav>
            </div>

            {/* Meta Info */}
            <div className="glass-panel-light rounded-lg p-4">
              <div className="space-y-3 text-sm">
                {topic && (
                  <div>
                    <span className="text-xs text-gray-500">Topic</span>
                    <p className="text-gray-300 mt-1">{topic}</p>
                  </div>
                )}
                {createdAt && (
                  <div>
                    <span className="text-xs text-gray-500">Created</span>
                    <p className="text-gray-300 mt-1">{createdAt}</p>
                  </div>
                )}
                <div>
                  <span className="text-xs text-gray-500">Status</span>
                  <div className="mt-1">
                    <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded font-semibold">
                      COMPLETED
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 min-w-0">
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
                <a
                  href={`${API_BASE_URL}/api/reports/${encodeURIComponent(decodedFilename)}`}
                  download
                  className="flex items-center gap-2 px-4 py-2 text-sm text-white bg-[#137fec] rounded-lg hover:bg-[#0e6bc9] transition-colors"
                >
                  <span className="material-icons text-base">download</span>
                  Export TXT
                </a>
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
                    report={report}
                    onRegenerate={handleRegenerate}
                    isLoading={isRegenerating}
                  />
                </div>
              </div>
            </div>

            {/* Loading indicator */}
            {isRegenerating && (
              <div className="mt-6 glass-panel rounded-lg px-6 py-4">
                <div className="flex items-center gap-3">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-[#137fec]"></div>
                  <span className="text-gray-400">재생성 중...</span>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
