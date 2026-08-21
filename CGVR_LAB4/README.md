# CGVR Lab 4

## Composite 2D Transformations using Matrix Representation

Implements **composite transformations** by multiplying homogeneous 3×3 matrices in OpenGL (PyOpenGL + GLUT).

You enter a shape once, then chain any of Lab 3’s four operations. The program builds one composite matrix

```text
M = Tn · … · T2 · T1
```

and applies **M** to every vertex (first transform entered is applied first).

### Supported Building Blocks (same as Lab 3)

1. **Translation** — by `(tx, ty)`
2. **Rotation** — CCR or CR, angle in degrees, about origin or an arbitrary pivot
3. **Scaling** — by `(sx, sy)` about origin or an arbitrary fixed point
4. **Reflection** — over the X or Y axis, about origin or an arbitrary point

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
python Composite_Transformations_2D.py
```

1. Enter shape vertices (1 or more).
2. Enter how many transforms to compose.
3. For each step, pick Translation / Rotation / Scaling / Reflection and its parameters.
4. OpenGL shows original (blue dashed) vs composite result (red solid).

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
| `Composite_Transformations_2D.py` | Composite homogeneous transforms with OpenGL visualization |
| `requirements.txt` | Python dependencies |
| `output/` | Folder for rendered output screenshots |
