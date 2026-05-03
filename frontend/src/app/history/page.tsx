'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import AppHeader from '@/components/AppHeader';
import { fetchSessions, type SessionListItem } from '@/lib/api';
import { useLocale } from '@/lib/i18n';

export default function HistoryPage() {
  const [sessions, setSessions] = useState<SessionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { t, locale } = useLocale();

  useEffect(() => {
    fetchSessions()
      .then(setSessions)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const statusLabel = (status: string) => {
    switch (status) {
      case 'running': return { text: t('history.status.running'), color: 'bg-blue-100 text-blue-700' };
      case 'completed': return { text: t('history.status.completed'), color: 'bg-green-100 text-green-700' };
      case 'error': return { text: t('history.status.error'), color: 'bg-red-100 text-red-700' };
      default: return { text: status, color: 'bg-gray-100 text-gray-700' };
    }
  };

  const dateLocale = locale === 'en' ? 'en-US' : 'ko-KR';

  return (
    <div className="min-h-screen bg-[#f6f8f7] text-[#121714]">
      <AppHeader current="history" />

      <main className="max-w-[1200px] mx-auto px-10 py-8">
        <h1 className="text-2xl font-bold mb-6">{t('history.title')}</h1>
        <p className="text-[#678373] mb-8">{t('history.subtitle')}</p>

        {loading && <p className="text-[#678373]">{t('history.loading')}</p>}
        {error && <p className="text-red-600">{error}</p>}

        {!loading && sessions.length === 0 && (
          <p className="text-[#678373]">{t('history.empty')}</p>
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
                      <span>{new Date(session.created_at).toLocaleString(dateLocale)}</span>
                      {session.total_rounds > 0 && (
                        <span>
                          {session.total_rounds} {t('history.roundsSuffix')}
                        </span>
                      )}
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
