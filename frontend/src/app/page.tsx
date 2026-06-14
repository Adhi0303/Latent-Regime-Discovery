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

  const [triggerRun, setTriggerRun] = useState(false);
  const [runningBot, setRunningBot] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetch(`http://localhost:8000/api/predict?ticker=${selectedTicker}&period=5y`)
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
    fetch(`http://localhost:8000/api/sentiment?ticker=${selectedTicker}`)
      .then((res) => res.json())
      .then((json) => {
        setSentimentData(json);
        setSentimentLoading(false);
      });
      
    // Fetch forecast
    setForecastLoading(true);
    fetch(`http://localhost:8000/api/forecast?ticker=${selectedTicker}`)
      .then((res) => res.json())
      .then((json) => {
        setForecastData(json);
        setForecastLoading(false);
      });
      
    // Fetch backtest
    setBacktestLoading(true);
    fetch(`http://localhost:8000/api/backtest?ticker=${selectedTicker}`)
      .then((res) => res.json())
      .then((json) => {
        setBacktestData(json);
        setBacktestLoading(false);
      });

    // Fetch Global Portfolio
    setPortfolioLoading(true);
    fetch(`http://localhost:8000/api/bot/portfolio`)
      .then((res) => res.json())
      .then((json) => {
        setPortfolioData(json);
        setPortfolioLoading(false);
      });

    // Fetch Predictions Scoreboard
    setPredictionsLoading(true);
    fetch(`http://localhost:8000/api/bot/predictions?ticker=${selectedTicker}`)
      .then((res) => res.json())
      .then((json) => {
        setPredictionsData(json);
        setPredictionsLoading(false);
      });

  }, [selectedTicker, triggerRun]);

  const forceBotRun = () => {
    setRunningBot(true);
    fetch(`http://localhost:8000/api/bot/run`, { method: 'POST' })
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

  if (!data) return <div className="text-white">Error loading data.</div>;

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

  const blocks = [];
  if (data.history && data.history.length > 0) {
    let currentRegime = data.history[0].regime;
    let startIdx = 0;

    for (let i = 1; i < data.history.length; i++) {
      if (data.history[i].regime !== currentRegime) {
        blocks.push({
          start: data.history[startIdx].date,
          end: data.history[i - 1].date,
          regime: currentRegime
        });
        currentRegime = data.history[i].regime;
        startIdx = i;
      }
    }
    blocks.push({
      start: data.history[startIdx].date,
      end: data.history[data.history.length - 1].date,
      regime: currentRegime
    });
  }

  const currentRegime = data.current_regime;

  return (
    <div className="min-h-screen bg-[#0E0E10] text-[#e0e0e0] p-8 font-sans selection:bg-blue-500/30">
      <header className="mb-10 flex items-center justify-between border-b border-white/5 pb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Latent Regime Discovery</h1>
          <p className="text-sm text-gray-400 mt-1">Autonomous Quantitative Strategy Dashboard</p>
        </div>
        <div className="flex items-center gap-4">
          <select 
            className="bg-[#18181B] border border-white/10 text-white text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2 outline-none cursor-pointer"
            value={selectedTicker}
            onChange={(e) => setSelectedTicker(e.target.value)}
          >
            <option value="^GSPC">S&P 500 (^GSPC)</option>
            <option value="BTC-USD">Bitcoin (BTC-USD)</option>
            <option value="TSLA">Tesla (TSLA)</option>
            <option value="NVDA">Nvidia (NVDA)</option>
            <option value="BRK-B">Berkshire Hathaway (BRK-B)</option>
          </select>
          <div className="flex items-center gap-2 rounded-full bg-blue-500/10 px-4 py-2 border border-blue-500/20">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-500"></span>
            </span>
            <span className="text-sm font-medium text-blue-400 hidden sm:inline">Live API Connection</span>
          </div>
        </div>
      </header>

      {/* View Toggle */}
      <div className="flex gap-4 mb-8 border-b border-white/10 pb-4">
        <button 
          className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${viewMode === 'dashboard' ? 'bg-blue-500 text-white' : 'bg-transparent text-gray-400 hover:text-white hover:bg-white/5'}`}
          onClick={() => setViewMode("dashboard")}
        >
          Live Dashboard
        </button>
        <button 
          className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${viewMode === 'backtest' ? 'bg-purple-500 text-white' : 'bg-transparent text-gray-400 hover:text-white hover:bg-white/5'}`}
          onClick={() => setViewMode("backtest")}
        >
          Strategy Simulator
        </button>
        <button 
          className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${viewMode === 'bot' ? 'bg-emerald-600 text-white' : 'bg-transparent text-gray-400 hover:text-white hover:bg-white/5'}`}
          onClick={() => setViewMode("bot")}
        >
          Multi-Asset Portfolio Bot
        </button>
        <button 
          className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${viewMode === 'scoreboard' ? 'bg-rose-600 text-white' : 'bg-transparent text-gray-400 hover:text-white hover:bg-white/5'}`}
          onClick={() => setViewMode("scoreboard")}
        >
          AI Scoreboard
        </button>
      </div>

      {viewMode === "dashboard" ? (
        <>
          {/* Top Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
            
            {/* Card 1: Asset / Price */}
            <div className="rounded-2xl bg-[#18181B] border border-white/5 p-6 shadow-xl relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 rounded-full blur-3xl -mr-10 -mt-10 transition-all group-hover:bg-blue-500/10"></div>
              <p className="text-sm font-medium text-gray-400 mb-1">Asset Tracked</p>
              <h2 className="text-4xl font-bold text-white tracking-tight">{data.ticker}</h2>
              <div className="mt-4 flex items-baseline gap-2">
                <span className="text-2xl font-semibold text-gray-200">
                  ${data.latest_close.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
                <span className="text-xs font-medium text-gray-500">Close Price</span>
              </div>
            </div>

            {/* Card 1.5: LSTM Forecast */}
            <div className="rounded-2xl bg-[#18181B] border border-white/5 p-6 shadow-xl relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/5 rounded-full blur-3xl -mr-10 -mt-10 transition-all group-hover:bg-purple-500/10"></div>
              <p className="text-sm font-medium text-gray-400 mb-1">AI Price Forecast (Tomorrow)</p>
              {forecastLoading ? (
                <div className="flex items-center gap-2 mt-4 text-gray-400">
                  <span className="animate-spin h-5 w-5 border-2 border-purple-500 border-t-transparent rounded-full"></span>
                  <span>Running LSTM...</span>
                </div>
              ) : forecastData ? (
                <>
                  <h2 className="text-4xl font-bold tracking-tight mt-1" style={{ color: forecastData.predicted_pct_change > 0 ? '#34d399' : '#fb7185' }}>
                    ${forecastData.final_prediction.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </h2>
                  <div className="mt-4 flex items-baseline gap-2">
                    <span className={`text-sm font-semibold ${forecastData.predicted_pct_change > 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {forecastData.predicted_pct_change > 0 ? '+' : ''}{forecastData.predicted_pct_change.toFixed(2)}%
                    </span>
                    <span className="text-xs font-medium text-gray-500">from today</span>
                  </div>
                </>
              ) : (
                <p className="text-sm text-rose-400 mt-4">Failed to load forecast.</p>
              )}
            </div>

            {/* Card 2: Current Regime */}
            <div className="rounded-2xl bg-[#18181B] border border-white/5 p-6 shadow-xl relative overflow-hidden">
              <div className={`absolute top-0 right-0 w-32 h-32 rounded-full blur-3xl -mr-10 -mt-10 ${currentRegime === 0 ? 'bg-emerald-500/10' : currentRegime === 1 ? 'bg-amber-500/10' : 'bg-rose-500/10'}`}></div>
              <p className="text-sm font-medium text-gray-400 mb-1">AI Detected Regime</p>
              <h2 className={`text-3xl font-bold tracking-tight ${regimeTextColors[currentRegime]}`}>
                {regimeLabels[currentRegime]}
              </h2>
              <div className="mt-4 flex items-center gap-2">
                {currentRegime === 0 && <TrendingUp className="w-5 h-5 text-emerald-400" />}
                {currentRegime === 1 && <AlertTriangle className="w-5 h-5 text-amber-400" />}
                {currentRegime === 2 && <ShieldAlert className="w-5 h-5 text-rose-400" />}
                <span className="text-sm text-gray-400">Updated: {data.latest_date}</span>
              </div>
            </div>

            {/* Card 3: Probabilities */}
            <div className="rounded-2xl bg-[#18181B] border border-white/5 p-6 shadow-xl flex flex-col justify-between">
              <p className="text-sm font-medium text-gray-400 mb-4">Regime Probabilities</p>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-emerald-400 font-medium">Bull</span>
                    <span className="text-gray-300">{(data.probabilities["0"] * 100).toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-[#27272A] rounded-full h-1.5">
                    <div className="bg-emerald-500 h-1.5 rounded-full" style={{ width: `${data.probabilities["0"] * 100}%` }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-amber-400 font-medium">Sideways</span>
                    <span className="text-gray-300">{(data.probabilities["1"] * 100).toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-[#27272A] rounded-full h-1.5">
                    <div className="bg-amber-500 h-1.5 rounded-full" style={{ width: `${data.probabilities["1"] * 100}%` }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-rose-400 font-medium">Bear</span>
                    <span className="text-gray-300">{(data.probabilities["2"] * 100).toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-[#27272A] rounded-full h-1.5">
                    <div className="bg-rose-500 h-1.5 rounded-full" style={{ width: `${data.probabilities["2"] * 100}%` }}></div>
                  </div>
                </div>
              </div>
            </div>

          </div>

          {/* Macro Sentiment Section */}
          <div className="rounded-2xl bg-[#18181B] border border-white/5 p-6 shadow-xl mb-10">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <span className="bg-blue-500/20 text-blue-400 p-1.5 rounded-lg"><Activity className="w-4 h-4" /></span>
                  Macro Analyst Sentiment
                </h3>
                <p className="text-sm text-gray-500 mt-1">Live news analysis scored by FinBERT LLM</p>
              </div>
              {sentimentLoading ? (
                <div className="flex items-center gap-2 text-gray-400 text-sm">
                  <span className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></span>
                  Reading headlines...
                </div>
              ) : sentimentData ? (
                <div className="text-right">
                  <div className="text-3xl font-bold" style={{ color: sentimentData.macro_score > 0 ? '#34d399' : sentimentData.macro_score < 0 ? '#fb7185' : '#fbbf24' }}>
                    {sentimentData.macro_score > 0 ? '+' : ''}{sentimentData.macro_score.toFixed(2)}
                  </div>
                  <div className="text-xs text-gray-500 font-medium">Aggregated Score</div>
                </div>
              ) : null}
            </div>

            {sentimentData && sentimentData.news && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {sentimentData.news.map((n: any, i: number) => (
                  <div key={i} className="flex items-start gap-3 p-4 rounded-xl bg-[#27272A]/30 border border-white/5 hover:bg-[#27272A]/60 transition-colors">
                    <div className={`mt-1 flex-shrink-0 w-2.5 h-2.5 rounded-full ${n.sentiment_label === 'positive' ? 'bg-emerald-500' : n.sentiment_label === 'negative' ? 'bg-rose-500' : 'bg-amber-500'}`}></div>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-sm font-medium text-gray-200 line-clamp-2">{n.title}</h4>
                      <div className="flex justify-between items-center mt-2">
                        <p className="text-xs text-gray-500">{n.publisher}</p>
                        <div className="text-xs font-mono font-medium" style={{ color: n.sentiment_score > 0 ? '#34d399' : n.sentiment_score < 0 ? '#fb7185' : '#fbbf24' }}>
                          {n.sentiment_score > 0 ? '+' : ''}{n.sentiment_score.toFixed(2)}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Chart Section */}
          <div className="rounded-2xl bg-[#18181B] border border-white/5 p-6 shadow-xl">
            <div className="mb-6">
              <h3 className="text-lg font-bold text-white">Historical Regime Map</h3>
              <p className="text-sm text-gray-500">{data.ticker} Price overlaid with AI-detected hidden states.</p>
            </div>
            
            <div className="h-[500px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data.history} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#27272A" vertical={false} />
                  <XAxis 
                    dataKey="date" 
                    stroke="#71717A" 
                    tick={{fill: '#71717A', fontSize: 12}}
                    tickMargin={10}
                    minTickGap={50}
                  />
                  <YAxis 
                    domain={['auto', 'auto']} 
                    stroke="#71717A" 
                    tick={{fill: '#71717A', fontSize: 12}}
                    tickFormatter={(val) => `$${val}`}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#27272A', borderColor: '#3F3F46', borderRadius: '8px', color: '#fff' }}
                    itemStyle={{ color: '#60A5FA' }}
                    labelStyle={{ color: '#A1A1AA', marginBottom: '4px' }}
                    formatter={(value: number) => [`$${value.toFixed(2)}`, 'Price']}
                  />
                  
                  {/* Draw Regime Backgrounds */}
                  {blocks.map((b, idx) => (
                    <ReferenceArea 
                      key={idx} 
                      x1={b.start} 
                      x2={b.end} 
                      fill={regimeColors[b.regime]} 
                      fillOpacity={1}
                      strokeOpacity={0}
                    />
                  ))}

                  <Line 
                    type="monotone" 
                    dataKey="close" 
                    stroke="#FFFFFF" 
                    strokeWidth={1.5}
                    dot={false}
                    activeDot={{ r: 6, fill: "#60A5FA", stroke: "#27272A", strokeWidth: 2 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      ) : viewMode === "backtest" ? (
        /* Backtest Simulator View */
        <div className="space-y-6">
          {backtestLoading ? (
             <div className="flex flex-col items-center justify-center py-20 text-gray-400">
               <Activity className="h-10 w-10 animate-spin text-purple-500 mb-4" />
               <p>Simulating 20 years of historical trading...</p>
             </div>
          ) : backtestData && backtestData.metrics ? (
            <>
              {/* KPIs */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="rounded-2xl bg-[#18181B] border border-white/5 p-6 shadow-xl relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/10 rounded-full blur-3xl -mr-10 -mt-10"></div>
                  <p className="text-sm font-medium text-gray-400 mb-1">AI Strategy Total Return</p>
                  <h2 className="text-4xl font-bold tracking-tight text-white mt-2">
                    {backtestData.metrics.ai_return > 0 ? '+' : ''}{backtestData.metrics.ai_return.toLocaleString()}%
                  </h2>
                  <p className="text-sm text-gray-500 mt-2">Max Drawdown: <span className="text-rose-400">{backtestData.metrics.ai_max_dd}%</span></p>
                </div>
                
                <div className="rounded-2xl bg-[#18181B] border border-white/5 p-6 shadow-xl relative overflow-hidden">
                  <p className="text-sm font-medium text-gray-400 mb-1">Buy & Hold Return</p>
                  <h2 className="text-4xl font-bold tracking-tight text-gray-300 mt-2">
                    {backtestData.metrics.buy_hold_return > 0 ? '+' : ''}{backtestData.metrics.buy_hold_return.toLocaleString()}%
                  </h2>
                  <p className="text-sm text-gray-500 mt-2">Max Drawdown: <span className="text-rose-400">{backtestData.metrics.buy_hold_max_dd}%</span></p>
                </div>

                <div className="rounded-2xl bg-[#18181B] border border-white/5 p-6 shadow-xl relative overflow-hidden">
                  <div className={`absolute top-0 right-0 w-32 h-32 rounded-full blur-3xl -mr-10 -mt-10 ${backtestData.metrics.alpha > 0 ? 'bg-emerald-500/10' : 'bg-rose-500/10'}`}></div>
                  <p className="text-sm font-medium text-gray-400 mb-1">AI Alpha (Outperformance)</p>
                  <h2 className={`text-4xl font-bold tracking-tight mt-2 ${backtestData.metrics.alpha > 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {backtestData.metrics.alpha > 0 ? '+' : ''}{backtestData.metrics.alpha.toLocaleString()}%
                  </h2>
                  <p className="text-sm text-gray-500 mt-2">Difference in total returns</p>
                </div>
              </div>

              {/* Chart Section */}
              <div className="rounded-2xl bg-[#18181B] border border-white/5 p-6 shadow-xl">
                <div className="mb-6">
                  <h3 className="text-lg font-bold text-white">Historical Portfolio Value ($)</h3>
                  <p className="text-sm text-gray-500">Starting with $10,000. AI Strategy (Purple) vs Buy & Hold (White).</p>
                </div>
                
                <div className="h-[500px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={backtestData.history} margin={{ top: 10, right: 10, left: 20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272A" vertical={false} />
                      <XAxis 
                        dataKey="date" 
                        stroke="#71717A" 
                        tick={{fill: '#71717A', fontSize: 12}}
                        tickMargin={10}
                        minTickGap={50}
                      />
                      <YAxis 
                        domain={['auto', 'auto']} 
                        stroke="#71717A" 
                        tick={{fill: '#71717A', fontSize: 12}}
                        tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`}
                        axisLine={false}
                        tickLine={false}
                      />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#27272A', borderColor: '#3F3F46', borderRadius: '8px', color: '#fff' }}
                        itemStyle={{ color: '#fff' }}
                        labelStyle={{ color: '#A1A1AA', marginBottom: '4px' }}
                        formatter={(value: number, name: string) => {
                          if (name === 'ai_strategy') return [`$${value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`, 'AI Strategy'];
                          if (name === 'buy_hold') return [`$${value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`, 'Buy & Hold'];
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
             <div className="text-red-400">Failed to run backtest simulation.</div>
          )}
        </div>
      ) : viewMode === "bot" ? (
        /* Multi-Asset Portfolio Bot View */
        <div className="space-y-6">
           <div className="flex justify-between items-end mb-6">
             <div>
               <h2 className="text-2xl font-bold text-white flex items-center gap-2"><Briefcase className="text-emerald-500"/> Multi-Asset Portfolio Manager</h2>
               <p className="text-gray-400 mt-1">Live simulation tracking NVDA, TSLA, and S&P 500 in a shared $10,000 cash pool.</p>
             </div>
             <button onClick={forceBotRun} disabled={runningBot} className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg font-medium shadow-lg transition-colors flex items-center gap-2 disabled:opacity-50">
               {runningBot ? <Activity className="w-4 h-4 animate-spin" /> : <Cpu className="w-4 h-4" />} 
               {runningBot ? 'Running Logic...' : 'Trigger Multi-Asset Cycle'}
             </button>
           </div>
           
           {portfolioLoading ? (
               <div className="flex flex-col items-center justify-center py-20 text-gray-400">
                 <Activity className="h-10 w-10 animate-spin text-emerald-500 mb-4" />
                 <p>Fetching unified portfolio state...</p>
               </div>
           ) : portfolioData ? (
             <>
               <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                 <div className="bg-[#18181B] border border-emerald-500/20 p-6 rounded-2xl shadow-xl flex items-center gap-4">
                   <div className="bg-emerald-500/10 p-4 rounded-full"><Briefcase className="text-emerald-400 w-8 h-8" /></div>
                   <div>
                     <p className="text-emerald-500 text-sm font-medium mb-1">Global Portfolio Value</p>
                     <h3 className="text-4xl font-bold text-white">
                        {/* We don't have total live value returned directly from the API endpoint easily without hitting yfinance again. 
                            The last ledger entry has portfolio_value_after. If no ledger, it's just cash. */}
                        ${portfolioData.ledger.length > 0 ? portfolioData.ledger[0].portfolio_value_after.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits:2}) : portfolioData.cash_balance.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits:2})}
                     </h3>
                   </div>
                 </div>
                 <div className="bg-[#18181B] border border-white/5 p-6 rounded-2xl shadow-xl flex items-center gap-4">
                   <div className="bg-blue-500/10 p-4 rounded-full"><Wallet className="text-blue-400 w-8 h-8" /></div>
                   <div>
                     <p className="text-gray-400 text-sm font-medium mb-1">Available Cash (Dry Powder)</p>
                     <h3 className="text-3xl font-bold text-gray-200">${portfolioData.cash_balance.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits:2})}</h3>
                   </div>
                 </div>
               </div>

               {/* Current Holdings Table */}
               <div className="bg-[#18181B] border border-white/5 rounded-2xl shadow-xl overflow-hidden mb-8">
                 <div className="px-6 py-4 border-b border-white/5 bg-[#27272A]/30 flex items-center gap-2">
                   <Activity className="w-4 h-4 text-emerald-400" />
                   <h3 className="font-bold text-white">Live Asset Holdings</h3>
                 </div>
                 {portfolioData.holdings.length > 0 ? (
                   <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-6">
                     {portfolioData.holdings.map((h: any, idx: number) => (
                       <div key={idx} className="bg-[#27272A]/30 border border-white/5 p-4 rounded-xl">
                         <p className="text-sm text-gray-400">{h.ticker}</p>
                         <p className="text-xl font-bold text-white mt-1">{h.amount.toFixed(4)} <span className="text-sm font-normal text-gray-500">shares</span></p>
                       </div>
                     ))}
                   </div>
                 ) : (
                   <div className="p-6 text-gray-500 text-center text-sm">No assets currently held. 100% Cash.</div>
                 )}
               </div>

               {/* Unified Ledger */}
               <div className="bg-[#18181B] border border-white/5 rounded-2xl shadow-xl overflow-hidden">
                 <div className="px-6 py-4 border-b border-white/5 bg-[#27272A]/30 flex items-center gap-2">
                   <History className="w-4 h-4 text-gray-400" />
                   <h3 className="font-bold text-white">Global Trade Ledger</h3>
                 </div>
                 <div className="overflow-x-auto max-h-[400px]">
                   <table className="w-full text-left text-sm">
                     <thead className="bg-[#18181B] text-gray-400 border-b border-white/10 sticky top-0">
                       <tr>
                         <th className="px-6 py-4 font-medium">Timestamp</th>
                         <th className="px-6 py-4 font-medium">Asset</th>
                         <th className="px-6 py-4 font-medium">Action</th>
                         <th className="px-6 py-4 font-medium">Shares</th>
                         <th className="px-6 py-4 font-medium">Price</th>
                         <th className="px-6 py-4 font-medium">Cash After</th>
                       </tr>
                     </thead>
                     <tbody className="divide-y divide-white/5">
                       {portfolioData.ledger.length > 0 ? portfolioData.ledger.map((row: any, idx: number) => (
                         <tr key={idx} className="hover:bg-[#27272A]/20 transition-colors">
                           <td className="px-6 py-4 text-gray-300 font-mono text-xs">{row.timestamp}</td>
                           <td className="px-6 py-4 text-white font-bold">{row.ticker}</td>
                           <td className="px-6 py-4">
                             <span className={`px-2.5 py-1 rounded-md text-xs font-bold ${row.action === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}`}>
                               {row.action}
                             </span>
                           </td>
                           <td className="px-6 py-4 text-gray-300">{row.shares_traded.toFixed(4)}</td>
                           <td className="px-6 py-4 text-gray-300">${row.price.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}</td>
                           <td className="px-6 py-4 text-gray-400">${row.cash_after.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}</td>
                         </tr>
                       )) : (
                         <tr><td colSpan={6} className="px-6 py-8 text-center text-gray-500">No trades have been executed yet.</td></tr>
                       )}
                     </tbody>
                   </table>
                 </div>
               </div>
             </>
           ) : (
             <div className="text-gray-400 mt-10 text-center">Failed to load portfolio.</div>
           )}
        </div>
      ) : (
        /* Scoreboard View */
        <div className="space-y-6">
           <div className="flex justify-between items-end mb-6">
             <div>
               <h2 className="text-2xl font-bold text-white flex items-center gap-2">AI Prediction Scoreboard</h2>
               <p className="text-gray-400 mt-1">Plotting yesterday's prediction against today's actual price to grade the AI.</p>
             </div>
             {predictionsData && predictionsData.mae > 0 && (
                <div className="bg-rose-500/10 border border-rose-500/30 px-4 py-2 rounded-lg text-right">
                  <p className="text-xs text-rose-400 font-medium">Mean Absolute Error (MAE)</p>
                  <p className="text-2xl font-bold text-rose-500">{predictionsData.mae.toFixed(2)}%</p>
                </div>
             )}
           </div>

           {predictionsLoading ? (
               <div className="flex flex-col items-center justify-center py-20 text-gray-400">
                 <Activity className="h-10 w-10 animate-spin text-rose-500 mb-4" />
                 <p>Fetching prediction history...</p>
               </div>
           ) : predictionsData && predictionsData.predictions && predictionsData.predictions.length > 0 ? (
             <div className="rounded-2xl bg-[#18181B] border border-white/5 p-6 shadow-xl">
               <div className="h-[500px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={predictionsData.predictions} margin={{ top: 10, right: 10, left: 20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272A" vertical={false} />
                      <XAxis 
                        dataKey="timestamp" 
                        stroke="#71717A" 
                        tick={{fill: '#71717A', fontSize: 12}}
                        tickMargin={10}
                        minTickGap={30}
                      />
                      <YAxis 
                        domain={['auto', 'auto']} 
                        stroke="#71717A" 
                        tick={{fill: '#71717A', fontSize: 12}}
                        tickFormatter={(val) => `$${val.toFixed(0)}`}
                        axisLine={false}
                        tickLine={false}
                      />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#27272A', borderColor: '#3F3F46', borderRadius: '8px', color: '#fff' }}
                        itemStyle={{ color: '#fff' }}
                        labelStyle={{ color: '#A1A1AA', marginBottom: '4px' }}
                        formatter={(value: number, name: string) => {
                          if (name === 'predicted_close') return [`$${value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`, 'AI Prediction'];
                          if (name === 'actual_close') return [`$${value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`, 'Actual Price'];
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
              <div className="text-gray-400 mt-10 text-center">No predictions logged yet. Run the bot cycle to start logging!</div>
           )}
        </div>
      )}
      
    </div>
  );
}
