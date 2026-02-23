'use client';

import { useEffect, useState } from 'react';

interface SpeechBubbleProps {
  message: string;
  direction?: 'up' | 'down';
  maxWidth?: number;
  autoHide?: number; // ms, 0 = no auto-hide
}

export default function SpeechBubble({
  message,
  direction = 'up',
  maxWidth = 200,
  autoHide = 8000,
}: SpeechBubbleProps) {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    setVisible(true);
    if (autoHide > 0) {
      const timer = setTimeout(() => setVisible(false), autoHide);
      return () => clearTimeout(timer);
    }
  }, [message, autoHide]);

  if (!visible || !message) return null;

  const truncated = message.length > 80 ? message.slice(0, 77) + '...' : message;

  return (
    <div
      className={`animate-speech-appear absolute z-10 ${
        direction === 'up' ? 'bottom-full mb-2' : 'top-full mt-2'
      }`}
      style={{ maxWidth }}
    >
      <div className="relative glass-panel rounded-lg px-3 py-2 text-xs text-white/90 leading-relaxed border border-white/20">
        {truncated}
        {/* Tail */}
        <div
          className={`absolute left-1/2 -translate-x-1/2 w-0 h-0 ${
            direction === 'up'
              ? 'top-full border-l-[6px] border-r-[6px] border-t-[6px] border-l-transparent border-r-transparent border-t-[rgba(26,35,46,0.8)]'
              : 'bottom-full border-l-[6px] border-r-[6px] border-b-[6px] border-l-transparent border-r-transparent border-b-[rgba(26,35,46,0.8)]'
          }`}
        />
      </div>
    </div>
  );
}
