"""
Basic OpenGL with Vertex & Fragment Shaders
-------------------------------------------
Requires: pip install PyOpenGL PyOpenGL_accelerate

Draws a colored triangle using GLSL shaders. A 4x4 model matrix uniform
applies 2D transforms (translate / rotate / scale) on the GPU.

Works on macOS with the system OpenGL 2.1 / GLSL 1.20 profile that GLUT
typically provides.
"""

import array
import math
import sys
from ctypes import c_void_p

from OpenGL.GL import (
    GL_ARRAY_BUFFER,
    GL_COLOR_BUFFER_BIT,
    GL_COMPILE_STATUS,
    GL_FALSE,
    GL_FLOAT,
    GL_FRAGMENT_SHADER,
    GL_LINK_STATUS,
    GL_STATIC_DRAW,
    GL_TRIANGLES,
    GL_VERTEX_SHADER,
    glAttachShader,
    glBindAttribLocation,
    glBindBuffer,
    glBufferData,
    glClear,
    glClearColor,
    glCompileShader,
    glCreateProgram,
    glCreateShader,
    glDeleteShader,
    glDrawArrays,
    glEnableVertexAttribArray,
    glGenBuffers,
    glGetProgramInfoLog,
    glGetProgramiv,
    glGetShaderInfoLog,
    glGetShaderiv,
    glGetString,
    glGetUniformLocation,
    glLinkProgram,
    glShaderSource,
    glUniformMatrix4fv,
    glUseProgram,
    glVertexAttribPointer,
    glViewport,
    GL_RENDERER,
    GL_VERSION,
    GL_SHADING_LANGUAGE_VERSION,
)
from OpenGL.GLUT import (
    GLUT_DOUBLE,
    GLUT_RGB,
    glutCreateWindow,
    glutDisplayFunc,
    glutInit,
    glutInitDisplayMode,
    glutInitWindowSize,
    glutKeyboardFunc,
    glutMainLoop,
    glutPostRedisplay,
    glutReshapeFunc,
    glutSwapBuffers,
)

try:
    from OpenGL.GLUT import glutLeaveMainLoop
except ImportError:  # Apple GLUT has no leave-main-loop
    def glutLeaveMainLoop():
        sys.exit(0)

WIN_W, WIN_H = 800, 700

# GLSL 1.20 = OpenGL 2.1 — the profile macOS GLUT usually exposes
VERTEX_SHADER = """
#version 120
attribute vec2 aPos;
attribute vec3 aColor;
uniform mat4 uModel;
varying vec3 vColor;

void main() {
    gl_Position = uModel * vec4(aPos, 0.0, 1.0);
    vColor = aColor;
}
"""

FRAGMENT_SHADER = """
#version 120
varying vec3 vColor;

void main() {
    gl_FragColor = vec4(vColor, 1.0);
}
"""

# Triangle: x, y, r, g, b
TRIANGLE = [
    0.0, 0.5, 0.95, 0.35, 0.35,
    -0.5, -0.5, 0.35, 0.55, 1.0,
    0.5, -0.5, 0.3, 0.9, 0.4,
]

tx, ty = 0.0, 0.0
angle_deg = 0.0
scale = 1.0

program = None
vbo = None
loc_model = -1


def _gl_ok(flag):
    return bool(int(flag))


def compile_shader(source, shader_type, label):
    shader = glCreateShader(shader_type)
    glShaderSource(shader, [source])
    glCompileShader(shader)
    if not _gl_ok(glGetShaderiv(shader, GL_COMPILE_STATUS)):
        log = glGetShaderInfoLog(shader)
        if isinstance(log, bytes):
            log = log.decode("utf-8", errors="replace")
        raise RuntimeError(f"{label} compile failed:\n{log}")
    return shader


def create_program(vs_src, fs_src):
    vs = compile_shader(vs_src, GL_VERTEX_SHADER, "Vertex shader")
    fs = compile_shader(fs_src, GL_FRAGMENT_SHADER, "Fragment shader")
    prog = glCreateProgram()
    glAttachShader(prog, vs)
    glAttachShader(prog, fs)
    # Bind before link so locations are stable on macOS
    glBindAttribLocation(prog, 0, "aPos")
    glBindAttribLocation(prog, 1, "aColor")
    glLinkProgram(prog)
    if not _gl_ok(glGetProgramiv(prog, GL_LINK_STATUS)):
        log = glGetProgramInfoLog(prog)
        if isinstance(log, bytes):
            log = log.decode("utf-8", errors="replace")
        raise RuntimeError(f"Program link failed:\n{log}")
    glDeleteShader(vs)
    glDeleteShader(fs)
    return prog


