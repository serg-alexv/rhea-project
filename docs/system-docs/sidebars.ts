import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docsSidebar: [
    'intro',
    'getting-started',
    {
      type: 'category',
      label: 'Architecture',
      items: [
        'architecture/services',
        'architecture/event-bus',
        'architecture/distributed-time',
      ],
    },
    {
      type: 'category',
      label: 'API Reference',
      items: [
        'api/tribunal',
        'api/orchestration',
        'api/clipboard',
        'api/sessions',
      ],
    },
    {
      type: 'category',
      label: 'Components',
      items: [
        'components/frontier-gem',
        'components/rhea-bridge',
        'components/session-server',
        'components/rhea-dash',
      ],
    },
    {
      type: 'category',
      label: 'Deployment',
      items: [
        'deployment/fly-deploy',
        'deployment/docker',
        'deployment/testflight',
      ],
    },
    {
      type: 'category',
      label: 'Concepts',
      items: [
        'concepts/tribunal',
        'concepts/characters',
        'concepts/playui',
      ],
    },
  ],
};

export default sidebars;
