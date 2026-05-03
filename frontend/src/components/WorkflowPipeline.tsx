'use client';

/**
 * 상세 워크플로우 파이프라인 시각화 (다국어 지원)
 * Dashboard의 Agent Team Status 아래 배치.
 * 6개 Phase + 라운드 루프 + 조기 종료 조건을 한눈에 파악 가능하도록 구성.
 */

import { useLocale, type Locale } from '@/lib/i18n';

interface PhaseConfig {
  num: string;
  title: string;
  agent: 'PI' | 'Specialist' | 'Critic' | 'Decision' | 'Final';
  icon: string;
  description: string;
  details: string[];
  duration?: string;
}

const AGENT_STYLE = {
  PI: {
    bg: 'bg-blue-50',
    iconBg: 'bg-blue-100',
    iconColor: 'text-blue-600',
    borderColor: 'border-blue-200',
    badge: 'bg-blue-100 text-blue-700',
  },
  Specialist: {
    bg: 'bg-purple-50',
    iconBg: 'bg-purple-100',
    iconColor: 'text-purple-600',
    borderColor: 'border-purple-200',
    badge: 'bg-purple-100 text-purple-700',
  },
  Critic: {
    bg: 'bg-amber-50',
    iconBg: 'bg-amber-100',
    iconColor: 'text-amber-600',
    borderColor: 'border-amber-200',
    badge: 'bg-amber-100 text-amber-700',
  },
  Decision: {
    bg: 'bg-gray-50',
    iconBg: 'bg-gray-100',
    iconColor: 'text-gray-600',
    borderColor: 'border-gray-200',
    badge: 'bg-gray-100 text-gray-700',
  },
  Final: {
    bg: 'bg-emerald-50',
    iconBg: 'bg-emerald-100',
    iconColor: 'text-emerald-600',
    borderColor: 'border-emerald-200',
    badge: 'bg-emerald-100 text-emerald-700',
  },
} as const;

// 에이전트 배지 라벨 (locale별)
const AGENT_BADGE_LABEL: Record<Locale, Record<string, string>> = {
  ko: {
    PI: 'PI Agent',
    Specialist: 'Specialist Agents',
    Critic: 'Critic Agent',
    Decision: 'Decision',
    Final: 'Final Report',
  },
  en: {
    PI: 'PI Agent',
    Specialist: 'Specialist Agents',
    Critic: 'Critic Agent',
    Decision: 'Decision',
    Final: 'Final Report',
  },
};

