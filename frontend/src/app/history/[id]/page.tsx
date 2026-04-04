'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { fetchSessionEvents, type SessionDetail, type SessionEvent } from '@/lib/api';

export default function HistoryDetailPage() {
  const params = useParams();
  const sessionId = params.id as string;
  const [data, setData] = useState<SessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set());

  useEffect(() => {
    fetchSessionEvents(sessionId)
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [sessionId]);

  const toggle = (id: number) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const agentStyle = (agent: string) => {
    switch (agent) {
      case 'pi': return { label: 'PI', bg: 'bg-purple-50 border-purple-200', badge: 'bg-purple-100 text-purple-700' };
      case 'specialist': return { label: 'Specialist', bg: 'bg-blue-50 border-blue-200', badge: 'bg-blue-100 text-blue-700' };
      case 'critic': return { label: 'Critic', bg: 'bg-amber-50 border-amber-200', badge: 'bg-amber-100 text-amber-700' };
      default: return { label: agent || 'System', bg: 'bg-gray-50 border-gray-200', badge: 'bg-gray-100 text-gray-700' };
    }
  };

  const [copied, setCopied] = useState(false);

  const buildFullText = (detail: SessionDetail) => {
    const lines: string[] = [];
    lines.push(`=== ${detail.topic} ===`);
    lines.push(`상태: ${detail.status === 'completed' ? '완료' : detail.status}`);
    if (detail.total_rounds > 0) lines.push(`총 ${detail.total_rounds}라운드`);
    lines.push(`이벤트: ${detail.events.length}개`);
    lines.push('');

    const groups = groupByRound(detail.events);
    for (const group of groups) {
      lines.push(`--- ${group.round === 0 ? '사전 준비' : `라운드 ${group.round}`} ---`);
      for (const ev of group.events) {
        const name = ev.agent_name || ev.agent || 'System';
        const label = eventLabel(ev.event_type);
        lines.push(`[${name}] ${label}`);
        if (ev.scores) {
          const scoreStr = Object.entries(ev.scores)
            .map(([role, score]) => {
              if (typeof score === 'object' && score !== null) {
                return `${role}: ${Object.entries(score).map(([k, v]) => `${k}=${v}`).join(', ')}`;
              }
              return `${role}: ${score}/5`;
            })
            .join(' | ');
          lines.push(`  점수: ${scoreStr}`);
        }
        if (ev.content) {
          lines.push(ev.content);
        }
        lines.push('');
      }
    }
    return lines.join('\n');
  };

  const handleCopy = () => {
    if (!data) return;
    navigator.clipboard.writeText(buildFullText(data)).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const handleDownload = () => {
    if (!data) return;
    const text = buildFullText(data);
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${data.topic.replace(/[^a-zA-Z0-9가-힣\s]/g, '').trim().slice(0, 50)}_session.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const eventLabel = (type: string) => {
    const labels: Record<string, string> = {
      planning: '팀 구성',
      introductions: '전문가 소개',
      researching: '분석',
      critique: '비평 평가',
      pi_summary: 'PI 종합',
      iteration: '라운드 변경',
      round_revision: '수정 분석',
      final_synthesis: '최종 보고서',
      team_selection: '통계적 선별',
      error: '오류',
    };
    return labels[type] || type;
  };

  // 이벤트를 라운드별로 그룹핑
  const groupByRound = (events: SessionEvent[]) => {
    const groups: { round: number; events: SessionEvent[] }[] = [];
    let currentRound = 0;
    let currentGroup: SessionEvent[] = [];

    for (const event of events) {
      if (event.event_type === 'iteration' && event.round > currentRound) {
        if (currentGroup.length > 0) {
          groups.push({ round: currentRound, events: currentGroup });
        }
        currentRound = event.round;
        currentGroup = [];
      } else {
        currentGroup.push(event);
      }
    }
    if (currentGroup.length > 0) {
      groups.push({ round: currentRound, events: currentGroup });
    }
    return groups;
  };

  return (
    <div className="min-h-screen bg-[#f6f8f7] text-[#121714]">
      <header className="sticky top-0 z-50 bg-white border-b border-[#dde4e0] shadow-sm">
        <div className="max-w-[1800px] mx-auto px-10 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <img src="/logo.png" alt="Virtual Lab" className="h-12" />
            </div>
            <nav className="flex items-center gap-6">
              <Link href="/" className="text-sm font-medium text-[#678373] hover:text-[#1b7440] transition-colors pb-0.5">Dashboard</Link>
              <Link href="/timeline" className="text-sm font-medium text-[#678373] hover:text-[#1b7440] transition-colors pb-0.5">Agents</Link>
              <Link href="/reports" className="text-sm font-medium text-[#678373] hover:text-[#1b7440] transition-colors pb-0.5">Reports</Link>
              <Link href="/history" className="text-sm font-bold text-[#1b7440] border-b-2 border-[#1b7440] pb-0.5">History</Link>
            </nav>
            <Link href="/history" className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-[#678373] hover:text-[#1b7440] hover:bg-[#1b7440]/5 transition-all">
              <span className="material-symbols-outlined text-sm">arrow_back</span>
              Back to History
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-[1200px] mx-auto px-10 py-8">
        {loading && <p className="text-[#678373]">로딩 중...</p>}
        {error && <p className="text-red-600">{error}</p>}

        {data && (
          <>
            {/* 세션 요약 */}
            <div className="mb-8">
              <h1 className="text-2xl font-bold mb-2">{data.topic}</h1>
              <div className="flex items-center gap-4 text-sm text-[#678373]">
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                  data.status === 'completed' ? 'bg-green-100 text-green-700' :
                  data.status === 'running' ? 'bg-blue-100 text-blue-700' : 'bg-red-100 text-red-700'
                }`}>
                  {data.status === 'completed' ? '완료' : data.status === 'running' ? '진행 중' : '오류'}
                </span>
                {data.total_rounds > 0 && <span>총 {data.total_rounds}라운드 진행</span>}
                <span>{data.events.length}개 이벤트</span>
              </div>

              <div className="flex items-center gap-3 mt-4">
                {/* 리포트 연결 링크 */}
                {data.status === 'completed' && (
                  <Link
                    href="/reports"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-[#1b7440] text-white rounded-lg text-sm font-medium hover:bg-[#145530] transition-colors"
                  >
                    <span className="material-symbols-outlined text-sm">description</span>
                    최종 보고서 보기
                  </Link>
                )}

                <button
                  onClick={handleCopy}
                  className="inline-flex items-center gap-2 px-4 py-2 border border-[#dde4e0] bg-white rounded-lg text-sm font-medium text-[#3a4d42] hover:bg-[#f6f8f7] transition-colors"
                >
                  <span className="material-symbols-outlined text-sm">
                    {copied ? 'check' : 'content_copy'}
                  </span>
                  {copied ? '복사 완료' : '전체 복사'}
                </button>

                <button
                  onClick={handleDownload}
                  className="inline-flex items-center gap-2 px-4 py-2 border border-[#dde4e0] bg-white rounded-lg text-sm font-medium text-[#3a4d42] hover:bg-[#f6f8f7] transition-colors"
                >
                  <span className="material-symbols-outlined text-sm">download</span>
                  TXT 저장
                </button>
              </div>
            </div>

            {/* 라운드별 타임라인 */}
            {groupByRound(data.events).map((group) => (
              <div key={group.round} className="mb-8">
                <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
                  <span className="w-8 h-8 bg-[#1b7440] text-white rounded-full flex items-center justify-center text-sm font-bold">
                    {group.round || 0}
                  </span>
                  {group.round === 0 ? '사전 준비' : `라운드 ${group.round}`}
                </h2>

                <div className="space-y-3 ml-4 border-l-2 border-[#dde4e0] pl-6">
                  {group.events.map((event) => {
                    const style = agentStyle(event.agent);
                    const isExpanded = expandedIds.has(event.id);

                    return (
                      <div
                        key={event.id}
                        className={`rounded-lg border p-4 ${style.bg} cursor-pointer transition-all hover:shadow-sm`}
                        onClick={() => toggle(event.id)}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <span className={`px-2 py-0.5 rounded text-xs font-medium ${style.badge}`}>
                              {event.agent_name || style.label}
                            </span>
                            <span className="text-sm font-medium">{eventLabel(event.event_type)}</span>
                            {event.scores && (
                              <div className="flex gap-1">
                                {Object.entries(event.scores).map(([role, score]) => (
                                  <span key={role} className="text-xs bg-white/80 px-2 py-0.5 rounded">
                                    {role.split(' ')[0]}: {typeof score === 'object' && score !== null
                                      ? Object.entries(score).map(([k, v]) => `${k}:${v}`).join(' ')
                                      : `${score}/5`}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                          <span className="text-xs text-[#678373]">
                            {isExpanded ? '접기' : '펼치기'}
                          </span>
                        </div>

                        {isExpanded && event.content && (
                          <div className="mt-3 pt-3 border-t border-black/10">
                            <pre className="text-sm whitespace-pre-wrap text-[#121714]/80 max-h-96 overflow-y-auto">
                              {event.content}
                            </pre>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </>
        )}
      </main>
    </div>
  );
}
