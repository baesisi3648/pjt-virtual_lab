/**
 * @TASK P4-T3 - Report Editor Demo Page
 * @SPEC TASKS.md#P4-T3
 *
 * ReportEditor 컴포넌트 데모 페이지
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
      setMessage(`✅ ${response.message}`);
    } catch (error) {
      console.error('재생성 실패:', error);
      setMessage(
        `❌ 재생성 실패: ${error instanceof Error ? error.message : '알 수 없는 오류'}`
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Report Editor Demo</h1>
          <p className="text-gray-600">
            Interactive Report Editor - 마크다운 보고서 수정 및 재검토 요청
          </p>
        </div>

        {message && (
          <div
            className={`mb-4 p-4 rounded ${
              message.startsWith('✅')
                ? 'bg-green-100 text-green-800'
                : 'bg-red-100 text-red-800'
            }`}
          >
            {message}
          </div>
        )}

        <div className="bg-white rounded-lg shadow-lg overflow-hidden" style={{ height: '70vh' }}>
          <ReportEditor
            report={report}
            onRegenerate={handleRegenerate}
            isLoading={isLoading}
          />
        </div>

        <div className="mt-8 p-6 bg-blue-50 rounded-lg">
          <h2 className="text-xl font-bold mb-4">사용 방법</h2>
          <ol className="list-decimal list-inside space-y-2 text-gray-700">
            <li>각 섹션 옆의 "재검토 요청" 버튼을 클릭합니다</li>
            <li>피드백을 입력합니다 (예: "알레르기 더 자세히")</li>
            <li>"제출" 버튼을 클릭하면 해당 섹션이 재생성됩니다</li>
            <li>"편집" 버튼으로 직접 수정도 가능합니다</li>
          </ol>
        </div>
      </div>
    </div>
  );
}
