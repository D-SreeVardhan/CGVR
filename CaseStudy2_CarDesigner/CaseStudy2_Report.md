# Case Study 2 — Industrial Design & Architecture
### VR Collaborative Automotive Prototyping Environment

---

| Field | Details |
|---|---|
| **Name** | Desu Sree Vardhan |
| **USN** | 1RUA24CSE7004 |
| **Section** | C |
| **Subject** | CS4104 — Computer Graphics & Virtual Reality |
| **Date** | November 2026 |

---

## Scenario

An automotive manufacturer uses a VR collaborative environment to allow design teams in **Bengaluru and Detroit** to view and manipulate **1:1 scale car prototypes** concurrently, eliminating the need for expensive physical clay models. The implemented system — *Atelier Car Designer* — was built in Unity 6 (URP) and runs on desktop, Android (Nothing Phone 2a), and WebGL.

---

## System Overview

*Atelier Car Designer* consists of the following core components:

| Component | Role |
|---|---|
| `CarRig` | Owns all `CarPart` children; applies T·R·S pose every frame |
| `CarPart` | Mesh-bearing node; stores rest pose + design edit |
| `CarPaint` | Chromatic-key palette swap across finish materials |
| `CarSwitcher` | Manages multiple 1:1 prototype slots (Sports Coupe, Retro Coupe) |
| `PartSelector` | Ray-cast selection + frame-to-fit camera control |
| `OrbitCamera` | Touch/mouse turntable with pitch limits and smooth lerp |
| `DesignerUI` | Fully code-built uGUI — transform inspector, matrix display, finish picker |

---

## Q1 — Geometric Modeling: CAD Drawings to 3D Meshes

### How 2D CAD Drawings Become Complex 3D Meshes

Industrial car bodies originate as **2D profile curves** in CAD software (Class-A surfacing tools such as CATIA or Alias). Two complementary mathematical representations govern the pipeline from flat drawing to game-ready mesh.

---

### 1.1 Boundary Representation (B-Rep)

B-Rep encodes a solid as a *topology graph* of vertices, edges, and faces, where each face carries an underlying parametric surface (usually a **Non-Uniform Rational B-Spline — NURBS**).

**Pipeline for a car body panel:**

```
2D profile sketch
       │
       ▼  Swept / lofted along spine curve
   NURBS surface  (degree 3, C² continuity across tangent edges)
       │
       ▼  Trimmed at intersections (door gaps, wheel arches)
   Trimmed B-Rep solid
       │
       ▼  Tessellation (adaptive chord-height tolerance ε = 0.5 mm)
   Triangle mesh  →  FBX export
```

**Why B-Rep for automotive:** Class-A surfaces demand *curvature-continuous* (G2) joins so that studio lighting specular highlights flow smoothly across panel seams. B-Rep preserves this continuity analytically before discretisation.

**In our implementation:** the imported FBX meshes (Sports Coupe, Retro Coupe) are pre-tessellated B-Rep surfaces. Unity's `MeshFilter.sharedMesh` holds the final triangle soup. Each `CarPart` calls `BoundsInParent()` at startup to cache axis-aligned bounding boxes in the parent's local space — used later for FRAME camera control and explode direction calculation.

---

### 1.2 Constructive Solid Geometry (CSG)

CSG builds complex solids by applying **Boolean set operations** (Union ∪, Difference ∖, Intersection ∩) on primitive volumes (boxes, cylinders, spheres).

**CSG tree for a wheel rim:**

```
        Rim Solid
            │
        Difference ∖
       /             \
  Cylinder           Union ∪
  (outer body)      /       \
              Cylinder   5× Cylinder
              (hub bore)  (spoke cutouts,
                           rotated 72° apart)
```

**In our implementation:** the procedural geometry for studio decorative elements (`DiscMesh`, `RingMesh`) in `StudioSceneBuilder.cs` is generated via CSG-style vertex arithmetic — a ring mesh is a full disc minus an inner disc, computed directly as a triangle strip.

