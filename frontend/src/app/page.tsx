'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import AppHeader from '@/components/AppHeader';
import WorkflowPipeline from '@/components/WorkflowPipeline';
import { useLocale } from '@/lib/i18n';

export default function HomePage() {
  const router = useRouter();
  const [backendStatus, setBackendStatus] = useState<'online' | 'offline' | 'checking'>('checking');
  const { t } = useLocale();
  const RESEARCH_TOPIC = "유전자편집식품(NGT) 표준 안전성 평가 프레임워크 도출";

  useEffect(() => {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    fetch(`${API_BASE_URL}/health`)
      .then(res => res.ok ? setBackendStatus('online') : setBackendStatus('offline'))
      .catch(() => setBackendStatus('offline'));
  }, []);

  const handleStart = () => {
    router.push(`/timeline?topic=${encodeURIComponent(RESEARCH_TOPIC)}`);
  };

  return (
    <div className="min-h-screen">
      <AppHeader current="dashboard" />

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-6">

        {/* Hero Section */}
        <section className="flex flex-col items-center text-center pt-12 pb-6 gap-4">
          <h2 className="text-4xl font-bold text-[var(--foreground)] leading-tight">
            AI-Powered Safety Assessment Framework
          </h2>
          <div className="flex items-center gap-2 flex-wrap justify-center">
            <span className="px-3 py-1 rounded-full bg-white border border-[var(--border)] text-[var(--text-muted)] text-sm shadow-sm flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
              NGT Safety
            </span>
            <span className="px-3 py-1 rounded-full bg-white border border-[var(--border)] text-[var(--text-muted)] text-sm shadow-sm flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
              Bio-Ethics
            </span>
            <span className="px-3 py-1 rounded-full bg-white border border-[var(--border)] text-[var(--text-muted)] text-sm shadow-sm flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-purple-500" />
              Risk Assessment
            </span>
          </div>
        </section>

        {/* Research Topic Card */}
        <section className="mb-6">
          <div className="glass-panel relative overflow-hidden p-8 flex items-center gap-6">
            <div className="absolute top-0 right-0 w-64 h-64 bg-[var(--primary-light)] rounded-full -translate-y-1/2 translate-x-1/2 opacity-50 pointer-events-none" />

            <div className="flex-shrink-0 w-16 h-16 bg-[var(--primary-light)] rounded-2xl flex items-center justify-center">
              <span className="material-symbols-outlined text-[var(--primary)] icon-lg">
                biotech
              </span>
            </div>

            <div className="flex-1 min-w-0">
              <h3 className="text-xl font-bold text-[var(--foreground)] mb-1">
                {t('topic.heading')}
              </h3>
              <p className="text-[var(--text-muted)] text-sm leading-relaxed">
                {t('topic.description')}
              </p>
            </div>

            <div className="flex-shrink-0">
              <button
                onClick={handleStart}
                disabled={backendStatus !== 'online'}
                className={`flex items-center gap-2 px-6 py-3 rounded-lg font-bold shadow-md transition-colors ${
                  backendStatus === 'online'
                    ? 'bg-[var(--primary)] hover:opacity-90 text-white'
                    : 'bg-[var(--border)] text-[var(--text-muted)] cursor-not-allowed'
                }`}
              >
                <span className="material-symbols-outlined">play_arrow</span>
                {t('topic.start')}
              </button>
            </div>
          </div>
        </section>

        {/* Agent Team Section */}
        <section className="mb-6">
          <div className="glass-panel p-6">

            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[var(--primary)]">groups</span>
                <h3 className="text-lg font-bold text-[var(--foreground)]">{t('team.heading')}</h3>
              </div>
              <span className="px-3 py-1 rounded-full bg-[var(--primary-light)] text-[var(--primary)] text-xs font-medium">
                {t('team.operational')}
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">

              {/* PI Agent */}
              <div className="bg-white border border-[var(--border)] rounded-xl p-4 flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center flex-shrink-0">
                  <span className="material-symbols-outlined text-blue-600 icon-md">
                    supervisor_account
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 mb-0.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                    <span className="text-xs text-[var(--text-muted)]">{t('team.active')}</span>
                  </div>
                  <p className="font-bold text-[var(--foreground)] text-sm">PI Agent</p>
                  <p className="text-xs text-[var(--text-muted)] truncate">{t('team.pi.role')}</p>
                </div>
              </div>

              {/* Critic Agent */}
              <div className="bg-white border border-[var(--border)] rounded-xl p-4 flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-red-50 flex items-center justify-center flex-shrink-0">
                  <span className="material-symbols-outlined text-red-600 icon-md">
                    gavel
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 mb-0.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                    <span className="text-xs text-[var(--text-muted)]">{t('team.active')}</span>
                  </div>
                  <p className="font-bold text-[var(--foreground)] text-sm">Critic Agent</p>
                  <p className="text-xs text-[var(--text-muted)] truncate">{t('team.critic.role')}</p>
                </div>
              </div>

              {/* Specialist Agent */}
              <div className="bg-white border border-[var(--border)] rounded-xl p-4 flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-purple-50 flex items-center justify-center flex-shrink-0">
                  <span className="material-symbols-outlined text-purple-600 icon-md">
                    school
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 mb-0.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                    <span className="text-xs text-[var(--text-muted)]">{t('team.active')}</span>
                  </div>
                  <p className="font-bold text-[var(--foreground)] text-sm">Specialist Agent</p>
                  <p className="text-xs text-[var(--text-muted)] truncate">{t('team.specialist.role')}</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Workflow Pipeline — Agent Team Status 바로 아래 */}
        <WorkflowPipeline />

        {/* Feature Navigation */}
        <section className="mb-10">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">

            {/* Agent Timeline — 정적 정보 카드 (페이지 이동 없음) */}
            <div className="glass-panel overflow-hidden cursor-default">
              <div className="h-8 bg-[var(--background)] relative">
                <div className="absolute -bottom-4 left-4 w-8 h-8 rounded-full bg-[var(--primary-light)] border-2 border-white flex items-center justify-center shadow-sm">
                  <span className="material-symbols-outlined text-[var(--primary)] icon-sm">
                    timeline
                  </span>
                </div>
              </div>
              <div className="pt-6 px-4 pb-5">
                <p className="font-bold text-[var(--foreground)] text-sm mb-1">
                  {t('feature.timeline.title')}
                </p>
                <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                  {t('feature.timeline.desc')}
                </p>
              </div>
            </div>

            {/* Workflow Pipeline — 같은 페이지의 상세 섹션으로 스크롤 */}
            <button
              type="button"
              onClick={() =>
                document
                  .getElementById('workflow-pipeline-section')
                  ?.scrollIntoView({ behavior: 'smooth' })
              }
              className="glass-panel-hover overflow-hidden group cursor-pointer text-left w-full"
            >
              <div className="h-8 bg-[var(--background)] relative">
                <div className="absolute -bottom-4 left-4 w-8 h-8 rounded-full bg-blue-50 border-2 border-white flex items-center justify-center shadow-sm">
                  <span className="material-symbols-outlined text-blue-600 icon-sm">
                    account_tree
                  </span>
                </div>
              </div>
              <div className="pt-6 px-4 pb-5">
                <p className="font-bold text-[var(--foreground)] text-sm mb-1 group-hover:text-[var(--primary)] transition-colors">
                  {t('feature.workflow.title')}
                </p>
                <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                  {t('feature.workflow.desc')}
                </p>
              </div>
            </button>

            {/* Research Reports */}
            <Link
              href="/reports"
              className="glass-panel-hover overflow-hidden group"
            >
              <div className="h-8 bg-[var(--background)] relative">
                <div className="absolute -bottom-4 left-4 w-8 h-8 rounded-full bg-purple-50 border-2 border-white flex items-center justify-center shadow-sm">
                  <span className="material-symbols-outlined text-purple-600 icon-sm">
                    description
                  </span>
                </div>
              </div>
              <div className="pt-6 px-4 pb-5">
                <p className="font-bold text-[var(--foreground)] text-sm mb-1 group-hover:text-[var(--primary)] transition-colors">
                  {t('feature.reports.title')}
                </p>
                <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                  {t('feature.reports.desc')}
                </p>
              </div>
            </Link>
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t border-[var(--border)] py-6 flex items-center justify-between">
          <span className="text-xs text-[var(--text-muted)] font-medium">{t('footer.status')}</span>
          <div className="flex items-center gap-5">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-green-500" />
              <span className="text-xs text-[var(--text-muted)]">FastAPI Core</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-green-500" />
              <span className="text-xs text-[var(--text-muted)]">LangGraph</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-green-500" />
              <span className="text-xs text-[var(--text-muted)]">Vector Store</span>
            </div>
          </div>
          <span className="text-xs text-[var(--text-muted)]">v2.4.0-stable</span>
        </footer>
      </main>
    </div>
  );
}
