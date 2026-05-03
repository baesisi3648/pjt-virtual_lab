/**
 * @TASK P4-T3 - Report Editor Tests
 * @SPEC TASKS.md#P4-T3
 *
 * Interactive Report Editor 컴포넌트 테스트
 */

import { describe, test, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ReportEditor from '../ReportEditor';

describe('ReportEditor', () => {
  const mockReport = `# Final Report

## 1. 개요
This is an overview section.

## 2. 위험 식별
### 알레르기 위험
Some allergy risks identified.

### 독성 위험
Toxicity concerns.

## 3. 제출 자료 요건
Required submission materials.

## 4. 결론
Final conclusion.`;

  test('마크다운 보고서를 렌더링한다', () => {
    render(<ReportEditor report={mockReport} onRegenerate={vi.fn()} />);

    expect(screen.getByText(/Final Report/i)).toBeInTheDocument();
    expect(screen.getByText(/개요/i)).toBeInTheDocument();
    expect(screen.getByText(/위험 식별/i)).toBeInTheDocument();
  });

  test('섹션별로 재검토 요청 버튼이 표시된다', () => {
    render(<ReportEditor report={mockReport} onRegenerate={vi.fn()} />);

    const regenerateButtons = screen.getAllByRole('button', { name: /재검토/i });
    expect(regenerateButtons.length).toBeGreaterThan(0);
  });

  test('재검토 버튼 클릭 시 피드백 모달이 열린다', () => {
    render(<ReportEditor report={mockReport} onRegenerate={vi.fn()} />);

    const regenerateButton = screen.getAllByRole('button', { name: /재검토/i })[0];
    fireEvent.click(regenerateButton);

    expect(screen.getByPlaceholderText(/피드백을 입력하세요/i)).toBeInTheDocument();
  });

  test('피드백 제출 시 onRegenerate 콜백이 호출된다', async () => {
    const mockRegenerate = vi.fn();
    render(<ReportEditor report={mockReport} onRegenerate={mockRegenerate} />);

    // 재검토 버튼 클릭
    const regenerateButton = screen.getAllByRole('button', { name: /재검토/i })[0];
    fireEvent.click(regenerateButton);

    // 피드백 입력
    const feedbackInput = screen.getByPlaceholderText(/피드백을 입력하세요/i);
    fireEvent.change(feedbackInput, { target: { value: '알레르기 더 자세히' } });

    // 제출
    const submitButton = screen.getByRole('button', { name: /제출/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockRegenerate).toHaveBeenCalledWith(
        expect.objectContaining({
          section: expect.any(String),
          feedback: '알레르기 더 자세히',
        })
      );
    });
  });

  test('편집 모드 토글이 가능하다', () => {
    render(<ReportEditor report={mockReport} onRegenerate={vi.fn()} />);

    const editButton = screen.getByRole('button', { name: /편집/i });
    fireEvent.click(editButton);

    // 편집 모드에서는 textarea가 표시되어야 함
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  test('편집된 내용을 저장할 수 있다', () => {
    render(<ReportEditor report={mockReport} onRegenerate={vi.fn()} />);

    // 편집 모드 활성화
    const editButton = screen.getByRole('button', { name: /편집/i });
    fireEvent.click(editButton);

    // 내용 수정
    const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: '# Modified Report' } });

    // 저장
    const saveButton = screen.getByRole('button', { name: /저장/i });
    fireEvent.click(saveButton);

    // 뷰 모드로 돌아가서 수정된 내용이 표시되어야 함
    expect(screen.getByText(/Modified Report/i)).toBeInTheDocument();
  });

  test('로딩 상태를 표시한다', () => {
    render(<ReportEditor report={mockReport} onRegenerate={vi.fn()} isLoading={true} />);

    expect(screen.getByText(/처리 중/i)).toBeInTheDocument();
  });

  test('빈 보고서 상태를 처리한다', () => {
    render(<ReportEditor report="" onRegenerate={vi.fn()} />);

    expect(screen.getByText(/보고서가 없습니다/i)).toBeInTheDocument();
  });
});
