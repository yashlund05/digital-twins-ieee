import React from 'react';
import LiquidGlassCard from './LiquidGlassCard';

export interface MetricChipProps {
  label: string;
  value: string | number;
  unit?: string;
  subtext?: string;
  badge?: string;
  badgeColor?: 'cyan' | 'violet' | 'emerald' | 'amber' | 'rose';
  icon?: React.ReactNode;
}

export const MetricChip: React.FC<MetricChipProps> = ({
  label,
  value,
  unit,
  subtext,
  badge,
  badgeColor = 'cyan',
  icon,
}) => {
  const badgeColors = {
    cyan: 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30',
    violet: 'bg-violet-500/15 text-violet-300 border-violet-500/30',
    emerald: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
    amber: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
    rose: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
  }[badgeColor];

  return (
    <LiquidGlassCard className="p-5 flex flex-col justify-between hover:border-cyan-400/40 hover:shadow-[0_8px_30px_rgba(6,182,212,0.15)] transition-all">
      <div className="flex items-start justify-between gap-2 mb-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          {label}
        </span>
        {icon && <span className="text-cyan-400">{icon}</span>}
      </div>

      <div className="flex items-baseline gap-1.5 my-1">
        <span className="text-3xl font-extrabold tracking-tight text-white font-mono">
          {value}
        </span>
        {unit && <span className="text-sm font-medium text-slate-400">{unit}</span>}
      </div>

      <div className="flex items-center justify-between mt-3 pt-2 border-t border-white/5 text-xs">
        {subtext && <span className="text-slate-400 truncate">{subtext}</span>}
        {badge && (
          <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold tracking-wide border ${badgeColors}`}>
            {badge}
          </span>
        )}
      </div>
    </LiquidGlassCard>
  );
};

export default MetricChip;