def mat4_identity():
    return [
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0,
    ]


def mat4_multiply(a, b):
    out = [0.0] * 16
    for col in range(4):
        for row in range(4):
            s = 0.0
            for k in range(4):
                s += a[k * 4 + row] * b[col * 4 + k]
            out[col * 4 + row] = s
    return out


def mat4_translate(tx_, ty_):
    m = mat4_identity()
    m[12] = tx_
    m[13] = ty_
    return m


def mat4_rotate_z(degrees):
    rad = math.radians(degrees)
    c, s = math.cos(rad), math.sin(rad)
    m = mat4_identity()
    m[0], m[1] = c, s
    m[4], m[5] = -s, c
    return m


def mat4_scale(sx, sy):
    m = mat4_identity()
    m[0] = sx
    m[5] = sy
    return m


def build_model_matrix():
    s = mat4_scale(scale, scale)
    r = mat4_rotate_z(angle_deg)
    t = mat4_translate(tx, ty)
    return mat4_multiply(t, mat4_multiply(r, s))


def print_state():
    print(
        f"[transform] tx={tx:.2f} ty={ty:.2f}  "
        f"angle={angle_deg:.1f} deg  scale={scale:.2f}"
    )


def bind_triangle_attribs():
    stride = 5 * 4
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, stride, None)
    glEnableVertexAttribArray(1)
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, c_void_p(8))


def init_gl():
    global program, vbo, loc_model

    renderer = glGetString(GL_RENDERER)
    version = glGetString(GL_VERSION)
    glsl = glGetString(GL_SHADING_LANGUAGE_VERSION)
    for label, val in (
        ("Renderer", renderer),
        ("OpenGL", version),
        ("GLSL", glsl),
    ):
        if isinstance(val, bytes):
            val = val.decode("utf-8", errors="replace")
        print(f"  {label}: {val}")
    print()

    glClearColor(0.05, 0.05, 0.08, 1.0)
    program = create_program(VERTEX_SHADER, FRAGMENT_SHADER)
    glUseProgram(program)
    loc_model = glGetUniformLocation(program, "uModel")

    data = array.array("f", TRIANGLE)
    raw = data.tobytes()
    vbo = int(glGenBuffers(1))
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, len(raw), raw, GL_STATIC_DRAW)
    bind_triangle_attribs()


def display():
    glClear(GL_COLOR_BUFFER_BIT)
    glUseProgram(program)
    glUniformMatrix4fv(loc_model, 1, GL_FALSE, build_model_matrix())
    bind_triangle_attribs()
    glDrawArrays(GL_TRIANGLES, 0, 3)
    glutSwapBuffers()


def reshape(w, h):
    glViewport(0, 0, max(1, w), max(1, h))


def keyboard(key, _x, _y):
    global tx, ty, angle_deg, scale
    if isinstance(key, bytes):
        key = key.decode("utf-8")

    step = 0.05
    if key in ("a", "A"):
        tx -= step
    elif key in ("d", "D"):
        tx += step
    elif key in ("w", "W"):
        ty += step
    elif key in ("s", "S"):
        ty -= step
    elif key in ("q", "Q"):
        angle_deg += 5.0
    elif key in ("e", "E"):
        angle_deg -= 5.0
    elif key in ("+", "="):
        scale = min(3.0, scale * 1.1)
    elif key in ("-", "_"):
        scale = max(0.2, scale / 1.1)
    elif key in ("r", "R"):
        tx = ty = 0.0
        angle_deg = 0.0
        scale = 1.0
    elif key == "\x1b":
        glutLeaveMainLoop()
        return
    else:
        return

    print_state()
    glutPostRedisplay()


def main():
    print("=" * 50)
    print(" Lab 8: Vertex & Fragment Shaders (OpenGL)")
    print("=" * 50)
    print("Colored triangle rendered via GLSL shaders.")
    print("Model matrix uniform applies T / R / S on the GPU.\n")
    print("Controls (click window first):")
    print("  W A S D  -> translate")
    print("  Q / E    -> rotate CCW / CW")
    print("  + / -    -> scale up / down")
    print("  R        -> reset transform")
    print("  Esc      -> quit\n")

    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(WIN_W, WIN_H)
    glutCreateWindow(b"Lab 8: Vertex & Fragment Shaders")

    try:
        init_gl()
    except Exception as exc:
        print("Failed to initialize shaders:", exc)
        sys.exit(1)

    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutMainLoop()


if __name__ == "__main__":
    main()
