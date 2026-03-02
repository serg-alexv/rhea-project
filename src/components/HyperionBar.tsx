'use client';

import React from 'react';
import useAtlasStore from '@/store/useAtlasStore'; // Assuming path is correct

// Placeholder for CrossNav component - actual implementation would be extracted
// This placeholder will contain the elements that were originally in CrossNav.
// For now, it will just render its children and some simulated content.
const CrossNavPlaceholder = ({ children }: { children: React.ReactNode }) => {
  return <div className="flex items-center">{children}</div>;
};

// Placeholder for CodeWormProfile component - actual implementation would be extracted
// This placeholder represents the profile section (e.g., user avatar, settings icon)
// based on the spec: "provider count, redis status, Phoebe (D-Metric value), CodeWormProfile"
const CodeWormProfilePlaceholder = () => {
  return (
    <div className="flex items-center space-x-4">
      <span className="text-white/50 text-xs">Provider: 123</span>
      <span className="text-white/50 text-xs">Redis: OK</span>
      <span className="text-white/50 text-xs">Phoebe: 98.7%</span>
      {/* Actual profile icon/avatar would go here */}
      <div className="w-8 h-8 bg-gray-600 rounded-full cursor-pointer" title="User Profile"></div>
    </div>
  );
};

const HyperionBar: React.FC = () => {
  const activeView = useAtlasStore((state) => state.activeView);
  const setActiveView = useAtlasStore((state) => state.setActiveView);

  // Ensure the ViewId type matches the one defined in useAtlasStore
  type ViewId = 'atlas-prime' | 'atlas-mesh' | 'theia-drift' | 'system-pw';

  const views: { id: ViewId; label: string }[] = [
    { id: 'atlas-prime', label: 'ATLAS PRIME' },
    { id: 'atlas-mesh', label: 'ATLAS MESH' },
    { id: 'theia-drift', label: 'THEIA DRIFT' },
    { id: 'system-pw', label: 'SYSTEM PW' },
  ];

  const renderTab = (viewId: ViewId, label: string) => {
    const isActive = activeView === viewId;
    const baseStyles = 'px-3 py-1 rounded-md font-medium transition-colors duration-200 ease-in-out relative text-sm';
    const activeStyles = 'text-cyan-400';
    const inactiveStyles = 'text-white/38 hover:text-white/72 hover:bg-white/5';

    return (
      <button
        key={viewId}
        onClick={() => setActiveView(viewId)}
        className={`${baseStyles} ${isActive ? activeStyles : inactiveStyles}`}
      >
        {label}
        {isActive && (
          <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-full h-0.5 bg-cyan-400 rounded-full"></span>
        )}
      </button>
    );
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-[100] h-[30px] bg-black flex items-center justify-between px-4 border-b border-white/10">
      {/* Left Zone: Logo + Separator */}
      <CrossNavPlaceholder>
        <span className="text-white font-bold mr-2 text-sm">RHEA</span>
        <span className="text-white/50 text-xs bg-cyan-500/20 px-1 rounded">DEV</span>
        <span className="w-px h-4 bg-white/20 mx-3"></span>
      </CrossNavPlaceholder>

      {/* Center Zone: View Tabs */}
      <div className="flex items-center space-x-2 flex-grow justify-center">
        {views.map((view) => renderTab(view.id, view.label))}
      </div>

      {/* Right Zone: Meta Info + Profile */}
      <CodeWormProfilePlaceholder />
    </nav>
  );
};

export default HyperionBar;
