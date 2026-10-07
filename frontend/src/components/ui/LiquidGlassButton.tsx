import React from 'react';

export interface LiquidGlassButtonProps {
  label: string;
  icon?: React.ReactNode;
  active?: boolean;
  onClick?: () => void;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const LiquidGlassButton: React.FC<LiquidGlassButtonProps> = ({
  label,
  icon,
  active = false,
  onClick,
  className = '',
  size = 'md',
}) => {
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-5 py-2.5 text-sm',
    lg: 'px-7 py-3.5 text-base font-semibold',
  }[size];

  return (
    <button
      onClick={onClick}
      className={`group relative flex items-center gap-2 rounded-full font-medium transition-all duration-300 ${sizeClasses} ${
        active
          ? 'bg-cyan-500/25 border-cyan-400/60 text-white shadow-[0_0_24px_rgba(6,182,212,0.4)]'
          : 'liquid-glass-button text-slate-300 hover:text-white'
      } ${className}`}
    >
      {icon && <span className="text-cyan-400 group-hover:scale-110 transition-transform">{icon}</span>}
      <span className="relative z-10 tracking-wide">{label}</span>
      <div className="absolute inset-0 rounded-full bg-gradient-to-r from-transparent via-white/10 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100 pointer-events-none" />
    </button>
  );
};

export default LiquidGlassButton;
