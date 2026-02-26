'use client';

import { useEffect, useMemo } from 'react';
import { ContextDensity, SessionEntry, useAtlasStore } from '@/store/useAtlasStore';

const ONTOLOGY_COLORS: Record<string, string> = {
  general: '#06b6d4',
  pharmacology: '#10b981',
  biochemistry: '#f59e0b',
  logic: '#8b5cf6',
  topology: '#f43f5e',
  systems_biology: '#6366f1',
};

function normalizeOntology(input: string): string {
  return input.trim().toLowerCase().replace(/\s+/g, '_');
}

function ontologyColor(ontology: string): string {
  return ONTOLOGY_COLORS[normalizeOntology(ontology)] ?? '#67e8f9';
}

function extractConsensusScore(result: string): number {
  if (!result) return 50;
  const agreement = result.match(/agreement:\s*(\d{1,3})%/i);
  if (agreement) return Math.max(0, Math.min(100, Number(agreement[1])));
  const consensus = result.match(/consensus[^\d]*(\d{1,3})/i);
  if (consensus) return Math.max(0, Math.min(100, Number(consensus[1])));
  return 50;
}

function mean(values: number[]): number {
  if (values.length === 0) return 0;
  return values.reduce((sum, v) => sum + v, 0) / values.length;
}

function stdDev(values: number[]): number {
  if (values.length <= 1) return 0;
  const avg = mean(values);
  const variance = values.reduce((sum, v) => sum + (v - avg) ** 2, 0) / values.length;
  return Math.sqrt(variance);
}

function hashText(input: string): number {
  let h = 2166136261;
  for (let i = 0; i < input.length; i++) {
    h ^= input.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

function groupByOntology(sessions: SessionEntry[]): Record<string, SessionEntry[]> {
  const groups: Record<string, SessionEntry[]> = {};
  for (const entry of sessions) {
    const key = entry.ontology || 'General';
    if (!groups[key]) groups[key] = [];
    groups[key].push(entry);
  }
  return groups;
}

function buildVectors(scores: number[], seed: number): ContextDensity['vectorField'] {
  const count = Math.min(16, Math.max(1, scores.length));
  const vectors: ContextDensity['vectorField'] = [];
  for (let i = 0; i < count; i++) {
    const score = scores[i] ?? scores[scores.length - 1] ?? 50;
    const next = scores[i + 1] ?? score;
    const directionDelta = (next - score) / 100;
    const angle = i * 0.7 + ((seed % 360) * Math.PI) / 180;
    const radius = 0.35 + (i % 4) * 0.12;
    const dx = Math.cos(angle) * directionDelta * 0.9;
    const dy = Math.sin(angle) * directionDelta * 0.55;
    const dz = (Math.sin(angle * 0.5) + directionDelta) * 0.25;
    const magnitude = Math.min(1, Math.max(0.05, Math.abs(directionDelta) * 3 + 0.12));
    const origin: [number, number, number] = [
      Math.cos(angle) * radius,
      Math.sin(angle) * radius * 0.7,
      (i - count / 2) * 0.05,
    ];
    const direction: [number, number, number] = [dx || 0.02, dy || 0.01, dz || 0.01];
    vectors.push({
      origin,
      direction,
      magnitude,
    });
  }
  return vectors;
}

export function computeDensity(sessions: SessionEntry[]): ContextDensity[] {
  const groups = groupByOntology([...sessions].reverse());
  const ontologies = Object.keys(groups);
  const total = Math.max(1, ontologies.length);

  const densities: ContextDensity[] = ontologies.map((ontology, index) => {
    const entries = groups[ontology];
    const scores = entries.map((e) => extractConsensusScore(e.result));
    const avgScore = mean(scores);
    const variance = stdDev(scores);
    const density = Math.min(1, (entries.length / 10) * (avgScore / 100));
    const consistency = Math.max(0, 1 - variance / 50);
    const seed = hashText(`${ontology}:${entries.length}:${scores.join(',')}`);
    const theta = (index / total) * Math.PI * 2 + ((seed % 37) * 0.01);
    const ringRadius = 3.3 + (seed % 9) * 0.12;

    const position: [number, number, number] = [
      Math.cos(theta) * ringRadius,
      -2 + (((seed >> 3) % 11) - 5) * 0.06,
      Math.sin(theta) * ringRadius * 0.55,
    ];

    return {
      id: `density-${normalizeOntology(ontology)}`,
      label: ontology,
      ontology,
      density,
      consistency,
      vectorField: buildVectors(scores, seed),
      color: ontologyColor(ontology),
      position,
      sampleCount: entries.length,
    };
  });

  return densities.sort((a, b) => b.density - a.density);
}

export function useDensityAnalysis() {
  const sessions = useAtlasStore((s) => s.sessionHistory);
  const setContextDensities = useAtlasStore((s) => s.setContextDensities);

  const densities = useMemo(() => computeDensity(sessions), [sessions]);

  useEffect(() => {
    setContextDensities(densities);
  }, [densities, setContextDensities]);

  return densities;
}
