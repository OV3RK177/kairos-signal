"use client";
import { useState, useEffect, useRef } from 'react';
import { Activity, Database, Server, Globe, Zap, Cpu, Radio, Lock } from 'lucide-react';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const logEndRef = useRef(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://159.203.91.55:8000';
        
        // 1. Get Stats
        const statsRes = await fetch(`${apiUrl}/stats`);
        const statsData = await statsRes.json();
        setStats(statsData);

        // 2. Get Logs
        const logsRes = await fetch(`${apiUrl}/logs`);
        const logsData = await logsRes.json();
        if (logsData.live_feed) {
          setLogs(logsData.live_feed.slice(-100)); 
        }
        setLoading(false);
      } catch (e) {
        console.error("Connection Error:", e);
        setLoading(true);
      }
    };

    const interval = setInterval(fetchData, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  return (
    <div className="min-h-screen bg-slate-950 text-emerald-500 font-mono p-4 md:p-6">
      
      {/* HEADER */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 border-b border-emerald-900/50 pb-6">
        <div>
          <h1 className="text-4xl md:text-5xl font-black tracking-widest text-white flex items-center gap-4">
            <Globe className={`w-8 h-8 ${loading ? 'text-yellow-500' : 'text-emerald-500 animate-pulse'}`} /> 
            KAIROS
          </h1>
          <div className="flex items-center gap-3 mt-2">
            <span className="text-[10px] bg-emerald-950/50 border border-emerald-900 px-2 py-0.5 rounded text-emerald-400 tracking-widest">
              NET: MAINNET-BETA
            </span>
            <span className="text-[10px] text-slate-500 tracking-widest">
              LATENCY: {loading ? '---' : '14ms'}
            </span>
          </div>
        </div>

        <div className="mt-4 md:mt-0 flex gap-4">
          <StatusBadge label="SWARM" status={loading ? "SEARCHING" : "HUNTING"} color={loading ? "yellow" : "green"} />
          <StatusBadge label="VAULT" status="SECURE" color="blue" />
          <StatusBadge label="AWS" status="ARCHIVING" color="purple" />
        </div>
      </header>

      {/* METRICS */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <MetricCard 
          icon={<Database className="w-5 h-5" />} 
          label="Total Intelligence" 
          value={stats ? parseInt(stats.estimated_data_points).toLocaleString() : "---"}
          sub="DATA POINTS INDEXED"
          color="text-white"
        />
        <MetricCard 
          icon={<Zap className="w-5 h-5" />} 
          label="Ingest Velocity" 
          value="3.6M"
          sub="POINTS / MINUTE"
          color="text-yellow-400"
        />
        <MetricCard 
          icon={<Server className="w-5 h-5" />} 
          label="Active Shards" 
          value={stats ? parseInt(stats.shard_count).toLocaleString() : "---"}
          sub="PARQUET FILES"
          color="text-blue-400"
        />
         <MetricCard 
          icon={<Cpu className="w-5 h-5" />} 
          label="Active Agents" 
          value="143"
          sub="GLOBAL COLLECTORS"
          color="text-purple-400"
        />
      </div>

      {/* TERMINAL */}
      <div className="border border-emerald-900/50 rounded-lg bg-black overflow-hidden shadow-2xl shadow-emerald-900/10 relative">
        <div className="bg-emerald-950/30 p-3 border-b border-emerald-900/50 flex items-center justify-between backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <Activity className="w-4 h-4 text-emerald-400" />
            <span className="text-xs font-bold tracking-widest text-emerald-400">LIVE INGESTION FEED // PORT 8000</span>
          </div>
          <div className="flex gap-4 text-[10px] font-bold tracking-wider opacity-70">
             <span className="text-yellow-400 flex items-center gap-1">● SLOT</span>
             <span className="text-blue-400 flex items-center gap-1">● TRADE</span>
             <span className="text-purple-400 flex items-center gap-1">● SKY</span>
          </div>
        </div>
        
        <div className="p-4 h-[500px] overflow-y-auto font-mono text-xs space-y-1 bg-black/95 custom-scrollbar">
          {logs.map((log, i) => (
            <div key={i} className="flex items-center border-b border-emerald-900/20 pb-1 mb-1 last:border-0 hover:bg-emerald-900/10 transition-colors group">
              <span className="text-slate-600 w-24 shrink-0 group-hover:text-slate-400 transition-colors">
                [{new Date().toLocaleTimeString()}]
              </span>
              <span className="break-all tracking-tight">
                {formatLog(log)}
              </span>
            </div>
          ))}
          {logs.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-emerald-900 space-y-4">
              <Radio className="w-12 h-12 animate-ping" />
              <span className="animate-pulse tracking-widest">ESTABLISHING SECURE UPLINK...</span>
            </div>
          )}
          <div ref={logEndRef} />
        </div>
      </div>
    </div>
  );
}

function MetricCard({ icon, label, value, sub, color }) {
  return (
    <div className="bg-emerald-950/20 border border-emerald-900/50 p-5 rounded hover:border-emerald-500/50 hover:bg-emerald-900/30 transition-all group cursor-crosshair">
      <div className="flex items-center gap-2 mb-3 text-emerald-600/80 text-[10px] uppercase font-bold tracking-widest group-hover:text-emerald-400">
        {icon} {label}
      </div>
      <div className={`text-3xl md:text-4xl font-black tracking-tighter ${color} drop-shadow-lg`}>
        {value}
      </div>
      <div className="text-[10px] text-slate-500 mt-2 font-bold tracking-wider flex items-center gap-1">
        {sub}
      </div>
    </div>
  );
}

function StatusBadge({ label, status, color }) {
  const colors = {
    green: "text-emerald-400",
    blue: "text-blue-400",
    yellow: "text-yellow-400",
    purple: "text-purple-400"
  };
  return (
    <div className="hidden md:flex flex-col items-end">
      <span className="text-[9px] text-slate-600 uppercase tracking-widest font-bold">{label}</span>
      <div className="flex items-center gap-2">
        <div className={`w-1.5 h-1.5 rounded-full ${color === 'green' ? 'bg-emerald-500' : color === 'blue' ? 'bg-blue-500' : 'bg-yellow-500'} animate-pulse`}></div>
        <span className={`text-xs font-bold ${colors[color]}`}>{status}</span>
      </div>
    </div>
  );
}

function formatLog(text) {
  if (text.includes("SLOT")) return <span className="text-yellow-300 font-bold drop-shadow-sm">{text}</span>;
  if (text.includes("TRADE")) return <span className="text-blue-300 font-bold drop-shadow-sm">{text}</span>;
  if (text.includes("WINGBITS")) return <span className="text-purple-300 font-bold drop-shadow-sm">{text}</span>;
  if (text.includes("PRESSURE")) return <span className="text-red-400 font-bold">{text}</span>;
  if (text.includes("CONNECTED")) return <span className="text-white font-bold bg-emerald-900/50 px-2 py-0.5 rounded">{text}</span>;
  return <span className="text-emerald-400/80">{text}</span>;
}
