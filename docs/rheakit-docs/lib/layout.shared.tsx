import type { BaseLayoutProps } from 'fumadocs-ui/layouts/shared';

export const gitConfig = {
  user: 'timelabs-npo',
  repo: 'rhea-project',
  branch: 'stage4-release',
};

export function baseOptions(): BaseLayoutProps {
  return {
    nav: {
      title: (
        <div className="flex items-center gap-3">
          <div className="h-2.5 w-2.5 rounded-full bg-[var(--color-rhea-cyan)] shadow-[0_0_18px_rgba(140,246,228,0.7)]" />
          <div className="flex flex-col leading-none">
            <span className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-[var(--color-rhea-cyan)]">
              RheaKit
            </span>
            <span className="text-sm font-medium text-white/90">
              Scientific UI surfaces for SwiftUI
            </span>
          </div>
        </div>
      ),
    },
    githubUrl: `https://github.com/${gitConfig.user}/${gitConfig.repo}`,
  };
}
