import { Analytics } from '@vercel/analytics/next'
import type { Metadata, Viewport } from 'next'
import { Cinzel, EB_Garamond } from 'next/font/google'
import './globals.css'

const cinzel = Cinzel({ subsets: ['latin'], variable: '--font-cinzel' })
const garamond = EB_Garamond({ subsets: ['latin'], variable: '--font-garamond' })

export const metadata: Metadata = {
  title: 'Grimório do Aventureiro | Classes, Raças e Magias de D&D',
  description:
    'Compêndio de Dungeons & Dragons com classes, raças e magias para jogadores e mestres.',
}

export const viewport: Viewport = {
  colorScheme: 'dark',
  themeColor: '#1c1512',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="pt-BR" className={`${cinzel.variable} ${garamond.variable} dark`}>
      <body className="antialiased">
        {children}
        {process.env.NODE_ENV === 'production' && <Analytics />}
      </body>
    </html>
  )
}
