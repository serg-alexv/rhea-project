import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Rhea System',
  tagline: 'Multi-model advisory system with distributed time',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
  },

  url: 'https://rhea-system.timelabs.dev',
  baseUrl: '/',

  organizationName: 'timelabs-npo',
  projectName: 'rhea',

  onBrokenLinks: 'throw',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          routeBasePath: 'docs',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/docusaurus-social-card.jpg',
    colorMode: {
      defaultMode: 'dark',
      respectPrefersColorScheme: false,
    },
    navbar: {
      title: 'Rhea System',
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docsSidebar',
          position: 'left',
          label: 'Docs',
        },
        {
          to: '/docs/api/tribunal',
          label: 'API Reference',
          position: 'left',
        },
        {
          href: 'https://github.com/nicksona/rh.1',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Documentation',
          items: [
            { label: 'Getting Started', to: '/docs/getting-started' },
            { label: 'Architecture', to: '/docs/architecture/services' },
            { label: 'API Reference', to: '/docs/api/tribunal' },
          ],
        },
        {
          title: 'Components',
          items: [
            { label: 'Rhea Bridge', to: '/docs/components/rhea-bridge' },
            { label: 'Frontier Gem', to: '/docs/components/frontier-gem' },
            { label: 'Session Server', to: '/docs/components/session-server' },
          ],
        },
        {
          title: 'Deployment',
          items: [
            { label: 'Fly.io', to: '/docs/deployment/fly-deploy' },
            { label: 'Docker', to: '/docs/deployment/docker' },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} TimeLabs NPO. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['bash', 'rust', 'python', 'toml'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