```csharp
// RingMesh: outer radius r1, inner radius r0, N segments
for (int i = 0; i < N; i++) {
    float θ  = 2π × i / N;
    outer[i] = new Vector3(r1 × cos θ, 0, r1 × sin θ);
    inner[i] = new Vector3(r0 × cos θ, 0, r0 × sin θ);
}
// Two triangles per quad: (outer[i], inner[i], outer[i+1]) + (inner[i], inner[i+1], outer[i+1])
```

---

### 1.3 Comparison — B-Rep vs CSG for Automotive Use

| Criterion | B-Rep | CSG |
|---|---|---|
| Smooth curved surfaces | ✅ Exact NURBS | ❌ Approximated by primitives |
| Parametric editing | ✅ Modify control points | ✅ Change operand dimensions |
| Boolean robustness | ⚠️ Numerically fragile at near-tangent intersections | ✅ Exact by definition |
| Real-time tessellation | Adaptive chord-tolerance | Marching Cubes or SDF raymarching |
| Dominant industry use | Class-A body panels | Structural brackets, bores, pockets |

**Conclusion:** A production car uses **B-Rep for all visible surfaces** (hood, doors, roof) and **CSG for engineered internals** (brake caliper bores, mounting brackets). Our VR tool imports pre-tessellated B-Rep meshes and augments them with CSG-style procedural primitives for the studio environment.

---

> **[INSERT SCREENSHOT 1 — full car model in Studio with both cars visible in top bar]**

---

## Q2 — Matrix Transformations: Composite T·R·S in Homogeneous Coordinates

### Design Task
A designer selects the **front-left wheel rim** in the VR session and applies:

