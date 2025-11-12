import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { I18nProvider } from '@/lib/i18n'
import Navigation from '@/components/Navigation'

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
        <I18nProvider>
          <div className="min-h-screen bg-background">
            <header className="border-b">
              <Navigation />
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
        </I18nProvider>
      </body>
    </html>
  )
}
