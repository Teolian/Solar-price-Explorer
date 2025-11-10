import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
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
              <h1 className="text-2xl font-bold">Solar×Price Explorer</h1>
              <p className="text-sm text-muted-foreground">
                JEPX Price Analysis with JMA Solar Radiation
              </p>
            </div>
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
