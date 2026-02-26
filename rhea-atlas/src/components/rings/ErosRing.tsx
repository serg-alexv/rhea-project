'use client';

import TitanRing, { RingSegment } from '@/components/TitanRing';

export default function ErosRing({
  radius,
  agreement,
}: {
  radius: number;
  agreement: number;
}) {
  const clamped = Math.max(0, Math.min(1, agreement));
  const segmentCount = 18;
  const step = (Math.PI * 2) / segmentCount;

  const data: RingSegment[] = Array.from({ length: segmentCount }, (_, i) => {
    const t = i / Math.max(1, segmentCount - 1);
    const wave = Math.sin(t * Math.PI * 2 + clamped * Math.PI) * 0.5 + 0.5;
    const localAgreement = Math.max(0, Math.min(1, clamped * 0.7 + wave * 0.3));
    const red = Math.round(244 - localAgreement * 142);
    const green = Math.round(63 + localAgreement * 149);
    const blue = Math.round(94 + localAgreement * 118);
    return {
      startAngle: i * step,
      endAngle: (i + 1) * step,
      color: `rgb(${red}, ${green}, ${blue})`,
      opacity: 0.16 + localAgreement * 0.34,
      thickness: 0.65 + localAgreement * 0.35,
    };
  });

  return (
    <TitanRing
      innerRadius={radius * 1.35}
      outerRadius={radius * 1.5}
      tilt={[Math.PI / 2 + toRad(12), 0, 0]}
      rotationSpeed={0.0018}
      pulseSpeed={0.6 + clamped * 1.1}
      pulseAmount={0.035}
      data={data}
    />
  );
}

function toRad(deg: number): number {
  return (deg * Math.PI) / 180;
}

