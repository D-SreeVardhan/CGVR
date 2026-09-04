# CGVR Lab 8

## Basic OpenGL Program using Vertex and Fragment Shaders

Implements a **programmable pipeline** in Python OpenGL (PyOpenGL + GLUT) and applies all five Lab 3 transforms through a shader uniform:

1. **Vertex shader** — `gl_Position = uModel * vec4(aPos, 0, 1)`; passes tinted color.
2. **Fragment shader** — outputs interpolated color.

Homogeneous **3×3** matrices are built on the CPU (translation, rotation, scaling, reflection, shearing), converted to a **4×4** column-major `mat4`, and uploaded as `uModel`.

- Dim blue triangle = original (identity)
- Bright triangle = transformed (GPU)

## Supported Transforms

1. **Translation** — `(tx, ty)` in NDC-ish space (try `0.3`)
2. **Rotation** — CCR / CR, angle, origin or arbitrary pivot
3. **Scaling** — `(sx, sy)` about origin or fixed point
4. **Reflection** — X or Y axis, origin or arbitrary point
5. **Shearing** — along X, Y, or both, about a reference point

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
python Shader_Basics.py
```

Pick a transform in the terminal, then view the shaded triangle.

### Keyboard Controls

| Control | Action |
|---------|--------|
| `o` | Toggle original (identity) triangle |
| `Esc` | Quit |

## Files

| File | Description |
|------|-------------|
| `Shader_Basics.py` | GLSL shaders + VBO + all five homogeneous transforms via `uModel` |
| `requirements.txt` | Python dependencies |
| `output/` | Screenshots |

## Notes

- Shaders use GLSL `#version 120` for macOS GLUT / OpenGL 2.1.
- Vertex layout: `vec2` position + `vec3` color.
