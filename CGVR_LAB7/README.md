# CGVR Lab 7

## Phong Illumination Model for a 3D Object

Implements the **Phong illumination model** on a 3D sphere using GLSL vertex and fragment shaders (OpenGL 2.1 / GLSL 1.20, macOS compatible).

### Model

The Phong model computes the final colour as the sum of three independent components:

```
I = Ia + Id + Is
```

| Component | Formula | Description |
|-----------|---------|-------------|
| **Ambient** | `Ia = Ka × La` | constant background fill |
| **Diffuse** | `Id = Kd × max(N·L, 0) × Ld` | matte, angle-dependent |
| **Specular** | `Is = Ks × max(R·V, 0)^n × Ls` | shiny highlight |

Where:
- **N** = surface normal
- **L** = normalize(lightPos − fragPos)
- **V** = normalize(viewPos  − fragPos)
- **R** = reflect(−L, N) = 2(N·L)N − L
- **n** = shininess exponent

### Phong vs Gouraud

| Mode | Where lighting is computed |
|------|---------------------------|
| **Phong** (default) | Per-fragment — accurate highlight shape |
| **Gouraud** | Per-vertex — interpolated, cheaper but less accurate |

Press `g` to toggle between them and observe the specular highlight difference, especially at low shininess.

## Output

Add rendered screenshots here:

```text
output/
```

## Requirements

```bash
pip install -r requirements.txt
```

## How to Run

```bash
python Phong_Illumination.py
```

### Keyboard Controls

| Key | Action |
|-----|--------|
| `1` / `2` / `3` | Toggle Ambient / Diffuse / Specular |
| `g` | Switch Phong ↔ Gouraud shading |
| `+` / `-` | Shininess ×2 / ÷2 |
| Arrow keys | Move light (X / Y axis) |
| `[` / `]` | Move light (Z axis) |
| Mouse drag | Orbit the sphere |
| `r` | Reset all parameters |
| `p` | Toggle info panel |
| `Esc` | Quit |

## Files

| File | Description |
|------|-------------|
| `Phong_Illumination.py` | Phong model with Phong/Gouraud shader toggle |
| `requirements.txt` | Python dependencies |
| `output/` | Folder for rendered output screenshots |
