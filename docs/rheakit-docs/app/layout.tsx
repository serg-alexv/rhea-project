import type { Metadata } from 'next';
import { IBM_Plex_Mono, Space_Grotesk } from 'next/font/google';
import type { ReactNode } from 'react';
import { Provider } from '@/components/provider';
import './global.css';

const display = Space_Grotesk({
  subsets: ['latin'],
  variable: '--font-display',
});

const mono = IBM_Plex_Mono({
  subsets: ['latin'],
  variable: '--font-ibm-mono',
  weight: ['400', '500', '600'],
});

export const metadata: Metadata = {
  metadataBase: new URL('https://rhea-tribunal.fly.dev'),
  title: {
    default: 'RheaKit Docs',
    template: '%s | RheaKit Docs',
  },
  description:
    'RheaKit is a SwiftUI library for scientific control surfaces, multi-agent observability, and proof-driven interfaces.',
  openGraph: {
    title: 'RheaKit Docs',
    description:
      'SwiftUI control surfaces for scientific tooling, multi-agent ops, and proof-first product interfaces.',
    url: 'https://rhea-tribunal.fly.dev/docs/',
    siteName: 'RheaKit Docs',
    type: 'website',
    images: ['/docs/og/image.png'],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'RheaKit Docs',
    description:
      'SwiftUI control surfaces for scientific tooling, multi-agent ops, and proof-first product interfaces.',
    images: ['/docs/og/image.png'],
  },
};

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <html
      lang="en"
      className={`${display.variable} ${mono.variable}`}
      suppressHydrationWarning
    >
      <body className="min-h-screen antialiased">
        <Provider>{children}</Provider>
      </body>
    </html>
  );
}
