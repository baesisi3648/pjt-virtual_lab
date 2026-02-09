/**
 * @TASK P4-T3 - Report Editor Component
 * @SPEC TASKS.md#P4-T3
 *
 * Interactive Report Editor - 마크다운 보고서 수정 및 재검토 요청
 * Dark mode 스타일 (앱 전체 테마와 통일)
 */

'use client';

import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface RegenerateRequest {
  section: string;
  feedback: string;
}

interface ReportEditorProps {
  report: string;
  onRegenerate: (request: RegenerateRequest) => void;
  isLoading?: boolean;
}

interface Section {
  title: string;
  content: string;
  level: number;
}

export default function ReportEditor({
  report,
  onRegenerate,
  isLoading = false,
}: ReportEditorProps) {
  const [isEditMode, setIsEditMode] = useState(false);
  const [editedReport, setEditedReport] = useState(report);
  const [currentReport, setCurrentReport] = useState(report);
  const [selectedSection, setSelectedSection] = useState<string | null>(null);
  const [feedback, setFeedback] = useState('');

  // report prop 변경 시 내부 state 동기화 (한/영 전환 등)
  useEffect(() => {
    setCurrentReport(report);
    setEditedReport(report);
  }, [report]);

  // 보고서를 섹션별로 파싱
  const parseSections = (markdown: string): Section[] => {
    const sections: Section[] = [];
    const lines = markdown.split('\n');
    let currentSection: Section | null = null;

    for (const line of lines) {
      const match = line.match(/^(#{1,6})\s+(.+)$/);
      if (match) {
        if (currentSection) {
          sections.push(currentSection);
        }
        currentSection = {
          title: match[2],
          content: line + '\n',
          level: match[1].length,
        };
      } else if (currentSection) {
        currentSection.content += line + '\n';
      }
    }

    if (currentSection) {
      sections.push(currentSection);
    }

    return sections;
  };

  const sections = parseSections(currentReport);

  // 재검토 요청 핸들러
  const handleRegenerateClick = (sectionTitle: string) => {
    setSelectedSection(sectionTitle);
  };

  const handleSubmitFeedback = () => {
    if (selectedSection && feedback) {
      onRegenerate({
        section: selectedSection,
        feedback: feedback,
      });
      setSelectedSection(null);
      setFeedback('');
    }
  };

  const handleCancelFeedback = () => {
    setSelectedSection(null);
    setFeedback('');
  };

  // 편집 모드 토글
  const handleEditToggle = () => {
    if (isEditMode) {
      setCurrentReport(editedReport);
      setIsEditMode(false);
    } else {
      setEditedReport(currentReport);
      setIsEditMode(true);
    }
  };

  // 편집 취소
  const handleCancelEdit = () => {
    setEditedReport(currentReport);
    setIsEditMode(false);
  };

  // 빈 보고서 처리
  if (!report && !currentReport) {
    return (
      <div className="p-6 text-center text-white/40">
        <p>보고서가 없습니다</p>
      </div>
    );
  }

  // 로딩 상태
  if (isLoading) {
    return (
      <div className="p-6 text-center">
        <div className="animate-pulse">
          <p className="text-white/50">처리 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="report-editor h-full flex flex-col">
      {/* 헤더 */}
      <div className="flex justify-between items-center p-6 border-b border-white/10">
        <h2 className="text-2xl font-bold text-white tracking-tight">최종 보고서</h2>
        <div className="flex gap-2">
          {isEditMode ? (
            <>
              <button
                onClick={handleCancelEdit}
                className="px-4 py-2 text-white/50 hover:text-white/80 text-sm"
              >
                취소
              </button>
              <button
                onClick={handleEditToggle}
                className="px-4 py-2 bg-[#137fec] text-white rounded-lg hover:bg-[#0e6bc9] text-sm font-medium"
              >
                저장
              </button>
            </>
          ) : (
            <button
              onClick={handleEditToggle}
              className="px-4 py-2 bg-white/10 text-white/80 rounded-lg hover:bg-white/15 text-sm font-medium flex items-center gap-2"
            >
              <span className="material-symbols-outlined text-base">edit</span>
              편집
            </button>
          )}
        </div>
      </div>

      {/* 컨텐츠 */}
      <div className="flex-1 overflow-y-auto p-8">
        {isEditMode ? (
          // 편집 모드: Textarea
          <textarea
            value={editedReport}
            onChange={(e) => setEditedReport(e.target.value)}
            className="w-full h-full p-4 border border-white/10 rounded-lg bg-black/20 text-gray-200 font-mono text-sm resize-none focus:outline-none focus:border-[#137fec] focus:ring-2 focus:ring-[#137fec]/20"
            placeholder="마크다운 형식으로 보고서를 작성하세요..."
          />
        ) : (
          // 뷰 모드: Markdown 렌더링 + 섹션별 재검토 버튼
          <div className="space-y-6">
            {sections.map((section, index) => (
              <div
                key={index}
                className="section-container border-l-4 border-[#137fec] pl-4 py-2 hover:bg-white/5 transition-colors rounded-r group"
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex-1 prose prose-invert prose-sm max-w-none
                    [&_h1]:text-white [&_h1]:text-2xl [&_h1]:font-bold [&_h1]:mb-3
                    [&_h2]:text-white [&_h2]:text-xl [&_h2]:font-semibold [&_h2]:mb-2
                    [&_h3]:text-white/90 [&_h3]:text-lg [&_h3]:font-medium [&_h3]:mb-2
                    [&_p]:text-gray-300 [&_p]:leading-relaxed [&_p]:mb-2
                    [&_li]:text-gray-300 [&_li]:leading-relaxed
                    [&_strong]:text-white
                    [&_a]:text-[#137fec]
                    [&_ul]:list-disc [&_ul]:pl-5
                    [&_ol]:list-decimal [&_ol]:pl-5"
                  >
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {section.content}
                    </ReactMarkdown>
                  </div>
                  {section.level <= 3 && (
                    <button
                      onClick={() => handleRegenerateClick(section.title)}
                      className="ml-4 px-3 py-1 text-xs bg-[#137fec]/10 text-[#137fec] border border-[#137fec]/20 rounded-lg hover:bg-[#137fec]/20 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1"
                    >
                      <span className="material-symbols-outlined text-sm">refresh</span>
                      재검토
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 피드백 모달 */}
      {selectedSection && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="glass-panel rounded-xl p-6 max-w-md w-full mx-4 shadow-2xl">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-[#137fec]/10 flex items-center justify-center">
                <span className="material-symbols-outlined text-[#137fec]">rate_review</span>
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">재검토 요청</h3>
                <p className="text-sm text-white/50">{selectedSection}</p>
              </div>
            </div>
            <textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="피드백을 입력하세요 (예: 알레르기 부분을 더 자세히 서술해주세요)"
              className="w-full h-32 p-3 border border-white/10 rounded-lg bg-black/20 text-gray-200 resize-none mb-4 focus:outline-none focus:border-[#137fec] focus:ring-2 focus:ring-[#137fec]/20 text-sm"
              autoFocus
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={handleCancelFeedback}
                className="px-4 py-2 text-white/50 hover:text-white/80 text-sm"
              >
                취소
              </button>
              <button
                onClick={handleSubmitFeedback}
                disabled={!feedback.trim()}
                className="px-4 py-2 bg-[#137fec] text-white rounded-lg hover:bg-[#0e6bc9] disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
              >
                제출
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
