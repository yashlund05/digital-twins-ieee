import { BusNode, BranchEdge } from '../types';

// IEEE 33-Bus System Spatial Layout in 3D
// Main trunk: 1 -> 18 along X axis
// Lateral 1: Bus 2 -> 19 -> 22 along -Z axis
// Lateral 2: Bus 3 -> 23 -> 25 along +Z axis
// Lateral 3: Bus 6 -> 26 -> 33 along +Y and +Z axis

export const IEEE33_BUS_NODES: BusNode[] = [
  // Main Trunk (1 - 18)
  { id: 1, name: 'Bus 1 (Substation)', x: -16, y: 0, z: 0, voltage: 1.0000, activePower: 0, reactivePower: 0, isSlack: true, branchGroup: 'trunk' },
  { id: 2, name: 'Bus 2', x: -14, y: 0.1, z: 0, voltage: 0.9970, activePower: 100, reactivePower: 60, branchGroup: 'trunk' },
  { id: 3, name: 'Bus 3', x: -12, y: 0.1, z: 0, voltage: 0.9829, activePower: 90, reactivePower: 40, branchGroup: 'trunk' },
  { id: 4, name: 'Bus 4', x: -10, y: 0.1, z: 0, voltage: 0.9754, activePower: 120, reactivePower: 80, branchGroup: 'trunk' },
  { id: 5, name: 'Bus 5', x: -8, y: 0.0, z: 0, voltage: 0.9680, activePower: 60, reactivePower: 30, branchGroup: 'trunk' },
  { id: 6, name: 'Bus 6', x: -6, y: -0.1, z: 0, voltage: 0.9495, activePower: 60, reactivePower: 20, branchGroup: 'trunk' },
  { id: 7, name: 'Bus 7', x: -4, y: -0.1, z: 0, voltage: 0.9460, activePower: 200, reactivePower: 100, branchGroup: 'trunk' },
  { id: 8, name: 'Bus 8', x: -2, y: -0.2, z: 0, voltage: 0.9413, activePower: 200, reactivePower: 100, branchGroup: 'trunk' },
  { id: 9, name: 'Bus 9', x: 0, y: -0.2, z: 0, voltage: 0.9350, activePower: 60, reactivePower: 20, branchGroup: 'trunk' },
  { id: 10, name: 'Bus 10', x: 2, y: -0.3, z: 0, voltage: 0.9292, activePower: 60, reactivePower: 20, branchGroup: 'trunk' },
  { id: 11, name: 'Bus 11', x: 4, y: -0.3, z: 0, voltage: 0.9283, activePower: 45, reactivePower: 30, branchGroup: 'trunk' },
  { id: 12, name: 'Bus 12', x: 6, y: -0.4, z: 0, voltage: 0.9268, activePower: 60, reactivePower: 35, branchGroup: 'trunk' },
  { id: 13, name: 'Bus 13', x: 8, y: -0.4, z: 0, voltage: 0.9207, activePower: 60, reactivePower: 35, branchGroup: 'trunk' },
  { id: 14, name: 'Bus 14', x: 10, y: -0.5, z: 0, voltage: 0.9185, activePower: 120, reactivePower: 80, branchGroup: 'trunk' },
  { id: 15, name: 'Bus 15', x: 12, y: -0.5, z: 0, voltage: 0.9171, activePower: 60, reactivePower: 10, branchGroup: 'trunk' },
  { id: 16, name: 'Bus 16', x: 14, y: -0.6, z: 0, voltage: 0.9157, activePower: 60, reactivePower: 20, branchGroup: 'trunk' },
  { id: 17, name: 'Bus 17', x: 16, y: -0.7, z: 0, voltage: 0.9136, activePower: 60, reactivePower: 20, branchGroup: 'trunk' },
  { id: 18, name: 'Bus 18 (Max Drop)', x: 18, y: -0.8, z: 0, voltage: 0.9131, activePower: 90, reactivePower: 40, branchGroup: 'trunk' },

  // Lateral 1 (Sub-feeder from Bus 2 -> 19 -> 22)
  { id: 19, name: 'Bus 19', x: -14, y: 0.8, z: -3, voltage: 0.9965, activePower: 90, reactivePower: 40, branchGroup: 'lateral1' },
  { id: 20, name: 'Bus 20', x: -14, y: 1.4, z: -6, voltage: 0.9929, activePower: 90, reactivePower: 40, branchGroup: 'lateral1' },
  { id: 21, name: 'Bus 21', x: -14, y: 2.0, z: -9, voltage: 0.9922, activePower: 90, reactivePower: 40, branchGroup: 'lateral1' },
  { id: 22, name: 'Bus 22', x: -14, y: 2.6, z: -12, voltage: 0.9916, activePower: 90, reactivePower: 40, branchGroup: 'lateral1' },

  // Lateral 2 (Sub-feeder from Bus 3 -> 23 -> 25)
  { id: 23, name: 'Bus 23', x: -12, y: 0.8, z: 3, voltage: 0.9793, activePower: 90, reactivePower: 50, branchGroup: 'lateral2' },
  { id: 24, name: 'Bus 24', x: -12, y: 1.5, z: 6, voltage: 0.9727, activePower: 420, reactivePower: 200, branchGroup: 'lateral2' },
  { id: 25, name: 'Bus 25', x: -12, y: 2.2, z: 9, voltage: 0.9693, activePower: 420, reactivePower: 200, branchGroup: 'lateral2' },

  // Lateral 3 (Sub-feeder from Bus 6 -> 26 -> 33)
  { id: 26, name: 'Bus 26', x: -6, y: 0.9, z: 3, voltage: 0.9477, activePower: 60, reactivePower: 25, branchGroup: 'lateral3' },
  { id: 27, name: 'Bus 27', x: -6, y: 1.7, z: 6, voltage: 0.9452, activePower: 60, reactivePower: 25, branchGroup: 'lateral3' },
  { id: 28, name: 'Bus 28', x: -4, y: 1.8, z: 8, voltage: 0.9337, activePower: 60, reactivePower: 20, branchGroup: 'lateral3' },
  { id: 29, name: 'Bus 29', x: -2, y: 1.9, z: 10, voltage: 0.9255, activePower: 120, reactivePower: 70, branchGroup: 'lateral3' },
  { id: 30, name: 'Bus 30', x: 0, y: 2.0, z: 12, voltage: 0.9219, activePower: 200, reactivePower: 600, branchGroup: 'lateral3' },
  { id: 31, name: 'Bus 31', x: 2, y: 2.1, z: 14, voltage: 0.9178, activePower: 150, reactivePower: 70, branchGroup: 'lateral3' },
  { id: 32, name: 'Bus 32', x: 4, y: 2.2, z: 16, voltage: 0.9169, activePower: 210, reactivePower: 100, branchGroup: 'lateral3' },
  { id: 33, name: 'Bus 33', x: 6, y: 2.3, z: 18, voltage: 0.9166, activePower: 60, reactivePower: 40, branchGroup: 'lateral3' },
];

