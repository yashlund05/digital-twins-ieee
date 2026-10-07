# Ayush Frontend WebGL & React Three Fiber Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a high-performance React 18 + React Three Fiber + Liquid Glass WebGL frontend on port 5569 with interactive 3D feeder grid, liquid metal chrome logo, dynamic GLSL fluid shaders, and live scientific data connectors.

**Architecture:** A standalone React 18 / Vite TypeScript project in `frontend/` powered by Three.js and `@react-three/fiber`, styled with Apple-inspired liquid glassmorphism and Tailwind CSS, wired directly to canonical digital twin research datasets.

**Tech Stack:** React 18, Vite, TypeScript, Three.js, `@react-three/fiber`, `@react-three/drei`, Tailwind CSS, Lucide React, Canvas WebGL shaders.

**Spec:** [docs/superpowers/specs/2026-10-06-ayush-frontend-webgl-design.md](file:///c:/Users/ARYAN%20-%20AYUSH/OneDrive/Desktop/digital%20twin/docs/superpowers/specs/2026-10-06-ayush-frontend-webgl-design.md)

## Global Constraints
- Absolute prohibition against git commit or git push (`git commit` and `git push` must NEVER be run).
- Author display name is exclusively "Ayush".
- Server must bind to port 5569.
- Numerical values must strictly reflect canonical frozen experiments E4–E13.

## Review Focus
1. Port collision: Stop existing Streamlit daemon on 5569 before launching Vite dev server on 5569.
2. WebGL fallback: Canvas context loss handling and high-DPI scaling.
3. 3D Raycasting: Clean hover state management on IEEE 33-bus nodes without performance stutter.
4. Mathematical accuracy: Client-side degradation surface matches $\Delta F_1 = -0.0018 \cdot \text{AoI}$.
5. Glass rendering: Specular highlight and backdrop filter compatibility across Chromium/WebKit browsers.

---

### Task 1: Project Scaffolding & Dependencies Setup

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`
- Create: `frontend/index.html`

- [ ] **Step 1: Write configuration files and package.json**
- [ ] **Step 2: Run npm install in frontend directory**
- [ ] **Step 3: Verify dependencies installed without peer resolution errors**

---

### Task 2: Data Models & Research Connectors

**Files:**
- Create: `frontend/src/types/index.ts`
- Create: `frontend/src/data/digitalTwinData.ts`
- Create: `frontend/src/data/ieee33BusData.ts`

- [ ] **Step 1: Define TypeScript interfaces for 3D Bus nodes, claims, metrics, and simulation parameters**
- [ ] **Step 2: Implement canonical digital twin dataset (C01–C13 claims, E4–E13 frozen benchmarks, baseline MAPEs)**
- [ ] **Step 3: Implement IEEE 33-bus 3D topological coordinates, voltages ($V_{\min} = 0.9131\,$pu at Bus 18), and branch pairs**

---

### Task 3: Liquid Glass & UI Component System

**Files:**
- Create: `frontend/src/index.css`
- Create: `frontend/src/components/ui/LiquidGlassCard.tsx`
- Create: `frontend/src/components/ui/LiquidGlassButton.tsx`
- Create: `frontend/src/components/ui/MetricChip.tsx`
- Create: `frontend/src/components/ui/NavigationBar.tsx`

- [ ] **Step 1: Implement Apple-inspired liquid glass styles in `index.css` (`backdrop-filter`, specular rim lighting, glow animations)**
- [ ] **Step 2: Implement `LiquidGlassCard` and `LiquidGlassButton` components from `ayush-frontend` examples**
- [ ] **Step 3: Implement glowing `MetricChip` and floating `NavigationBar` with tab switching**

---

### Task 4: WebGL Shaders & React Three Fiber 3D Canvas

**Files:**
- Create: `frontend/src/components/canvas/FluidShaderBackground.tsx`
- Create: `frontend/src/components/canvas/LiquidChromeLogo.tsx`
- Create: `frontend/src/components/canvas/Feeder3DCanvas.tsx`
- Create: `frontend/src/components/canvas/FeederGrid3D.tsx`

- [ ] **Step 1: Implement `FluidShaderBackground` with Three.js custom Perlin noise vertex and fragment shaders**
- [ ] **Step 2: Implement `LiquidChromeLogo` using real-time WebGL simplex noise displacement and chrome highlights**
- [ ] **Step 3: Implement `Feeder3DCanvas` & `FeederGrid3D` rendering the 33-bus system with OrbitControls, node voltage colormaps, glowing links, and interactive tooltip inspection**

---

### Task 5: Interactive Research Views

**Files:**
- Create: `frontend/src/components/views/ExecutiveDashboard.tsx`
- Create: `frontend/src/components/views/FeederInspector.tsx`
- Create: `frontend/src/components/views/StalenessStudio.tsx`
- Create: `frontend/src/components/views/MitigationLab.tsx`
- Create: `frontend/src/components/views/ClaimsAuditRegistry.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/main.tsx`

- [ ] **Step 1: Build Executive Dashboard view with liquid glass KPIs and architecture flow**
- [ ] **Step 2: Build 3D Feeder Inspector view with real-time node metrics inspector**
- [ ] **Step 3: Build Staleness Studio view with interactive sliders and client-side degradation curves**
- [ ] **Step 4: Build Mitigation Lab view with dynamic threshold slider and mode-switching comparisons**
- [ ] **Step 5: Build Claims Audit Registry view with C01–C13 status table**
- [ ] **Step 6: Assemble master `App.tsx` with view routing and ambient sound/visual toggle**

---

### Task 6: Server Transition & Live Verification

- [ ] **Step 1: Terminate background Streamlit process on port 5569**
- [ ] **Step 2: Launch Vite development server on port 5569 as background daemon**
- [ ] **Step 3: Verify `http://localhost:5569` returns `HTTP 200 OK`**
- [ ] **Step 4: Verify `git status` has zero commits and zero pushes**
