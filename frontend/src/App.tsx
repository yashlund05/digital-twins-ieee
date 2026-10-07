import React, { useState } from 'react';
import FluidShaderBackground from './components/canvas/FluidShaderBackground';
import NavigationBar, { ActiveTab } from './components/ui/NavigationBar';
import ExecutiveDashboard from './components/views/ExecutiveDashboard';
import FeederInspector from './components/views/FeederInspector';
import StalenessStudio from './components/views/StalenessStudio';
import MitigationLab from './components/views/MitigationLab';
import ClaimsAuditRegistry from './components/views/ClaimsAuditRegistry';
import LiquidGlassCard from './components/ui/LiquidGlassCard';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('overview');

  return (
    <div className="relative min-h-screen w-full bg-[#070A14] text-slate-100 font-sans selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* 1. Dynamic WebGL Simplex Fluid Shader Canvas Background */}
      <FluidShaderBackground />

      {/* 2. Foreground Glass Content Container */}
      <div className="relative z-10 flex min-h-screen flex-col justify-between py-6 px-4 md:px-8 max-w-7xl mx-auto">
        {/* Sticky Header Navigation */}
        <NavigationBar activeTab={activeTab} onTabChange={setActiveTab} />

        {/* View Switcher */}
        <main className="flex-1 my-4">
          {activeTab === 'overview' && <ExecutiveDashboard />}
          {activeTab === 'feeder' && <FeederInspector />}
          {activeTab === 'staleness' && <StalenessStudio />}
          {activeTab === 'mitigation' && <MitigationLab />}
          {activeTab === 'claims' && <ClaimsAuditRegistry />}
        </main>

        {/* Liquid Glass Footer */}
        <footer className="mt-8 pt-4 border-t border-white/5">
          <LiquidGlassCard className="py-3 px-6 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-400 gap-2">
            <div>
              <span className="font-semibold text-slate-200">IEEE Transactions on Smart Grid</span> · Digital Twin Research Suite
            </div>
            <div className="font-mono text-[11px] text-slate-400">
              Lead Author: <strong className="text-cyan-300">Ayush</strong> · Port 5569 · React Three Fiber + Liquid Glass
            </div>
          </LiquidGlassCard>
        </footer>
      </div>
    </div>
  );
};

export default App;
