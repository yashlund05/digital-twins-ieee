import React, { useMemo } from 'react';
import * as THREE from 'three';
import { IEEE33_BUS_NODES, IEEE33_BRANCHES } from '../../data/ieee33BusData';
import { BusNode } from '../../types';

export interface FeederGrid3DProps {
  onSelectBus: (bus: BusNode | null) => void;
  selectedBusId: number | null;
}

/**
 * Returns voltage colormap:
 * 1.00 pu -> Cyan (#06B6D4)
 * 0.95 pu -> Indigo (#6366F1)
 * 0.92 pu -> Rose Warning (#F43F5E)
 */
function getVoltageColor(v: number): THREE.Color {
  const norm = Math.max(0, Math.min(1, (v - 0.913) / (1.0 - 0.913)));
  const color = new THREE.Color();
  if (norm > 0.5) {
    // Cyan to Indigo
    color.lerpColors(new THREE.Color('#6366F1'), new THREE.Color('#06B6D4'), (norm - 0.5) * 2);
  } else {
    // Rose to Indigo
    color.lerpColors(new THREE.Color('#F43F5E'), new THREE.Color('#6366F1'), norm * 2);
  }
  return color;
}

export const FeederGrid3D: React.FC<FeederGrid3DProps> = ({ onSelectBus, selectedBusId }) => {
  // Build Line Segments for Branches
  const lineGeometry = useMemo(() => {
    const points: THREE.Vector3[] = [];
    const busMap = new Map(IEEE33_BUS_NODES.map((b) => [b.id, b]));

    IEEE33_BRANCHES.forEach((branch) => {
      const fromNode = busMap.get(branch.from);
      const toNode = busMap.get(branch.to);
      if (fromNode && toNode) {
        points.push(new THREE.Vector3(fromNode.x, fromNode.y, fromNode.z));
        points.push(new THREE.Vector3(toNode.x, toNode.y, toNode.z));
      }
    });

    const geom = new THREE.BufferGeometry().setFromPoints(points);
    return geom;
  }, []);

  return (
    <group>
      {/* Branch Lines (Glowing Cyber Grid) */}
      <lineSegments geometry={lineGeometry}>
        <lineBasicMaterial color="#38BDF8" transparent opacity={0.45} linewidth={2} />
      </lineSegments>

      {/* 33 Bus Spheres */}
      {IEEE33_BUS_NODES.map((bus) => {
        const isSelected = selectedBusId === bus.id;
        const color = getVoltageColor(bus.voltage);
        const radius = bus.isSlack ? 0.75 : 0.42;

        return (
          <group
            key={bus.id}
            position={[bus.x, bus.y, bus.z]}
            onClick={(e) => {
              e.stopPropagation();
              onSelectBus(bus);
            }}
            onPointerOver={(e) => {
              e.stopPropagation();
              document.body.style.cursor = 'pointer';
            }}
            onPointerOut={() => {
              document.body.style.cursor = 'auto';
            }}
          >
            {/* Core Node Sphere */}
            <mesh>
              <sphereGeometry args={[radius, 32, 32]} />
              <meshStandardMaterial
                color={color}
                emissive={color}
                emissiveIntensity={isSelected ? 1.2 : 0.6}
                roughness={0.2}
                metalness={0.8}
              />
            </mesh>

            {/* Selection Pulse Ring */}
            {isSelected && (
              <mesh>
                <ringGeometry args={[radius * 1.4, radius * 1.8, 32]} />
                <meshBasicMaterial color="#38BDF8" side={THREE.DoubleSide} transparent opacity={0.8} />
              </mesh>
            )}

            {/* Slack Substation Marker */}
            {bus.isSlack && (
              <mesh position={[0, 1.2, 0]}>
                <octahedronGeometry args={[0.35]} />
                <meshStandardMaterial color="#FBBF24" emissive="#FBBF24" emissiveIntensity={0.8} />
              </mesh>
            )}
          </group>
        );
      })}
    </group>
  );
};

export default FeederGrid3D;
