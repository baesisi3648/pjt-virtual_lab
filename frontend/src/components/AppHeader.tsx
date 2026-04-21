'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useLocale } from '@/lib/i18n';

export type AppHeaderCurrent = 'dashboard' | 'reports' | 'history' | null;

interface AppHeaderProps {
  current?: AppHeaderCurrent;
}

/**
 * 모든 페이지에서 공유되는 헤더.
 *
 * 구성:
 * - Left: 클릭 가능한 로고 (h-16, "/"로 이동)
 * - Center: Dashboard / Reports / History pill nav
 * - Right: 언어 토글 (KO/EN) + Backend 상태 (컴팩트)
 *
 * max-w-7xl로 통일, 3-column grid로 nav 정중앙 배치.
 * 로컬 실행 환경: .env의 OPENAI_API_KEY를 사용하므로 API Key 토글 불필요.
 */
export default function AppHeader({ current = null }: AppHeaderProps) {
  const [backendStatus, setBackendStatus] = useState<'online' | 'offline' | 'checking'>(
    'checking'
  );
  const { locale, setLocale, t } = useLocale();

  useEffect(() => {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    fetch(`${API_BASE_URL}/health`)
      .then((res) =>
        res.ok ? setBackendStatus('online') : setBackendStatus('offline')
      )
      .catch(() => setBackendStatus('offline'));
  }, []);

  const navItems: { id: Exclude<AppHeaderCurrent, null>; label: string; href: string }[] = [
    { id: 'dashboard', label: 'Dashboard', href: '/' },
    { id: 'reports', label: 'Reports', href: '/reports' },
    { id: 'history', label: 'History', href: '/history' },
  ];

  const backendLabel =
    backendStatus === 'online'
      ? t('header.backend.live')
      : backendStatus === 'offline'
      ? t('header.backend.offline')
      : '...';

  const backendDotClass =
    backendStatus === 'online'
      ? 'bg-green-500'
      : backendStatus === 'offline'
      ? 'bg-red-500'
      : 'bg-yellow-500 animate-pulse';

  return (
    <header className="sticky top-0 z-50 bg-white border-b border-[var(--border)] shadow-sm">
      <div className="max-w-7xl mx-auto px-8 py-4 grid grid-cols-[1fr_auto_1fr] items-center gap-4">
        {/* Left: Logo (clickable, 확대됨) */}
        <Link
          href="/"
          className="flex items-center justify-self-start hover:opacity-80 transition-opacity"
          aria-label="Dashboard로 이동"
        >
          <img src="/logo.png" alt="Virtual Lab" className="h-16" />
        </Link>

        {/* Center: Pill Nav */}
        <nav className="bg-[var(--background)] border border-[var(--border)] rounded-full p-1 flex items-center gap-1 justify-self-center">
          {navItems.map((item) => {
            const isActive = current === item.id;
            return isActive ? (
              <span
                key={item.id}
                className="px-5 py-2 bg-[var(--primary)] text-white rounded-full text-sm font-medium"
              >
                {item.label}
              </span>
            ) : (
              <Link
                key={item.id}
                href={item.href}
                className="px-5 py-2 text-[var(--text-muted)] hover:text-[var(--primary)] rounded-full text-sm font-medium transition-colors"
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Right: Language + Backend (compact) */}
        <div className="flex items-center gap-2 justify-self-end">
          {/* Language Toggle (KO / EN) */}
          <div className="flex items-center rounded-full bg-white border border-[var(--border)] overflow-hidden">
            <button
              onClick={() => setLocale('ko')}
              className={`px-2.5 py-1.5 text-xs font-semibold transition-colors ${
                locale === 'ko'
                  ? 'bg-[var(--primary)] text-white'
                  : 'text-[var(--text-muted)] hover:text-[var(--foreground)]'
              }`}
              aria-label="한국어"
            >
              KO
            </button>
            <button
              onClick={() => setLocale('en')}
              className={`px-2.5 py-1.5 text-xs font-semibold transition-colors ${
                locale === 'en'
                  ? 'bg-[var(--primary)] text-white'
                  : 'text-[var(--text-muted)] hover:text-[var(--foreground)]'
              }`}
              aria-label="English"
            >
              EN
            </button>
          </div>

          <div
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white border border-[var(--border)]"
            title={`Backend ${backendLabel}`}
          >
            <span className={`w-2 h-2 rounded-full ${backendDotClass}`} />
            <span className="text-xs text-[var(--text-muted)]">{backendLabel}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
