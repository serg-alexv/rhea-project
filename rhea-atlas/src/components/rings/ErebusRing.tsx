'use client';

import TitanRing from '@/components/TitanRing';

export default function ErebusRing({
  radius,
  auditCount,
}: {
  radius: number;
  auditCount: number;
}) {
  const widthFactor = Math.max(0.7, Math.min(1.2, 0.72 + auditCount * 0.015));
  const opacity = Math.max(0.08, Math.min(0.22, 0.08 + auditCount * 0.004));

  return (
    <TitanRing
      innerRadius={radius * 1.1}
      outerRadius={radius * 1.15}
      color="#0f172a"
      opacity={opacity}
      rotationSpeed={0.001}
      data={[
        {
          startAngle: 0,
          endAngle: Math.PI * 2,
          color: '#1f2937',
          opacity,
          thickness: widthFactor,
        },
      ]}
    />
  );
}

