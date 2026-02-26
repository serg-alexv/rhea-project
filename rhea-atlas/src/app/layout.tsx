import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import HyperionBar from '@/components/HyperionBar'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Rhea Atlas — Knowledge Topology',
  description: 'Multi-model research consensus explorer',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <HyperionBar />
        {children}
      </body>
    </html>
  )
}
