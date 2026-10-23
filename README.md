# Computer Graphics and Virtual Reality — Lab Record

| | |
|---|---|
| **Subject** | Computer Graphics and Virtual Reality |
| **Student** | Desu Sree Vardhan |
| **USN** | 1RUA24CSE7004 |
| **Stack** | Python · PyOpenGL · GLSL · Unity 6 · C# · URP |

---

## Labs

| # | Experiment | Tech | Concepts |
|---|-----------|------|---------|
| [1](CGVR_LAB1/) | DDA and Bresenham's Line Drawing | Python · PyOpenGL | Rasterisation, incremental line algorithms |
| [2](CGVR_LAB2/) | Midpoint Circle Drawing | Python · PyOpenGL | Midpoint decision parameter, 8-way symmetry |
| [3](CGVR_LAB3/) | 2D Transformations — Homogeneous Coordinates | Python · PyOpenGL | Translation, rotation, scaling via 3×3 matrices |
| [4](CGVR_LAB4/) | Composite 2D Transformations | Python · PyOpenGL | Matrix concatenation, pivot-point transforms |
| [5](CGVR_LAB5/) | Cohen–Sutherland Line Clipping | Python · PyOpenGL | Outcodes, Clip–Sutherland reject/trivial-accept |
| [6](CGVR_LAB6/) | Z-Buffer Hidden Surface Removal | Python · PyOpenGL | Depth buffer, painter's algorithm comparison |
| [7](CGVR_LAB7/) | Phong Illumination Model | Python · PyOpenGL · GLSL | Ambient/diffuse/specular, per-fragment shading |
| [8](CGVR_LAB8/) | Vertex and Fragment Shaders | Unity 6 · URP · HLSL | MVP transform, barycentric edge detection, N·L lighting |
| [9](CGVR_LAB9/) | Simple Interactive 3D Scene | Unity 6 · URP · C# | Runtime scene building, CharacterController, interact mode |
| [10](CGVR_LAB10/) | 3D Viewing Pipeline | Unity 6 · URP · C# | Model→World→Eye→Clip→NDC→Screen, perspective vs orthographic |

---

## Lab Highlights

### Labs 1 – 7 · Python / PyOpenGL
Implemented in pure Python using PyOpenGL and GLUT. Each lab runs as a standalone script with live keyboard controls and an on-screen algorithm panel.

### Lab 8 · Vertex and Fragment Shaders
A procedurally generated icosahedron rendered by a custom URP HLSL shader. The vertex shader transforms each of the 12 corners and passes a position-derived HSV color; the fragment shader cycles through three modes — raw vertex gradient, barycentric wireframe overlay, and per-pixel N·L + specular lighting.

![Lab 8](CGVR_LAB8/output/Screenshot%202026-10-23%20at%2012.06.54%E2%80%AFPM.png)

### Lab 9 · Interactive 3D Scene
A Unity scene built entirely at runtime from a single C# script attached to the Main Camera. A `CharacterController` provides gravity and collision so the camera cannot clip through the floor or objects. Tab switches between first-person camera mode and an interact mode where objects can be selected, translated, rotated, and scaled.

![Lab 9](CGVR_LAB9/output/Lab9_CameraMode.png)

### Lab 10 · 3D Viewing Pipeline
Split-screen Unity scene with a perspective camera on the left and an orthographic camera on the right — both driven by the same orbit. A live HUD panel tracks every stage of the GPU pipeline (model matrix → view matrix → projection matrix → NDC → screen coordinates) for a selected object, updating in real time as the camera moves.

![Lab 10](CGVR_LAB10/output/Screenshot%202026-10-23%20at%2011.30.45%E2%80%AFPM.png)

---

## Running the Python labs

```bash
cd CGVR_LAB<N>
pip install -r requirements.txt   # PyOpenGL + PyOpenGL_accelerate
python <script>.py
```

## Running the Unity labs (8, 9, 10)

1. Open the project folder in **Unity Hub** (Unity 6, Universal 3D template).
2. Attach the lab script to **Main Camera**.
3. **Edit → Project Settings → Player → Active Input Handling → Both**.
4. Press **▶ Play**.

Each script builds its entire scene at runtime — no prefabs or manual scene setup required.
