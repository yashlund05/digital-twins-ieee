import React from 'react';
import MetricChip from '../ui/MetricChip';
import LiquidGlassCard from '../ui/LiquidGlassCard';
import LiquidChromeLogo from '../canvas/LiquidChromeLogo';
import { CANONICAL_BENCHMARKS, MODEL_PERFORMANCES } from '../../data/digitalTwinData';
import { ShieldCheck, Zap, Activity, Clock, CheckCircle2 } from 'lucide-react';

export const ExecutiveDashboard: React.FC = () => {
  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Hero Section with Liquid Chrome Logo */}
      <LiquidGlassCard elevated className="overflow-hidden p-8">
        <div className="flex flex-col lg:flex-row items-center justify-between gap-8">
          <div className="space-y-4 max-w-2xl text-center lg:text-left">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full liquid-glass text-xs font-mono text-cyan-300 border border-cyan-500/30">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
              CYBER-PHYSICAL DISTRIBUTION FEEDER DIGITAL TWIN
            </div>
            <h1 className="text-3xl md:text-5xl font-black tracking-tight text-white leading-tight">
              Synchronization Staleness & <br />
              <span className="text-gradient-cyan">Unsupervised Anomaly Detection</span>
            </h1>
            <p className="text-sm md:text-base text-slate-300 leading-relaxed">
              Controlled experimental quantification of Age-of-Information (AoI) staleness on joint short-term load estimation and residual-driven anomaly detection in an OpenDSS IEEE 33-bus benchmark feeder.
            </p>
            <div className="pt-2 flex flex-wrap gap-3 justify-center lg:justify-start">
              <span className="px-3 py-1 rounded-full text-xs font-mono bg-white/5 border border-white/10 text-slate-300">
                Author: <strong className="text-white">Ayush</strong>
              </span>
              <span className="px-3 py-1 rounded-full text-xs font-mono bg-white/5 border border-white/10 text-slate-300">
                Benchmark: IEEE 33-Bus + Pecan Street
              </span>
              <span className="px-3 py-1 rounded-full text-xs font-mono bg-white/5 border border-white/10 text-slate-300">
                Statistical Rigor: N=5 Seeds (120 Conditions)
              </span>
            </div>
          </div>

          <div className="flex flex-col items-center">
            <LiquidChromeLogo size={200} />
            <span className="mt-3 text-xs font-mono text-slate-400 tracking-wider">
              REAL-TIME WEBGL SIMPLEX ENGINE
            </span>
          </div>
        </div>
      </LiquidGlassCard>

      {/* 5 Canonical Benchmark Metric Chips */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricChip
          label="Residual LSTM-AE F1"
          value={CANONICAL_BENCHMARKS.residualLSTMF1.toFixed(4)}
          subtext="Frozen E4 Benchmark Peak"
          badge="CANONICAL"
          badgeColor="cyan"
          icon={<ShieldCheck className="w-4 h-4" />}
        />
        <MetricChip
          label="Detection Gain"
          value={`+${CANONICAL_BENCHMARKS.detectionGainPercent.toFixed(1)}%`}
          subtext="vs Raw Sensor Baseline"
          badge="+81.6% GAIN"
          badgeColor="emerald"
          icon={<Zap className="w-4 h-4" />}
        />
        <MetricChip
          label="Forecaster MAPE"
          value="8.95%"
          subtext="Residual Generator Baseline"
          badge="PROPOSED"
          badgeColor="violet"
          icon={<Activity className="w-4 h-4" />}
        />
        <MetricChip
          label="Critical AoI Boundary"
          value="≤ 10.0 s"
          subtext="F1 Inflection Change Point"
          badge="AoI* LIMIT"
          badgeColor="amber"
          icon={<Clock className="w-4 h-4" />}
        />
        <MetricChip
          label="Multi-Seed Power"
          value={CANONICAL_BENCHMARKS.seedConditions}
          unit="runs"
          subtext="5 Seeds × 24 Grid Points"
          badge="VERIFIED"
          badgeColor="emerald"
          icon={<CheckCircle2 className="w-4 h-4" />}
        />
      </div>

      {/* Architectural Flow & Forecaster Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* End-to-End Pipeline Card */}
        <LiquidGlassCard className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between border-b border-white/10 pb-3">
            <h3 className="font-bold text-base text-white flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
              Cyber-Physical Digital Twin Architecture
            </h3>
            <span className="text-xs font-mono text-slate-400">IEEE TSG Pipeline</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2 text-xs">
            <div className="p-4 rounded-2xl bg-white/5 border border-white/10 space-y-2">
              <div className="font-mono text-cyan-300 font-bold uppercase tracking-wider text-[11px]">
                1. Physical Layer
              </div>
              <p className="text-slate-300 leading-relaxed">
                IEEE 33-bus feeder simulation in OpenDSS, driven by 15-minute Pecan Street residential demand profiles.
              </p>
            </div>
            <div className="p-4 rounded-2xl bg-white/5 border border-white/10 space-y-2">
              <div className="font-mono text-violet-300 font-bold uppercase tracking-wider text-[11px]">
                2. Cyber Network
              </div>
              <p className="text-slate-300 leading-relaxed">
                Zero-order-hold staleness generator with delay parameter &Delta;t &in; [0, 300]s and packet drops P &in; [0, 0.20].
              </p>
            </div>
            <div className="p-4 rounded-2xl bg-white/5 border border-white/10 space-y-2">
              <div className="font-mono text-emerald-300 font-bold uppercase tracking-wider text-[11px]">
                3. Twin Analytics
              </div>
              <p className="text-slate-300 leading-relaxed">
                Physics-informed state estimation produces residual vector r_t = y_t - y&#770;_t, fed to LSTM-Autoencoder.
              </p>
            </div>
          </div>
        </LiquidGlassCard>

        {/* Forecaster Baseline Comparison */}
        <LiquidGlassCard className="lg:col-span-5 space-y-4">
          <div className="flex items-center justify-between border-b border-white/10 pb-3">
            <h3 className="font-bold text-base text-white">Forecaster Model Benchmarks</h3>
            <span className="text-xs font-mono text-slate-400">Mean Absolute % Error</span>
          </div>

          <div className="space-y-3 pt-1">
            {MODEL_PERFORMANCES.map((m) => (
              <div
                key={m.name}
                className="flex items-center justify-between p-3 rounded-2xl bg-white/5 border border-white/5 hover:border-white/20 transition-colors"
              >
                <div>
                  <div className="text-sm font-semibold text-white">{m.name}</div>
                  <div className="text-[11px] text-slate-400 font-mono">{m.type}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-mono font-bold text-cyan-300">{m.mape.toFixed(2)}% MAPE</div>
                  <div className="text-[10px] text-slate-400 font-mono">RMSE: {m.rmse.toFixed(2)} kW</div>
                </div>
              </div>
            ))}
          </div>
        </LiquidGlassCard>
      </div>
    </div>
  );
};

export default ExecutiveDashboard;
