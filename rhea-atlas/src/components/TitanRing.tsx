'use client';

import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

export interface RingSegment {
  startAngle: number;
  endAngle: number;
  color: string;
  opacity: number;
  thickness: number;
}

export interface TitanRingProps {
  innerRadius: number;
  outerRadius: number;
  segments?: number;
  color?: string;
  opacity?: number;
  tilt?: [number, number, number];
  data?: RingSegment[];
  pulseSpeed?: number;
  pulseAmount?: number;
  rotationSpeed?: number;
}

function normalizeSegments(input: RingSegment[] | undefined, color: string, opacity: number): RingSegment[] {
  if (input && input.length) return input;
  return [{
    startAngle: 0,
    endAngle: Math.PI * 2,
    color,
    opacity,
    thickness: 1,
  }];
}

export default function TitanRing({
  innerRadius,
  outerRadius,
  segments = 64,
  color = '#67e8f9',
  opacity = 0.2,
  tilt = [Math.PI / 2, 0, 0],
  data,
  pulseSpeed,
  pulseAmount = 0.08,
  rotationSpeed = 0.001,
}: TitanRingProps) {
  const groupRef = useRef<THREE.Group>(null);
  const baseScale = useRef(1);

  const ringSegments = useMemo(
    () => normalizeSegments(data, color, opacity),
    [data, color, opacity],
  );

  useFrame((state) => {
    if (!groupRef.current) return;
    groupRef.current.rotation.z += rotationSpeed;
    if (pulseSpeed && pulseSpeed > 0) {
      const pulse = 1 + Math.sin(state.clock.elapsedTime * pulseSpeed) * pulseAmount;
      groupRef.current.scale.setScalar(baseScale.current * pulse);
    }
  });

  const bandWidth = Math.max(0.001, outerRadius - innerRadius);

  return (
    <group ref={groupRef} rotation={tilt}>
      {ringSegments.map((segment, index) => {
        const start = Math.max(0, segment.startAngle);
        const end = Math.max(start + 0.001, segment.endAngle);
        const thetaLength = Math.min(Math.PI * 2, end - start);
        const thickness = Math.max(0.05, segment.thickness);
        const halfShrink = bandWidth * Math.max(0, (1 - thickness) * 0.5);
        const localInner = Math.max(0.001, innerRadius + halfShrink);
        const localOuter = Math.max(localInner + 0.001, outerRadius - halfShrink);

        return (
          <mesh key={`${index}-${start.toFixed(3)}-${end.toFixed(3)}`}>
            <ringGeometry args={[localInner, localOuter, segments, 1, start, thetaLength]} />
            <meshBasicMaterial
              color={segment.color}
              transparent
              opacity={Math.max(0, Math.min(1, segment.opacity))}
              side={THREE.DoubleSide}
              depthWrite={false}
            />
          </mesh>
        );
      })}
    </group>
  );
}

