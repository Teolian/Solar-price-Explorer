'use client'

import Link from 'next/link'
import { useI18n } from '@/lib/i18n'

export default function Navigation() {
  const { language, setLanguage, t } = useI18n()

  return (
    <>
      <div className="container mx-auto px-4 py-4 flex items-center justify-between">
        <div>
          <Link href="/">
            <h1 className="text-2xl font-bold cursor-pointer hover:text-primary">
              Solar×Price Explorer
            </h1>
          </Link>
          <p className="text-sm text-muted-foreground">
            JEPX Price Analysis with JMA Solar Radiation
          </p>
        </div>

        {/* Language Switcher */}
        <div className="flex items-center space-x-2">
          <span className="text-sm text-muted-foreground">Language:</span>
          <button
            onClick={() => setLanguage('en')}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              language === 'en'
                ? 'bg-primary text-primary-foreground'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            EN
          </button>
          <button
            onClick={() => setLanguage('ja')}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              language === 'ja'
                ? 'bg-primary text-primary-foreground'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            日本語
          </button>
        </div>
      </div>

      <nav className="container mx-auto px-4 py-2">
        <ul className="flex space-x-6 text-sm">
          <li>
            <Link
              href="/"
              className="hover:text-primary transition-colors"
            >
              {t('nav.overview')}
            </Link>
          </li>
          <li>
            <Link
              href="/business"
              className="hover:text-primary transition-colors font-semibold"
            >
              {t('nav.business')}
            </Link>
          </li>
          <li>
            <Link
              href="/insights"
              className="hover:text-primary transition-colors"
            >
              {t('nav.insights')}
            </Link>
          </li>
          <li>
            <Link
              href="/compare"
              className="hover:text-primary transition-colors"
            >
              {t('nav.compare')}
            </Link>
          </li>
          <li>
            <Link
              href="/correlations"
              className="hover:text-primary transition-colors"
            >
              {t('nav.correlations')}
            </Link>
          </li>
          <li>
            <Link
              href="/forecast"
              className="hover:text-primary transition-colors"
            >
              {t('nav.forecast')}
            </Link>
          </li>
          <li>
            <Link
              href="/data"
              className="hover:text-primary transition-colors"
            >
              {t('nav.data')}
            </Link>
          </li>
        </ul>
      </nav>
    </>
  )
}
