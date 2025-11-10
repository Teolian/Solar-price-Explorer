export default function Home() {
  return (
    <div className="space-y-6">
      <section className="rounded-lg border bg-card p-6">
        <h2 className="text-xl font-semibold mb-4">Overview</h2>
        <p className="text-muted-foreground">
          Solar×Price Explorer analyzes the correlation between JEPX electricity
          spot prices and JMA solar radiation data across Japanese power areas.
        </p>
      </section>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded-lg border bg-card p-4">
          <h3 className="font-medium mb-2">Data Sources</h3>
          <ul className="text-sm text-muted-foreground space-y-1">
            <li>• JEPX Spot Prices</li>
            <li>• JMA Solar Radiation</li>
            <li>• 9 Power Areas</li>
          </ul>
        </div>

        <div className="rounded-lg border bg-card p-4">
          <h3 className="font-medium mb-2">Features</h3>
          <ul className="text-sm text-muted-foreground space-y-1">
            <li>• Price-Radiation Correlation</li>
            <li>• ML-based Forecasting</li>
            <li>• Area Comparison</li>
          </ul>
        </div>

        <div className="rounded-lg border bg-card p-4">
          <h3 className="font-medium mb-2">Timezone</h3>
          <p className="text-sm text-muted-foreground">
            All timestamps in JST (UTC+9)
          </p>
        </div>
      </div>

      <section className="rounded-lg border bg-card p-6">
        <h2 className="text-xl font-semibold mb-4">Quick Start</h2>
        <div className="space-y-2 text-sm text-muted-foreground">
          <p>1. ETL scripts ingest data from JEPX and JMA sources</p>
          <p>2. Feature builder creates ML-ready datasets</p>
          <p>3. Baseline XGBoost model generates price forecasts</p>
          <p>4. API endpoints serve data and predictions</p>
        </div>
      </section>

      <section className="rounded-lg border bg-muted/50 p-6">
        <h3 className="font-medium mb-2">Implementation Status</h3>
        <p className="text-sm text-muted-foreground">
          Core infrastructure completed. ETL data fetching and frontend UI
          implementation in progress.
        </p>
      </section>
    </div>
  )
}
