import React from 'react';
import LiquidGlassCard from '../ui/LiquidGlassCard';
import { CANONICAL_CLAIMS_REGISTRY } from '../../data/digitalTwinData';
import { Database, ShieldCheck, CheckCircle2, FileText, Check } from 'lucide-react';

export const ClaimsAuditRegistry: React.FC = () => {
  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Database className="text-cyan-400 w-6 h-6" />
            Machine-Verified Scientific Claims Registry (C01–C10)
          </h2>
          <p className="text-xs md:text-sm text-slate-300">
            Immutable frozen experiment run audit verifying numerical consistency across IEEE publication artifacts.
          </p>
        </div>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-2xl liquid-glass text-xs font-mono text-emerald-300 border border-emerald-500/30">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>ALL 10 CLAIMS VERIFIED (TOLERANCE ≤ 1e-4)</span>
        </div>
      </div>

      {/* Claims Table Card */}
      <LiquidGlassCard elevated className="p-6 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-white/10 text-slate-400 font-mono uppercase tracking-wider">
                <th className="py-3 px-3">Claim ID</th>
                <th className="py-3 px-4">Hypothesis & Description</th>
                <th className="py-3 px-3">Canonical Value</th>
                <th className="py-3 px-4">Frozen Source Run</th>
                <th className="py-3 px-4">Artifact File</th>
                <th className="py-3 px-3 text-right">Gate Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 font-sans">
              {CANONICAL_CLAIMS_REGISTRY.map((claim) => (
                <tr key={claim.id} className="hover:bg-white/[0.02] transition-colors">
                  <td className="py-3.5 px-3 font-mono font-bold text-cyan-300">
                    {claim.id}
                  </td>
                  <td className="py-3.5 px-4 font-medium text-white max-w-xs">
                    <div>{claim.title}</div>
                    <div className="text-[11px] text-slate-400 font-normal mt-0.5">
                      {claim.scientificImpact}
                    </div>
                  </td>
                  <td className="py-3.5 px-3 font-mono font-bold text-emerald-300">
                    {claim.value}
                  </td>
                  <td className="py-3.5 px-4 font-mono text-slate-300">
                    <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10">
                      {claim.sourceRun}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 font-mono text-slate-400 text-[11px] flex items-center gap-1.5 mt-3">
                    <FileText className="w-3.5 h-3.5 text-slate-500" />
                    {claim.sourceFile}
                  </td>
                  <td className="py-3.5 px-3 text-right">
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                      <Check className="w-3 h-3" />
                      {claim.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </LiquidGlassCard>

      {/* Safety Gate Checklist */}
      <LiquidGlassCard className="p-6">
        <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-cyan-400" />
          IEEE TSG Submission Safety Gate Checklist
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-4 rounded-2xl bg-white/5 border border-white/10 space-y-2">
            <div className="flex items-center gap-2 font-bold text-white">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              E13 Manuscript Gate
            </div>
            <p className="text-slate-300 leading-relaxed">
              Every numerical claim quoted in manuscript sections matches frozen source runs E4, E5, E10, and E11 within numerical tolerance &epsilon; &le; 1e-4.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-white/5 border border-white/10 space-y-2">
            <div className="flex items-center gap-2 font-bold text-white">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              Negative Result Transparency
            </div>
            <p className="text-slate-300 leading-relaxed">
              Multi-seed hypothesis H3 is formally reported as falsified (p = 1.0000, NOT_SUPPORTED), upholding high scientific integrity.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-white/5 border border-white/10 space-y-2">
            <div className="flex items-center gap-2 font-bold text-white">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              Zero Temporal Leakage
            </div>
            <p className="text-slate-300 leading-relaxed">
              Temporal train/validation/test splits are strictly forward-in-time, ensuring zero lookahead bias during short-term forecasting.
            </p>
          </div>
        </div>
      </LiquidGlassCard>
    </div>
  );
};

export default ClaimsAuditRegistry;
