# CGVR Lab 8

## Vertex and Fragment Shaders — Unity

A regular icosahedron (20 faces, 30 edges, 12 vertices) drawn with a custom two-stage shader.

1. **Vertex shader** — runs once per corner. Multiplies position by the MVP matrix,
   transforms the normal to world space, and passes both alongside the per-vertex color.
2. **Fragment shader** — runs once per pixel. Reads the rasterizer-interpolated values
   and writes one of three effects selectable at runtime.

---

## What the shader demonstrates

| Stage | OpenGL equivalent | What this lab does |
|-------|-------------------|--------------------|
| Vertex | `gl_Position = uMVP * aPos` | `TransformObjectToHClip(positionOS)` |
| Vertex | `vColor = aColor` | Per-vertex HSV gradient passed as COLOR |
| Vertex | `vNormal = normalMatrix * aNormal` | `TransformObjectToWorldNormal` |
| Rasterizer | interpolation | Blends color + normal across each triangle |
| Fragment | `gl_FragColor = vColor` | Mode 0: raw vertex gradient |
| Fragment | edge / vertex detection | Mode 1: barycentric-based wireframe overlay |
| Fragment | `N·L + specular` | Mode 2: per-pixel Phong lighting |

Press **M** to cycle the fragment shader. The mesh never changes — only the per-pixel stage does.

---

## Fragment modes

| Mode | What the fragment shader writes |
|------|---------------------------------|
| **Vertex Gradient** | The color interpolated from the three corners of each face — pure rasterizer output |
| **Gradient + Edges** | Gradient darkened at edges (barycentric min → 0), white dots at vertices (barycentric max → 1) |
| **Lit + Edges** | N·L diffuse + specular computed per pixel from the interpolated face normal, edges overlaid |

---

## Unity Setup

Use a **Unity 6 Universal 3D (URP)** project.

1. Copy `Lab8Shader.shader` into `Assets/Resources/`.
   Create the `Resources` folder if it is not there.
2. Copy `Lab8Controller.cs` into `Assets/`.
3. Select **Main Camera** → **Add Component → Lab8Controller** → Press **Play**.

The icosahedron is procedurally built at runtime.

---

## Controls

| Key | Action |
|-----|--------|
| Left-drag / Arrow keys | Rotate |
| Scroll / `+` `-` | Scale |
| `M` | Cycle fragment shader mode |
| `Space` | Pause / resume auto-spin |
| `R` | Reset transform |

---

## Vertex color scheme

Each of the 12 icosahedron vertices has a unique color derived from its position:

- **Hue** = azimuthal angle around the Y axis → full rainbow spectrum around the equator
- **Saturation / Value** = driven by elevation → crown is bright, base is deep

The rasterizer blends these continuously across all 20 faces, visibly demonstrating the vertex-to-fragment interpolation the programmable pipeline performs.

---

## Output

| File | Description |
|------|-------------|
| `Screenshot 2026-10-23 at 12.06.54 PM.png` | Vertex gradient mode — raw rasterizer interpolation |

---

## Files

| File | Description |
|------|-------------|
| `Lab8Controller.cs` | Builds the icosahedron mesh, drives interaction, draws the HUD |
| `Lab8Shader.shader` | URP HLSL vertex and fragment shader |
| `README.md` | This setup guide |
| `output/` | Play-mode screenshots |