// Phase 정의 (locale별)
const PHASES_BY_LOCALE: Record<Locale, PhaseConfig[]> = {
  ko: [
    {
      num: '01',
      title: 'Team Formation',
      agent: 'PI',
      icon: 'groups',
      description: 'PI가 통계적 방법으로 연구팀을 구성합니다',
      details: [
        '10회 독립적 팀 구성 시뮬레이션 (병렬 실행)',
        '빈도 분석 → 유사 역할 클러스터링',
        'PI가 최종 전문가 팀 확정',
        '전문가별 자기소개 생성',
      ],
      duration: '≈ 2-3분',
    },
    {
      num: '02',
      title: 'Round 1 Research',
      agent: 'Specialist',
      icon: 'science',
      description: '전문가들이 병렬로 초기 분석을 수행합니다',
      details: [
        'RAG 검색 — Pinecone (500 규제 문서)',
        'Web 검색 — Tavily API',
        'EFSA Journal 전용 검색',
        '각 전문가가 자기 분야 관점에서 해석 중심 분석',
      ],
      duration: '≈ 3-5분',
    },
    {
      num: '03',
      title: 'Critique',
      agent: 'Critic',
      icon: 'fact_check',
      description: 'Critic이 전문가별로 4축 점수와 피드백을 제공합니다',
      details: [
        '① 과학적 근거 (Evidence) — 1-5점',
        '② 범용성 (Universality) — 1-5점',
        '③ 비례성 (Proportionality) — 1-5점',
        '④ 가독성 (Readability) — 1-5점',
        '전문가별 구체적 개선 지시 생성',
      ],
      duration: '≈ 1-2분',
    },
    {
      num: '04',
      title: 'PI Summary',
      agent: 'PI',
      icon: 'psychology',
      description: 'PI가 라운드 논의를 종합해 임시 결론을 도출합니다',
      details: [
        '라운드별 쟁점과 합의사항 정리',
        '미해결 쟁점 식별 (다음 라운드 주제)',
        '임시 결론 도출',
        '이전 라운드 결과와의 연속성 확보',
      ],
      duration: '≈ 1-2분',
    },
    {
      num: '05',
      title: 'Round Revision Loop',
      agent: 'Decision',
      icon: 'autorenew',
      description: '품질 기준 도달까지 반복 (최대 7라운드)',
      details: [
        '모든 전문가가 5/5 만점 → 조기 종료 (Phase 6으로)',
        '일부라도 미달 → 피드백 반영한 수정 진행',
        '최우선 개선 축에 집중하여 재작성',
        '현재 최대 7라운드 설정 (만점 시 조기 종료)',
      ],
      duration: '라운드당 ≈ 5-8분',
    },
    {
      num: '06',
      title: 'Final Synthesis',
      agent: 'Final',
      icon: 'task_alt',
      description: 'PI가 전체 라운드의 베스트 파트를 선별해 최종 보고서를 작성합니다',
      details: [
        '모든 라운드의 PI 요약 + 최종 라운드 정제본 통합',
        '웹 검색 + EFSA 검색 최신 정보 보강',
        '5개 Mermaid 의사결정 흐름도 생성 (통합 + SDN/ODM 4개)',
        '참고문헌·에이전트 기여도·전문가 자기소개 포함',
      ],
      duration: '≈ 3-5분',
    },
  ],
  en: [
    {
      num: '01',
      title: 'Team Formation',
      agent: 'PI',
      icon: 'groups',
      description: 'PI statistically composes the research team',
      details: [
        '10 independent team composition trials (parallel)',
        'Frequency analysis → similar-role clustering',
        'PI finalizes the expert team',
        'Generate per-specialist self-introductions',
      ],
      duration: '≈ 2-3 min',
    },
    {
      num: '02',
      title: 'Round 1 Research',
      agent: 'Specialist',
      icon: 'science',
      description: 'Specialists perform initial analysis in parallel',
      details: [
        'RAG search — Pinecone (500 regulatory docs)',
        'Web search — Tavily API',
        'EFSA Journal dedicated search',
        'Each specialist writes interpretive analysis from their domain',
      ],
      duration: '≈ 3-5 min',
    },
    {
      num: '03',
      title: 'Critique',
      agent: 'Critic',
      icon: 'fact_check',
      description: 'Critic scores each specialist on 4 axes + feedback',
      details: [
        '① Evidence — 1-5',
        '② Universality — 1-5',
        '③ Proportionality — 1-5',
        '④ Readability — 1-5',
        'Specific improvement instructions per specialist',
      ],
      duration: '≈ 1-2 min',
    },
    {
      num: '04',
      title: 'PI Summary',
      agent: 'PI',
      icon: 'psychology',
      description: 'PI synthesizes round discussion into an interim conclusion',
      details: [
        'Summarize round issues and agreements',
        'Identify unresolved issues (next round topics)',
        'Draft interim conclusion',
        'Maintain continuity with prior rounds',
      ],
      duration: '≈ 1-2 min',
    },
    {
      num: '05',
      title: 'Round Revision Loop',
      agent: 'Decision',
      icon: 'autorenew',
      description: 'Repeat until quality bar is met (up to 7 rounds)',
      details: [
        'All specialists at 5/5 → early exit (to Phase 6)',
        'Any score below target → revise using feedback',
        'Focus on weakest axis for rewrite',
        'Max rounds currently set to 7 (early exit on perfect)',
      ],
      duration: '≈ 5-8 min / round',
    },
    {
      num: '06',
      title: 'Final Synthesis',
      agent: 'Final',
      icon: 'task_alt',
      description: 'PI distills the best parts of all rounds into a final report',
      details: [
        'Combine all-round PI summaries + polished last round',
        'Augment with web + EFSA latest info',
        'Generate 5 Mermaid decision flowcharts (overall + SDN/ODM ×4)',
        'Include references, agent contribution stats, self-introductions',
      ],
      duration: '≈ 3-5 min',
    },
  ],
};

