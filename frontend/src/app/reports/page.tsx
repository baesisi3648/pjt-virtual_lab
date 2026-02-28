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
    <div className="min-h-screen bg-[#f6f8f7] text-[#121714]">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white border-b border-[#dde4e0] shadow-sm">
        <div className="max-w-[1800px] mx-auto px-10 py-3">
          <div className="flex items-center justify-between">
            {/* Left: Logo + Brand */}
            <div className="flex items-center">
              <img src="/logo.png" alt="Virtual Lab" className="h-10" />
            </div>

            {/* Center: Nav Links */}
            <nav className="flex items-center gap-6">
              <Link
                href="/"
                className="text-sm font-medium text-[#678373] hover:text-[#1b7440] transition-colors pb-0.5"
              >
                Dashboard
              </Link>
              <Link
                href="/timeline"
                className="text-sm font-medium text-[#678373] hover:text-[#1b7440] transition-colors pb-0.5"
              >
                Agents
              </Link>
              <span className="text-sm font-bold text-[#1b7440] border-b-2 border-[#1b7440] pb-0.5">
                Reports
              </span>
            </nav>

            {/* Right: Back to Home */}
            <Link
              href="/"
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-[#678373] hover:text-[#1b7440] hover:bg-[#1b7440]/5 transition-all"
            >
              <span className="material-symbols-outlined text-sm">arrow_back</span>
              Back to Home
            </Link>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="max-w-[1200px] mx-auto px-6 py-10">
        {/* Page Title Section */}
        <div className="mb-8">
          <div className="flex items-center gap-2 text-sm text-[#678373] mb-4">
            <Link href="/" className="hover:text-[#1b7440] transition-colors">Home</Link>
            <span className="material-symbols-outlined text-base">chevron_right</span>
            <span>Research Reports</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-[#1b7440]/10 flex items-center justify-center flex-shrink-0">
              <span className="material-symbols-outlined text-[#1b7440] text-2xl">description</span>
            </div>
            <div>
              <h1 className="text-4xl font-bold text-[#121714]">Research Reports</h1>
              <p className="text-[#678373] mt-1">AI가 생성한 연구 보고서 목록</p>
            </div>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#1b7440] mx-auto mb-3"></div>
              <p className="text-[#678373] text-sm">Loading reports...</p>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-white border-2 border-red-200 p-6 rounded-xl">
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-red-500">error</span>
              <p className="text-red-600">{error}</p>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && reports.length === 0 && (
          <div className="bg-white rounded-xl border border-dashed border-slate-300 p-12 text-center">
            <div className="w-20 h-20 rounded-full bg-slate-50 flex items-center justify-center mx-auto mb-4">
              <span className="material-symbols-outlined text-slate-400 text-[40px]">
                folder_open
              </span>
            </div>
            <h3 className="text-xl font-semibold text-[#121714] mb-2">보고서가 없습니다</h3>
            <p className="text-[#678373] text-sm mb-6">
              연구를 실행하면 보고서가 자동으로 저장됩니다.
            </p>
            <Link
              href="/timeline"
              className="inline-flex items-center gap-2 px-6 py-3 border border-slate-300 hover:bg-slate-50 rounded-xl font-medium text-[#121714] transition-colors"
            >
              <span className="material-symbols-outlined text-sm">play_arrow</span>
              연구 시작하기
            </Link>
          </div>
        )}

        {/* Report List */}
        {!loading && !error && reports.length > 0 && (
          <div className="space-y-3">
            {reports.map((report) => (
              <div
                key={report.filename}
                className="bg-white rounded-xl border border-slate-200 p-5 group
                           hover:border-[#1b7440]/50 hover:shadow-lg hover:shadow-[#1b7440]/5
                           transition-all duration-200"
              >
                <div className="flex items-center justify-between">
                  <Link
                    href={`/reports/${encodeURIComponent(report.filename)}`}
                    className="flex items-center gap-4 flex-1 min-w-0"
                  >
                    {/* Icon */}
                    <div className="w-11 h-11 rounded-lg bg-[#1b7440]/10 flex items-center justify-center flex-shrink-0 group-hover:bg-[#1b7440] transition-colors duration-200">
                      <span className="material-symbols-outlined text-[#1b7440] text-xl group-hover:text-white transition-colors duration-200">
                        article
                      </span>
                    </div>

                    {/* Text */}
                    <div className="min-w-0">
                      <h3 className="text-lg font-bold text-[#121714] truncate group-hover:text-[#1b7440] transition-colors duration-200">
                        {report.topic}
                      </h3>
                      <div className="flex items-center gap-4 text-sm text-[#678373] mt-1">
                        <span className="flex items-center gap-1">
                          <span className="material-symbols-outlined text-xs">calendar_today</span>
                          {report.created_at}
                        </span>
                        <span className="flex items-center gap-1">
                          <span className="material-symbols-outlined text-xs">sd_storage</span>
                          {formatSize(report.size)}
                        </span>
                      </div>
                    </div>
                  </Link>

                  {/* Actions */}
                  <div className="flex items-center gap-2 flex-shrink-0 ml-4">
                    <button
                      onClick={(e) => handleDelete(report.filename, e)}
                      className="flex items-center gap-1.5 px-3 py-2 text-sm text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                      title="보고서 삭제"
                    >
                      <span className="material-symbols-outlined text-base">delete</span>
                      <span className="hidden sm:inline">삭제</span>
                    </button>
                    <Link href={`/reports/${encodeURIComponent(report.filename)}`}>
                      <span className="material-symbols-outlined text-[#678373] group-hover:text-[#1b7440] transition-colors duration-200 text-2xl">
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
