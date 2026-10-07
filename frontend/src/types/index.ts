export interface BusNode {
  id: number;
  name: string;
  x: number;
  y: number;
  z: number;
  voltage: number; // pu (e.g. 0.9131 - 1.000)
  activePower: number; // kW
  reactivePower: number; // kVAR
  isSlack?: boolean;
  branchGroup: 'trunk' | 'lateral1' | 'lateral2' | 'lateral3';
}

export interface BranchEdge {
  from: number;
  to: number;
  r: number;
  x: number;
}

export interface CanonicalClaim {
  id: string;
  title: string;
  value: string | number;
  metric: string;
  sourceRun: string;
  sourceFile: string;
  scientificImpact: string;
  status: 'VERIFIED' | 'PASS';
}

export interface ModelComparison {
  name: string;
  mape: number;
  rmse: number;
  type: string;
  rank: number;
}

export interface StalenessCondition {
  deltaT: number;
  pDrop: number;
  aoiMean: number;
  f1Score: number;
  precision: number;
  recall: number;
  fpr: number;
}
