/**
 * @TASK P4-T1 - Next.js API Route Test
 * @SPEC TASKS.md#P4-T1
 *
 * Next.js API Route가 정상 작동하는지 확인하는 테스트 엔드포인트
 */

import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({
    status: 'ok',
    message: 'Next.js frontend is running',
    timestamp: new Date().toISOString(),
  });
}
