'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { fetchReports, deleteReport, type ReportListItem } from '@/lib/api';

export default function ReportsPage() {
  const [reports, setReports] = useState<ReportListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchReports()
      .then(setReports)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    return `${(bytes / 1024).toFixed(1)} KB`;
  };

  const handleDelete = async (filename: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm('이 보고서를 삭제하시겠습니까?')) return;
    try {
      await deleteReport(filename);
      setReports((prev) => prev.filter((r) => r.filename !== filename));
    } catch (err) {
      alert(`삭제 실패: ${err instanceof Error ? err.message : '알 수 없는 오류'}`);
    }
  };

  return (
    <div className="min-h-screen bg-[#101922] text-white">
      {/* Header */}
      <header className="sticky top-0 z-50 glass-panel border-b border-white/10">
        <div className="max-w-[1800px] mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
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

            <nav className="flex items-center gap-2 bg-white/5 rounded-full p-1.5">
              <Link href="/" className="px-6 py-2 hover:bg-white/5 rounded-full text-sm font-medium transition-colors">
                Dashboard
              </Link>
              <Link href="/timeline" className="px-6 py-2 hover:bg-white/5 rounded-full text-sm font-medium transition-colors">
                Agents
              </Link>
              <div className="px-6 py-2 bg-[#137fec] rounded-full text-sm font-medium">
                Reports
              </div>
            </nav>

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

      {/* Main */}
      <main className="max-w-[1200px] mx-auto px-6 py-8">
        <div className="flex items-center gap-3 mb-8">
          <span className="material-symbols-outlined text-[#0bda5b] text-3xl">description</span>
          <div>
            <h2 className="text-2xl font-bold">Research Reports</h2>
            <p className="text-white/40 text-sm">AI가 생성한 연구 보고서 목록</p>
          </div>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#137fec] mx-auto mb-3"></div>
              <p className="text-white/40 font-mono text-sm">Loading reports...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="glass-panel border-2 border-red-500/30 p-6 rounded-lg">
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-red-400">error</span>
              <p className="text-red-300">{error}</p>
            </div>
          </div>
        )}

        {!loading && !error && reports.length === 0 && (
          <div className="glass-panel p-12 rounded-lg text-center">
            <span className="material-symbols-outlined text-white/20 mb-4" style={{ fontSize: '64px' }}>
              folder_open
            </span>
            <h3 className="text-xl font-semibold text-white/60 mb-2">보고서가 없습니다</h3>
            <p className="text-white/40 text-sm mb-6">
              연구를 실행하면 보고서가 자동으로 저장됩니다.
            </p>
            <Link
              href="/timeline"
              className="inline-flex items-center gap-2 px-6 py-3 bg-[#137fec] hover:bg-[#137fec]/80 rounded-lg font-medium transition-colors"
            >
              <span className="material-symbols-outlined text-sm">play_arrow</span>
              연구 시작하기
            </Link>
          </div>
        )}

        {!loading && !error && reports.length > 0 && (
          <div className="space-y-4">
            {reports.map((report) => (
              <div
                key={report.filename}
                className="glass-panel-hover p-6 rounded-lg group transition-all"
              >
                <div className="flex items-center justify-between">
                  <Link
                    href={`/reports/${encodeURIComponent(report.filename)}`}
                    className="flex items-center gap-4 flex-1 min-w-0"
                  >
                    <div className="w-12 h-12 rounded-lg bg-[#137fec]/10 flex items-center justify-center flex-shrink-0 group-hover:bg-[#137fec]/20 transition-colors">
                      <span className="material-symbols-outlined text-[#137fec] text-2xl">article</span>
                    </div>
                    <div className="min-w-0">
                      <h3 className="text-lg font-semibold truncate group-hover:text-[#137fec] transition-colors">
                        {report.topic}
                      </h3>
                      <div className="flex items-center gap-4 text-sm text-white/40 mt-1">
                        <span className="flex items-center gap-1">
                          <span className="material-symbols-outlined text-xs">calendar_today</span>
                          {report.created_at}
                        </span>
                        <span className="flex items-center gap-1">
                          <span className="material-symbols-outlined text-xs">straighten</span>
                          {formatSize(report.size)}
                        </span>
                      </div>
                    </div>
                  </Link>
                  <div className="flex items-center gap-3 flex-shrink-0 ml-4">
                    <button
                      onClick={(e) => handleDelete(report.filename, e)}
                      className="flex items-center gap-1.5 px-3 py-2 text-sm text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-colors"
                      title="보고서 삭제"
                    >
                      <span className="material-symbols-outlined text-base">delete</span>
                      <span className="hidden sm:inline">삭제</span>
                    </button>
                    <Link href={`/reports/${encodeURIComponent(report.filename)}`}>
                      <span className="material-symbols-outlined text-white/20 group-hover:text-[#137fec] transition-colors text-2xl">
                        chevron_right
                      </span>
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
