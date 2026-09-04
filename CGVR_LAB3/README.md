# CGVR Lab 3

## 2D Transformations using Homogeneous Coordinates

Interactive visualization of 2D geometric transformations with **3×3 homogeneous matrices**, using Python OpenGL (PyOpenGL + GLUT).

Enter one or more points (vertices) in the terminal, choose a transformation, then compare:

- **Blue dashed** — original shape
- **Red solid** — transformed shape

### Supported Transformations

1. **Translation** — by `(tx, ty)`
2. **Rotation** — CCR or CR, angle in degrees, about origin or an arbitrary pivot
3. **Scaling** — by `(sx, sy)` about origin or an arbitrary fixed point
4. **Reflection** — over the X or Y axis, about origin or an arbitrary point
5. **Shearing** — along X, along Y, or both (`shx`, `shy`), about origin or a reference point

## Output

Add your rendered screenshots to this folder:

```text
output/
```

## Requirements

```bash
pip install -r requirements.txt
```

## How to Run

```bash
python Transformations_2D.py
```

Follow the terminal prompts for vertices and transformation parameters. The OpenGL window then shows both shapes on a coordinate grid.

### Keyboard and Mouse Controls

| Control | Action |
|---------|--------|
| `+` / `-` | Zoom in / out |
| Mouse wheel | Zoom in / out |
| Arrow keys | Pan the view |
| `l` | Toggle vertex-coordinate labels |
| `m` | Toggle calculation / math panel |
| `r` | Reset zoom and pan |
| `q` / `Esc` | Quit |

## Files

| File | Description |
|------|-------------|
| `Transformations_2D.py` | Homogeneous 2D transforms with OpenGL visualization |
| `requirements.txt` | Python dependencies |
| `output/` | Folder for rendered output screenshots |
