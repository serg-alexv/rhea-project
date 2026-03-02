import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import HyperionBar from '@/components/HyperionBar' // Assuming this path is correct
import MnemosyneWhisper from '@/components/MnemosyneWhisper' // Import MnemosyneWhisper

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Rhea Atlas',
  description: 'Data context visualization platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className} style={{ margin: 0, padding: 0, overflow: 'hidden' }}>
        <HyperionBar />
        <MnemosyneWhisper /> {/* Add MnemosyneWhisper here */}
        {children}
      </body>
    </html>
  )
}
