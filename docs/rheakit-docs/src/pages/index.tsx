import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero hero--dark')}>
      <div className="container" style={{padding: '4rem 0'}}>
        <Heading as="h1" className="hero__title">
          {siteConfig.title}
        </Heading>
        <p className="hero__subtitle">{siteConfig.tagline}</p>
        <div style={{display: 'flex', gap: '1rem', marginTop: '2rem'}}>
          <Link
            className="button button--primary button--lg"
            to="/docs/getting-started">
            Get Started
          </Link>
          <Link
            className="button button--secondary button--lg"
            to="/docs/category/components">
            Components
          </Link>
        </div>
      </div>
    </header>
  );
}

const features = [
  {
    title: 'Multi-Agent Observatory',
    description:
      'Monitor, message, and manage AI agents in real time. TeamChat provides a live radio feed with WebSocket streaming, agent filtering, and turn-based experiment mode.',
  },
  {
    title: 'Built-in Verification',
    description:
      'Aletheia proof store, multi-model tribunal consensus, and ontology-driven hypothesis verification — all as native SwiftUI views.',
  },
  {
    title: 'Unified Design System',
    description:
      'Dark-first glass-card aesthetic with RheaTheme. Consistent colors, mode-aware palettes, and the .glassCard() modifier for instant frosted-glass panels.',
  },
];

function Feature({title, description}: {title: string; description: string}) {
  return (
    <div className={clsx('col col--4')} style={{marginBottom: '2rem'}}>
      <div style={{padding: '1.5rem'}}>
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function Home(): JSX.Element {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout title={siteConfig.title} description={siteConfig.tagline}>
      <HomepageHeader />
      <main>
        <section style={{padding: '3rem 0'}}>
          <div className="container">
            <div className="row">
              {features.map((props, idx) => (
                <Feature key={idx} {...props} />
              ))}
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}
