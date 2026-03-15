export function DocsHero() {
  return (
    <div className="hero-grid rounded-[2rem] px-6 py-8 md:px-10 md:py-12">
      <div className="relative z-10 grid gap-8 lg:grid-cols-[1.35fr_0.9fr]">
        <div className="space-y-6">
          <div className="signal-badge rounded-full">
            <span className="h-2 w-2 rounded-full bg-[var(--color-rhea-green)]" />
            Research-grade SwiftUI surfaces
          </div>
          <div className="space-y-4">
            <h2 className="max-w-4xl text-4xl font-semibold tracking-[-0.05em] text-white md:text-6xl">
              Build the operator cockpit, not just another dashboard.
            </h2>
            <p className="max-w-2xl text-base leading-7 text-white/78 md:text-lg">
              RheaKit packages the control planes behind Rhea: live agent radios, proof
              stores, task orchestration, node-based workflows, molecular views, and
              budget governors, all as production SwiftUI surfaces.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <a
              className="rounded-full border border-[rgba(140,246,228,0.24)] bg-[rgba(140,246,228,0.12)] px-5 py-3 text-sm font-medium text-white transition hover:bg-[rgba(140,246,228,0.18)]"
              href="./getting-started"
            >
              Start with the package
            </a>
            <a
              className="rounded-full border border-white/12 px-5 py-3 text-sm font-medium text-white/86 transition hover:border-white/22 hover:bg-white/4"
              href="./components"
            >
              Browse the component atlas
            </a>
            <a
              className="rounded-full border border-white/12 px-5 py-3 text-sm font-medium text-white/86 transition hover:border-white/22 hover:bg-white/4"
              href="https://github.com/timelabs-npo/rhea-project/tree/stage4-release/packages/RheaKit"
            >
              Open package source
            </a>
          </div>
        </div>
        <div className="relative z-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-1">
          <div className="metric-plate rounded-3xl p-5">
            <p className="text-xs uppercase tracking-[0.24em] text-[var(--color-rhea-cyan)]">
              Package surface
            </p>
            <p className="metric-value mt-3 text-4xl font-semibold text-white">39</p>
            <p className="mt-2 text-sm text-white/68">
              Swift source files currently ship in the RheaKit target, spanning ops,
              visualization, auth, transport, and privacy surfaces.
            </p>
          </div>
          <div className="metric-plate rounded-3xl p-5">
            <p className="text-xs uppercase tracking-[0.24em] text-[var(--color-rhea-cyan)]">
              Runtime targets
            </p>
            <p className="metric-value mt-3 text-4xl font-semibold text-white">
              iOS 17+ <span className="text-white/40">/</span> macOS 14+
            </p>
            <p className="mt-2 text-sm text-white/68">
              One Swift package, one shared state spine, one backend contract for
              simulator and device.
            </p>
          </div>
          <div className="metric-plate rounded-3xl p-5 sm:col-span-2 lg:col-span-1">
            <p className="text-xs uppercase tracking-[0.24em] text-[var(--color-rhea-cyan)]">
              Product posture
            </p>
            <p className="mt-3 text-xl font-medium tracking-[-0.04em] text-white">
              Pleasant entry. Brutal verification.
            </p>
            <p className="mt-2 text-sm text-white/68">
              The interface stays calm, but every surface is designed to expose source
              truth, staleness, disagreement, and operational drift.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export function LaunchRail() {
  return (
    <div className="docs-card-grid">
      <div className="component-pulse rounded-3xl p-5">
        <p className="text-xs uppercase tracking-[0.2em] text-[var(--color-rhea-cyan)]">
          Install
        </p>
        <h3 className="mt-3 text-xl font-medium text-white">Drop the package into an app</h3>
        <p className="mt-2 text-sm text-white/70">
          Configure the API endpoint, spin up the shared store, and mount the first
          control surface.
        </p>
        <a className="mt-4 inline-flex text-sm font-medium text-[var(--color-rhea-cyan)]" href="./getting-started">
          Open getting started
        </a>
      </div>
      <div className="component-pulse rounded-3xl p-5">
        <p className="text-xs uppercase tracking-[0.2em] text-[var(--color-rhea-cyan)]">
          Compose
        </p>
        <h3 className="mt-3 text-xl font-medium text-white">Use the opinionated visual language</h3>
        <p className="mt-2 text-sm text-white/70">
          RheaTheme, GlassCard, semantic status colors, and monospaced data layouts keep
          every pane coherent.
        </p>
        <a className="mt-4 inline-flex text-sm font-medium text-[var(--color-rhea-cyan)]" href="./design-system">
          Review the design system
        </a>
      </div>
      <div className="component-pulse rounded-3xl p-5">
        <p className="text-xs uppercase tracking-[0.2em] text-[var(--color-rhea-cyan)]">
          Scale
        </p>
        <h3 className="mt-3 text-xl font-medium text-white">Navigate the component atlas</h3>
        <p className="mt-2 text-sm text-white/70">
          The package spans live radio feeds, proof browsers, supervisor panels, node
          editors, and molecular viewers.
        </p>
        <a className="mt-4 inline-flex text-sm font-medium text-[var(--color-rhea-cyan)]" href="./components">
          Explore components
        </a>
      </div>
    </div>
  );
}

export function CoverageNote() {
  return (
    <div className="callout-shell rounded-3xl px-5 py-5">
      <p className="m-0 text-sm leading-7 text-white/76">
        These docs cover the primary operational panes and the package spine first. The
        package already ships additional surfaces such as <code>OfficeView</code>,{' '}
        <code>OpsView</code>, <code>ModelsView</code>, <code>WalletView</code>,{' '}
        <code>SettingsView</code>, <code>AtlasWebView</code>, <code>NDIFlowView</code>,{' '}
        <code>RelayPrivacyView</code>, <code>RuliadView</code>, and <code>ToolsHubView</code>.
        Those are next in line for deeper narrative pages.
      </p>
    </div>
  );
}
