'use client';

import TitanRing from '@/components/TitanRing';

export default function PhoebeRing({
  radius,
  confidence,
  changeRate,
}: {
  radius: number;
  confidence: number;
  changeRate: number;
}) {
  const c = Math.max(0, Math.min(1, confidence));
  const rate = Math.max(0.1, Math.min(2.5, changeRate));

  return (
    <TitanRing
      innerRadius={radius * 1.7}
      outerRadius={radius * 1.8}
      color="#a78bfa"
      opacity={0.1 + c * 0.25}
      tilt={[Math.PI / 2 + toRad(8), 0, 0]}
      rotationSpeed={0.0028}
      pulseSpeed={0.8 + rate * 1.2}
      pulseAmount={0.06 + (1 - c) * 0.04}
    />
  );
}

function toRad(deg: number): number {
  return (deg * Math.PI) / 180;
}

