/**
 * @TASK P4-T3 - Report Editor Component
 * @SPEC TASKS.md#P4-T3
 *
 * Interactive Report Editor - 마크다운 보고서 수정 및 재검토 요청
 */

'use client';

import { useState } from 'react';
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
      // 저장
      setCurrentReport(editedReport);
      setIsEditMode(false);
    } else {
      // 편집 시작
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
      <div className="p-6 text-center text-gray-500">
        <p>보고서가 없습니다</p>
      </div>
    );
  }

  // 로딩 상태
  if (isLoading) {
    return (
      <div className="p-6 text-center">
        <div className="animate-pulse">
          <p className="text-gray-600">처리 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="report-editor h-full flex flex-col">
      {/* 헤더 */}
      <div className="flex justify-between items-center p-4 border-b">
        <h2 className="text-xl font-bold">최종 보고서</h2>
        <div className="flex gap-2">
          {isEditMode ? (
            <>
              <button
                onClick={handleCancelEdit}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                취소
              </button>
              <button
                onClick={handleEditToggle}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              >
                저장
              </button>
            </>
          ) : (
            <button
              onClick={handleEditToggle}
              className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
            >
              편집
            </button>
          )}
        </div>
      </div>

      {/* 컨텐츠 */}
      <div className="flex-1 overflow-y-auto p-6">
        {isEditMode ? (
          // 편집 모드: Textarea
          <textarea
            value={editedReport}
            onChange={(e) => setEditedReport(e.target.value)}
            className="w-full h-full p-4 border rounded font-mono text-sm resize-none"
            placeholder="마크다운 형식으로 보고서를 작성하세요..."
          />
        ) : (
          // 뷰 모드: Markdown 렌더링 + 섹션별 재검토 버튼
          <div className="space-y-6">
            {sections.map((section, index) => (
              <div
                key={index}
                className="section-container border-l-4 border-blue-500 pl-4 py-2 hover:bg-gray-50 transition-colors"
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex-1 prose prose-sm max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {section.content}
                    </ReactMarkdown>
                  </div>
                  {section.level <= 3 && (
                    <button
                      onClick={() => handleRegenerateClick(section.title)}
                      className="ml-4 px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 flex-shrink-0"
                    >
                      재검토 요청
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
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-bold mb-4">
              재검토 요청: {selectedSection}
            </h3>
            <textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="피드백을 입력하세요 (예: 알레르기 더 자세히)"
              className="w-full h-32 p-3 border rounded resize-none mb-4"
              autoFocus
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={handleCancelFeedback}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                취소
              </button>
              <button
                onClick={handleSubmitFeedback}
                disabled={!feedback.trim()}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
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
