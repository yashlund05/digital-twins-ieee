# Design Specification: Ayush Frontend WebGL & React Three Fiber Platform

**Author**: Ayush  
**Date**: 2026-10-06  
**Status**: APPROVED  
**Target Platform**: Localhost Port 5569 (Vite + React 18 + R3F + Tailwind CSS)

---

## 1. Executive Summary

This specification defines the migration of the Digital Twin user experience from a standard Python dashboard to a hardware-accelerated creative engineering platform. Based on the `ayush-frontend` skill specifications, this interface combines:
1. **Shader Gradient**: Real-time GLSL Simplex/Perlin noise fluid animated canvas background.
2. **React Three Fiber (R3F) 3D Feeder Inspector**: Interactive 3D spatial representation of the IEEE 33-Bus distribution network with OrbitControls, node voltage drop colormaps, and branch connection lines.
3. **Liquid Metal Logo**: WebGL fragment shader simulation rendering the Digital Twin insignia with real-time fluid simplex distortion and specular chrome highlights.
4. **Apple-Inspired Liquid Glass UI**: Refractive UI surfaces featuring hardware-accelerated backdrop blur (`blur(20px)`), saturation boost (`180%`), specular rim highlights, and dual-depth inset shadows.
5. **Bidirectional Data Connectors**: Direct binding to verified research data (E4 baseline $F_1 = 0.9780$, AoI degradation surface $\Delta F_1 = -0.0018 \cdot \text{AoI}$, dynamic threshold mitigation $\tau(\text{AoI})$, and canonical claims C01–C13).

---

## 2. Directory & Component Architecture

All files are created locally under `frontend/` without git commits or pushes:

```
frontend/
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.js
├── postcss.config.js
└── src/
    ├── index.css                        # Glassmorphism utilities & cyber palette
    ├── main.tsx                         # Entry point
    ├── App.tsx                          # App shell, tab router, ambient lighting
    ├── types/
    │   └── index.ts                     # TypeScript definitions for bus, claims, metrics
    ├── data/
    │   ├── digitalTwinData.ts           # Canonical metrics, C01-C13 registry, baseline models
    │   └── ieee33BusData.ts             # 33 nodes coordinates, voltages, active power, branches
    ├── components/
    │   ├── canvas/
    │   │   ├── FluidShaderBackground.tsx # Three.js GLSL Perlin mesh fluid background
    │   │   ├── Feeder3DCanvas.tsx        # R3F Canvas with OrbitControls, lighting, starfield
    │   │   ├── FeederGrid3D.tsx          # 33 Bus spheres, branch cylinders, voltage color scale
    │   │   └── LiquidChromeLogo.tsx      # WebGL simplex displacement chrome logo canvas
    │   ├── ui/
    │   │   ├── LiquidGlassCard.tsx       # Apple liquid glass container
    │   │   ├── LiquidGlassButton.tsx     # Pill & rounded glass action buttons
    │   │   ├── MetricChip.tsx            # Glowing KPI chip with delta badge
    │   │   └── NavigationBar.tsx         # Floating header bar
    │   └── views/
    │       ├── ExecutiveDashboard.tsx    # KPIs, live state indicator, architecture flow
    │       ├── FeederInspector.tsx       # 3D interactive grid explorer with bus inspector
    │       ├── StalenessStudio.tsx       # Real-time AoI sliders, 3D degradation surface
    │       ├── MitigationLab.tsx         # Interactive AoI-adaptive thresholding & representation switch
    │       └── ClaimsAuditRegistry.tsx   # Canonical claims C01-C13 machine verification table
```

---

## 3. WebGL & Shader Specifications

### 3.1 Fluid Shader Gradient
- Vertex shader: Deforms a 128x128 plane grid using 3D Simplex noise with time and frequency uniforms.
- Fragment shader: Blends three key brand tones:
  - Base Deep Slate: `#070A14`
  - Electric Cyan: `#0EA5E9`
  - Deep Violet: `#8B5CF6`
- Includes subtle pseudo-random film grain to prevent banding artifacts on 8-bit displays.

### 3.2 Liquid Metal Logo Shader
- Real-time 2D fluid displacement shader ported from `collidingScopes/liquid-logo`.
- Quad geometry rendered with uniform `u_time`, `u_speed = 1.0`, `u_intensity = 1.2`, and `u_colorShift = 0.5`.
- Procedural noise highlights simulating liquid chrome reflection.

### 3.3 IEEE 33-Bus 3D Network
- Nodes: 33 instances of `SphereGeometry`, colored dynamically using an HSL colormap based on nodal voltage:
  - $V = 1.00\,$pu $\rightarrow$ Neon Cyan (`#06B6D4`)
  - $V \le 0.92\,$pu $\rightarrow$ High-voltage drop Warning Coral (`#F43F5E`)
- Edges: Glowing line segments connecting bus pairs `(from_bus, to_bus)` according to Baran & Wu feeder topology.
- Interactive Raycaster: Hovering over any bus opens an interactive floating glass popover displaying Voltage ($V$), Active Power ($P$), Reactive Power ($Q$), and Lateral Branch identity.

---

## 4. Verification & Testing Strategy

1. **Scaffold & Build**: Verify `npm install` and `npm run build` execute without TypeScript or bundler errors.
2. **Local Daemon**: Launch Vite development server on `http://127.0.0.1:5569`.
3. **HTTP Health Check**: Query status code via PowerShell (`Invoke-WebRequest -Uri 'http://127.0.0.1:5569'`) expecting `200 OK`.
4. **Shader Compilation**: Verify zero WebGL shader errors in runtime browser console.
5. **Research Accuracy**: Verify all metrics in `digitalTwinData.ts` match canonical frozen experiments (E4, E5, E10, E11, E12, E13).