// 섹션 헤더/레전드/종료조건 텍스트
const SECTION_TEXT: Record<Locale, {
  heading: string;
  badge: string;
  subtitle: string;
  legend: string;
  phase: string;
  loopLabel: string;
  loopPath: string;
  exitHeading: string;
  exitEarly: string;
  exitEarlyDesc: string;
  exitMax: string;
  exitMaxDesc: string;
}> = {
  ko: {
    heading: 'Workflow Pipeline',
    badge: '6 Phases · 최대 7 Rounds',
    subtitle: '전체 흐름을 한눈에 확인하세요',
    legend: 'AGENTS:',
    phase: 'Phase',
    loopLabel: '루프 경로',
    loopPath: 'Phase 02 (수정) → Phase 03 (재채점) → Phase 04 → 다시 이 지점',
    exitHeading: '종료 조건',
    exitEarly: '조기 종료',
    exitEarlyDesc: '모든 전문가의 4개 축이 전부 5/5 만점 도달 시',
    exitMax: '최대 라운드 도달',
    exitMaxDesc: '7 라운드까지 진행 후 현재까지의 베스트로 최종 합성',
  },
  en: {
    heading: 'Workflow Pipeline',
    badge: '6 Phases · Max 7 Rounds',
    subtitle: 'See the full flow at a glance',
    legend: 'AGENTS:',
    phase: 'Phase',
    loopLabel: 'Loop path',
    loopPath: 'Phase 02 (revise) → Phase 03 (re-score) → Phase 04 → back here',
    exitHeading: 'Exit Conditions',
    exitEarly: 'Early exit',
    exitEarlyDesc: 'When every specialist reaches 5/5 on all four axes',
    exitMax: 'Max rounds reached',
    exitMaxDesc: 'After 7 rounds, synthesize the final report from the best so far',
  },
};

