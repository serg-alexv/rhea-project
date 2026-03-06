import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docs: [
    'intro',
    'getting-started',
    'design-system',
    {
      type: 'category',
      label: 'Components',
      link: {
        type: 'generated-index',
        description: 'SwiftUI views for monitoring and interacting with the Rhea multi-agent system.',
        slug: '/category/components',
      },
      items: [
        'components/bio-renderer',
        'components/node-editor',
        'components/team-chat',
        'components/clipboard',
        'components/dialog',
        'components/governor',
        'components/tasks',
        'components/aletheia',
        'components/processes',
        'components/pulse-monitor',
      ],
    },
    'architecture',
    'api-reference',
  ],
};

export default sidebars;
