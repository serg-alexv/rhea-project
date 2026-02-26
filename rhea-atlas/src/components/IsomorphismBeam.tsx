'use client';

import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface IsomorphismBeamProps {
  start: THREE.Vector3;
  end: THREE.Vector3;
  color?: string;
  speed?: number;
}

export default function IsomorphismBeam({
  start,
  end,
  color = '#00ffff',
  speed = 1.0,
}: IsomorphismBeamProps) {
  const materialRef = useRef<THREE.ShaderMaterial>(null);

  // Create curve between points
  const curve = useMemo(() => {
    const midPoint = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5);
    const height = start.distanceTo(end) * 0.2;
    midPoint.y += height;
    return new THREE.QuadraticBezierCurve3(start, midPoint, end);
  }, [start, end]);

  const shaderMaterial = useMemo(() => {
    return new THREE.ShaderMaterial({
      uniforms: {
        uTime: { value: 0 },
        uColor: { value: new THREE.Color(color) },
        uSpeed: { value: speed },
      },
      vertexShader: `
        varying vec2 vUv;
        void main() {
          vUv = uv;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        uniform float uTime;
        uniform vec3 uColor;
        uniform float uSpeed;
        varying vec2 vUv;
        void main() {
          float pulse = mod(vUv.x - uTime * uSpeed * 0.5, 1.0);
          float strength = smoothstep(0.0, 0.1, 1.0 - abs(pulse - 0.5));
          vec3 finalColor = mix(uColor * 0.2, uColor, strength);
          gl_FragColor = vec4(finalColor, strength * 0.8);
        }
      `,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
  }, [color, speed]);

  useFrame((state) => {
    if (materialRef.current) {
      materialRef.current.uniforms.uTime.value = state.clock.elapsedTime;
    }
  });

  return (
    <mesh>
      <tubeGeometry args={[curve, 64, 0.02, 8, false]} />
      <primitive object={shaderMaterial} ref={materialRef} attach="material" />
    </mesh>
  );
}
