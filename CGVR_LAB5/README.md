# CGVR Lab 5

## Cohen–Sutherland Line Clipping Algorithm

Implements the **Cohen–Sutherland** line-clipping algorithm using Python OpenGL (PyOpenGL + GLUT).

Enter an axis-aligned clip window and a line. The program assigns 4-bit region outcodes (TBRL), performs trivial accept / reject / clip, and shows:

- **Green** — clip window
- **Blue dashed** — original line
- **Red solid** — clipped segment (if any)

### Algorithm Summary

1. Compute outcodes for both endpoints (Top, Bottom, Right, Left).
2. **Trivial accept** — both codes are `0000` (fully inside).
3. **Trivial reject** — bitwise AND of codes is non-zero (fully outside).
4. Otherwise clip against one window edge, update the outside endpoint, and repeat.

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
python Cohen_Sutherland_Clipping.py
```

Follow the terminal prompts for clip-window bounds and line endpoints. The OpenGL window then shows the window, lines, and a calculation panel.

### Keyboard and Mouse Controls

| Control | Action |
|---------|--------|
| `+` / `-` | Zoom in / out |
| Mouse wheel | Zoom in / out |
| Arrow keys | Pan the view |
| `l` | Toggle endpoint-coordinate labels |
| `m` | Toggle calculation / math panel |
| `r` | Reset zoom and pan |
| `q` / `Esc` | Quit |

## Files

| File | Description |
|------|-------------|
| `Cohen_Sutherland_Clipping.py` | Cohen–Sutherland clipping with OpenGL visualization |
| `requirements.txt` | Python dependencies |
| `output/` | Folder for rendered output screenshots |
