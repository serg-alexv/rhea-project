'use client';

import { useMemo } from 'react';
import * as THREE from 'three';
import TitanRing from '@/components/TitanRing';

interface TethysDot {
  ontology: string;
  count: number;
  color?: string;
}

export default function TethysRing({
  radius,
  dots,
}: {
  radius: number;
  dots: TethysDot[];
}) {
  const safeDots = dots.length ? dots : [{ ontology: 'general', count: 1, color: '#67e8f9' }];

  const placements = useMemo(() => {
    const step = (Math.PI * 2) / safeDots.length;
    return safeDots.map((dot, i) => {
      const angle = i * step;
      const orbit = radius * 1.575;
      return {
        key: `${dot.ontology}-${i}`,
        position: [Math.cos(angle) * orbit, Math.sin(angle) * orbit, 0] as [number, number, number],
        size: 0.022 + Math.min(0.06, dot.count * 0.007),
        color: dot.color ?? '#67e8f9',
      };
    });
  }, [radius, safeDots]);

  return (
    <group rotation={[Math.PI / 2 + toRad(20), 0, 0]}>
      <TitanRing
        innerRadius={radius * 1.55}
        outerRadius={radius * 1.6}
        color="#334155"
        opacity={0.1}
        rotationSpeed={0.0022}
      />
      {placements.map((dot) => (
        <mesh key={dot.key} position={dot.position}>
          <sphereGeometry args={[dot.size, 10, 10]} />
          <meshBasicMaterial color={dot.color} transparent opacity={0.65} />
        </mesh>
      ))}
    </group>
  );
}

function toRad(deg: number): number {
  return (deg * Math.PI) / 180;
}

