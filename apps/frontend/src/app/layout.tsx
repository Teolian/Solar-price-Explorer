import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import Link from 'next/link'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Solar×Price Explorer',
  description: 'JEPX price analysis with JMA solar radiation data',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen bg-background">
          <header className="border-b">
            <div className="container mx-auto px-4 py-4">
              <Link href="/">
                <h1 className="text-2xl font-bold cursor-pointer hover:text-primary">
                  Solar×Price Explorer
                </h1>
              </Link>
              <p className="text-sm text-muted-foreground">
                JEPX Price Analysis with JMA Solar Radiation
              </p>
            </div>
            <nav className="container mx-auto px-4 py-2">
              <ul className="flex space-x-6 text-sm">
                <li>
                  <Link
                    href="/"
                    className="hover:text-primary transition-colors"
                  >
                    Overview
                  </Link>
                </li>
                <li>
                  <Link
                    href="/correlations"
                    className="hover:text-primary transition-colors"
                  >
                    Correlations
                  </Link>
                </li>
                <li>
                  <Link
                    href="/forecast"
                    className="hover:text-primary transition-colors"
                  >
                    Forecast
                  </Link>
                </li>
                <li>
                  <Link
                    href="/data"
                    className="hover:text-primary transition-colors"
                  >
                    Data Explorer
                  </Link>
                </li>
              </ul>
            </nav>
          </header>
          <main className="container mx-auto px-4 py-6">
            {children}
          </main>
          <footer className="border-t mt-12">
            <div className="container mx-auto px-4 py-4 text-center text-sm text-muted-foreground">
              JST Timezone | Data: JEPX, JMA
            </div>
          </footer>
        </div>
      </body>
    </html>
  )
}
