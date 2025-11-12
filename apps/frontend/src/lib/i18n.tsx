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
    'compare.subtitle': 'Compare electricity prices and solar radiation across Japanese power areas',
    'compare.select_areas': 'Select Areas to Compare',
    'compare.time_period': 'Time Period',
    'compare.compare_button': 'Compare',
    'compare.areas': 'Areas',
    'compare.select_at_least_one': 'Please select at least one area',
    'compare.lowest_price': 'Lowest Avg Price',
    'compare.highest_price': 'Highest Avg Price',
    'compare.highest_solar': 'Highest Solar',
    'compare.strongest_correlation': 'Strongest Correlation',
    'compare.average': 'Average',
    'compare.minimum': 'Minimum',
    'compare.maximum': 'Maximum',
    'compare.price_comparison': 'Price Comparison Across Areas',
    'compare.solar_comparison': 'Average Solar Radiation (GHI) Across Areas',
    'compare.avg_ghi': 'Avg GHI',
    'compare.correlation_chart': 'Price-Solar Correlation by Area',
    'compare.price_chart_desc': 'Compare average, minimum, and maximum electricity prices across selected areas',
    'compare.solar_chart_desc': 'Average solar radiation (GHI) shows geographical and weather pattern differences',
    'compare.correlation_chart_desc': 'Negative correlation indicates solar generation reduces prices; positive indicates opposite effect',
    'compare.detailed_stats': 'Detailed Statistics',
    'compare.avg_price': 'Avg Price',
    'compare.min_price': 'Min Price',
    'compare.max_price': 'Max Price',
    'compare.avg_solar': 'Avg Solar',
    'compare.data_points': 'Data Points',
    'compare.lowest_price_area': 'Lowest Average Price',
    'compare.highest_price_area': 'Highest Average Price',
    'compare.best_solar_area': 'Highest Solar Radiation',
    'compare.best_correlation': 'Strongest Correlation',
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
    'correlations.strength': 'Strength',
    'correlations.strong': 'Strong',
    'correlations.moderate': 'Moderate',
    'correlations.weak': 'Weak',
    'correlations.coefficient': 'Correlation Coefficient',

    // Forecast Page
    'forecast.title': 'Price Forecast',
    'forecast.subtitle': 'Generate electricity price forecasts using trained ML models',
    'forecast.training_required': 'ML Model Training Required',
    'forecast.training_desc': 'Price forecasting uses machine learning models trained on historical data. Before generating forecasts, you need to train a model for your selected area.',
    'forecast.how_to_train': 'How to Train a Model',
    'forecast.option_api': 'Option 1: Using API Directly',
    'forecast.option_python': 'Option 2: Using Python',
    'forecast.requirements': 'Requirements',
    'forecast.req_price_data': 'Historical price data (JEPX)',
    'forecast.req_solar_data': 'Solar radiation data (Open-Meteo)',
    'forecast.req_ml_features': 'ML features built from raw data',
    'forecast.req_data_volume': 'At least 30 days of data recommended',
    'forecast.training_note': 'Note: Training typically takes 30-60 seconds depending on data volume. The model uses XGBoost algorithm optimized for time-series price prediction.',
    'forecast.horizon': 'Horizon',
    'forecast.generating': 'Generating...',
    'forecast.generate_button': 'Generate Forecast',
    'forecast.results': 'Forecast Results',
    'forecast.predicted_price': 'Predicted Price',
    'forecast.forecast_data': 'Forecast Data',
    'forecast.showing_hours': 'Showing first 24 hours. Total: {total} hours.',
    'forecast.model': 'Model',
    'forecast.model_note': 'Forecast generated using XGBoost baseline model. Results are for analysis purposes only.',
    'forecast.no_model': 'ML Model Training Required',
    'forecast.train_instructions': 'To enable price forecasting, you need to train a machine learning model with historical data.',
    'forecast.option1': 'Option 1: Using API Directly',
    'forecast.option2': 'Option 2: Using Python Script',
    'forecast.req1': 'Historical price data (JEPX)',
    'forecast.req2': 'Solar radiation data (Open-Meteo)',
    'forecast.req3': 'ML features built from raw data',
    'forecast.req4': 'At least 30 days of data recommended',
    'forecast.training_time': 'Training Time',
    'forecast.training_time_est': 'Estimated 1-5 minutes depending on data size',
    'forecast.note': 'Note: This is for demo purposes. Production forecasting requires more sophisticated approaches.',

    // Data Explorer Page
    'data.title': 'Data Explorer',
    'data.subtitle': 'Browse and export raw price and radiation data',
    'data.data_type': 'Data Type',
    'data.load_data': 'Load Data',
    'data.export_csv': 'Export CSV',
    'data.electricity_prices': 'Electricity Prices',
    'data.interactive_chart': 'Interactive chart: Zoom in/out, pan to explore price trends over time',
    'data.price_data': 'Price Data',
    'data.solar_radiation': 'Solar Radiation',
    'data.ghi_global': 'GHI (Global)',
    'data.dni_direct': 'DNI (Direct)',
    'data.dhi_diffuse': 'DHI (Diffuse)',
    'data.radiation_explanation': 'GHI = Total solar radiation | DNI = Direct sunlight | DHI = Scattered/cloud-filtered light',
    'data.radiation_data': 'Radiation Data',
    'data.timestamp': 'Timestamp (JST)',
    'data.station': 'Station',
    'data.volume': 'Volume (kWh)',
    'data.no_data': 'No data available for the selected period',
    'data.showing': 'Showing {count} records',
    'data.showing_records': 'Showing first 100 of {count} records. Export to view all.',

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
    'compare.subtitle': '日本の電力エリア間で電力価格と太陽光照射量を比較',
    'compare.select_areas': '比較する地域を選択',
    'compare.time_period': '期間',
    'compare.compare_button': '比較',
    'compare.areas': 'エリア',
    'compare.select_at_least_one': '少なくとも1つのエリアを選択してください',
    'compare.lowest_price': '最低平均価格',
    'compare.highest_price': '最高平均価格',
    'compare.highest_solar': '最高太陽光',
    'compare.strongest_correlation': '最強相関',
    'compare.average': '平均',
    'compare.minimum': '最小',
    'compare.maximum': '最大',
    'compare.price_comparison': 'エリア間価格比較',
    'compare.solar_comparison': 'エリア間平均太陽光照射量（GHI）',
    'compare.avg_ghi': '平均GHI',
    'compare.correlation_chart': 'エリア別価格-太陽光相関',
    'compare.price_chart_desc': '選択したエリア間で平均、最小、最大電力価格を比較',
    'compare.solar_chart_desc': '平均太陽光照射量（GHI）は地理的・気象的パターンの違いを示します',
    'compare.correlation_chart_desc': '負の相関は太陽光発電が価格を下げることを、正の相関は逆の効果を示します',
    'compare.detailed_stats': '詳細統計',
    'compare.avg_price': '平均価格',
    'compare.min_price': '最小価格',
    'compare.max_price': '最大価格',
    'compare.avg_solar': '平均太陽光',
    'compare.data_points': 'データポイント数',
    'compare.lowest_price_area': '最低平均価格',
    'compare.highest_price_area': '最高平均価格',
    'compare.best_solar_area': '最高太陽光照射量',
    'compare.best_correlation': '最強相関',
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
    'correlations.strength': '強度',
    'correlations.strong': '強',
    'correlations.moderate': '中',
    'correlations.weak': '弱',
    'correlations.coefficient': '相関係数',

    // 予測ページ
    'forecast.title': '価格予測',
    'forecast.subtitle': 'トレーニング済みMLモデルを使用した電力価格予測',
    'forecast.training_required': 'MLモデルのトレーニングが必要',
    'forecast.training_desc': '価格予測には履歴データでトレーニングされた機械学習モデルを使用します。予測を生成する前に、選択したエリアのモデルをトレーニングする必要があります。',
    'forecast.how_to_train': 'モデルのトレーニング方法',
    'forecast.option_api': 'オプション1：APIを直接使用',
    'forecast.option_python': 'オプション2：Pythonを使用',
    'forecast.requirements': '要件',
    'forecast.req_price_data': '履歴価格データ（JEPX）',
    'forecast.req_solar_data': '太陽光照射量データ（Open-Meteo）',
    'forecast.req_ml_features': '生データから構築されたML特徴量',
    'forecast.req_data_volume': '最低30日分のデータを推奨',
    'forecast.training_note': '注：トレーニングはデータ量に応じて通常30〜60秒かかります。モデルは時系列価格予測に最適化されたXGBoostアルゴリズムを使用しています。',
    'forecast.horizon': '予測期間',
    'forecast.generating': '生成中...',
    'forecast.generate_button': '予測を生成',
    'forecast.results': '予測結果',
    'forecast.predicted_price': '予測価格',
    'forecast.forecast_data': '予測データ',
    'forecast.showing_hours': '最初の24時間を表示中。合計：{total}時間。',
    'forecast.model': 'モデル',
    'forecast.model_note': 'XGBoostベースラインモデルを使用して生成された予測です。結果は分析目的のみです。',
    'forecast.no_model': 'MLモデルのトレーニングが必要',
    'forecast.train_instructions': '価格予測を有効にするには、履歴データを使用して機械学習モデルをトレーニングする必要があります。',
    'forecast.option1': 'オプション1：APIを直接使用',
    'forecast.option2': 'オプション2：Pythonスクリプトを使用',
    'forecast.req1': '履歴価格データ（JEPX）',
    'forecast.req2': '太陽光照射量データ（Open-Meteo）',
    'forecast.req3': '生データから構築されたML特徴量',
    'forecast.req4': '最低30日分のデータを推奨',
    'forecast.training_time': 'トレーニング時間',
    'forecast.training_time_est': 'データサイズに応じて1〜5分程度',
    'forecast.note': '注：これはデモ目的です。本番環境の予測にはより高度なアプローチが必要です。',

    // データエクスプローラーページ
    'data.title': 'データエクスプローラー',
    'data.subtitle': '生データの閲覧とエクスポート',
    'data.data_type': 'データ種別',
    'data.load_data': 'データ読み込み',
    'data.export_csv': 'CSV出力',
    'data.electricity_prices': '電力価格',
    'data.interactive_chart': 'インタラクティブチャート：ズームイン/アウト、パンで価格推移を探索できます',
    'data.price_data': '価格データ',
    'data.solar_radiation': '太陽光照射量',
    'data.ghi_global': 'GHI（全天）',
    'data.dni_direct': 'DNI（直達）',
    'data.dhi_diffuse': 'DHI（散乱）',
    'data.radiation_explanation': 'GHI = 全天日射量 | DNI = 直達日射量 | DHI = 散乱日射量',
    'data.radiation_data': '太陽光照射量データ',
    'data.timestamp': 'タイムスタンプ（JST）',
    'data.station': '観測地点',
    'data.volume': '取引量（kWh）',
    'data.no_data': '選択期間のデータがありません',
    'data.showing': '{count}件のレコードを表示中',
    'data.showing_records': '最初の100件を表示（全{count}件）。すべて表示するにはエクスポートしてください。',

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
