import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'RheaKit',
  tagline: 'AI-driven UI component library for SwiftUI',
  favicon: 'img/favicon.ico',

  url: 'https://rheakit.dev',
  baseUrl: '/',

  organizationName: 'timelabs-npo',
  projectName: 'rheakit',

  onBrokenLinks: 'throw',
  markdown: {
    hooks: {
      onBrokenMarkdownLinks: 'warn',
    },
  },

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
    colorMode: {
      defaultMode: 'dark',
      disableSwitch: false,
      respectPrefersColorScheme: false,
    },
    navbar: {
      title: 'RheaKit',
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docs',
          position: 'left',
          label: 'Docs',
        },
        {
          to: '/docs/category/components',
          label: 'Components',
          position: 'left',
        },
        {
          to: '/docs/api-reference',
          label: 'API',
          position: 'left',
        },
        {
          href: 'https://github.com/timelabs-npo/rheakit',
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
            {label: 'Getting Started', to: '/docs/getting-started'},
            {label: 'Components', to: '/docs/category/components'},
            {label: 'Design System', to: '/docs/design-system'},
          ],
        },
        {
          title: 'Architecture',
          items: [
            {label: 'Overview', to: '/docs/architecture'},
            {label: 'API Reference', to: '/docs/api-reference'},
          ],
        },
        {
          title: 'More',
          items: [
            {label: 'GitHub', href: 'https://github.com/timelabs-npo/rheakit'},
          ],
        },
      ],
      copyright: `© ${new Date().getFullYear()} TimeLabs NPO. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['swift'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
