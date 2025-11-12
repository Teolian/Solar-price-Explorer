'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

type Language = 'en' | 'ja'

interface I18nContextType {
  language: Language
  setLanguage: (lang: Language) => void
  t: (key: string) => string
}

const I18nContext = createContext<I18nContextType | undefined>(undefined)

export const translations = {
  en: {
    // Navigation
    'nav.overview': 'Overview',
    'nav.business': 'Business Value',
    'nav.insights': 'Hourly Patterns',
    'nav.compare': 'Compare Areas',
    'nav.correlations': 'Correlations',
    'nav.forecast': 'Forecast',
    'nav.data': 'Data Explorer',

    // Common
    'common.area': 'Area',
    'common.loading': 'Loading...',
    'common.error': 'Error',
    'common.save': 'Save',
    'common.cancel': 'Cancel',
    'common.close': 'Close',

    // Business Value Page
    'business.title': 'Business Value Analysis',
    'business.subtitle': 'Calculate potential savings and optimize your energy consumption strategy',
    'business.peak_price': 'Peak Hours Price',
    'business.solar_price': 'Solar Hours Price',
    'business.price_diff': 'Price Difference',
    'business.savings_pct': 'Savings Potential',
    'business.peak_hours_desc': 'per kWh (7-9, 18-20)',
    'business.solar_hours_desc': 'per kWh (10-14)',
    'business.savings_per_kwh': 'savings per kWh',
    'business.by_shifting': 'by shifting to solar hours',

    'business.calculator_title': 'Savings Calculator',
    'business.daily_consumption': 'Daily Energy Consumption (kWh):',
    'business.monthly_savings': 'Monthly Savings',
    'business.annual_savings': 'Annual Savings',
    'business.by_shifting_30': 'By shifting 30% of consumption to solar hours',
    'business.estimated_yearly': 'Estimated yearly savings potential',
    'business.recommendation': 'Recommendation:',
    'business.recommendation_text': 'Schedule energy-intensive operations during solar hours (10:00-14:00) to maximize savings. Consider installing battery storage to capture cheap solar energy for use during peak hours.',

    'business.examples_title': 'Example Scenarios',
    'business.small_business': 'Small Business',
    'business.medium_factory': 'Medium Factory',
    'business.large_factory': 'Large Factory',
    'business.daily_usage': 'Daily Usage:',
    'business.monthly_savings_label': 'Monthly Savings:',
    'business.annual_savings_label': 'Annual Savings:',

    'business.best_time_title': 'Best Time to Buy/Consume Electricity',
    'business.best_times': 'Best Times (Low Prices)',
    'business.worst_times': 'Avoid Times (High Prices)',
    'business.avg_price': 'Average price:',
    'business.savings_up_to': 'Savings up to',
    'business.vs_peak': 'vs peak hours',
    'business.premium': 'Premium',
    'business.vs_solar': 'vs solar hours',

    'business.recommended_actions': 'Recommended Actions:',
    'business.action_manufacturing': 'Run manufacturing processes',
    'business.action_battery': 'Charge battery storage systems',
    'business.action_machinery': 'Operate heavy machinery',
    'business.action_hvac': 'Run HVAC systems (pre-cooling/heating)',
    'business.action_minimize': 'Minimize energy-intensive operations',
    'business.action_use_battery': 'Use battery storage if available',
    'business.action_delay': 'Delay non-critical processes',
    'business.action_reduce_hvac': 'Reduce HVAC load',

    'business.hourly_chart_title': 'Hourly Price Optimization Guide',
    'business.strategic_plan_title': 'Strategic Action Plan',

    'business.strategy_1_title': 'Shift Consumption to Solar Hours',
    'business.strategy_1_desc': 'Move {pct}% of energy consumption to 10:00-14:00 → Save approximately ¥{amount}/month',
    'business.strategy_2_title': 'Install Battery Storage',
    'business.strategy_2_desc': 'Capture energy during cheap hours (¥{price}/kWh) and use during peak hours. Arbitrage ¥{diff}/kWh difference.',
    'business.strategy_3_title': 'Monitor JEPX Prices Daily',
    'business.strategy_3_desc': 'Use this tool to track real-time price patterns and adjust operations accordingly. Set up alerts for exceptional price opportunities.',
  },
  ja: {
    // ナビゲーション
    'nav.overview': '概要',
    'nav.business': 'ビジネス価値',
    'nav.insights': '時間帯別パターン',
    'nav.compare': '地域比較',
    'nav.correlations': '相関分析',
    'nav.forecast': '予測',
    'nav.data': 'データエクスプローラー',

    // 共通
    'common.area': 'エリア',
    'common.loading': '読み込み中...',
    'common.error': 'エラー',
    'common.save': '保存',
    'common.cancel': 'キャンセル',
    'common.close': '閉じる',

    // ビジネス価値ページ
    'business.title': 'ビジネス価値分析',
    'business.subtitle': '潜在的なコスト削減を計算し、エネルギー消費戦略を最適化します',
    'business.peak_price': 'ピーク時間帯価格',
    'business.solar_price': '太陽光時間帯価格',
    'business.price_diff': '価格差',
    'business.savings_pct': '削減可能率',
    'business.peak_hours_desc': '円/kWh (7-9時、18-20時)',
    'business.solar_hours_desc': '円/kWh (10-14時)',
    'business.savings_per_kwh': '1kWhあたりの削減額',
    'business.by_shifting': '太陽光時間帯へのシフトで',

    'business.calculator_title': 'コスト削減計算機',
    'business.daily_consumption': '1日のエネルギー消費量 (kWh):',
    'business.monthly_savings': '月間削減額',
    'business.annual_savings': '年間削減額',
    'business.by_shifting_30': '消費量の30%を太陽光時間帯にシフトした場合',
    'business.estimated_yearly': '推定年間削減可能額',
    'business.recommendation': '推奨事項:',
    'business.recommendation_text': 'エネルギー集約型の作業を太陽光時間帯（10:00-14:00）にスケジュールして削減効果を最大化してください。安価な太陽光エネルギーを蓄積してピーク時間帯に使用するため、蓄電池の設置を検討してください。',

    'business.examples_title': '使用例シナリオ',
    'business.small_business': '小規模事業所',
    'business.medium_factory': '中規模工場',
    'business.large_factory': '大規模工場',
    'business.daily_usage': '1日の使用量:',
    'business.monthly_savings_label': '月間削減額:',
    'business.annual_savings_label': '年間削減額:',

    'business.best_time_title': '電力購入・消費の最適時間帯',
    'business.best_times': '最適時間帯（低価格）',
    'business.worst_times': '回避すべき時間帯（高価格）',
    'business.avg_price': '平均価格:',
    'business.savings_up_to': '最大',
    'business.vs_peak': '削減（対ピーク時）',
    'business.premium': 'プレミアム',
    'business.vs_solar': '（対太陽光時）',

    'business.recommended_actions': '推奨アクション:',
    'business.action_manufacturing': '製造プロセスの稼働',
    'business.action_battery': '蓄電システムの充電',
    'business.action_machinery': '重機械の稼働',
    'business.action_hvac': '空調システムの予冷・予熱',
    'business.action_minimize': 'エネルギー集約型作業の最小化',
    'business.action_use_battery': '蓄電池の活用（可能な場合）',
    'business.action_delay': '非緊急作業の延期',
    'business.action_reduce_hvac': '空調負荷の削減',

    'business.hourly_chart_title': '時間別価格最適化ガイド',
    'business.strategic_plan_title': '戦略的アクションプラン',

    'business.strategy_1_title': '消費量を太陽光時間帯にシフト',
    'business.strategy_1_desc': 'エネルギー消費の{pct}%を10:00-14:00にシフト → 月間約¥{amount}の削減',
    'business.strategy_2_title': '蓄電システムの導入',
    'business.strategy_2_desc': '安価な時間帯（¥{price}/kWh）にエネルギーを蓄積し、ピーク時に使用。¥{diff}/kWhの差額で利益を得る。',
    'business.strategy_3_title': 'JEPX価格の日次モニタリング',
    'business.strategy_3_desc': 'このツールを使用してリアルタイムの価格パターンを追跡し、それに応じて操業を調整してください。特別な価格機会のアラートを設定してください。',
  }
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>('en')

  useEffect(() => {
    // Load saved language from localStorage
    const savedLang = localStorage.getItem('language') as Language
    if (savedLang && (savedLang === 'en' || savedLang === 'ja')) {
      setLanguageState(savedLang)
    }
  }, [])

  const setLanguage = (lang: Language) => {
    setLanguageState(lang)
    localStorage.setItem('language', lang)
  }

  const t = (key: string): string => {
    return translations[language][key] || key
  }

  return (
    <I18nContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </I18nContext.Provider>
  )
}

export function useI18n() {
  const context = useContext(I18nContext)
  if (!context) {
    throw new Error('useI18n must be used within I18nProvider')
  }
  return context
}
