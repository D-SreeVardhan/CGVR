# CGVR Lab 10

## 3D Viewing Pipeline — Unity

Demonstrates the complete real-time 3D viewing pipeline using Unity's live GPU matrices:

```
Model Space  →  World Space  →  Eye/Camera Space
     →  Clip Space  →  NDC  →  Screen Space
```

A live panel tracks every stage for the selected object, and a split-screen view lets
you directly compare **Perspective** vs **Orthographic** projection side by side.

---

## What it Shows

| Pipeline Stage | What Happens | Data Shown |
|---|---|---|
| ① Model → World | Object's transform applied | position, rotation, scale |
| ② World → Eye | Scene seen from camera | worldToCameraMatrix |
| ③ Eye → Clip | Projection (perspective / ortho) | projectionMatrix (4×4) |
| ④ Clip → NDC | Perspective divide ÷ w | clip coords → (x/w, y/w, z/w) |
| ⑤ NDC → Screen | Viewport mapping | screen pixel (x, y), depth |

---

## Unity Setup

### Step 1 — Use the existing Unity project
Re-use the CGVR_Lab9 Unity project (or any 3D / URP Unity 6 project).

### Step 2 — Create a new Scene
**File → New Scene → Save** (name it `Lab10`)

### Step 3 — Add the script
1. Right-click `Assets` → **Create → C# Script** → name it `Lab10Controller`
2. Open it and **replace all contents** with `Lab10Controller.cs`
3. Save (`⌘ S`)

### Step 4 — Attach to camera
1. Click **Main Camera** in the Hierarchy
2. **Inspector → Add Component** → search `Lab10Controller` → add
3. Press **▶ Play**

> **Note:** If you get an input error, go to  
> **Edit → Project Settings → Player → Other Settings → Active Input Handling → Both**

---

## Controls

| Key | Action |
|-----|--------|
| `← → ↑ ↓` | Orbit camera around the scene |
| `+` / `-` | Zoom in / out |
| `F` / `G` | Widen / narrow field of view |
| `V` | Toggle split view (Perspective \| Orthographic) |
| `1` / `2` / `3` | Select object — updates all pipeline stage data |
| `H` | Show / hide the pipeline panel |
| Scroll wheel | Zoom |

---

## Scene Contents (built at runtime)

| Object | Shape | Colour | Position |
|--------|-------|--------|----------|
| Cube | Box | Red | (-3.5, 0.5, 2) |
| Sphere | Sphere | Blue | (0, 0.5, 0) |
| Cylinder | Cylinder | Yellow | (3.5, 1.0, -2) |
| Floor | Plane | Dark grey | (0, 0, 0) |

Objects are placed at different Z-depths deliberately — this makes the perspective
foreshortening effect clearly visible when you switch projection modes.

---

## Output

| File | Description |
|------|-------------|
| `Lab10_ViewingPipeline.png` | Split-screen: perspective vs orthographic with live pipeline panel |

---

## Files

| File | Description |
|------|-------------|
| `Lab10Controller.cs` | Unity C# script — self-contained, attach to Main Camera |
| `README.md` | This setup guide |
| `output/` | Screenshots from Play mode |
