import React from 'react';
import ComponentCreator from '@docusaurus/ComponentCreator';

export default [
  {
    path: '/docs',
    component: ComponentCreator('/docs', '5b4'),
    routes: [
      {
        path: '/docs',
        component: ComponentCreator('/docs', '7f4'),
        routes: [
          {
            path: '/docs',
            component: ComponentCreator('/docs', 'c6c'),
            routes: [
              {
                path: '/docs/',
                component: ComponentCreator('/docs/', 'be8'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/docs/api-reference',
                component: ComponentCreator('/docs/api-reference', '0a0'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/docs/architecture',
                component: ComponentCreator('/docs/architecture', '38d'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/docs/category/components',
                component: ComponentCreator('/docs/category/components', 'd2a'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/docs/components/aletheia',
                component: ComponentCreator('/docs/components/aletheia', '1c0'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/docs/components/bio-renderer',
                component: ComponentCreator('/docs/components/bio-renderer', 'fc2'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/docs/components/clipboard',
                component: ComponentCreator('/docs/components/clipboard', 'bd5'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/docs/components/dialog',
                component: ComponentCreator('/docs/components/dialog', 'f2b'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/docs/components/governor',
                component: ComponentCreator('/docs/components/governor', '70b'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/docs/components/node-editor',
                component: ComponentCreator('/docs/components/node-editor', '76a'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/docs/components/processes',
                component: ComponentCreator('/docs/components/processes', '66a'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/docs/components/pulse-monitor',
                component: ComponentCreator('/docs/components/pulse-monitor', 'c5a'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/docs/components/tasks',
                component: ComponentCreator('/docs/components/tasks', 'f76'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/docs/components/team-chat',
                component: ComponentCreator('/docs/components/team-chat', '086'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/docs/design-system',
                component: ComponentCreator('/docs/design-system', '716'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/docs/getting-started',
                component: ComponentCreator('/docs/getting-started', '565'),
                exact: true,
                sidebar: "docs"
              }
            ]
          }
        ]
      }
    ]
  },
  {
    path: '/',
    component: ComponentCreator('/', 'e5f'),
    exact: true
  },
  {
    path: '*',
    component: ComponentCreator('*'),
  },
];