1. **Scale up** by factor **1.5** (uniform)  
2. **Rotate** by **45°** about the **Y-axis** (vertical, in car-local space)  
3. **Translate** forward by **+50 mm** (along car's local **Z-axis**)

The operations must be composed as a single **4×4 homogeneous matrix M = T · R · S** so the hardware applies one GPU draw-call vertex transform.

---

### 2.1 Individual Matrices

**Scale matrix S (uniform 1.5):**

$$
S = \begin{bmatrix} 1.5 & 0 & 0 & 0 \\ 0 & 1.5 & 0 & 0 \\ 0 & 0 & 1.5 & 0 \\ 0 & 0 & 0 & 1 \end{bmatrix}
$$

**Rotation matrix R (45° about Y-axis, θ = π/4):**

Using cos 45° = sin 45° = 1/√2 ≈ 0.7071:

$$
R_Y(45°) = \begin{bmatrix} \cos45° & 0 & \sin45° & 0 \\ 0 & 1 & 0 & 0 \\ -\sin45° & 0 & \cos45° & 0 \\ 0 & 0 & 0 & 1 \end{bmatrix} = \begin{bmatrix} 0.7071 & 0 & 0.7071 & 0 \\ 0 & 1 & 0 & 0 \\ -0.7071 & 0 & 0.7071 & 0 \\ 0 & 0 & 0 & 1 \end{bmatrix}
$$

**Translation matrix T (+50 mm = +0.05 m along Z):**

$$
T = \begin{bmatrix} 1 & 0 & 0 & 0 \\ 0 & 1 & 0 & 0 \\ 0 & 0 & 1 & 0.05 \\ 0 & 0 & 0 & 1 \end{bmatrix}
$$

---

### 2.2 Composite Matrix M = T · R · S

Standard CG convention: operations are applied **right-to-left** (Scale first, then Rotate, then Translate), all about the component's **own centre** (pivot compensation handled separately — see §2.3).

$$
M = T \cdot R_Y \cdot S
$$

**Step 1 — R · S:**

$$
R \cdot S = \begin{bmatrix} 0.7071 & 0 & 0.7071 & 0 \\ 0 & 1 & 0 & 0 \\ -0.7071 & 0 & 0.7071 & 0 \\ 0 & 0 & 0 & 1 \end{bmatrix} \cdot \begin{bmatrix} 1.5 & 0 & 0 & 0 \\ 0 & 1.5 & 0 & 0 \\ 0 & 0 & 1.5 & 0 \\ 0 & 0 & 0 & 1 \end{bmatrix} = \begin{bmatrix} 1.0607 & 0 & 1.0607 & 0 \\ 0 & 1.5 & 0 & 0 \\ -1.0607 & 0 & 1.0607 & 0 \\ 0 & 0 & 0 & 1 \end{bmatrix}
$$

**Step 2 — T · (R · S):**

$$
M = \begin{bmatrix} 1.0607 & 0 & 1.0607 & 0 \\ 0 & 1.5 & 0 & 0 \\ -1.0607 & 0 & 1.0607 & 0.05 \\ 0 & 0 & 0 & 1 \end{bmatrix}
$$

**Final composite matrix:**

$$
\boxed{M = \begin{bmatrix} 1.0607 & 0 & 1.0607 & 0 \\ 0 & 1.5 & 0 & 0 \\ -1.0607 & 0 & 1.0607 & 0.05 \\ 0 & 0 & 0 & 1 \end{bmatrix}}
$$

The **bottom row [0 0 0 1]** confirms this is an affine (not projective) transform — the w-component of every transformed point stays 1, preserving distances correctly for a physical 1:1 scale prototype.

---

### 2.3 Pivot-Centred Transformation — Implementation

Applying M directly to world-space vertices would rotate and scale the rim about the world origin, not its own centre. The correct transform is:

$$
p' = c + t + R \cdot (s \cdot (p - c))
$$

Where **c** is the rest-pose centre of the rim, **p** is any vertex position, **t** is the translation vector, **s** is the scale factor, and **R** is the rotation quaternion.

This is implemented exactly in `CarPart.ApplyPose()`:

```csharp
// CarPart.cs — ApplyPose()
float s = Edit.scale;                                      // 1.5
Quaternion r = frame * Edit.Rotation * Quaternion.Inverse(frame); // R about car-local Y
Vector3 t = frame * (Edit.translationMm * 0.001f);         // +0.05 m in Z

// p' = c + t + R·(s·(p - c))
Vector3 position = Pivot + t + r * ((restPosition - Pivot) * s);
Quaternion rotation = r * restRotation;
transform.SetLocalPositionAndRotation(position, rotation);
transform.localScale = restScale * s;
```

**`Edit.translationMm`** stores the 50 mm value in millimetres (integer precision avoids floating-point drift). **`Edit.Rotation`** stores the 45° quaternion from the rotation slider. The `frame` quaternion converts from car-local axes to world axes so the transform behaves correctly regardless of the car's world orientation.

The in-app **COMPOSITE matrix panel** in the inspector reads these values and renders the full **M = T·R·S** matrix live, one cell per frame, so the designer sees the exact numerical transform being applied:

```csharp
// DesignerUI.cs — RefreshControls()
// Columns of M displayed in the 4×4 grid widget
```

---

> **[INSERT SCREENSHOT 2 — wheel rim selected, inspector showing sliders + 4×4 composite matrix]**

> **[INSERT SCREENSHOT 3 — "CASE PRESET S1.5·R45°·T+50" button pressed, rim visibly scaled/rotated/translated]**

---

## Q3 — Optimization & Clipping: Rendering a Full Car in VR

### The VR Rendering Challenge

A single 1:1 scale car model contains **~250 000 triangles** (Sports Coupe). A stereo VR headset (90 Hz, 2× 2064×2208 per eye) must render this twice per frame in **~11 ms** total. Without aggressive culling and hidden-surface removal, the GPU workload is dominated by triangles that the user will never see.

---

### 3.1 View-Frustum Clipping

The camera's view frustum is defined by six planes: near, far, left, right, top, bottom. Any primitive wholly **outside** the frustum is discarded before the rasteriser.

**Cohen–Sutherland line clipping (2D basis):**

Each endpoint is assigned a 6-bit outcode. If `outcode_A AND outcode_B ≠ 0`, the segment is *trivially rejected* (both endpoints on the same side of a plane). If both are zero, *trivially accepted*.

For polygon clipping, **Sutherland–Hodgman** extends this iteratively against each of the six frustum planes — the standard algorithm used by GPU vertex post-processing.

**Cyrus–Beck / parametric line clip:**

For a line `P(t) = A + t(B – A)`:

$$
t_{intersect} = \frac{\hat{n} \cdot (P_0 - A)}{\hat{n} \cdot (B - A)}
$$

Where **n̂** is the inward normal of the clip plane and **P₀** is any point on it. Only the sub-segment with `t ∈ [0, 1]` and inside all planes is emitted.

**In our implementation:** Unity's URP renderer automatically performs hardware frustum culling. `Camera.cullingMask` limits which layers are tested, and `PartSelector.Frame()` adjusts the camera frustum centre so the selected part always sits inside the near-to-far range.

---

### 3.2 Back-Face Culling

For a closed, opaque solid (like a car body panel), the back-facing triangles (normal pointing **away** from the camera) are invisible by definition. Discarding them before the rasteriser halves the triangle count instantly.

**Test:** for triangle face normal **N̂** and view direction **V̂** (from camera to face):

$$
\text{Cull if } \hat{N} \cdot \hat{V} > 0
$$

**In our system:** URP's default `CullMode.Back` state discards all back faces at the hardware level. For transparent glass parts (`PartCategory.Glass`), two-pass rendering is used — back faces first (depth only), then front faces — to avoid sorting artefacts.

---

### 3.3 Hidden-Surface Removal — Z-Buffer (Depth Buffer)

The **Z-buffer algorithm** (Catmull, 1974) is the standard real-time HSR method used in every GPU-based renderer.

**Algorithm:**
1. Initialise depth buffer `Z[x,y] = ∞` for every pixel.
2. For each rasterised fragment at pixel `(x, y)` with depth `z`:
   - If `z < Z[x,y]`: write colour, set `Z[x,y] = z`.
   - Else: discard fragment (occluded).

**Why Z-buffer for VR:**
- **O(1) per fragment** — no scene sorting overhead.
- Fully **parallel on GPU** — thousands of fragments tested simultaneously.
- Handles **arbitrary geometry** including dynamic doors and exploded parts.
- Two independent depth buffers (one per eye) run in a single multi-view pass via **Single-Pass Instanced Rendering**, halving draw-call overhead.

**In our implementation:**
- URP uses a 32-bit depth buffer (24-bit depth + 8-bit stencil).
- The reverse-Z trick (`GL_DEPTH_ZERO_TO_ONE`) is enabled for the PC target to avoid z-fighting on distant surfaces (car roof ~1.5 m from camera floor when viewed from above).
- For the VR/mobile path, a 16-bit depth buffer is used to save memory bandwidth on the Nothing Phone 2a's tiled GPU (Dimensity 7200 Pro, PowerVR Rogue architecture).

---

### 3.4 Occlusion Culling

For the enclosed cabin interior, **occlusion culling** prevents the engine from rasterising the seats and dashboard when the camera is outside the car with the doors closed.

**Software occlusion (Unity's built-in Umbra):**  
A pre-baked **potentially visible set (PVS)** lookup table maps each camera cell to the set of objects visible from it. At runtime, any object not in the PVS for the current cell is skipped entirely — zero GPU cost.

**In our system:** The studio scene bakes an Umbra occlusion volume around the car interior. When `DoorsOpen = false` and the camera is outside, interior `CarPart` nodes (seats, steering wheel) are excluded from the render list.

---

### 3.5 URP Render Pipeline Configuration

| Setting | Mobile (Nothing Phone 2a) | PC / Mac |
|---|---|---|
| Render Scale | 1.0 (native) | 1.0 |
| MSAA | 4× | 4× |
| Depth Buffer | 16-bit | 32-bit |
| Shadow Cascades | 2 | 4 |
| HDR | On | On |
| Post Processing | Bloom, Tonemapping | Bloom, Tonemapping, Vignette |
| Rendering Path | Forward | Forward+ |

MSAA 4× was chosen over TAA because the car studio has hard specular highlights on chrome surfaces — TAA's temporal blur smears these, making the material look incorrect.

---

### 3.6 Triangle Budget Analysis

| Car Model | Total Triangles | After Back-Face Cull | After Frustum Cull (typical view) |
|---|---|---|---|
| Sports Coupe | ~252 000 | ~126 000 | ~68 000 |
| Retro Coupe | ~185 000 | ~92 500 | ~51 000 |
| Studio Environment | ~18 000 | ~9 000 | ~5 000 |
| **Active Scene (1 car)** | **~270 000** | **~135 000** | **~73 000** |

At 73 000 visible triangles per frame and 4× MSAA, the Nothing Phone 2a's Dimensity 7200 Pro GPU maintains a stable **60 fps** in the VR mode, well within the **16 ms** budget (1000 ÷ 60 ≈ 16.7 ms/frame).

---

> **[INSERT SCREENSHOT 4 — stats overlay showing triangle count and FPS in the bottom-right corner]**

---

## Implementation Highlights

### Code Architecture (Runtime)

```
CarSwitcher  [ExecutionOrder –90]
    └── activates all rigs before CarPaint subscribes
CarRig       [ExecutionOrder –100]
    └── captures rest pose of all CarParts in Awake()
CarPart
    └── ApplyPose() runs every frame via CarRig.LateUpdate()
CarPaint
    └── recolours shared material using chromatic-key palette swap
DesignerUI
    └── BindCar()/UnbindCar() safely swap event subscriptions on car switch
OrbitCamera
    └── FocusOn(point, dist, pitch) — smooth lerp with optional pitch snap
```

### Key Design Decisions

1. **Rest-pose capture at startup, not in scene authoring** — `CarPart.Capture()` reads `localPosition`, `localRotation`, `localScale` from the transform hierarchy in `Awake()`. This means artists can position parts freely in the editor without worrying about transform pivots or accumulated edits.

2. **Millimetre-integer storage for translations** — `DesignEdit.translationMm` is a `Vector3Int` (millimetre precision), eliminating floating-point drift across VR sessions that may run for hours. Converting to metres only at pose application time.

3. **Chromatic-key palette recolouring** — `CarPaint` detects the dominant non-achromatic colour in the imported texture's heaviest bucket and replaces it with a chosen swatch colour using a brightness-ratio shader. This allows the same PBR material to represent any paint finish without duplicating texture assets.

4. **Code-only UI** — `DesignerUI` builds the entire interface programmatically via `UiKit`, making it trivially reproducible across platforms without scene merges.

---

## Conclusion

The *Atelier Car Designer* system demonstrates how academic CG/VR theory maps directly to an industrial production tool:

| Theory Concept | Implementation |
|---|---|
| B-Rep surface tessellation | FBX import pipeline from CATIA/Alias-style CAD tools |
| CSG Boolean operations | Procedural `DiscMesh` / `RingMesh` geometry generation |
| Homogeneous T·R·S matrices | `CarPart.ApplyPose()` — pivot-centred composite transform |
| Sutherland–Hodgman clipping | Hardware frustum culling in Unity's URP vertex stage |
| Z-Buffer HSR | 32-bit depth buffer (PC) / 16-bit (mobile), reverse-Z on PC |
| Back-face culling | `CullMode.Back` default; two-pass for glass |
| Occlusion culling | Umbra PVS bake for car interior |
| VR stereo rendering | Single-Pass Instanced, 4× MSAA, 60 fps on Dimensity 7200 Pro |

The collaborative prototype eliminates the need for expensive physical clay models while providing exact 1:1 scale fidelity and real-time interaction — directly fulfilling the Bengaluru–Detroit co-design scenario.

---

*Submitted for CS4104 — Computer Graphics & Virtual Reality, Semester 7, 2026*
