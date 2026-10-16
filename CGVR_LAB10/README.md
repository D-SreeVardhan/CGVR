# CGVR Lab 10

## 3D Viewing Pipeline — Projection and Viewport Mapping

Implements the complete **3D Viewing Pipeline** using OpenGL + GLSL shaders, with every transformation stage displayed live in the info panel.

### Pipeline Stages

```
Model Space ──[Model Matrix]──► World Space
World Space ──[View  Matrix]──► Eye / Camera Space
Eye Space   ──[Proj  Matrix]──► Clip Space
Clip Space  ──[÷ w  (P-div)]──► NDC Space   ∈ [-1, 1]³
NDC Space   ──[Viewport Map]──► Screen Space  [px]
```

### Stage Details

| Stage | Transform | Description |
|-------|-----------|-------------|
| **Model → World** | `M = R × S` | Object rotation & scale |
| **World → Eye** | `V = LookAt(eye, center, up)` | Camera orientation |
| **Eye → Clip** | `P = Perspective` or `Ortho` | Frustum projection |
| **Clip → NDC** | `x_ndc = x_clip / w_clip` | Perspective divide |
| **NDC → Screen** | `x_s = (x_ndc+1) × W/2` | Viewport mapping |

The left panel shows the **actual 4×4 matrices** for stages 1–3, updated live as you orbit the camera or rotate the cube.

### Split View (`v` key)

Press `v` to see **Perspective** (left) and **Orthographic** (right) projections rendered simultaneously — the classic way to observe the difference parallel vs convergent projection makes on depth perception.

## Output

```text
output/
```

## Requirements

```bash
pip install -r requirements.txt
```

## How to Run

```bash
python Viewing_Pipeline_3D.py
```

### Controls

| Key | Action |
|-----|--------|
| Arrow keys | Orbit camera |
| `[` / `]` | Zoom in / out |
| `W` / `S` | Pitch main cube |
| `A` / `D` | Yaw main cube |
| `o` | Toggle Perspective ↔ Orthographic |
| `v` | Split view (Perspective \| Orthographic) |
| `+` / `-` | FOV (perspective) or ortho size |
| Mouse drag | Orbit camera |
| `r` | Reset all |
| `p` | Toggle info panel |
| `Esc` | Quit |

## Files

| File | Description |
|------|-------------|
| `Viewing_Pipeline_3D.py` | Full MVP pipeline demo with live matrices |
| `requirements.txt` | Python dependencies |
| `output/` | Folder for rendered output screenshots |
