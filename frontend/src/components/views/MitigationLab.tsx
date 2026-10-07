import React, { useState } from 'react';
import LiquidGlassCard from '../ui/LiquidGlassCard';
import MetricChip from '../ui/MetricChip';
import LiquidGlassButton from '../ui/LiquidGlassButton';
import { ShieldCheck, ToggleLeft, ToggleRight, Sparkles, CheckCircle2, ArrowRight } from 'lucide-react';

export const MitigationLab: React.FC = () => {
  const [activeAoI, setActiveAoI] = useState<number>(25); // 25s staleness
  const [enableAdaptiveThreshold, setEnableAdaptiveThreshold] = useState<boolean>(true);
  const [enableDualModeSwitching, setEnableDualModeSwitching] = useState<boolean>(true);
  const [alphaSensitivity, setAlphaSensitivity] = useState<number>(0.65);

  const criticalAoI = 10.0;

  // Unmitigated metrics at activeAoI
  const unmitigatedF1 = Math.max(0.25, 0.9780 - 0.0018 * activeAoI - 0.08);
  const unmitigatedFPR = Math.min(0.35, 0.015 + 0.008 * activeAoI);

  // Mitigated with Dynamic Thresholding
  const thresholdExpansion = 1 + alphaSensitivity * (activeAoI / criticalAoI);
  const dynamicF1Boost = enableAdaptiveThreshold ? Math.min(0.32, 0.012 * activeAoI * alphaSensitivity) : 0;
  const dynamicFPRReduction = enableAdaptiveThreshold ? 0.65 : 0;

  // Mitigated with Dual-Mode Switching
  const isFallbackTriggered = activeAoI > criticalAoI && enableDualModeSwitching;
  const fallbackF1 = isFallbackTriggered ? 0.76 : unmitigatedF1 + dynamicF1Boost;
  const finalF1 = Math.min(0.978, fallbackF1);
  const finalFPR = isFallbackTriggered
    ? 0.024
    : unmitigatedFPR * (1 - dynamicFPRReduction);

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* View Header */}
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <ShieldCheck className="text-cyan-400 w-6 h-6" />
          Dual-Mode Mitigation Lab & Dynamic Thresholding
        </h2>
        <p className="text-xs md:text-sm text-slate-300">
          Interactive evaluation of the two proposed IEEE publication mitigation mechanisms under severe synchronization latency.
        </p>
      </div>

      {/* Control Sliders & Switches */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <LiquidGlassCard elevated className="lg:col-span-6 p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-white/10 pb-3">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-400">
              Mitigation Architecture Controller
            </span>
            <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300">
              ACTIVE DEFENSE
            </span>
          </div>

          {/* Simulated Staleness Slider */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-sm">
              <span className="font-semibold text-white">Staleness Condition (AoI)</span>
              <span className="font-mono font-bold text-cyan-300">{activeAoI} seconds</span>
            </div>
            <input
              type="range"
              min="0"
              max="60"
              step="1"
              value={activeAoI}
              onChange={(e) => setActiveAoI(Number(e.target.value))}
              className="w-full accent-cyan-400 cursor-pointer h-2 bg-slate-800 rounded-lg"
            />
            <div className="flex justify-between text-[10px] font-mono text-slate-400">
              <span>0s (Synced)</span>
              <span className="text-rose-400 font-bold">10s (Critical AoI*)</span>
              <span>30s</span>
              <span>60s (Heavy Lag)</span>
            </div>
          </div>

          {/* Dynamic Sensitivity Alpha Slider */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-sm">
              <span className="font-semibold text-white">Threshold Adaptation Sensitivity (α)</span>
              <span className="font-mono font-bold text-violet-300">{alphaSensitivity.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0.1"
              max="1.5"
              step="0.05"
              value={alphaSensitivity}
              onChange={(e) => setAlphaSensitivity(Number(e.target.value))}
              className="w-full accent-violet-400 cursor-pointer h-2 bg-slate-800 rounded-lg"
            />
            <div className="flex justify-between text-[10px] font-mono text-slate-400">
              <span>0.10 (Conservative)</span>
              <span>0.65 (Optimal TSG)</span>
              <span>1.50 (Aggressive Rejection)</span>
            </div>
          </div>

          {/* Toggle Switches */}
          <div className="space-y-3 pt-2">
            <div
              onClick={() => setEnableAdaptiveThreshold(!enableAdaptiveThreshold)}
              className="flex items-center justify-between p-3.5 rounded-2xl bg-white/5 border border-white/10 cursor-pointer hover:border-cyan-400/40 transition-colors"
            >
              <div>
                <div className="text-sm font-semibold text-white">AoI-Adaptive Dynamic Threshold τ(AoI)</div>
                <div className="text-[11px] text-slate-400 font-mono">
                  Scale decision boundary τ = τ₀ · (1 + α · AoI / AoI*)
                </div>
              </div>
              {enableAdaptiveThreshold ? (
                <ToggleRight className="w-7 h-7 text-cyan-400" />
              ) : (
                <ToggleLeft className="w-7 h-7 text-slate-500" />
              )}
            </div>

            <div
              onClick={() => setEnableDualModeSwitching(!enableDualModeSwitching)}
              className="flex items-center justify-between p-3.5 rounded-2xl bg-white/5 border border-white/10 cursor-pointer hover:border-emerald-400/40 transition-colors"
            >
              <div>
                <div className="text-sm font-semibold text-white">Dual-Mode Representation Switching</div>
                <div className="text-[11px] text-slate-400 font-mono">
                  Fallback to raw space when AoI exceeds critical breakpoint (10s)
                </div>
              </div>
              {enableDualModeSwitching ? (
                <ToggleRight className="w-7 h-7 text-emerald-400" />
              ) : (
                <ToggleLeft className="w-7 h-7 text-slate-500" />
              )}
            </div>
          </div>
        </LiquidGlassCard>

        {/* Real-Time Mitigation Outcomes */}
        <div className="lg:col-span-6 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <MetricChip
              label="Mitigated Anomaly F1"
              value={finalF1.toFixed(4)}
              subtext={`Unmitigated: ${unmitigatedF1.toFixed(4)}`}
              badge={`+${(((finalF1 - unmitigatedF1) / unmitigatedF1) * 100).toFixed(1)}% RECOVERY`}
              badgeColor="emerald"
              icon={<Sparkles className="w-4 h-4" />}
            />
            <MetricChip
              label="Suppressed False Positive Rate"
              value={`${(finalFPR * 100).toFixed(2)}%`}
              subtext={`Raw FPR: ${(unmitigatedFPR * 100).toFixed(2)}%`}
              badge="REDUCED"
              badgeColor="cyan"
              icon={<ShieldCheck className="w-4 h-4" />}
            />
          </div>

          {/* Representation Mode Status Card */}
          <LiquidGlassCard className="p-6 space-y-3">
            <div className="text-xs font-mono font-bold text-slate-400 uppercase">
              Current Operating Representation
            </div>
            <div className="flex items-center gap-3">
              <span
                className={`px-3 py-1.5 rounded-xl font-mono text-sm font-bold border ${
                  isFallbackTriggered
                    ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                    : 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                }`}
              >
                {isFallbackTriggered ? 'MODE B: ROBUST RAW REPRESENTATION' : 'MODE A: PHYSICS RESIDUAL (LSTM-AE)'}
              </span>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed pt-1">
              {isFallbackTriggered
                ? 'Staleness AoI exceeds 10.0s breakpoint. Dual-Mode Representation Switcher successfully disengaged stale residual calculation, protecting detector from false-positive avalanche.'
                : 'Staleness AoI is within nominal envelope (≤ 10.0s). Physics-informed residual generator active with peak detection sensitivity.'}
            </p>

            <div className="flex items-center gap-2 pt-2 text-[11px] font-mono text-slate-400">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Boundary Factor τ / τ₀ = {thresholdExpansion.toFixed(2)}×</span>
            </div>
          </LiquidGlassCard>
        </div>
      </div>
    </div>
  );
};

export default MitigationLab;
