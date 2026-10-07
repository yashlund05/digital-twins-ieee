import React from 'react';

export interface LiquidGlassCardProps {
  children: React.ReactNode;
  className?: string;
  elevated?: boolean;
  onClick?: () => void;
}

export const LiquidGlassCard: React.FC<LiquidGlassCardProps> = ({
  children,
  className = '',
  elevated = false,
  onClick,
}) => {
  return (
    <div
      onClick={onClick}
      className={`relative rounded-3xl p-6 transition-all duration-300 ${
        elevated ? 'liquid-glass-elevated' : 'liquid-glass'
      } ${className}`}
    >
      {/* Subtle Specular Rim Light */}
      <div className="pointer-events-none absolute inset-0 rounded-3xl bg-gradient-to-tr from-white/5 via-transparent to-cyan-500/10" />
      <div className="relative z-10">{children}</div>
    </div>
  );
};

export default LiquidGlassCard;
