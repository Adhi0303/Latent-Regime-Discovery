"use client";

import { useEffect, useState } from "react";
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceArea 
} from "recharts";
import { Activity, TrendingUp, AlertTriangle, ShieldAlert, Cpu, History, Wallet, Briefcase } from "lucide-react";

export default function Dashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedTicker, setSelectedTicker] = useState("^GSPC");
  
  const [sentimentData, setSentimentData] = useState<any>(null);
  const [sentimentLoading, setSentimentLoading] = useState(true);

  const [forecastData, setForecastData] = useState<any>(null);
  const [forecastLoading, setForecastLoading] = useState(true);

  const [backtestData, setBacktestData] = useState<any>(null);
  const [backtestLoading, setBacktestLoading] = useState(true);

  const [portfolioData, setPortfolioData] = useState<any>(null);
  const [portfolioLoading, setPortfolioLoading] = useState(true);

  const [predictionsData, setPredictionsData] = useState<any>(null);
  const [predictionsLoading, setPredictionsLoading] = useState(true);

  const [viewMode, setViewMode] = useState<"dashboard" | "backtest" | "bot" | "scoreboard">("dashboard");

  // Chart interactivity states
  const [timeFilter, setTimeFilter] = useState<string>("all");
  const [zoomDomain, setZoomDomain] = useState<{ left: string | null; right: string | null }>({ left: null, right: null });
  const [zoomRefArea, setZoomRefArea] = useState<{ left: string | null; right: string | null }>({ left: null, right: null });
  const [showRegimes, setShowRegimes] = useState({ bull: true, bear: true, sideways: true });

  const [triggerRun, setTriggerRun] = useState(false);
  const [runningBot, setRunningBot] = useState(false);

  useEffect(() => {
    const encodedTicker = encodeURIComponent(selectedTicker);
    setLoading(true);
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/predict?ticker=${encodedTicker}&period=5y`)
      .then((res) => res.json())
      .then((json) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
      
    // Fetch sentiment concurrently
    setSentimentLoading(true);
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/sentiment?ticker=${encodedTicker}`)
      .then((res) => res.json())
      .then((json) => {
        setSentimentData(json);
        setSentimentLoading(false);
      })
      .catch(() => setSentimentLoading(false));
      
    // Fetch forecast
    setForecastLoading(true);
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/forecast?ticker=${encodedTicker}`)
      .then((res) => res.json())
      .then((json) => {
        setForecastData(json);
        setForecastLoading(false);
      })
      .catch(() => setForecastLoading(false));
      
    // Fetch backtest
    setBacktestLoading(true);
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/backtest?ticker=${encodedTicker}`)
      .then((res) => res.json())
      .then((json) => {
        setBacktestData(json);
        setBacktestLoading(false);
      })
      .catch(() => setBacktestLoading(false));

    // Fetch Global Portfolio
    setPortfolioLoading(true);
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/bot/portfolio`)
      .then((res) => res.json())
      .then((json) => {
        setPortfolioData(json);
        setPortfolioLoading(false);
      })
      .catch(() => setPortfolioLoading(false));

    // Fetch Predictions Scoreboard
    setPredictionsLoading(true);
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/bot/predictions?ticker=${encodedTicker}`)
      .then((res) => res.json())
      .then((json) => {
        setPredictionsData(json);
        setPredictionsLoading(false);
      })
      .catch(() => setPredictionsLoading(false));

  }, [selectedTicker, triggerRun]);

  const forceBotRun = () => {
    setRunningBot(true);
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/bot/run`, { method: 'POST' })
      .then((res) => res.json())
      .then(() => {
         setTriggerRun(!triggerRun);
         setRunningBot(false);
      })
      .catch(() => setRunningBot(false));
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#121212] text-white">
        <div className="flex flex-col items-center gap-4">
          <Activity className="h-10 w-10 animate-pulse text-blue-500" />
          <p className="text-xl font-medium tracking-wide">Connecting to Quantum HMM Engine...</p>
        </div>
      </div>
    );
  }

  if (!data || data.detail) return (
    <div className="flex h-screen items-center justify-center bg-[#0E0E10] text-white flex-col gap-4">
      <ShieldAlert className="h-12 w-12 text-rose-500" />
      <p className="text-xl font-bold text-rose-400">Backend API Unavailable</p>
      <p className="text-sm text-gray-400 max-w-sm text-center">
        The Hugging Face backend is still loading or unavailable. Please wait 1-2 minutes and refresh the page.
      </p>
      <p className="text-xs text-gray-600">Error: {data?.detail || "Could not connect to API"}</p>
    </div>
  );

  const regimeLabels: Record<number, string> = {
    0: "Bull Market",
    1: "Sideways / Correction",
    2: "Bear Market / Crisis"
  };

  const regimeColors: Record<number, string> = {
    0: "rgba(16, 185, 129, 0.15)",
    1: "rgba(245, 158, 11, 0.15)",
    2: "rgba(239, 68, 68, 0.15)"
  };

  const regimeTextColors: Record<number, string> = {
    0: "text-emerald-400",
    1: "text-amber-400",
    2: "text-rose-400"
  };

  // Filter chart data based on time period and zoom
  let chartData = [];
  if (data && data.history) {
    chartData = [...data.history];
    
    // Apply time filter
    if (timeFilter !== 'all' && chartData.length > 0) {
      const lastDate = new Date(chartData[chartData.length - 1].date);
      let cutoffDate = new Date(lastDate);
      
      if (timeFilter === '1w') cutoffDate.setDate(cutoffDate.getDate() - 7);
      else if (timeFilter === '1m') cutoffDate.setMonth(cutoffDate.getMonth() - 1);
      else if (timeFilter === '6m') cutoffDate.setMonth(cutoffDate.getMonth() - 6);
      else if (timeFilter === '1y') cutoffDate.setFullYear(cutoffDate.getFullYear() - 1);
      
      chartData = chartData.filter(d => new Date(d.date) >= cutoffDate);
    }

    // Apply zoom filter
    if (zoomDomain.left && zoomDomain.right) {
      const leftDate = new Date(zoomDomain.left);
      const rightDate = new Date(zoomDomain.right);
      const start = leftDate < rightDate ? leftDate : rightDate;
      const end = leftDate < rightDate ? rightDate : leftDate;
      chartData = chartData.filter(d => {
        const dDate = new Date(d.date);
        return dDate >= start && dDate <= end;
      });
    }
  }

  // Calculate regime blocks for the filtered data
  const blocks = [];
  if (chartData.length > 0) {
    let currentRegime = chartData[0].regime;
    let startIdx = 0;

    for (let i = 1; i < chartData.length; i++) {
      if (chartData[i].regime !== currentRegime) {
        blocks.push({
          start: chartData[startIdx].date,
          end: chartData[i - 1].date,
          regime: currentRegime
        });
        currentRegime = chartData[i].regime;
        startIdx = i;
      }
    }
    blocks.push({
      start: chartData[startIdx].date,
      end: chartData[chartData.length - 1].date,
      regime: currentRegime
    });
  }

  // Helper for regime names mapping
  const regimeNameMap: Record<number, string> = {
    0: "bull",
    1: "sideways",
    2: "bear"
  };

  const currentRegime = data.current_regime;

  return (
    <div className="flex h-screen bg-[#0A0A0B] text-[#e0e0e0] font-sans selection:bg-blue-500/30 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 border-r border-[#27272A] bg-[#0A0A0B] flex flex-col shrink-0">
        <div className="h-16 flex items-center px-6 border-b border-[#27272A]">
          <div className="flex items-center gap-2">
            <Cpu className="w-5 h-5 text-blue-500" />
            <span className="font-bold text-sm tracking-wide text-white">Latent Discovery</span>
          </div>
        </div>
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          <div className="text-xs font-semibold text-gray-500 mb-2 mt-2 px-2 uppercase tracking-wider">Dashboard</div>
          <button onClick={() => setViewMode("dashboard")} className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${viewMode === 'dashboard' ? 'bg-[#141414] text-white border border-[#27272A]' : 'text-gray-400 hover:text-white hover:bg-[#141414] border border-transparent'}`}>
            <Activity className="w-4 h-4" /> Live Overview
          </button>
          <button onClick={() => setViewMode("backtest")} className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${viewMode === 'backtest' ? 'bg-[#141414] text-white border border-[#27272A]' : 'text-gray-400 hover:text-white hover:bg-[#141414] border border-transparent'}`}>
            <History className="w-4 h-4" /> Strategy Simulator
          </button>
          <div className="text-xs font-semibold text-gray-500 mb-2 mt-6 px-2 uppercase tracking-wider">Trading</div>
          <button onClick={() => setViewMode("bot")} className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${viewMode === 'bot' ? 'bg-[#141414] text-white border border-[#27272A]' : 'text-gray-400 hover:text-white hover:bg-[#141414] border border-transparent'}`}>
            <Briefcase className="w-4 h-4" /> Portfolio Bot
          </button>
          <button onClick={() => setViewMode("scoreboard")} className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${viewMode === 'scoreboard' ? 'bg-[#141414] text-white border border-[#27272A]' : 'text-gray-400 hover:text-white hover:bg-[#141414] border border-transparent'}`}>
            <TrendingUp className="w-4 h-4" /> AI Scoreboard
          </button>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden bg-[#0A0A0B]">
        {/* Top Header */}
        <header className="h-16 border-b border-[#27272A] flex items-center justify-between px-8 shrink-0 bg-[#0A0A0B]">
          <h1 className="text-lg font-semibold text-white">
            {viewMode === "dashboard" && "Live Dashboard"}
            {viewMode === "backtest" && "Strategy Simulator"}
            {viewMode === "bot" && "Multi-Asset Portfolio Bot"}
            {viewMode === "scoreboard" && "AI Scoreboard"}
          </h1>
          <div className="flex items-center gap-4">
            <select 
              className="bg-[#141414] border border-[#27272A] text-white text-sm rounded-md focus:ring-blue-500 focus:border-blue-500 block py-1.5 px-3 outline-none cursor-pointer"
              value={selectedTicker}
              onChange={(e) => setSelectedTicker(e.target.value)}
            >
              <option value="^GSPC">S&P 500 (^GSPC)</option>
              <option value="BTC-USD">Bitcoin (BTC-USD)</option>
              <option value="TSLA">Tesla (TSLA)</option>
              <option value="NVDA">Nvidia (NVDA)</option>
              <option value="BRK-B">Berkshire Hathaway (BRK-B)</option>
            </select>
            <div className="flex items-center gap-2 rounded-md bg-[#141414] px-3 py-1.5 border border-[#27272A]">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
              </span>
              <span className="text-xs font-medium text-gray-300">Live API Connection</span>
            </div>
          </div>
        </header>

        {/* Scrollable Content Area */}
        <div className="flex-1 p-6 flex flex-col overflow-hidden min-h-0 gap-4">
          {viewMode === "dashboard" ? (
            <div className="flex flex-col h-full gap-4 min-h-0">
              {/* Top Cards Grid (Compact) */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 shrink-0">
                {/* Card 1 */}
                <div className="rounded-xl bg-[#141414] border border-[#27272A] p-4 shadow-sm flex flex-col justify-center">
                  <p className="text-xs font-medium text-gray-400 mb-1">Asset Tracked</p>
                  <div className="flex items-baseline gap-2">
                    <h2 className="text-xl font-bold text-white tracking-tight">{data.ticker}</h2>
                    <span className="text-sm font-semibold text-gray-300">
                      ${data.latest_close.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                  </div>
                </div>

                {/* Card 1.5 */}
                <div className="rounded-xl bg-[#141414] border border-[#27272A] p-4 shadow-sm flex flex-col justify-center">
                  <p className="text-xs font-medium text-gray-400 mb-1">AI Price Forecast</p>
                  {forecastLoading ? (
                    <div className="text-xs text-gray-400">Loading...</div>
                  ) : forecastData ? (
                    <div className="flex items-baseline gap-2">
                      <h2 className="text-xl font-bold tracking-tight" style={{ color: forecastData.predicted_pct_change > 0 ? '#34d399' : '#fb7185' }}>
                        ${forecastData.final_prediction.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </h2>
                      <span className={`text-xs font-semibold ${forecastData.predicted_pct_change > 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {forecastData.predicted_pct_change > 0 ? '+' : ''}{forecastData.predicted_pct_change.toFixed(2)}%
                      </span>
                    </div>
                  ) : (
                    <div className="text-xs text-rose-400">Failed</div>
                  )}
                </div>

                {/* Card 2 */}
                <div className="rounded-xl bg-[#141414] border border-[#27272A] p-4 shadow-sm flex flex-col justify-center">
                  <p className="text-xs font-medium text-gray-400 mb-1">Detected Regime</p>
                  <div className="flex items-center gap-2">
                    <h2 className={`text-xl font-bold tracking-tight ${regimeTextColors[currentRegime]}`}>
                      {regimeLabels[currentRegime]}
                    </h2>
                  </div>
                </div>

                {/* Card 3 */}
                <div className="rounded-xl bg-[#141414] border border-[#27272A] p-4 shadow-sm flex flex-col justify-center">
                  <p className="text-xs font-medium text-gray-400 mb-2">Regime Probabilities</p>
                  <div className="flex gap-2 h-1.5 w-full bg-[#27272A] rounded-full overflow-hidden">
                    <div className="bg-emerald-500 h-full" style={{ width: `${data.probabilities["0"] * 100}%` }}></div>
                    <div className="bg-amber-500 h-full" style={{ width: `${data.probabilities["1"] * 100}%` }}></div>
                    <div className="bg-rose-500 h-full" style={{ width: `${data.probabilities["2"] * 100}%` }}></div>
                  </div>
                  <div className="flex justify-between text-[10px] mt-1 text-gray-500">
                    <span>Bu: {(data.probabilities["0"] * 100).toFixed(0)}%</span>
                    <span>Si: {(data.probabilities["1"] * 100).toFixed(0)}%</span>
                    <span>Be: {(data.probabilities["2"] * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </div>

              {/* Side-by-Side Content */}
              <div className="flex-1 flex gap-4 min-h-0">
                {/* Chart Section (Left) */}
                <div className="flex-[2] rounded-xl bg-[#141414] border border-[#27272A] p-4 flex flex-col shadow-sm min-w-0">
                  <div className="mb-4 flex justify-between items-center shrink-0">
                    <h3 className="text-sm font-bold text-white">Historical Regime Map</h3>
                    <div className="flex items-center gap-2 bg-[#27272A]/50 p-1 rounded-md border border-[#27272A]">
                      {['1w', '1m', '6m', '1y', 'all'].map((tf) => (
                        <button
                          key={tf}
                          onClick={() => { setTimeFilter(tf); setZoomDomain({left: null, right: null}); }}
                          className={`px-2 py-0.5 text-[10px] font-medium rounded transition-colors ${timeFilter === tf ? 'bg-[#3F3F46] text-white' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}
                        >
                          {tf.toUpperCase()}
                        </button>
                      ))}
                    </div>
                  </div>
                  
                  <div className="flex-1 w-full min-h-0 relative select-none">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart 
                        data={chartData} 
                        margin={{ top: 5, right: 5, left: 5, bottom: 0 }}
                        onMouseDown={(e) => e && setZoomRefArea({ ...zoomRefArea, left: e.activeLabel ? String(e.activeLabel) : null })}
                        onMouseMove={(e) => e && zoomRefArea.left && setZoomRefArea({ ...zoomRefArea, right: e.activeLabel ? String(e.activeLabel) : null })}
                        onMouseUp={() => {
                          if (zoomRefArea.left && zoomRefArea.right && zoomRefArea.left !== zoomRefArea.right) {
                            setZoomDomain({ left: zoomRefArea.left, right: zoomRefArea.right });
                          }
                          setZoomRefArea({ left: null, right: null });
                        }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="#27272A" vertical={false} />
                        <XAxis 
                          dataKey="date" 
                          stroke="#71717A" 
                          tick={{fill: '#71717A', fontSize: 10}}
                          tickMargin={8}
                          minTickGap={30}
                        />
                        <YAxis 
                          domain={['auto', 'auto']} 
                          stroke="#71717A" 
                          tick={{fill: '#71717A', fontSize: 10}}
                          tickFormatter={(val) => `$${val}`}
                          axisLine={false}
                          tickLine={false}
                        />
                        <Tooltip 
                          contentStyle={{ backgroundColor: '#27272A', borderColor: '#3F3F46', borderRadius: '8px', color: '#fff', fontSize: '12px', padding: '8px' }}
                          itemStyle={{ color: '#60A5FA' }}
                          labelStyle={{ color: '#A1A1AA', marginBottom: '4px' }}
                          formatter={(value: any) => [`$${Number(value).toFixed(2)}`, 'Price']}
                        />
                        
                        {blocks.map((b, idx) => {
                          const regimeName = regimeNameMap[b.regime] as keyof typeof showRegimes;
                          if (!showRegimes[regimeName]) return null;
                          return (
                            <ReferenceArea 
                              key={idx} 
                              x1={b.start} 
                              x2={b.end} 
                              fill={regimeColors[b.regime]} 
                              fillOpacity={1}
                              strokeOpacity={0}
                            />
                          );
                        })}

                        {zoomRefArea.left && zoomRefArea.right ? (
                          <ReferenceArea x1={zoomRefArea.left} x2={zoomRefArea.right} strokeOpacity={0.3} fill="#FFFFFF" fillOpacity={0.1} />
                        ) : null}

                        <Line 
                          type="monotone" 
                          dataKey="close" 
                          stroke="#FFFFFF" 
                          strokeWidth={1.5}
                          dot={false}
                          activeDot={{ r: 4, fill: "#60A5FA", stroke: "#27272A", strokeWidth: 2 }}
                          isAnimationActive={false}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Sentiment Section (Right) */}
                <div className="flex-1 rounded-xl bg-[#141414] border border-[#27272A] p-4 flex flex-col shadow-sm min-w-0">
                  <div className="mb-3 flex justify-between items-center shrink-0">
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      Macro Sentiment
                    </h3>
                    {sentimentData && (
                      <div className="text-xs font-bold px-2 py-1 rounded bg-[#27272A]" style={{ color: sentimentData.macro_score > 0 ? '#34d399' : sentimentData.macro_score < 0 ? '#fb7185' : '#fbbf24' }}>
                        {sentimentData.macro_score > 0 ? '+' : ''}{sentimentData.macro_score.toFixed(2)}
                      </div>
                    )}
                  </div>
                  
                  <div className="flex-1 overflow-y-auto pr-1 space-y-2 min-h-0">
                    {sentimentLoading ? (
                      <div className="text-xs text-gray-500 py-4 text-center">Reading headlines...</div>
                    ) : sentimentData && sentimentData.news ? (
                      sentimentData.news.map((n: any, i: number) => (
                        <a key={i} href={n.url || "#"} target="_blank" rel="noopener noreferrer" className="block focus:outline-none">
                          <div className="flex items-start gap-2 p-2.5 rounded-lg bg-[#0A0A0B] border border-[#27272A] hover:bg-[#1C1C1E] transition-colors">
                            <div className={`mt-1 flex-shrink-0 w-2 h-2 rounded-full ${n.sentiment_label === 'positive' ? 'bg-emerald-500' : n.sentiment_label === 'negative' ? 'bg-rose-500' : 'bg-amber-500'}`}></div>
                            <div className="flex-1 min-w-0">
                              <h4 className="text-xs font-medium text-gray-200 line-clamp-2 leading-tight hover:text-blue-400 transition-colors">{n.title}</h4>
                              <div className="flex justify-between items-center mt-1.5">
                                <p className="text-[10px] text-gray-500 truncate">{n.publisher}</p>
                                <div className="text-[10px] font-mono font-medium" style={{ color: n.sentiment_score > 0 ? '#34d399' : n.sentiment_score < 0 ? '#fb7185' : '#fbbf24' }}>
                                  {n.sentiment_score > 0 ? '+' : ''}{n.sentiment_score.toFixed(2)}
                                </div>
                              </div>
                            </div>
                          </div>
                        </a>
                      ))
                    ) : (
                      <div className="text-xs text-gray-500 py-4 text-center">No sentiment data.</div>
                    )}
                  </div>
                </div>
              </div>
            </div>
) : viewMode === "backtest" ? (
        /* Backtest Simulator View */
        <div className="flex flex-col h-full gap-4 min-h-0">
          {backtestLoading ? (
             <div className="flex flex-col items-center justify-center flex-1 text-gray-400">
               <Activity className="h-8 w-8 animate-spin text-purple-500 mb-3" />
               <p className="text-sm">Simulating 20 years of historical trading...</p>
             </div>
          ) : backtestData && backtestData.metrics ? (
            <>
              {/* KPIs */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 shrink-0">
                <div className="rounded-xl bg-[#141414] border border-[#27272A] p-4 shadow-sm relative overflow-hidden flex flex-col justify-center">
                  <div className="absolute top-0 right-0 w-24 h-24 bg-purple-500/10 rounded-full blur-2xl -mr-8 -mt-8"></div>
                  <p className="text-xs font-medium text-gray-400 mb-1">AI Strategy Total Return</p>
                  <h2 className="text-2xl font-bold tracking-tight text-white mt-1">
                    {backtestData.metrics.ai_return > 0 ? '+' : ''}{backtestData.metrics.ai_return.toLocaleString()}%
                  </h2>
                  <p className="text-[10px] text-gray-500 mt-1">Max Drawdown: <span className="text-rose-400">{backtestData.metrics.ai_max_dd}%</span></p>
                </div>
                
                <div className="rounded-xl bg-[#141414] border border-[#27272A] p-4 shadow-sm relative overflow-hidden flex flex-col justify-center">
                  <p className="text-xs font-medium text-gray-400 mb-1">Buy & Hold Return</p>
                  <h2 className="text-2xl font-bold tracking-tight text-gray-300 mt-1">
                    {backtestData.metrics.buy_hold_return > 0 ? '+' : ''}{backtestData.metrics.buy_hold_return.toLocaleString()}%
                  </h2>
                  <p className="text-[10px] text-gray-500 mt-1">Max Drawdown: <span className="text-rose-400">{backtestData.metrics.buy_hold_max_dd}%</span></p>
                </div>

                <div className="rounded-xl bg-[#141414] border border-[#27272A] p-4 shadow-sm relative overflow-hidden flex flex-col justify-center">
                  <div className={`absolute top-0 right-0 w-24 h-24 rounded-full blur-2xl -mr-8 -mt-8 ${backtestData.metrics.alpha > 0 ? 'bg-emerald-500/10' : 'bg-rose-500/10'}`}></div>
                  <p className="text-xs font-medium text-gray-400 mb-1">AI Alpha (Outperformance)</p>
                  <h2 className={`text-2xl font-bold tracking-tight mt-1 ${backtestData.metrics.alpha > 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {backtestData.metrics.alpha > 0 ? '+' : ''}{backtestData.metrics.alpha.toLocaleString()}%
                  </h2>
                  <p className="text-[10px] text-gray-500 mt-1">Difference in total returns</p>
                </div>
              </div>

              {/* Chart Section */}
              <div className="flex-1 flex flex-col rounded-xl bg-[#141414] border border-[#27272A] p-4 shadow-sm min-h-0">
                <div className="mb-3 shrink-0">
                  <h3 className="text-sm font-bold text-white">Historical Portfolio Value ($)</h3>
                  <p className="text-xs text-gray-500">Starting with $10,000. AI Strategy (Purple) vs Buy & Hold (White).</p>
                </div>
                
                <div className="flex-1 w-full min-h-0">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={backtestData.history} margin={{ top: 5, right: 5, left: 5, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272A" vertical={false} />
                      <XAxis 
                        dataKey="date" 
                        stroke="#71717A" 
                        tick={{fill: '#71717A', fontSize: 10}}
                        tickMargin={8}
                        minTickGap={30}
                      />
                      <YAxis 
                        domain={['auto', 'auto']} 
                        stroke="#71717A" 
                        tick={{fill: '#71717A', fontSize: 10}}
                        tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`}
                        axisLine={false}
                        tickLine={false}
                      />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#27272A', borderColor: '#3F3F46', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                        itemStyle={{ color: '#fff' }}
                        labelStyle={{ color: '#A1A1AA', marginBottom: '4px' }}
                        formatter={(value: any, name: any) => {
                          const numValue = Number(value);
                          if (name === 'ai_strategy') return [`$${numValue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`, 'AI Strategy'];
                          if (name === 'buy_hold') return [`$${numValue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`, 'Buy & Hold'];
                          return [value, name];
                        }}
                      />
                      
                      <Line 
                        type="monotone" 
                        dataKey="buy_hold" 
                        stroke="#FFFFFF" 
                        strokeWidth={1.5}
                        dot={false}
                        activeDot={{ r: 4 }}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="ai_strategy" 
                        stroke="#A855F7" 
                        strokeWidth={2}
                        dot={false}
                        activeDot={{ r: 6, fill: "#A855F7", stroke: "#27272A", strokeWidth: 2 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </>
          ) : (
             <div className="flex-1 flex items-center justify-center text-red-400 text-sm">Failed to run backtest simulation.</div>
          )}
        </div>
      ) : viewMode === "bot" ? (
        /* Multi-Asset Portfolio Bot View */
        <div className="flex flex-col h-full gap-4 min-h-0">
           <div className="flex justify-between items-end shrink-0">
             <div>
               <h2 className="text-xl font-bold text-white flex items-center gap-2"><Briefcase className="text-emerald-500 w-5 h-5"/> Multi-Asset Portfolio Manager</h2>
               <p className="text-xs text-gray-400 mt-1">Live simulation tracking NVDA, TSLA, and S&P 500 in a shared $10,000 cash pool.</p>
             </div>
             <button onClick={forceBotRun} disabled={runningBot} className="bg-emerald-600 hover:bg-emerald-500 text-white px-3 py-1.5 text-sm rounded-lg font-medium shadow-lg transition-colors flex items-center gap-2 disabled:opacity-50">
               {runningBot ? <Activity className="w-3 h-3 animate-spin" /> : <Cpu className="w-3 h-3" />} 
               {runningBot ? 'Running Logic...' : 'Trigger Multi-Asset Cycle'}
             </button>
           </div>
           
           {portfolioLoading ? (
               <div className="flex flex-col items-center justify-center flex-1 text-gray-400">
                 <Activity className="h-8 w-8 animate-spin text-emerald-500 mb-3" />
                 <p className="text-sm">Fetching unified portfolio state...</p>
               </div>
           ) : portfolioData ? (
             <>
               <div className="grid grid-cols-1 md:grid-cols-2 gap-4 shrink-0">
                 <div className="bg-[#141414] border border-emerald-500/20 p-4 rounded-xl shadow-sm flex items-center gap-4">
                   <div className="bg-emerald-500/10 p-3 rounded-full"><Briefcase className="text-emerald-400 w-5 h-5" /></div>
                   <div>
                     <p className="text-emerald-500 text-xs font-medium mb-0.5">Global Portfolio Value</p>
                     <h3 className="text-2xl font-bold text-white">
                        ${portfolioData.ledger.length > 0 ? portfolioData.ledger[0].portfolio_value_after.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits:2}) : portfolioData.cash_balance.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits:2})}
                     </h3>
                   </div>
                 </div>
                 <div className="bg-[#141414] border border-[#27272A] p-4 rounded-xl shadow-sm flex items-center gap-4">
                   <div className="bg-blue-500/10 p-3 rounded-full"><Wallet className="text-blue-400 w-5 h-5" /></div>
                   <div>
                     <p className="text-gray-400 text-xs font-medium mb-0.5">Available Cash (Dry Powder)</p>
                     <h3 className="text-2xl font-bold text-gray-200">${portfolioData.cash_balance.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits:2})}</h3>
                   </div>
                 </div>
               </div>

               {/* Side-by-Side Area */}
               <div className="flex-1 flex gap-4 min-h-0">
                 {/* Current Holdings Table (Left) */}
                 <div className="flex-[1] flex flex-col min-w-0 bg-[#141414] border border-[#27272A] rounded-xl shadow-sm overflow-hidden">
                   <div className="px-4 py-3 border-b border-[#27272A] bg-[#0A0A0B] flex items-center gap-2 shrink-0">
                     <Activity className="w-4 h-4 text-emerald-400" />
                     <h3 className="text-sm font-bold text-white">Live Asset Holdings</h3>
                   </div>
                   <div className="flex-1 overflow-y-auto p-4 min-h-0">
                     {portfolioData.holdings.length > 0 ? (
                        <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
                          {portfolioData.holdings.map((h: any, idx: number) => (
                            <div key={idx} className="bg-[#0A0A0B] border border-[#27272A] p-3 rounded-lg flex flex-col">
                              <p className="text-xs font-bold text-gray-400">{h.ticker}</p>
                              <p className="text-lg font-bold text-emerald-400 mt-0.5">
                                ${(h.value || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                              </p>
                              <div className="mt-2 pt-2 border-t border-[#27272A] flex justify-between items-center text-[10px]">
                                <span className="text-gray-500">Amount:</span>
                                <span className="text-gray-300 font-medium">{h.amount.toFixed(4)} shares</span>
                              </div>
                              <div className="mt-1 flex justify-between items-center text-[10px]">
                                <span className="text-gray-500">Bought at:</span>
                                <span className="text-gray-300 font-medium">${(h.latest_price || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                     ) : (
                       <div className="flex h-full items-center justify-center text-gray-500 text-xs">No assets currently held. 100% Cash.</div>
                     )}
                   </div>
                 </div>

                 {/* Unified Ledger (Right) */}
                 <div className="flex-[1.2] flex flex-col min-w-0 bg-[#141414] border border-[#27272A] rounded-xl shadow-sm overflow-hidden">
                   <div className="px-4 py-3 border-b border-[#27272A] bg-[#0A0A0B] flex items-center gap-2 shrink-0">
                     <History className="w-4 h-4 text-gray-400" />
                     <h3 className="text-sm font-bold text-white">Global Trade Ledger</h3>
                   </div>
                   <div className="flex-1 overflow-y-auto min-h-0">
                     <table className="w-full text-left text-xs">
                       <thead className="bg-[#141414] text-gray-400 border-b border-[#27272A] sticky top-0 z-10">
                         <tr>
                           <th className="px-4 py-3 font-medium whitespace-nowrap">Timestamp</th>
                           <th className="px-4 py-3 font-medium">Asset</th>
                           <th className="px-4 py-3 font-medium">Action</th>
                           <th className="px-4 py-3 font-medium">Shares</th>
                           <th className="px-4 py-3 font-medium whitespace-nowrap">Price</th>
                           <th className="px-4 py-3 font-medium whitespace-nowrap">Cash After</th>
                         </tr>
                       </thead>
                       <tbody className="divide-y divide-white/5">
                         {portfolioData.ledger.length > 0 ? portfolioData.ledger.map((row: any, idx: number) => (
                           <tr key={idx} className="hover:bg-[#27272A]/20 transition-colors">
                             <td className="px-4 py-3 text-gray-300 font-mono text-[10px] whitespace-nowrap">{row.timestamp}</td>
                             <td className="px-4 py-3 text-white font-bold">{row.ticker}</td>
                             <td className="px-4 py-3">
                               <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${row.action === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}`}>
                                 {row.action}
                               </span>
                             </td>
                             <td className="px-4 py-3 text-gray-300">{row.shares_traded.toFixed(4)}</td>
                             <td className="px-4 py-3 text-gray-300">${row.price.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}</td>
                             <td className="px-4 py-3 text-gray-400">${row.cash_after.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}</td>
                           </tr>
                         )) : (
                           <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-500 text-xs">No trades have been executed yet.</td></tr>
                         )}
                       </tbody>
                     </table>
                   </div>
                 </div>
               </div>
             </>
           ) : (
             <div className="text-gray-400 mt-10 text-center text-sm flex-1">Failed to load portfolio.</div>
           )}
        </div>

      ) : (
        /* Scoreboard View */
        <div className="flex flex-col h-full gap-4 min-h-0">
           <div className="flex justify-between items-end shrink-0">
             <div>
               <h2 className="text-xl font-bold text-white flex items-center gap-2">AI Prediction Scoreboard</h2>
               <p className="text-xs text-gray-400 mt-1">Plotting yesterday's prediction against today's actual price to grade the AI.</p>
             </div>
             {predictionsData && predictionsData.mae > 0 && (
                <div className="bg-rose-500/10 border border-rose-500/30 px-3 py-1.5 rounded-lg text-right">
                  <p className="text-[10px] text-rose-400 font-medium">Mean Absolute Error</p>
                  <p className="text-lg font-bold text-rose-500">{predictionsData.mae.toFixed(2)}%</p>
                </div>
             )}
           </div>

           {predictionsLoading ? (
               <div className="flex flex-col items-center justify-center flex-1 text-gray-400">
                 <Activity className="h-8 w-8 animate-spin text-rose-500 mb-3" />
                 <p className="text-sm">Fetching prediction history...</p>
               </div>
           ) : predictionsData && predictionsData.predictions && predictionsData.predictions.length > 0 ? (
             <div className="flex-1 flex flex-col rounded-xl bg-[#141414] border border-[#27272A] p-4 shadow-sm min-h-0">
               <div className="flex-1 w-full min-h-0">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={predictionsData.predictions} margin={{ top: 10, right: 10, left: 5, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272A" vertical={false} />
                      <XAxis 
                        dataKey="timestamp" 
                        stroke="#71717A" 
                        tick={{fill: '#71717A', fontSize: 10}}
                        tickMargin={8}
                        minTickGap={30}
                      />
                      <YAxis 
                        domain={['auto', 'auto']} 
                        stroke="#71717A" 
                        tick={{fill: '#71717A', fontSize: 10}}
                        tickFormatter={(val) => `$${val.toFixed(0)}`}
                        axisLine={false}
                        tickLine={false}
                      />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#27272A', borderColor: '#3F3F46', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                        itemStyle={{ color: '#fff' }}
                        labelStyle={{ color: '#A1A1AA', marginBottom: '4px' }}
                        formatter={(value: any, name: any) => {
                          const numValue = Number(value);
                          if (name === 'predicted_close') return [`$${numValue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`, 'AI Prediction'];
                          if (name === 'actual_close') return [`$${numValue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`, 'Actual Price'];
                          return [value, name];
                        }}
                      />
                      
                      <Line 
                        type="monotone" 
                        dataKey="actual_close" 
                        stroke="#FFFFFF" 
                        strokeWidth={2}
                        dot={{ r: 3 }}
                        activeDot={{ r: 5 }}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="predicted_close" 
                        stroke="#F43F5E" 
                        strokeDasharray="5 5"
                        strokeWidth={2}
                        dot={{ r: 3 }}
                        activeDot={{ r: 5 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
             </div>
           ) : (
              <div className="flex-1 flex items-center justify-center text-gray-500 text-sm">No predictions logged yet. Run the bot cycle to start logging!</div>
           )}
        </div>
      )}
        </div>
      </main>
    </div>
  );
}
