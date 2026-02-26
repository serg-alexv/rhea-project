'use client';

import { useEffect } from 'react';
import { useAtlasStore } from '@/store/useAtlasStore';

export function useAtlasSync() {
  const { setDMetric, updateIsland } = useAtlasStore();

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const res = await fetch('http://localhost:8000/health');
        const data = await res.json();
        
        // Sync global metrics
        setDMetric(data.d_metric);
        
        // Sync island status (Mocking drift based on audit count)
        const drift = data.audit_records * 0.05;
        updateIsland('1', { complexity: 1.2 + drift });
        updateIsland('2', { complexity: 0.8 + drift });
        
      } catch (err) {
        console.error("Atlas sync failure:", err);
      }
    };

    const interval = setInterval(fetchHealth, 5000);
    return () => clearInterval(interval);
  }, [setDMetric, updateIsland]);
}
