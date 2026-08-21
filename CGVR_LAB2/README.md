# CGVR Lab 2

## Midpoint Circle Drawing Algorithm

Interactive visualization of the **midpoint (Bresenham) circle** algorithm using Python OpenGL (PyOpenGL + GLUT).

Enter the circle center `(xc, yc)` and radius `r` in the terminal. The OpenGL window animates the raster points on a coordinate grid and connects revealed points into an outline.

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
python Midpoint_Circle_Algo.py
```

The terminal prompts for `xc`, `yc`, and `r`. The OpenGL window then plots the circle point-by-point.

### Keyboard and Mouse Controls

| Control | Action |
|---------|--------|
| `+` / `-` | Zoom in / out |
| Mouse wheel | Zoom in / out |
| Arrow keys | Pan the view |
| `a` | Replay the draw animation |
| `r` | Reset zoom and pan (fit to circle) |
| `q` / `Esc` | Quit |

## Files

| File | Description |
|------|-------------|
| `Midpoint_Circle_Algo.py` | Midpoint circle algorithm with OpenGL visualization |
| `requirements.txt` | Python dependencies |
| `output/` | Folder for rendered output screenshots |
