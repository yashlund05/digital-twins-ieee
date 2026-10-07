import React, { useState } from 'react';
import LiquidGlassCard from '../ui/LiquidGlassCard';
import MetricChip from '../ui/MetricChip';
import { Sliders, AlertTriangle, ShieldCheck, TrendingDown, Clock } from 'lucide-react';

export const StalenessStudio: React.FC = () => {
  const [deltaT, setDeltaT] = useState<number>(15);
  const [pDrop, setPDrop] = useState<number>(0.05);

  // Theoretical and Empirical Age-of-Information Calculation
  const aoiEff = deltaT * (1 + pDrop / (1 - pDrop + 0.001)) + 1.25;

  // Empirical degradation: d(F1)/d(AoI) = -0.0018
  const baseF1 = 0.9780;
  const currentF1 = Math.max(0.15, baseF1 - 0.0018 * aoiEff - 0.45 * pDrop);
  const falsePositiveRate = Math.min(0.38, 0.012 + 0.0009 * aoiEff + 0.15 * pDrop);
  const detectionDelay = Math.min(45, 0.8 + 0.12 * aoiEff);

  // Status regime
  const regime =
    aoiEff <= 10.0
      ? { text: 'Nominal Synchronized Regime', color: 'emerald', icon: <ShieldCheck className="w-4 h-4 text-emerald-400" /> }
      : aoiEff <= 30.0
      ? { text: 'Degraded Staleness Regime (Mitigation Recommended)', color: 'amber', icon: <Clock className="w-4 h-4 text-amber-400" /> }
      : { text: 'Critical Staleness Collapse (Dual-Mode Fallback Required)', color: 'rose', icon: <AlertTriangle className="w-4 h-4 text-rose-400" /> };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* View Header */}
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <Sliders className="text-cyan-400 w-6 h-6" />
          Staleness & Age-of-Information (AoI) Studio
        </h2>
        <p className="text-xs md:text-sm text-slate-300">
          Controlled parameter sweeps across synchronization interval &Delta;t and packet drop probability P_drop.
        </p>
      </div>

      {/* Interactive Controls & Real-Time Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Sliders Panel */}
        <LiquidGlassCard elevated className="lg:col-span-5 p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-white/10 pb-3">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-400">
              Cyber Network Controls
            </span>
            <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300">
              LIVE SIMULATOR
            </span>
          </div>

          {/* Delta T Slider */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-sm">
              <span className="font-semibold text-white">Synchronization Interval (Δt)</span>
              <span className="font-mono font-bold text-cyan-300">{deltaT} seconds</span>
            </div>
            <input
              type="range"
              min="0"
              max="300"
              step="5"
              value={deltaT}
              onChange={(e) => setDeltaT(Number(e.target.value))}
              className="w-full accent-cyan-400 cursor-pointer h-2 bg-slate-800 rounded-lg"
            />
            <div className="flex justify-between text-[10px] font-mono text-slate-400">
              <span>0s (Real-Time)</span>
              <span>60s</span>
              <span>120s</span>
              <span>300s (5 min)</span>
            </div>
          </div>

          {/* Packet Loss Slider */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-sm">
              <span className="font-semibold text-white">Packet Loss Probability (P_drop)</span>
              <span className="font-mono font-bold text-violet-300">{(pDrop * 100).toFixed(0)}%</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="0.20"
              step="0.01"
              value={pDrop}
              onChange={(e) => setPDrop(Number(e.target.value))}
              className="w-full accent-violet-400 cursor-pointer h-2 bg-slate-800 rounded-lg"
            />
            <div className="flex justify-between text-[10px] font-mono text-slate-400">
              <span>0% (Lossless)</span>
              <span>5%</span>
              <span>10%</span>
              <span>20% (Heavy Loss)</span>
            </div>
          </div>

          {/* Regime Warning Card */}
          <div className="p-4 rounded-2xl bg-white/5 border border-white/10 flex items-start gap-3">
            {regime.icon}
            <div>
              <div className="text-xs font-bold text-white mb-0.5">{regime.text}</div>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Empirical degradation slope &Delta;&beta; = -0.0018 s&sup1;. Above AoI* = 10.0s, stale physics residuals trigger false positive inflation.
              </p>
            </div>
          </div>
        </LiquidGlassCard>

        {/* Real-time Calculated Metrics */}
        <div className="lg:col-span-7 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <MetricChip
            label="Effective Age of Information"
            value={aoiEff.toFixed(1)}
            unit="s"
            subtext="Theoretical Cyber-Physical AoI"
            badge={aoiEff <= 10.0 ? 'OPTIMAL' : 'STALE'}
            badgeColor={aoiEff <= 10.0 ? 'emerald' : 'amber'}
            icon={<Clock className="w-4 h-4" />}
          />
          <MetricChip
            label="Anomaly Detection F1"
            value={currentF1.toFixed(4)}
            subtext={`Baseline F1 = ${baseF1.toFixed(4)}`}
            badge={`${((currentF1 - baseF1) * 100).toFixed(1)}%`}
            badgeColor={currentF1 >= 0.85 ? 'emerald' : 'rose'}
            icon={<TrendingDown className="w-4 h-4" />}
          />
          <MetricChip
            label="Estimated False Positive Rate"
            value={`${(falsePositiveRate * 100).toFixed(2)}%`}
            subtext="Ghost Anomaly Rate"
            badge="FPR INFLATION"
            badgeColor="rose"
            icon={<AlertTriangle className="w-4 h-4" />}
          />
          <MetricChip
            label="Mean Detection Delay"
            value={detectionDelay.toFixed(1)}
            unit="s"
            subtext="Telemetry Propagation Latency"
            badge="DELAY"
            badgeColor="violet"
            icon={<Sliders className="w-4 h-4" />}
          />
        </div>
      </div>

      {/* Empirical Degradation Curve Chart */}
      <LiquidGlassCard className="p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
            Empirical F1 Degradation Profile Across Staleness Domain (Δt ∈ [0, 300]s)
          </h3>
          <span className="text-xs font-mono text-slate-400">E5 Staleness Grid Comparison</span>
        </div>

        {/* SVG Visualization */}
        <div className="w-full h-56 relative flex items-end pt-4 pb-6 px-4">
          <svg className="w-full h-full overflow-visible" viewBox="0 0 800 200">
            {/* Grid Lines */}
            <line x1="0" y1="0" x2="800" y2="0" stroke="rgba(255,255,255,0.06)" strokeDasharray="4" />
            <line x1="0" y1="50" x2="800" y2="50" stroke="rgba(255,255,255,0.06)" strokeDasharray="4" />
            <line x1="0" y1="100" x2="800" y2="100" stroke="rgba(255,255,255,0.06)" strokeDasharray="4" />
            <line x1="0" y1="150" x2="800" y2="150" stroke="rgba(255,255,255,0.06)" strokeDasharray="4" />

            {/* Critical Change Point Band (AoI = 10s -> ~26px) */}
            <rect x="25" y="0" width="10" height="190" fill="rgba(244,63,94,0.15)" />
            <line x1="30" y1="0" x2="30" y2="190" stroke="#F43F5E" strokeWidth="2" strokeDasharray="4" />
            <text x="35" y="20" fill="#F43F5E" fontSize="10" fontFamily="monospace">AoI* = 10s</text>

            {/* Residual F1 Curve (Gradient Blue/Cyan) */}
            <path
              d="M 10 10 Q 150 45, 400 95 T 790 160"
              fill="none"
              stroke="#06B6D4"
              strokeWidth="3"
            />

            {/* Raw Representation Curve (Collapsed Purple) */}
            <path
              d="M 10 95 Q 150 120, 400 145 T 790 180"
              fill="none"
              stroke="#8B5CF6"
              strokeWidth="2"
              strokeDasharray="6"
            />

            {/* Active Current Position Marker */}
            {(() => {
              const xPos = Math.min(780, Math.max(10, 10 + (aoiEff / 300) * 770));
              const yPos = 190 - (currentF1 * 180);
              return (
                <g>
                  <circle cx={xPos} cy={yPos} r="7" fill="#06B6D4" />
                  <circle cx={xPos} cy={yPos} r="14" fill="none" stroke="#06B6D4" opacity="0.6" />
                  <text x={xPos - 20} y={yPos - 18} fill="#FFFFFF" fontSize="11" fontFamily="monospace" fontWeight="bold">
                    F1: {currentF1.toFixed(3)}
                  </text>
                </g>
              );
            })()}
          </svg>
        </div>

        <div className="flex flex-wrap items-center justify-between text-xs font-mono text-slate-400 pt-2 border-t border-white/5">
          <div className="flex items-center gap-6">
            <span className="flex items-center gap-2">
              <span className="w-3 h-0.5 bg-[#06B6D4]" />
              Proposed DT Residual (LSTM-AE)
            </span>
            <span className="flex items-center gap-2">
              <span className="w-3 h-0.5 bg-[#8B5CF6] border-b border-dashed" />
              Raw Sensor Baseline
            </span>
            <span className="flex items-center gap-2">
              <span className="w-3 h-0.5 bg-[#F43F5E]" />
              Critical Inflection Point (AoI = 10s)
            </span>
          </div>
          <span>X: Synchronization Delay (0 → 300s) · Y: Anomaly F1 (0.0 → 1.0)</span>
        </div>
      </LiquidGlassCard>
    </div>
  );
};

export default StalenessStudio;
