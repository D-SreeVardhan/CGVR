# CGVR Lab 1

## DDA and Bresenham's Line Drawing Algorithms

This experiment visualizes two classic line rasterization algorithms using Python OpenGL (PyOpenGL + GLUT):

1. **Digital Differential Analyzer (DDA)** — incrementally calculates the next point using floating-point arithmetic.
2. **Bresenham's Line Algorithm** — plots the line with efficient integer-based error calculations.

Enter the start and end coordinates in the terminal, then select the algorithm. The OpenGL window animates the line by plotting its points one at a time on a coordinate grid.

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
python Bresenhams_Line_Algo.py
```

The terminal prompts for the line's start point, end point, and the algorithm to use. The OpenGL window then displays the animated line.

### Keyboard and Mouse Controls

| Control | Action |
|---------|--------|
| `+` / `-` | Zoom in / out |
| Mouse wheel | Zoom in / out |
| Arrow keys | Pan the view |
| `r` | Reset zoom and pan |
| `l` | Toggle point-coordinate labels |
| `q` | Quit |

## Files

| File | Description |
|------|-------------|
| `Bresenhams_Line_Algo.py` | Main program: interactive DDA and Bresenham line visualization |
| `requirements.txt` | Python dependencies |
| `output/` | Folder for rendered output screenshots |
