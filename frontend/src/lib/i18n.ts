'use client';

/**
 * 경량 i18n 유틸 (외부 라이브러리 없이 localStorage 기반)
 *
 * - getLocale(): 현재 언어
 * - setLocale(): 언어 변경 + 이벤트 dispatch
 * - useLocale(): 훅 (컴포넌트용)
 * - t(key): 번역 함수
 */

import { useEffect, useState } from 'react';

export type Locale = 'ko' | 'en';

const LOCALE_KEY = 'vl_locale';
export const LOCALE_CHANGED_EVENT = 'vl_locale_changed';

export function getLocale(): Locale {
  if (typeof window === 'undefined') return 'ko';
  const stored = localStorage.getItem(LOCALE_KEY);
  return stored === 'en' ? 'en' : 'ko';
}

export function setLocale(locale: Locale): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(LOCALE_KEY, locale);
  window.dispatchEvent(new CustomEvent(LOCALE_CHANGED_EVENT));
}

// ── 번역 사전 ──────────────────────────────────────────

const TRANSLATIONS = {
  ko: {
    // Research Topic
    'topic.heading': '연구 주제 (Research Topic)',
    'topic.description':
      '유전자편집식품(NGT)의 카테고리별(SDN-1, SDN-2, SDN-3, ODM) 표준 안전성 평가체계 확립을 위한 AI 에이전트 팀 회의를 진행합니다.',
    'topic.start': 'START ASSESSMENT',

    // Agent Team
    'team.heading': 'Agent Team Status',
    'team.operational': '시스템 정상',
    'team.active': '활성',
    'team.pi.role': '총괄 책임자',
    'team.critic.role': '품질 관리',
    'team.specialist.role': '도메인 전문가',

    // Feature Navigation
    'feature.timeline.title': 'Agent Timeline',
    'feature.timeline.desc':
      '실시간으로 에이전트 간 협업 과정을 모니터링하고 각 단계의 의사결정을 추적합니다.',
    'feature.workflow.title': 'Workflow Pipeline',
    'feature.workflow.desc':
      '최대 7라운드 팀 회의 파이프라인을 단계별 카드로 시각화하고 에이전트 활동을 실시간 추적합니다.',
    'feature.reports.title': 'Research Reports',
    'feature.reports.desc':
      'AI가 생성한 연구 보고서를 확인하고 Markdown 형식으로 다운로드할 수 있습니다.',

    // Footer
    'footer.status': '시스템 상태',

    // Header
    'header.backend.live': 'Live',
    'header.backend.offline': 'Offline',

    // Reports list
    'reports.breadcrumbHome': 'Home',
    'reports.breadcrumbSelf': 'Research Reports',
    'reports.title': 'Research Reports',
    'reports.subtitle': 'AI가 생성한 연구 보고서 목록',
    'reports.loading': 'Loading reports...',
    'reports.empty.title': '보고서가 없습니다',
    'reports.empty.desc': '연구를 실행하면 보고서가 자동으로 저장됩니다.',
    'reports.empty.cta': 'Dashboard에서 시작하기',
    'reports.deleteBtn': '삭제',
    'reports.deleteBtnTitle': '보고서 삭제',

    // Reports detail
    'reportDetail.loading': 'Loading report...',
    'reportDetail.errorTitle': '보고서를 불러올 수 없습니다',
    'reportDetail.errorBack': '보고서 목록으로',
    'reportDetail.translating': '영어로 번역 중...',
    'reportDetail.regenerating': '재생성 중...',
    'reportDetail.translate': '영어로 번역',
    'reportDetail.lang.ko': '한국어',
    'reportDetail.lang.en': 'English',

    // History list
    'history.title': 'Research History',
    'history.subtitle': '에이전트 회의 과정을 라운드별로 확인할 수 있습니다.',
    'history.loading': '로딩 중...',
    'history.empty': '아직 연구 세션이 없습니다. Dashboard에서 연구를 시작해보세요.',
    'history.roundsSuffix': '라운드',
    'history.status.running': '진행 중',
    'history.status.completed': '완료',
    'history.status.error': '오류',

    // History detail
    'historyDetail.totalRoundsPrefix': '총',
    'historyDetail.totalRoundsSuffix': '라운드 진행',
    'historyDetail.eventsSuffix': '개 이벤트',
    'historyDetail.totalPrefix': '총',
    'historyDetail.viewFinalReport': '최종 보고서 보기',
    'historyDetail.copy': '전체 복사',
    'historyDetail.copied': '복사 완료',
    'historyDetail.downloadTxt': 'TXT 저장',
    'historyDetail.preparation': '사전 준비',
    'historyDetail.roundPrefix': '라운드',
    'historyDetail.expand': '펼치기',
    'historyDetail.collapse': '접기',

    // Event labels
    'event.planning': '팀 구성',
    'event.introductions': '전문가 소개',
    'event.researching': '분석',
    'event.critique': '비평 평가',
    'event.pi_summary': 'PI 종합',
    'event.iteration': '라운드 변경',
    'event.round_revision': '수정 분석',
    'event.final_synthesis': '최종 보고서',
    'event.team_selection': '통계적 선별',
    'event.errorLabel': '오류',
  },
  en: {
    'topic.heading': 'Research Topic',
    'topic.description':
      'AI agent team meeting to establish a standardized safety assessment framework for gene-edited foods (NGT) across categories (SDN-1, SDN-2, SDN-3, ODM).',
    'topic.start': 'START ASSESSMENT',

    'team.heading': 'Agent Team Status',
    'team.operational': 'All Systems Operational',
    'team.active': 'Active',
    'team.pi.role': 'Principal Investigator',
    'team.critic.role': 'Quality Assurance',
    'team.specialist.role': 'Domain Expert',

    'feature.timeline.title': 'Agent Timeline',
    'feature.timeline.desc':
      'Monitor agent collaboration in real time and trace decisions at each stage.',
    'feature.workflow.title': 'Workflow Pipeline',
    'feature.workflow.desc':
      'Visualize the 7-round team meeting pipeline as step-by-step cards and track agent activity live.',
    'feature.reports.title': 'Research Reports',
    'feature.reports.desc':
      'View AI-generated research reports and download them as Markdown.',

    'footer.status': 'System Status',

    'header.backend.live': 'Live',
    'header.backend.offline': 'Offline',

    'reports.breadcrumbHome': 'Home',
    'reports.breadcrumbSelf': 'Research Reports',
    'reports.title': 'Research Reports',
    'reports.subtitle': 'AI-generated research reports',
    'reports.loading': 'Loading reports...',
    'reports.empty.title': 'No reports yet',
    'reports.empty.desc': 'Run a research session to save a report.',
    'reports.empty.cta': 'Start on Dashboard',
    'reports.deleteBtn': 'Delete',
    'reports.deleteBtnTitle': 'Delete report',

    'reportDetail.loading': 'Loading report...',
    'reportDetail.errorTitle': 'Could not load report',
    'reportDetail.errorBack': 'Back to reports',
    'reportDetail.translating': 'Translating to English...',
    'reportDetail.regenerating': 'Regenerating...',
    'reportDetail.translate': 'Translate to English',
    'reportDetail.lang.ko': '한국어',
    'reportDetail.lang.en': 'English',

    'history.title': 'Research History',
    'history.subtitle': 'Review the agent meeting process round by round.',
    'history.loading': 'Loading...',
    'history.empty': 'No research sessions yet. Start one from the Dashboard.',
    'history.roundsSuffix': 'rounds',
    'history.status.running': 'Running',
    'history.status.completed': 'Completed',
    'history.status.error': 'Error',

    'historyDetail.totalRoundsPrefix': 'Total',
    'historyDetail.totalRoundsSuffix': 'rounds',
    'historyDetail.eventsSuffix': 'events',
    'historyDetail.totalPrefix': 'Total',
    'historyDetail.viewFinalReport': 'View Final Report',
    'historyDetail.copy': 'Copy All',
    'historyDetail.copied': 'Copied',
    'historyDetail.downloadTxt': 'Download TXT',
    'historyDetail.preparation': 'Preparation',
    'historyDetail.roundPrefix': 'Round',
    'historyDetail.expand': 'Expand',
    'historyDetail.collapse': 'Collapse',

    'event.planning': 'Team Formation',
    'event.introductions': 'Introductions',
    'event.researching': 'Research',
    'event.critique': 'Critique',
    'event.pi_summary': 'PI Summary',
    'event.iteration': 'Round Change',
    'event.round_revision': 'Revision',
    'event.final_synthesis': 'Final Report',
    'event.team_selection': 'Statistical Selection',
    'event.errorLabel': 'Error',
  },
} as const;

export type TranslationKey = keyof typeof TRANSLATIONS['ko'];

export function t(key: TranslationKey, locale?: Locale): string {
  const loc = locale ?? getLocale();
  return TRANSLATIONS[loc][key] ?? key;
}

/**
 * React hook: 현재 locale + t 함수 + locale 변경 함수 반환
 */
export function useLocale() {
  const [locale, setLocaleState] = useState<Locale>('ko');

  useEffect(() => {
    setLocaleState(getLocale());
    const handler = () => setLocaleState(getLocale());
    window.addEventListener(LOCALE_CHANGED_EVENT, handler);
    window.addEventListener('storage', handler);
    return () => {
      window.removeEventListener(LOCALE_CHANGED_EVENT, handler);
      window.removeEventListener('storage', handler);
    };
  }, []);

  const changeLocale = (newLocale: Locale) => {
    setLocale(newLocale);
    setLocaleState(newLocale);
  };

  return {
    locale,
    setLocale: changeLocale,
    t: (key: TranslationKey) => t(key, locale),
  };
}
