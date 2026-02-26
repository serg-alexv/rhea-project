'use client';

import TitanRing, { RingSegment } from '@/components/TitanRing';

export default function ChronosRing({
  radius,
  count,
  recencyBias = 1,
}: {
  radius: number;
  count: number;
  recencyBias?: number;
}) {
  const segmentCount = Math.max(1, Math.min(24, count));
  const step = (Math.PI * 2) / segmentCount;
  const gap = step * 0.12;

  const data: RingSegment[] = Array.from({ length: segmentCount }, (_, i) => {
    const t = segmentCount <= 1 ? 1 : i / (segmentCount - 1);
    const recency = Math.pow(1 - t, Math.max(0.6, recencyBias));
    return {
      startAngle: i * step + gap * 0.5,
      endAngle: (i + 1) * step - gap * 0.5,
      color: '#67e8f9',
      opacity: 0.16 + recency * 0.42,
      thickness: 0.72 + recency * 0.28,
    };
  });

  return (
    <TitanRing
      innerRadius={radius * 1.2}
      outerRadius={radius * 1.3}
      tilt={[Math.PI / 2 + THREE_DEG(5), 0, 0]}
      rotationSpeed={0.0014}
      data={data}
    />
  );
}

function THREE_DEG(deg: number): number {
  return (deg * Math.PI) / 180;
}

