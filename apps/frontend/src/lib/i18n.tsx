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

    // Overview (Dashboard) Page
    'overview.title': 'JEPX Price & Solar Radiation Dashboard',
    'overview.latest_price': 'Latest Price',
    'overview.avg_price_7d': 'Average Price (7 Days)',
    'overview.avg_radiation': 'Average Solar Radiation',
    'overview.correlation': 'Price-Solar Correlation',
    'overview.price_trend': 'Price Trend (Last 3 Days)',
    'overview.radiation_trend': 'Solar Radiation Trend',
    'overview.price': 'Price',
    'overview.radiation': 'Solar Radiation',
    'overview.time': 'Time',
    'overview.ghi': 'GHI (W/m²)',

    // Insights (Hourly Patterns) Page
    'insights.title': 'Hourly Energy Price Patterns',
    'insights.subtitle': 'Analyze price and solar radiation patterns by hour of day',
    'insights.lowest_price': 'Lowest Price Hour',
    'insights.highest_price': 'Highest Price Hour',
    'insights.peak_solar': 'Peak Solar Hour',
    'insights.pattern_analysis': 'Pattern Analysis',
    'insights.avg_price': 'Average Price',
    'insights.avg_solar': 'Average Solar (GHI)',
    'insights.data_points': 'Data Points',
    'insights.understanding': 'Understanding the Pattern',
    'insights.night_hours': 'Night Hours (0-6)',
    'insights.morning_peak': 'Morning Peak (7-9)',
    'insights.solar_hours': 'Solar Hours (10-14)',
    'insights.evening_peak': 'Evening Peak (18-20)',
    'insights.chart_title': 'Hourly Price vs Solar Radiation',
    'insights.hour': 'Hour',

    // Compare Areas Page
    'compare.title': 'Multi-Area Comparison',
    'compare.subtitle': 'Compare electricity prices and solar radiation across different regions',
    'compare.select_areas': 'Select Areas to Compare',
    'compare.lowest_price_area': 'Lowest Average Price',
    'compare.highest_price_area': 'Highest Average Price',
    'compare.best_solar_area': 'Highest Solar Radiation',
    'compare.best_correlation': 'Strongest Correlation',
    'compare.price_comparison': 'Price Comparison',
    'compare.solar_comparison': 'Solar Radiation Comparison',
    'compare.correlation_comparison': 'Correlation Strength',
    'compare.strong': 'Strong',
    'compare.moderate': 'Moderate',
    'compare.weak': 'Weak',

    // Correlations Page
    'correlations.title': 'Price-Solar Correlation Analysis',
    'correlations.subtitle': 'Statistical analysis of the relationship between electricity prices and solar radiation',
    'correlations.key_findings': 'Key Findings',
    'correlations.ghi_correlation': 'GHI Correlation',
    'correlations.dni_correlation': 'DNI Correlation',
    'correlations.dhi_correlation': 'DHI Correlation',
    'correlations.interpretation': 'Interpretation',
    'correlations.negative_desc': 'Negative correlation detected: Higher solar radiation is associated with lower electricity prices. Solar power generation effectively reduces spot market prices during sunny midday hours.',
    'correlations.positive_desc': 'Positive correlation: Higher solar radiation is associated with higher prices, which may indicate demand-side factors dominating supply effects.',
    'correlations.weak_desc': 'Weak correlation: The relationship between solar radiation and prices is not strong in this area/period. Other factors may be more influential.',
    'correlations.analysis_period': 'Analysis Period',
    'correlations.data_points_count': 'Data Points',
    'correlations.scatter_title': 'Price vs {type} Scatter Plot',

    // Forecast Page
    'forecast.title': 'Price Forecasting (ML-Based)',
    'forecast.subtitle': 'Machine learning predictions for future electricity prices',
    'forecast.no_model': 'ML Model Training Required',
    'forecast.train_instructions': 'To enable price forecasting, you need to train a machine learning model with historical data.',
    'forecast.option1': 'Option 1: Using API Directly',
    'forecast.option2': 'Option 2: Using Python Script',
    'forecast.requirements': 'Requirements',
    'forecast.req1': 'Historical price data (JEPX)',
    'forecast.req2': 'Solar radiation data (Open-Meteo)',
    'forecast.req3': 'ML features built from raw data',
    'forecast.req4': 'At least 30 days of data recommended',
    'forecast.training_time': 'Training Time',
    'forecast.training_time_est': 'Estimated 1-5 minutes depending on data size',
    'forecast.note': 'Note: This is for demo purposes. Production forecasting requires more sophisticated approaches.',

    // Data Explorer Page
    'data.title': 'Data Explorer',
    'data.subtitle': 'Browse and analyze raw JEPX price and solar radiation data',
    'data.price_data': 'Price Data',
    'data.radiation_data': 'Solar Radiation Data',
    'data.timestamp': 'Timestamp',
    'data.station': 'Station',
    'data.volume': 'Volume (kWh)',
    'data.no_data': 'No data available for the selected period',
    'data.showing': 'Showing {count} records',

    // Chart Labels
    'chart.price_jpy_kwh': 'Price (JPY/kWh)',
    'chart.solar_radiation': 'Solar Radiation (W/m²)',
    'chart.hour_of_day': 'Hour of Day',
    'chart.area': 'Area',
    'chart.correlation_strength': 'Correlation Strength',
    'chart.best_hours': 'Best Hours',
    'chart.worst_hours': 'Worst Hours',
    'chart.normal_hours': 'Normal Hours',
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

    // 概要（ダッシュボード）ページ
    'overview.title': 'JEPX価格・太陽光照射量ダッシュボード',
    'overview.latest_price': '最新価格',
    'overview.avg_price_7d': '平均価格（7日間）',
    'overview.avg_radiation': '平均太陽光照射量',
    'overview.correlation': '価格-太陽光相関',
    'overview.price_trend': '価格推移（直近3日間）',
    'overview.radiation_trend': '太陽光照射量推移',
    'overview.price': '価格',
    'overview.radiation': '太陽光照射量',
    'overview.time': '時刻',
    'overview.ghi': '全天日射量 (W/m²)',

    // インサイト（時間別パターン）ページ
    'insights.title': '時間帯別電力価格パターン',
    'insights.subtitle': '時間帯ごとの価格と太陽光照射量のパターンを分析',
    'insights.lowest_price': '最低価格時間帯',
    'insights.highest_price': '最高価格時間帯',
    'insights.peak_solar': '太陽光ピーク時間帯',
    'insights.pattern_analysis': 'パターン分析',
    'insights.avg_price': '平均価格',
    'insights.avg_solar': '平均太陽光（GHI）',
    'insights.data_points': 'データポイント数',
    'insights.understanding': 'パターンの理解',
    'insights.night_hours': '夜間（0-6時）',
    'insights.morning_peak': '朝ピーク（7-9時）',
    'insights.solar_hours': '太陽光時間帯（10-14時）',
    'insights.evening_peak': '夕方ピーク（18-20時）',
    'insights.chart_title': '時間別価格 vs 太陽光照射量',
    'insights.hour': '時刻',

    // 地域比較ページ
    'compare.title': '複数地域比較',
    'compare.subtitle': '異なる地域の電力価格と太陽光照射量を比較',
    'compare.select_areas': '比較する地域を選択',
    'compare.lowest_price_area': '最低平均価格',
    'compare.highest_price_area': '最高平均価格',
    'compare.best_solar_area': '最高太陽光照射量',
    'compare.best_correlation': '最強相関',
    'compare.price_comparison': '価格比較',
    'compare.solar_comparison': '太陽光照射量比較',
    'compare.correlation_comparison': '相関強度',
    'compare.strong': '強',
    'compare.moderate': '中',
    'compare.weak': '弱',

    // 相関分析ページ
    'correlations.title': '価格-太陽光相関分析',
    'correlations.subtitle': '電力価格と太陽光照射量の関係性の統計分析',
    'correlations.key_findings': '主要な知見',
    'correlations.ghi_correlation': 'GHI相関',
    'correlations.dni_correlation': 'DNI相関',
    'correlations.dhi_correlation': 'DHI相関',
    'correlations.interpretation': '解釈',
    'correlations.negative_desc': '負の相関が検出されました：太陽光照射量が多いほど電力価格が低くなります。太陽光発電が晴天の正午時間帯にスポット市場価格を効果的に引き下げています。',
    'correlations.positive_desc': '正の相関：太陽光照射量が多いほど価格が高くなっており、需要側の要因が供給効果を上回っている可能性があります。',
    'correlations.weak_desc': '弱い相関：この地域・期間では太陽光照射量と価格の関係性は強くありません。他の要因がより影響力を持っている可能性があります。',
    'correlations.analysis_period': '分析期間',
    'correlations.data_points_count': 'データポイント数',
    'correlations.scatter_title': '価格 vs {type} 散布図',

    // 予測ページ
    'forecast.title': '価格予測（機械学習ベース）',
    'forecast.subtitle': '機械学習による将来の電力価格予測',
    'forecast.no_model': 'MLモデルのトレーニングが必要',
    'forecast.train_instructions': '価格予測を有効にするには、履歴データを使用して機械学習モデルをトレーニングする必要があります。',
    'forecast.option1': 'オプション1：APIを直接使用',
    'forecast.option2': 'オプション2：Pythonスクリプトを使用',
    'forecast.requirements': '要件',
    'forecast.req1': '履歴価格データ（JEPX）',
    'forecast.req2': '太陽光照射量データ（Open-Meteo）',
    'forecast.req3': '生データから構築されたML特徴量',
    'forecast.req4': '最低30日分のデータを推奨',
    'forecast.training_time': 'トレーニング時間',
    'forecast.training_time_est': 'データサイズに応じて1〜5分程度',
    'forecast.note': '注：これはデモ目的です。本番環境の予測にはより高度なアプローチが必要です。',

    // データエクスプローラーページ
    'data.title': 'データエクスプローラー',
    'data.subtitle': 'JEPX価格と太陽光照射量の生データを参照・分析',
    'data.price_data': '価格データ',
    'data.radiation_data': '太陽光照射量データ',
    'data.timestamp': 'タイムスタンプ',
    'data.station': '観測地点',
    'data.volume': '取引量（kWh）',
    'data.no_data': '選択期間のデータがありません',
    'data.showing': '{count}件のレコードを表示中',

    // グラフラベル
    'chart.price_jpy_kwh': '価格（円/kWh）',
    'chart.solar_radiation': '太陽光照射量（W/m²）',
    'chart.hour_of_day': '時刻',
    'chart.area': '地域',
    'chart.correlation_strength': '相関強度',
    'chart.best_hours': '最適時間帯',
    'chart.worst_hours': '回避時間帯',
    'chart.normal_hours': '通常時間帯',
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
