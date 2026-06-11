"use client";

import { useEffect, useState } from "react";
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceArea 
} from "recharts";
import { Activity, TrendingUp, AlertTriangle, ShieldAlert } from "lucide-react";

export default function Dashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedTicker, setSelectedTicker] = useState("^GSPC");

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
  }, [selectedTicker]);

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

  // Regime mapping
  const regimeLabels: Record<number, string> = {
    0: "Bull Market",
    1: "Sideways / Correction",
    2: "Bear Market / Crisis"
  };

  const regimeColors: Record<number, string> = {
    0: "rgba(16, 185, 129, 0.15)", // Green
    1: "rgba(245, 158, 11, 0.15)", // Orange
    2: "rgba(239, 68, 68, 0.15)"   // Red
  };

  const regimeTextColors: Record<number, string> = {
    0: "text-emerald-400",
    1: "text-amber-400",
    2: "text-rose-400"
  };

  // Build contiguous blocks for chart background coloring
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

      {/* Top Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        
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
      
    </div>
  );
}
