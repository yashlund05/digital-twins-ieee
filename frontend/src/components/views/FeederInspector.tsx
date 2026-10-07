import React, { useState } from 'react';
import Feeder3DCanvas from '../canvas/Feeder3DCanvas';
import LiquidGlassCard from '../ui/LiquidGlassCard';
import { IEEE33_BUS_NODES } from '../../data/ieee33BusData';
import { BusNode } from '../../types';
import { Cpu, Activity, Zap, CheckCircle2 } from 'lucide-react';

export const FeederInspector: React.FC = () => {
  const [selectedBus, setSelectedBus] = useState<BusNode | null>(IEEE33_BUS_NODES[17]); // Default Bus 18

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header Info */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Cpu className="text-cyan-400 w-6 h-6" />
            3D Cyber-Physical IEEE 33-Bus Feeder Inspector
          </h2>
          <p className="text-xs md:text-sm text-slate-300">
            Hardware-accelerated Three.js spatial network. Interactive raycast inspection with real-time OpenDSS power flow voltage colormaps.
          </p>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 liquid-glass px-4 py-2 rounded-2xl text-xs font-mono">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-[#06B6D4] shadow-[0_0_8px_#06B6D4]" />
            <span className="text-slate-300">1.00 pu (Nominal)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-[#6366F1]" />
            <span className="text-slate-300">0.95 pu</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-[#F43F5E] shadow-[0_0_8px_#F43F5E]" />
            <span className="text-slate-300">0.913 pu (Critical Drop)</span>
          </div>
        </div>
      </div>

      {/* Main 3D Canvas + Inspector Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* 3D Canvas Container */}
        <div className="lg:col-span-8">
          <Feeder3DCanvas
            selectedBusId={selectedBus ? selectedBus.id : null}
            onSelectBus={(bus) => setSelectedBus(bus)}
          />
        </div>

        {/* Floating Liquid Glass Node Inspector */}
        <div className="lg:col-span-4 space-y-4">
          <LiquidGlassCard elevated className="p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-400">
                Nodal Telemetry Inspector
              </span>
              <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                {selectedBus ? `BUS #${selectedBus.id}` : 'SELECT A NODE'}
              </span>
            </div>

            {selectedBus ? (
              <div className="space-y-4">
                <div>
                  <h3 className="text-xl font-bold text-white">{selectedBus.name}</h3>
                  <span className="text-xs font-mono text-slate-400 uppercase">
                    Topology Group: {selectedBus.branchGroup}
                  </span>
                </div>

                {/* Voltage Meter */}
                <div className="p-4 rounded-2xl bg-white/5 border border-white/10 space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-300">Nodal Voltage Magnitude</span>
                    <span className="font-mono font-bold text-white">{selectedBus.voltage.toFixed(4)} pu</span>
                  </div>
                  {/* Progress Bar */}
                  <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{
                        width: `${Math.max(10, Math.min(100, (selectedBus.voltage - 0.9) * 1000))}%`,
                        backgroundColor: selectedBus.voltage < 0.93 ? '#F43F5E' : '#06B6D4',
                      }}
                    />
                  </div>
                  <div className="flex justify-between text-[10px] font-mono text-slate-400">
                    <span>Min Limit: 0.90 pu</span>
                    <span>Nominal: 1.00 pu</span>
                  </div>
                </div>

                {/* Power Loads */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded-2xl bg-white/5 border border-white/10">
                    <span className="text-[11px] text-slate-400 block mb-1">Active Load (P)</span>
                    <span className="text-lg font-mono font-bold text-cyan-300">
                      {selectedBus.activePower} kW
                    </span>
                  </div>
                  <div className="p-3 rounded-2xl bg-white/5 border border-white/10">
                    <span className="text-[11px] text-slate-400 block mb-1">Reactive Load (Q)</span>
                    <span className="text-lg font-mono font-bold text-violet-300">
                      {selectedBus.reactivePower} kVAR
                    </span>
                  </div>
                </div>

                {/* Special Status */}
                {selectedBus.isSlack && (
                  <div className="flex items-center gap-2 p-3 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs">
                    <Zap className="w-4 h-4" />
                    <span>Slack Substation Bus (12.66 kV, Voltage Angle Reference 0.0°)</span>
                  </div>
                )}

                {selectedBus.id === 18 && (
                  <div className="flex items-center gap-2 p-3 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
                    <Activity className="w-4 h-4" />
                    <span>Maximum Feeder Voltage Drop Point (0.9131 pu at Trunk Endpoint)</span>
                  </div>
                )}
              </div>
            ) : (
              <div className="py-12 text-center text-slate-400 text-sm">
                Click on any node in the 3D grid to inspect its electrical parameters.
              </div>
            )}
          </LiquidGlassCard>

          {/* Feeder Benchmark Summary */}
          <LiquidGlassCard className="p-5 space-y-2 text-xs">
            <div className="font-bold text-white mb-2 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              Benchmark Feeder Topologies
            </div>
            <div className="flex justify-between text-slate-300">
              <span>Main Feeder Trunk:</span>
              <span className="font-mono text-cyan-300">Buses 1 → 18</span>
            </div>
            <div className="flex justify-between text-slate-300">
              <span>Lateral Sub-Feeder 1:</span>
              <span className="font-mono text-violet-300">Buses 2 → 19 → 22</span>
            </div>
            <div className="flex justify-between text-slate-300">
              <span>Lateral Sub-Feeder 2:</span>
              <span className="font-mono text-violet-300">Buses 3 → 23 → 25</span>
            </div>
            <div className="flex justify-between text-slate-300">
              <span>Lateral Sub-Feeder 3:</span>
              <span className="font-mono text-violet-300">Buses 6 → 26 → 33</span>
            </div>
          </LiquidGlassCard>
        </div>
      </div>
    </div>
  );
};

export default FeederInspector;
