import React from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stars } from '@react-three/drei';
import FeederGrid3D from './FeederGrid3D';
import { BusNode } from '../../types';

export interface Feeder3DCanvasProps {
  onSelectBus: (bus: BusNode | null) => void;
  selectedBusId: number | null;
  className?: string;
}

export const Feeder3DCanvas: React.FC<Feeder3DCanvasProps> = ({
  onSelectBus,
  selectedBusId,
  className = '',
}) => {
  return (
    <div className={`relative w-full h-[520px] rounded-3xl overflow-hidden border border-white/10 ${className}`}>
      {/* Background Starfield and Canvas */}
      <Canvas
        camera={{ position: [0, 14, 30], fov: 45 }}
        gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
        onPointerMissed={() => onSelectBus(null)}
      >
        <ambientLight intensity={0.6} />
        <directionalLight position={[10, 20, 15]} intensity={1.2} />
        <pointLight position={[-10, -10, -10]} intensity={0.5} color="#06B6D4" />
        <pointLight position={[15, 10, 10]} intensity={0.5} color="#8B5CF6" />

        <Stars radius={100} depth={50} count={2500} factor={4} saturation={0} fade speed={1} />

        <FeederGrid3D onSelectBus={onSelectBus} selectedBusId={selectedBusId} />

        <OrbitControls
          enableDamping
          dampingFactor={0.05}
          maxDistance={70}
          minDistance={8}
          maxPolarAngle={Math.PI / 2 + 0.1}
        />
      </Canvas>

      {/* Control Overlay Hint */}
      <div className="pointer-events-none absolute bottom-4 left-4 z-10 flex items-center gap-2 rounded-full px-3 py-1.5 liquid-glass text-[11px] font-mono text-slate-300">
        <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
        <span>Drag: Rotate · Scroll: Zoom · Click Bus to Inspect</span>
      </div>
    </div>
  );
};

export default Feeder3DCanvas;
