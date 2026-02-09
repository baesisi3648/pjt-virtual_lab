/**
 * Virtual Lab - Main Landing Page (Dark Mode)
 * NGT (Novel Genomic Techniques) Safety Assessment Framework
 */

'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';

export default function Home() {
  const [apiStatus, setApiStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then(res => res.json())
      .then(data => {
        setApiStatus(data.status === 'ok' ? 'online' : 'offline');
      })
      .catch(() => {
        setApiStatus('offline');
      });
  }, []);

  return (
    <div className="min-h-screen bg-gray-950">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-950/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">Virtual Lab</h1>
              <p className="text-sm text-gray-400">NGT Safety Assessment Framework</p>
            </div>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${
                apiStatus === 'online' ? 'bg-green-500' :
                apiStatus === 'offline' ? 'bg-red-500' : 'bg-gray-500 animate-pulse'
              }`} />
              <span className="text-sm text-gray-400">
                Backend: {apiStatus === 'online' ? 'Online' : apiStatus === 'offline' ? 'Offline' : 'Checking...'}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-16">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <h2 className="text-5xl font-bold text-white mb-4">
            AI-Powered Safety Assessment
          </h2>
          <p className="text-xl text-gray-400 max-w-3xl mx-auto mb-8">
            유전자편집식품(NGT)의 표준 안전성 평가 프레임워크를 AI 에이전트 시스템으로 자동화합니다.
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <div className="px-4 py-2 bg-blue-950 border border-blue-800 rounded-lg">
              <span className="text-sm font-medium text-blue-300">RAG Search (Pinecone)</span>
            </div>
            <div className="px-4 py-2 bg-purple-950 border border-purple-800 rounded-lg">
              <span className="text-sm font-medium text-purple-300">Web Search (Tavily)</span>
            </div>
            <div className="px-4 py-2 bg-green-950 border border-green-800 rounded-lg">
              <span className="text-sm font-medium text-green-300">LangGraph AI Agents</span>
            </div>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto mb-16">
          {/* Timeline Feature */}
          <Link href="/timeline">
            <div className="bg-gray-900 rounded-2xl shadow-lg p-8 hover:shadow-xl transition-all cursor-pointer border border-gray-800 hover:border-blue-600">
              <div className="text-4xl mb-4">⏱️</div>
              <h3 className="text-2xl font-bold text-white mb-2">
                Live Process Timeline
              </h3>
              <p className="text-gray-400 mb-4">
                AI 에이전트들이 협업하여 연구를 수행하는 과정을 실시간으로 확인하세요.
              </p>
              <ul className="space-y-2 text-sm text-gray-500">
                <li className="text-gray-400">✓ 실시간 에이전트 활동 모니터링</li>
                <li className="text-gray-400">✓ 단계별 진행 상황 추적</li>
                <li className="text-gray-400">✓ 최종 보고서 자동 생성</li>
              </ul>
              <div className="mt-6 text-blue-400 font-medium">
                시작하기 →
              </div>
            </div>
          </Link>

          {/* Report Editor Feature */}
          <Link href="/report-demo">
            <div className="bg-gray-900 rounded-2xl shadow-lg p-8 hover:shadow-xl transition-all cursor-pointer border border-gray-800 hover:border-purple-600">
              <div className="text-4xl mb-4">📝</div>
              <h3 className="text-2xl font-bold text-white mb-2">
                Interactive Report Editor
              </h3>
              <p className="text-gray-400 mb-4">
                생성된 보고서를 직접 수정하고, AI에게 섹션별 재작성을 요청하세요.
              </p>
              <ul className="space-y-2 text-sm">
                <li className="text-gray-400">✓ 마크다운 기반 실시간 편집</li>
                <li className="text-gray-400">✓ 섹션별 재검토 요청</li>
                <li className="text-gray-400">✓ 피드백 기반 자동 재생성</li>
              </ul>
              <div className="mt-6 text-purple-400 font-medium">
                데모 보기 →
              </div>
            </div>
          </Link>
        </div>

        {/* Tech Stack */}
        <div className="bg-gray-900 rounded-2xl shadow-lg p-8 max-w-5xl mx-auto border border-gray-800">
          <h3 className="text-2xl font-bold text-white mb-6 text-center">
            Technology Stack
          </h3>
          <div className="grid md:grid-cols-3 gap-6">
            <div>
              <h4 className="font-semibold text-gray-200 mb-3">Backend</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li>FastAPI + LangGraph</li>
                <li>OpenAI GPT-4o / GPT-4o-mini</li>
                <li>SQLite Database</li>
                <li>Pinecone Vector DB (316 docs)</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-200 mb-3">Frontend</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li>Next.js 16 + React 19</li>
                <li>TypeScript + Tailwind CSS 4</li>
                <li>Server-Sent Events (SSE)</li>
                <li>Turbopack</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-200 mb-3">AI Features</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li>RAG Search (규제 문서)</li>
                <li>Web Search (최신 정보)</li>
                <li>Multi-Agent Collaboration</li>
                <li>Dynamic Agent Factory</li>
              </ul>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 mt-16">
        <div className="container mx-auto px-4 py-6 text-center text-sm text-gray-500">
          <p>Virtual Lab MVP - NGT Safety Assessment Framework</p>
        </div>
      </footer>
    </div>
  );
}
