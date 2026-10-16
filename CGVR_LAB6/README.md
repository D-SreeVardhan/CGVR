# CGVR Lab 6

## Z-Buffer Algorithm for Hidden Surface Removal

Implements the **Z-buffer (depth buffer)** algorithm using Python OpenGL (PyOpenGL + GLUT).

Five overlapping coloured quads are placed at different depths. Press `z` to toggle the Z-buffer on and off — when disabled, the last-drawn polygon overrides all others regardless of depth, making the artefact visible.

### Algorithm

```
init depthBuffer[x][y] = INF  for all pixels
for each polygon:
    for each fragment (x, y, z):
        if z < depthBuffer[x][y]:
            colorBuffer[x][y] = fragment.color
            depthBuffer[x][y] = z
```

- **Z-Buffer ON** — closest fragment wins; correct depth order shown.
- **Z-Buffer OFF** — last drawn polygon wins; hidden surfaces appear.

## Output

Add your rendered screenshots here:

```text
output/
```

## Requirements

```bash
pip install -r requirements.txt
```

## How to Run

```bash
python Z_Buffer_Hidden_Surface.py
```

### Keyboard Controls

| Control | Action |
|---------|--------|
| `z` | Toggle Z-buffer on / off |
| Arrow keys | Orbit the scene |
| `+` / `-` | Zoom in / out |
| `p` | Toggle info panel |
| `Esc` | Quit |

## Files

| File | Description |
|------|-------------|
| `Z_Buffer_Hidden_Surface.py` | Z-buffer demo with 5 overlapping quads |
| `requirements.txt` | Python dependencies |
| `output/` | Folder for rendered output screenshots |
