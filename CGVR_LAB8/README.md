# CGVR Lab 8

## Basic OpenGL Program using Vertex and Fragment Shaders

Implements a minimal **programmable pipeline** in Python OpenGL (PyOpenGL + GLUT):

1. **Vertex shader** — transforms each vertex with a `mat4` model uniform and passes color.
2. **Fragment shader** — outputs the interpolated vertex color.

A colored triangle is uploaded once to a VBO. Translate / rotate / scale are applied on the GPU through the model matrix (homogeneous 4×4).

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
python Shader_Basics.py
```

### Keyboard Controls

| Control | Action |
|---------|--------|
| `W` `A` `S` `D` | Translate up / left / down / right |
| `Q` / `E` | Rotate counter-clockwise / clockwise |
| `+` / `-` | Scale up / down |
| `R` | Reset transform |
| `Esc` | Quit |

## Files

| File | Description |
|------|-------------|
| `Shader_Basics.py` | GLSL vertex + fragment shaders, VBO triangle, model matrix |
| `requirements.txt` | Python dependencies |
| `output/` | Folder for rendered output screenshots |

## Notes

- Shaders use GLSL `#version 120` for broad GLUT compatibility.
- Vertex layout: `vec2` position + `vec3` color per vertex.
