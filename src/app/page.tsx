'use client';

import React, { useEffect } from 'react';
import useAtlasStore from '@/store/useAtlasStore';
import useWhisperStore from '@/store/useWhisperStore'; // Import useWhisperStore

// Placeholder components for different views
// In a real application, these would be imported from their respective files.
const AtlasPrimeView: React.FC = () => (
  <div className="view-container">
    <h1>Atlas Prime View</h1>
    {/* Content for Atlas Prime */}
  </div>
);
const AtlasMeshView: React.FC = () => (
  <div className="view-container">
    <h1>Atlas Mesh View</h1>
    {/* Content for Atlas Mesh */}
  </div>
);
const TheiaDriftView: React.FC = () => (
  <div className="view-container">
    <h1>Theia Drift View</h1>
    {/* Content for Theia Drift */}
  </div>
);
const SystemPWView: React.FC = () => (
  <div className="view-container">
    <h1>System PW View</h1>
    {/* Content for System PW */}
  </div>
);

// Define ViewId type to match useAtlasStore
type ViewId = 'atlas-prime' | 'atlas-mesh' | 'theia-drift' | 'system-pw';

const Page: React.FC = () => {
  const activeView = useAtlasStore((state) => state.activeView);
  // We need recordAction from useWhisperStore
  const recordAction = useWhisperStore((state) => state.recordAction);
  // We don't need to directly call updateMood here as recordAction handles it internally.

  useEffect(() => {
    // Record 'session_start' action on initial component mount
    recordAction('session_start');

    // This effect will re-run if activeView changes, triggering 'view_change' action
    // We only need to explicitly record 'view_change' when activeView changes.
    // The initial 'session_start' covers the first load.
    // Mood updates will be handled internally by recordAction.
    // So, we just need to ensure the effect runs when activeView changes.

    // The dependency array ensures this effect runs on mount and when activeView changes.
    // recordAction is stable as it's a hook getter.
  }, [activeView, recordAction]);

  // Define the mapping of ViewId to its corresponding component
  const renderView = (viewId: ViewId) => {
    switch (viewId) {
      case 'atlas-prime':
        return <AtlasPrimeView />;
      case 'atlas-mesh':
        return <AtlasMeshView />;
      case 'theia-drift':
        return <TheiaDriftView />;
      case 'system-pw':
        return <SystemPWView />;
      default:
        return null; // Should not happen with correct type guarding
    }
  };

  return (
    <div className="w-screen h-screen bg-black" style={{ paddingTop: '30px' }}>
      {renderView(activeView)}
    </div>
  );
};

export default Page;