export const IEEE33_BRANCHES: BranchEdge[] = [
  // Trunk
  { from: 1, to: 2, r: 0.0922, x: 0.0470 },
  { from: 2, to: 3, r: 0.4930, x: 0.2511 },
  { from: 3, to: 4, r: 0.3660, x: 0.1864 },
  { from: 4, to: 5, r: 0.3811, x: 0.1941 },
  { from: 5, to: 6, r: 0.8190, x: 0.7070 },
  { from: 6, to: 7, r: 0.1872, x: 0.6188 },
  { from: 7, to: 8, r: 0.7114, x: 0.2351 },
  { from: 8, to: 9, r: 1.0300, x: 0.7400 },
  { from: 9, to: 10, r: 1.0440, x: 0.7400 },
  { from: 10, to: 11, r: 0.1966, x: 0.0650 },
  { from: 11, to: 12, r: 0.3744, x: 0.1238 },
  { from: 12, to: 13, r: 1.4680, x: 1.1550 },
  { from: 13, to: 14, r: 0.5410, x: 0.7129 },
  { from: 14, to: 15, r: 0.5910, x: 0.5260 },
  { from: 15, to: 16, r: 0.7463, x: 0.5450 },
  { from: 16, to: 17, r: 1.2890, x: 1.7210 },
  { from: 17, to: 18, r: 0.7320, x: 0.5740 },
  // Lateral 1
  { from: 2, to: 19, r: 0.1640, x: 0.1565 },
  { from: 19, to: 20, r: 1.5042, x: 1.3554 },
  { from: 20, to: 21, r: 0.4095, x: 0.4784 },
  { from: 21, to: 22, r: 0.7089, x: 0.9373 },
  // Lateral 2
  { from: 3, to: 23, r: 0.4512, x: 0.3083 },
  { from: 23, to: 24, r: 0.8980, x: 0.7091 },
  { from: 24, to: 25, r: 0.8960, x: 0.7011 },
  // Lateral 3
  { from: 6, to: 26, r: 0.2030, x: 0.1034 },
  { from: 26, to: 27, r: 0.2842, x: 0.1447 },
  { from: 27, to: 28, r: 1.0590, x: 0.9337 },
  { from: 28, to: 29, r: 0.8042, x: 0.7006 },
  { from: 29, to: 30, r: 0.5075, x: 0.2585 },
  { from: 30, to: 31, r: 0.9744, x: 0.9630 },
  { from: 31, to: 32, r: 0.3105, x: 0.3619 },
  { from: 32, to: 33, r: 0.3410, x: 0.5302 },
];
