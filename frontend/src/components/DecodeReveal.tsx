import React, { useState, useEffect } from 'react';

interface DecodeRevealProps {
  value: string;
  durationMs?: number;
  className?: string;
}

const GLYPHS = '0123456789ABCDEF!@#$%&*';

export const DecodeReveal: React.FC<DecodeRevealProps> = ({
  value,
  durationMs = 320,
  className = ''
}) => {
  const [display, setDisplay] = useState(value);

  useEffect(() => {
    // Check for reduced motion
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setDisplay(value);
      return;
    }

    let frame = 0;
    const totalFrames = Math.max(4, Math.floor(durationMs / 40));
    const targetLength = value.length;

    const interval = setInterval(() => {
      frame++;
      const progress = frame / totalFrames;
      const revealedLength = Math.floor(progress * targetLength);

      let scrambled = '';
      for (let i = 0; i < targetLength; i++) {
        if (i < revealedLength) {
          scrambled += value[i];
        } else {
          scrambled += GLYPHS[Math.floor(Math.random() * GLYPHS.length)];
        }
      }

      setDisplay(scrambled);

      if (frame >= totalFrames) {
        clearInterval(interval);
        setDisplay(value);
      }
    }, 40);

    return () => clearInterval(interval);
  }, [value, durationMs]);

  return <span className={`font-mono transition-opacity ${className}`}>{display}</span>;
};
