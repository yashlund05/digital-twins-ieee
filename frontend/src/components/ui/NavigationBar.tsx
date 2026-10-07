import React from 'react';
import LiquidGlassButton from './LiquidGlassButton';
import { Activity, Cpu, Sliders, ShieldCheck, Database } from 'lucide-react';

export type ActiveTab = 'overview' | 'feeder' | 'staleness' | 'mitigation' | 'claims';

export interface NavigationBarProps {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
}

export const NavigationBar: React.FC<NavigationBarProps> = ({ activeTab, onTabChange }) => {
  return (
    <header className="sticky top-4 z-50 w-full max-w-7xl mx-auto px-4 mb-6">
      <div className="liquid-glass rounded-full px-4 py-2.5 flex items-center justify-between gap-4 border border-white/20 shadow-2xl">
        {/* Brand & Author */}
        <div className="flex items-center gap-3 pl-2">
          <div className="relative flex items-center justify-center w-9 h-9 rounded-full bg-gradient-to-tr from-cyan-500 to-violet-600 shadow-md">
            <span className="text-white font-black text-sm">⚡</span>
            <span className="absolute -top-0.5 -right-0.5 flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-cyan-500" />
            </span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-sm tracking-wider text-white">DIGITAL TWIN</span>
              <span className="px-1.5 py-0.5 text-[9px] font-mono font-bold bg-cyan-500/20 text-cyan-300 rounded border border-cyan-500/30">
                IEEE TSG
              </span>
            </div>
            <p className="text-[10px] text-slate-400 tracking-wide font-mono">
              Research Platform · Lead Author: <strong className="text-slate-200">Ayush</strong>
            </p>
          </div>
        </div>

        {/* Tab Controls */}
        <nav className="flex items-center gap-1.5 overflow-x-auto py-1">
          <LiquidGlassButton
            size="sm"
            label="Command Center"
            icon={<Activity className="w-3.5 h-3.5" />}
            active={activeTab === 'overview'}
            onClick={() => onTabChange('overview')}
          />
          <LiquidGlassButton
            size="sm"
            label="3D Cyber Grid"
            icon={<Cpu className="w-3.5 h-3.5" />}
            active={activeTab === 'feeder'}
            onClick={() => onTabChange('feeder')}
          />
          <LiquidGlassButton
            size="sm"
            label="Staleness Studio"
            icon={<Sliders className="w-3.5 h-3.5" />}
            active={activeTab === 'staleness'}
            onClick={() => onTabChange('staleness')}
          />
          <LiquidGlassButton
            size="sm"
            label="Mitigation Lab"
            icon={<ShieldCheck className="w-3.5 h-3.5" />}
            active={activeTab === 'mitigation'}
            onClick={() => onTabChange('mitigation')}
          />
          <LiquidGlassButton
            size="sm"
            label="Claims Audit"
            icon={<Database className="w-3.5 h-3.5" />}
            active={activeTab === 'claims'}
            onClick={() => onTabChange('claims')}
          />
        </nav>

        {/* Status Chip */}
        <div className="hidden lg:flex items-center gap-2 pr-2">
          <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_#34d399]" />
          <span className="text-xs font-mono text-emerald-400 tracking-tight">PORT 5569 · ACTIVE</span>
        </div>
      </div>
    </header>
  );
};

export default NavigationBar;
