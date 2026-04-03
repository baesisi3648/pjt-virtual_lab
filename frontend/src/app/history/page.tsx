'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { fetchSessions, type SessionListItem } from '@/lib/api';

export default function HistoryPage() {
  const [sessions, setSessions] = useState<SessionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchSessions()
      .then(setSessions)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const statusLabel = (status: string) => {
    switch (status) {
      case 'running': return { text: '진행 중', color: 'bg-blue-100 text-blue-700' };
      case 'completed': return { text: '완료', color: 'bg-green-100 text-green-700' };
      case 'error': return { text: '오류', color: 'bg-red-100 text-red-700' };
      default: return { text: status, color: 'bg-gray-100 text-gray-700' };
    }
  };

  return (
    <div className="min-h-screen bg-[#f6f8f7] text-[#121714]">
      <header className="sticky top-0 z-50 bg-white border-b border-[#dde4e0] shadow-sm">
        <div className="max-w-[1800px] mx-auto px-10 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <img src="/logo.png" alt="Virtual Lab" className="h-12" />
            </div>
            <nav className="flex items-center gap-6">
              <Link href="/" className="text-sm font-medium text-[#678373] hover:text-[#1b7440] transition-colors pb-0.5">Dashboard</Link>
              <Link href="/timeline" className="text-sm font-medium text-[#678373] hover:text-[#1b7440] transition-colors pb-0.5">Agents</Link>
              <Link href="/reports" className="text-sm font-medium text-[#678373] hover:text-[#1b7440] transition-colors pb-0.5">Reports</Link>
              <span className="text-sm font-bold text-[#1b7440] border-b-2 border-[#1b7440] pb-0.5">History</span>
            </nav>
            <Link href="/" className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-[#678373] hover:text-[#1b7440] hover:bg-[#1b7440]/5 transition-all">
              <span className="material-symbols-outlined text-sm">arrow_back</span>
              Back to Home
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-[1200px] mx-auto px-10 py-8">
        <h1 className="text-2xl font-bold mb-6">Research History</h1>
        <p className="text-[#678373] mb-8">에이전트 회의 과정을 라운드별로 확인할 수 있습니다.</p>

        {loading && <p className="text-[#678373]">로딩 중...</p>}
        {error && <p className="text-red-600">{error}</p>}

        {!loading && sessions.length === 0 && (
          <p className="text-[#678373]">아직 연구 세션이 없습니다. Dashboard에서 연구를 시작해보세요.</p>
        )}

        <div className="space-y-3">
          {sessions.map((session) => {
            const sl = statusLabel(session.status);
            return (
              <Link
                key={session.id}
                href={`/history/${session.id}`}
                className="block bg-white rounded-xl border border-[#dde4e0] p-5 hover:shadow-md hover:border-[#1b7440]/30 transition-all"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg mb-1">{session.topic}</h3>
                    <div className="flex items-center gap-3 text-sm text-[#678373]">
                      <span>{new Date(session.created_at).toLocaleString('ko-KR')}</span>
                      {session.total_rounds > 0 && <span>{session.total_rounds}라운드</span>}
                    </div>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${sl.color}`}>
                    {sl.text}
                  </span>
                </div>
              </Link>
            );
          })}
        </div>
      </main>
    </div>
  );
}
