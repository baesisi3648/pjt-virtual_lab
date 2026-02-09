/**
 * @TASK P4-T3 - Report Editor Demo Page (Dark Mode)
 * @SPEC TASKS.md#P4-T3
 *
 * ReportEditor 컴포넌트 데모 페이지
 * "Paper Document" style with sidebar navigation
 */

'use client';

import { useState } from 'react';
import ReportEditor from '@/components/ReportEditor';
import { regenerateSection } from '@/lib/api';

const SAMPLE_REPORT = `# NGT 안전성 평가 프레임워크 최종 보고서

## 1. 개요

유전자편집식품(NGT)의 안전성을 체계적으로 평가하기 위한 표준 프레임워크를 제안합니다.

## 2. 위험 식별

### 2.1 알레르기 위험
- 새로운 단백질 발현으로 인한 알레르기 반응 가능성
- 기존 알레르겐과의 교차반응 평가 필요

### 2.2 독성 위험
- 비의도적 유전자 변형으로 인한 독성 물질 생성
- 대사 경로 변화에 따른 부작용

## 3. 제출 자료 요건

### 3.1 필수 제출 자료
1. 유전자 편집 정보
2. 알레르기 평가 자료
3. 독성 평가 자료
4. 영양학적 평가 자료

### 3.2 선택 제출 자료
- 장기 섭취 연구 데이터
- 환경 영향 평가

## 4. 결론

본 프레임워크는 NGT 안전성 평가의 표준화를 통해 소비자 안전을 보장하고, 신속한 심사를 가능하게 합니다.`;

export default function ReportDemoPage() {
  const [report, setReport] = useState(SAMPLE_REPORT);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [activeSection, setActiveSection] = useState('executive-summary');

  const handleRegenerate = async (request: {
    section: string;
    feedback: string;
  }) => {
    setIsLoading(true);
    setMessage('');

    try {
      const response = await regenerateSection({
        section: request.section,
        feedback: request.feedback,
        current_report: report,
      });

      setReport(response.updated_report);
      setMessage(`${response.message}`);
    } catch (error) {
      console.error('재생성 실패:', error);
      setMessage(
        `재생성 실패: ${error instanceof Error ? error.message : '알 수 없는 오류'}`
      );
    } finally {
      setIsLoading(false);
    }
  };

  const navSections = [
    { id: 'executive-summary', label: 'Executive Summary', icon: 'dashboard' },
    { id: 'risk-analysis', label: 'Risk Analysis', icon: 'analytics' },
    { id: 'guideline-assessment', label: 'Guideline Assessment', icon: 'science' },
    { id: 'update-items', label: 'Update Items', icon: 'genetics' },
    { id: 'conclusion', label: 'Conclusion', icon: 'verified_user' },
  ];

  return (
    <div className="min-h-screen bg-[#0f1216]">
      {/* Header */}
      <header className="sticky top-0 z-50 glass-panel">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Left: Logo + Breadcrumbs */}
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-3">
                <span className="material-icons text-[#137fec] text-2xl">biotech</span>
                <span className="text-lg font-bold">BioLab AI</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <span>Projects</span>
                <span className="material-icons text-xs">chevron_right</span>
                <span>Research</span>
                <span className="material-icons text-xs">chevron_right</span>
                <span className="text-white">Safety Assessment</span>
              </div>
            </div>

            {/* Right: Search + Settings + Avatar */}
            <div className="flex items-center gap-4">
              <div className="relative">
                <span className="material-icons absolute left-3 top-2 text-gray-500 text-sm">search</span>
                <input
                  type="text"
                  placeholder="Search reports..."
                  className="pl-9 pr-4 py-2 bg-gray-800/50 border border-gray-700 rounded-lg text-sm text-gray-300 placeholder-gray-500 focus:outline-none focus:border-[#137fec]/50 w-64"
                />
              </div>
              <button className="material-icons text-gray-400 hover:text-white transition-colors">
                settings
              </button>
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#137fec] to-purple-600 flex items-center justify-center text-white text-sm font-bold">
                U
              </div>
            </div>
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

            {/* Status Card */}
            <div className="glass-panel-light rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-gray-500">Status</span>
                <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded font-semibold">
                  APPROVED
                </span>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-1.5 mt-3">
                <div className="bg-green-500 h-1.5 rounded-full" style={{ width: '100%' }}></div>
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
                  <span className="text-sm text-gray-400">Last updated: 2026-02-09</span>
                </div>
                <div className="flex items-center gap-3">
                  <button className="flex items-center gap-2 px-4 py-2 text-sm text-gray-300 glass-panel-light rounded-lg hover:glass-panel-hover transition-all">
                    <span className="material-icons text-base">share</span>
                    Share
                  </button>
                  <button className="flex items-center gap-2 px-4 py-2 text-sm text-white bg-[#137fec] rounded-lg hover:bg-[#0e6bc9] transition-colors">
                    <span className="material-icons text-base">download</span>
                    Export PDF
                  </button>
                </div>
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
              {/* Decorative corner borders */}
              <div className="report-paper rounded-lg shadow-2xl overflow-hidden relative">
                {/* Top-left corner */}
                <div className="absolute top-0 left-0 w-12 h-12 border-t-4 border-l-4 border-[#137fec]/30"></div>
                {/* Top-right corner */}
                <div className="absolute top-0 right-0 w-12 h-12 border-t-4 border-r-4 border-[#137fec]/30"></div>
                {/* Bottom-left corner */}
                <div className="absolute bottom-0 left-0 w-12 h-12 border-b-4 border-l-4 border-[#137fec]/30"></div>
                {/* Bottom-right corner */}
                <div className="absolute bottom-0 right-0 w-12 h-12 border-b-4 border-r-4 border-[#137fec]/30"></div>

                {/* Report Editor Component */}
                <div className="min-h-[800px]">
                  <ReportEditor
                    report={report}
                    onRegenerate={handleRegenerate}
                    isLoading={isLoading}
                  />
                </div>
              </div>
            </div>

            {/* Loading indicator */}
            {isLoading && (
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
