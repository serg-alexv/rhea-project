'use client';

import { memo, useMemo } from 'react';
import { Line } from '@react-three/drei';
import * as THREE from 'three';
import { ContextDensity } from '@/store/useAtlasStore';

type DensityVector = ContextDensity['vectorField'][number];

interface FlowArrowProps {
  origin: DensityVector['origin'];
  direction: DensityVector['direction'];
  magnitude: number;
  color: string;
}

function FlowArrow({ origin, direction, magnitude, color }: FlowArrowProps) {
  const opacity = Math.min(0.95, 0.25 + magnitude * 0.75);

  const { points, headPosition, quaternion, headRadius, headHeight } = useMemo(() => {
    const dir = new THREE.Vector3(...direction);
    if (dir.lengthSq() < 1e-6) dir.set(0.04, 0.02, 0.01);
    const unit = dir.clone().normalize();
    const length = 0.1 + magnitude * 0.4;
    const end = unit.clone().multiplyScalar(length);
    const quat = new THREE.Quaternion().setFromUnitVectors(
      new THREE.Vector3(0, 1, 0),
      unit,
    );

    return {
      points: [
        [0, 0, 0],
        [end.x, end.y, end.z],
      ] as [number, number, number][],
      headPosition: [end.x, end.y, end.z] as [number, number, number],
      quaternion: quat,
      headRadius: 0.015 + magnitude * 0.015,
      headHeight: 0.045 + magnitude * 0.05,
    };
  }, [direction, magnitude]);

  return (
    <group position={origin}>
      <Line
        points={points}
        color={color}
        transparent
        opacity={opacity}
      />
      <mesh position={headPosition} quaternion={quaternion}>
        <coneGeometry args={[headRadius, headHeight, 6]} />
        <meshBasicMaterial color={color} transparent opacity={opacity} />
      </mesh>
    </group>
  );
}

function DensityFieldBase({
  vectors,
  color,
  maxArrows = 16,
}: {
  vectors: ContextDensity['vectorField'];
  color: string;
  maxArrows?: number;
}) {
  const trimmed = useMemo(() => vectors.slice(0, Math.max(0, maxArrows)), [maxArrows, vectors]);

  if (trimmed.length === 0) return null;

  return (
    <group>
      {trimmed.map((vector, index) => (
        <FlowArrow
          key={`${index}-${vector.magnitude.toFixed(3)}`}
          origin={vector.origin}
          direction={vector.direction}
          magnitude={vector.magnitude}
          color={color}
        />
      ))}
    </group>
  );
}

const DensityField = memo(DensityFieldBase);
export default DensityField;

