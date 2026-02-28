'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function HomePage() {
  const router = useRouter();
  const [backendStatus, setBackendStatus] = useState<'online' | 'offline' | 'checking'>('checking');
  const RESEARCH_TOPIC = "유전자편집식품(NGT) 표준 안전성 평가 프레임워크 도출";

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then(res => res.ok ? setBackendStatus('online') : setBackendStatus('offline'))
      .catch(() => setBackendStatus('offline'));
  }, []);

  const handleStart = () => {
    router.push(`/timeline?topic=${encodeURIComponent(RESEARCH_TOPIC)}`);
  };

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white border-b border-[var(--border)] shadow-sm">
        <div className="max-w-5xl mx-auto px-6 py-3 flex items-center justify-between">

          {/* Left: Logo */}
          <div className="flex items-center">
            <img src="/logo.png" alt="Virtual Lab" className="h-10" />
          </div>

          {/* Center: Pill Nav */}
          <nav className="bg-[var(--background)] border border-[var(--border)] rounded-full p-1 flex items-center gap-1">
            <div className="px-5 py-2 bg-[var(--primary)] text-white rounded-full text-sm font-medium">
              Dashboard
            </div>
            <Link
              href="/timeline"
              className="px-5 py-2 text-[var(--text-muted)] hover:text-[var(--primary)] rounded-full text-sm font-medium transition-colors"
            >
              Agents
            </Link>
            <Link
              href="/reports"
              className="px-5 py-2 text-[var(--text-muted)] hover:text-[var(--primary)] rounded-full text-sm font-medium transition-colors"
            >
              Reports
            </Link>
          </nav>

          {/* Right: Backend Status */}
          <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-white border border-[var(--border)]">
            <span
              className={`w-2 h-2 rounded-full ${
                backendStatus === 'online'
                  ? 'bg-green-500'
                  : backendStatus === 'offline'
                  ? 'bg-red-500'
                  : 'bg-yellow-500 animate-pulse'
              }`}
            />
            <span className="text-sm text-[var(--text-muted)]">
              {backendStatus === 'online'
                ? 'Backend Online'
                : backendStatus === 'offline'
                ? 'Backend Offline'
                : 'Checking...'}
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-6">

        {/* Hero Section */}
        <section className="flex flex-col items-center text-center pt-8 pb-6 gap-4">
          <div className="w-20 h-20 bg-[var(--primary-light)] rounded-2xl flex items-center justify-center">
            <span className="material-symbols-outlined text-[var(--primary)] icon-xl">
              psychology
            </span>
          </div>
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
            {/* Decorative circle */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-[var(--primary-light)] rounded-full -translate-y-1/2 translate-x-1/2 opacity-50 pointer-events-none" />

            {/* Icon */}
            <div className="flex-shrink-0 w-16 h-16 bg-[var(--primary-light)] rounded-2xl flex items-center justify-center">
              <span className="material-symbols-outlined text-[var(--primary)] icon-lg">
                biotech
              </span>
            </div>

            {/* Text */}
            <div className="flex-1 min-w-0">
              <h3 className="text-xl font-bold text-[var(--foreground)] mb-1">
                연구 주제 (Research Topic)
              </h3>
              <p className="text-[var(--text-muted)] text-sm leading-relaxed">
                유전자편집식품(NGT)의 카테고리별(SDN-1, SDN-2, SDN-3, ODM) 표준 안전성 평가체계 확립을 위한 AI 에이전트 팀 회의를 진행합니다.
              </p>
            </div>

            {/* Start Button */}
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
                START ASSESSMENT
              </button>
            </div>
          </div>
        </section>

        {/* Agent Team Section */}
        <section className="mb-6">
          <div className="glass-panel p-6">

            {/* Section header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[var(--primary)]">groups</span>
                <h3 className="text-lg font-bold text-[var(--foreground)]">Agent Team Status</h3>
              </div>
              <span className="px-3 py-1 rounded-full bg-[var(--primary-light)] text-[var(--primary)] text-xs font-medium">
                All Systems Operational
              </span>
            </div>

            {/* 3-column grid */}
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
                    <span className="text-xs text-[var(--text-muted)]">Active</span>
                  </div>
                  <p className="font-bold text-[var(--foreground)] text-sm">PI Agent</p>
                  <p className="text-xs text-[var(--text-muted)] truncate">Principal Investigator</p>
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
                    <span className="text-xs text-[var(--text-muted)]">Active</span>
                  </div>
                  <p className="font-bold text-[var(--foreground)] text-sm">Critic Agent</p>
                  <p className="text-xs text-[var(--text-muted)] truncate">Quality Assurance</p>
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
                    <span className="text-xs text-[var(--text-muted)]">Active</span>
                  </div>
                  <p className="font-bold text-[var(--foreground)] text-sm">Specialist Agent</p>
                  <p className="text-xs text-[var(--text-muted)] truncate">Domain Expert</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Feature Navigation */}
        <section className="mb-10">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">

            {/* Agent Timeline */}
            <Link
              href="/timeline"
              className="glass-panel-hover overflow-hidden group"
            >
              <div className="h-8 bg-[var(--background)] relative">
                <div className="absolute -bottom-4 left-4 w-8 h-8 rounded-full bg-[var(--primary-light)] border-2 border-white flex items-center justify-center shadow-sm">
                  <span className="material-symbols-outlined text-[var(--primary)] icon-sm">
                    timeline
                  </span>
                </div>
              </div>
              <div className="pt-6 px-4 pb-5">
                <p className="font-bold text-[var(--foreground)] text-sm mb-1 group-hover:text-[var(--primary)] transition-colors">
                  Agent Timeline
                </p>
                <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                  실시간으로 에이전트 간 협업 과정을 모니터링하고 각 단계의 의사결정을 추적합니다.
                </p>
              </div>
            </Link>

            {/* Workflow Pipeline */}
            <Link
              href="/timeline"
              className="glass-panel-hover overflow-hidden group"
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
                  Workflow Pipeline
                </p>
                <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                  3라운드 팀 회의 파이프라인을 단계별 카드로 시각화하고 에이전트 활동을 실시간 추적합니다.
                </p>
              </div>
            </Link>

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
                  Research Reports
                </p>
                <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                  AI가 생성한 연구 보고서를 확인하고 Markdown 형식으로 다운로드할 수 있습니다.
                </p>
              </div>
            </Link>
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t border-[var(--border)] py-6 flex items-center justify-between">
          <span className="text-xs text-[var(--text-muted)] font-medium">System Status</span>
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