function PhaseCard({
  phase,
  index,
  total,
  section,
  badgeLabels,
}: {
  phase: PhaseConfig;
  index: number;
  total: number;
  section: typeof SECTION_TEXT['ko'];
  badgeLabels: Record<string, string>;
}) {
  const style = AGENT_STYLE[phase.agent];
  const isLoop = phase.agent === 'Decision';

  return (
    <div className="relative flex gap-4">
      <div className="flex flex-col items-center flex-shrink-0">
        <div
          className={`w-12 h-12 rounded-full ${style.iconBg} border-2 ${style.borderColor} flex items-center justify-center z-10 shadow-sm`}
        >
          <span className={`material-symbols-outlined ${style.iconColor}`}>
            {phase.icon}
          </span>
        </div>
        {index < total - 1 && (
          <div
            className={`w-0.5 flex-1 min-h-[40px] ${
              isLoop ? 'border-l-2 border-dashed border-[var(--border)]' : 'bg-[var(--border)]'
            }`}
          />
        )}
      </div>

      <div className={`flex-1 mb-6 ${style.bg} ${style.borderColor} border rounded-xl p-4`}>
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs font-mono font-bold text-[var(--text-muted)]">
            {section.phase} {phase.num}
          </span>
          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${style.badge}`}>
            {badgeLabels[phase.agent]}
          </span>
          {phase.duration && (
            <span className="ml-auto text-[10px] text-[var(--text-muted)] font-mono">
              {phase.duration}
            </span>
          )}
        </div>

        <h4 className="font-bold text-sm text-[var(--foreground)] mb-1">{phase.title}</h4>
        <p className="text-xs text-[var(--text-muted)] mb-3 leading-relaxed">
          {phase.description}
        </p>

        <ul className="space-y-1">
          {phase.details.map((detail, i) => (
            <li
              key={i}
              className="text-xs text-[var(--foreground)] flex items-start gap-2 leading-relaxed"
            >
              <span className={`${style.iconColor} mt-0.5 flex-shrink-0`}>•</span>
              <span>{detail}</span>
            </li>
          ))}
        </ul>

        {isLoop && (
          <div className="mt-3 pt-3 border-t border-dashed border-gray-300 flex items-center gap-2 text-[11px]">
            <span className="material-symbols-outlined icon-sm text-gray-500">
              sync
            </span>
            <span className="text-gray-600">
              <strong>{section.loopLabel}</strong>: {section.loopPath}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

export default function WorkflowPipeline() {
  const { locale } = useLocale();
  const phases = PHASES_BY_LOCALE[locale];
  const section = SECTION_TEXT[locale];
  const badgeLabels = AGENT_BADGE_LABEL[locale];

  return (
    <section id="workflow-pipeline-section" className="mb-6 scroll-mt-20">
      <div className="glass-panel p-6">
        {/* Section Header */}
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[var(--primary)]">
              account_tree
            </span>
            <h3 className="text-lg font-bold text-[var(--foreground)]">
              {section.heading}
            </h3>
            <span className="px-2.5 py-0.5 rounded-full bg-[var(--primary-light)] text-[var(--primary)] text-[11px] font-medium">
              {section.badge}
            </span>
          </div>
          <span className="text-xs text-[var(--text-muted)]">
            {section.subtitle}
          </span>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-3 mb-5 pb-4 border-b border-[var(--border)]">
          <span className="text-[11px] text-[var(--text-muted)] font-medium">
            {section.legend}
          </span>
          <div className="flex items-center gap-1.5 text-[11px]">
            <span className="w-2 h-2 rounded-full bg-blue-500" />
            <span className="text-[var(--foreground)]">PI</span>
          </div>
          <div className="flex items-center gap-1.5 text-[11px]">
            <span className="w-2 h-2 rounded-full bg-purple-500" />
            <span className="text-[var(--foreground)]">Specialist</span>
          </div>
          <div className="flex items-center gap-1.5 text-[11px]">
            <span className="w-2 h-2 rounded-full bg-amber-500" />
            <span className="text-[var(--foreground)]">Critic</span>
          </div>
          <div className="flex items-center gap-1.5 text-[11px]">
            <span className="w-2 h-2 rounded-full bg-gray-500" />
            <span className="text-[var(--foreground)]">Decision</span>
          </div>
          <div className="flex items-center gap-1.5 text-[11px]">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span className="text-[var(--foreground)]">Final</span>
          </div>
        </div>

        {/* Phases Timeline */}
        <div className="relative">
          {phases.map((phase, i) => (
            <PhaseCard
              key={phase.num}
              phase={phase}
              index={i}
              total={phases.length}
              section={section}
              badgeLabels={badgeLabels}
            />
          ))}
        </div>

        {/* Exit Conditions Summary */}
        <div className="mt-4 p-4 bg-[var(--background)] rounded-xl border border-[var(--border)]">
          <div className="flex items-center gap-2 mb-2">
            <span className="material-symbols-outlined icon-sm text-[var(--primary)]">
              rule
            </span>
            <p className="text-xs font-bold text-[var(--foreground)]">
              {section.exitHeading}
            </p>
          </div>
          <ul className="space-y-1 text-xs text-[var(--text-muted)]">
            <li className="flex items-start gap-2">
              <span className="text-green-600 flex-shrink-0">✓</span>
              <span>
                <strong className="text-[var(--foreground)]">{section.exitEarly}</strong>:{' '}
                {section.exitEarlyDesc}
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-red-600 flex-shrink-0">⏹</span>
              <span>
                <strong className="text-[var(--foreground)]">{section.exitMax}</strong>:{' '}
                {section.exitMaxDesc}
              </span>
            </li>
          </ul>
        </div>
      </div>
    </section>
  );
}
