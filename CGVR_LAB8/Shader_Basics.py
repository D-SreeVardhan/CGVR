"""
Lab 8: Vertex & Fragment Shaders + 2D Transforms
------------------------------------------------
Requires: pip install PyOpenGL PyOpenGL_accelerate

GLSL vertex/fragment shaders draw a triangle. Homogeneous 3x3 transforms
(translation, rotation, scaling, reflection, shearing) are built on the CPU
and uploaded as a mat4 uniform so the GPU applies them.

macOS: uses GLSL #version 120 (OpenGL 2.1 / typical GLUT profile).
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
    GL_RENDERER,
    GL_SHADING_LANGUAGE_VERSION,
    GL_STATIC_DRAW,
    GL_TRIANGLES,
    GL_VERSION,
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
    glUniform3f,
    glUniformMatrix4fv,
    glUseProgram,
    glVertexAttribPointer,
    glViewport,
)
from OpenGL.GLUT import (
    GLUT_BITMAP_HELVETICA_12,
    GLUT_BITMAP_HELVETICA_18,
    GLUT_DOUBLE,
    GLUT_RGB,
    glutBitmapCharacter,
    glutCreateWindow,
    glutDisplayFunc,
    glutInit,
    glutInitDisplayMode,
    glutInitWindowSize,
    glutKeyboardFunc,
    glutMainLoop,
    glutReshapeFunc,
    glutSwapBuffers,
)

try:
    from OpenGL.GLUT import glutLeaveMainLoop
except ImportError:
    def glutLeaveMainLoop():
        sys.exit(0)

WIN_W, WIN_H = 900, 700

VERTEX_SHADER = """
#version 120
attribute vec2 aPos;
attribute vec3 aColor;
uniform mat4 uModel;
uniform vec3 uTint;
varying vec3 vColor;

void main() {
    gl_Position = uModel * vec4(aPos, 0.0, 1.0);
    vColor = aColor * uTint;
}
"""

FRAGMENT_SHADER = """
#version 120
varying vec3 vColor;

void main() {
    gl_FragColor = vec4(vColor, 1.0);
}
"""

# Triangle in NDC-ish coords: x, y, r, g, b
TRIANGLE = [
    0.0, 0.45, 0.95, 0.35, 0.35,
    -0.45, -0.4, 0.35, 0.55, 1.0,
    0.45, -0.4, 0.3, 0.9, 0.4,
]

program = None
vbo = None
loc_model = loc_tint = -1
model_mat4 = None
transform_name = ""
transform_mat3 = None
show_original = True


# ------------------------------------------------------------------
# Homogeneous 3x3 (same math as Lab 3)
# ------------------------------------------------------------------

def identity_matrix():
    return [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]


def translation_matrix(tx, ty):
    return [
        [1.0, 0.0, tx],
        [0.0, 1.0, ty],
        [0.0, 0.0, 1.0],
    ]


def rotation_matrix(angle_in_degrees):
    angle = math.radians(angle_in_degrees)
    c = math.cos(angle)
    s = math.sin(angle)
    return [
        [c, -s, 0.0],
        [s, c, 0.0],
        [0.0, 0.0, 1.0],
    ]


def scaling_matrix(sx, sy):
    return [
        [sx, 0.0, 0.0],
        [0.0, sy, 0.0],
        [0.0, 0.0, 1.0],
    ]


def reflection_matrix(axis):
    if axis == "x":
        return scaling_matrix(1.0, -1.0)
    if axis == "y":
        return scaling_matrix(-1.0, 1.0)
    raise ValueError(f"Unsupported reflection axis: {axis}")


def shearing_matrix(shx, shy):
    return [
        [1.0, shx, 0.0],
        [shy, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]


def multiply_matrices(a, b):
    result = [[0.0, 0.0, 0.0] for _ in range(3)]
    for row in range(3):
        for col in range(3):
            result[row][col] = sum(a[row][k] * b[k][col] for k in range(3))
    return result


def about_point(matrix, px, py):
    return multiply_matrices(
        translation_matrix(px, py),
        multiply_matrices(matrix, translation_matrix(-px, -py)),
    )


def clean(value):
    if abs(value) < 1e-9:
        return 0.0
    return round(value, 6)


def print_matrix(matrix):
    for row in matrix:
        print("  ".join(f"{clean(value):7.2f}" for value in row))


def mat3_to_mat4_column_major(m3):
    """
    Lab 3 row-major 3x3 [[a,b,tx],[c,d,ty],[0,0,1]]
    -> OpenGL column-major 4x4.
    """
    a, b, tx = m3[0]
    c, d, ty = m3[1]
    return [
        a, c, 0.0, 0.0,
        b, d, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        tx, ty, 0.0, 1.0,
    ]


def mat4_identity():
    return [
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0,
    ]


# ------------------------------------------------------------------
# Terminal input (Lab 3 menus)
# ------------------------------------------------------------------

def read_pivot(label="Pivot"):
    print(f"\n{label} point")
    print("  1. Origin (0, 0)")
    print("  2. Arbitrary point")
    choice = input("Choice: ").strip()
    if choice == "1":
        return 0.0, 0.0, "origin (0, 0)"
    if choice == "2":
        px = float(input("  px: "))
        py = float(input("  py: "))
        return px, py, f"({px:g}, {py:g})"
    raise SystemExit("Invalid pivot choice.")


def read_rotation():
    print("\nRotation direction")
    print("  1. CCR (counter-clockwise)")
    print("  2. CR  (clockwise)")
    direction = input("Choice: ").strip().lower()
    if direction in ("1", "ccr"):
        sense, sense_name = 1.0, "CCR"
    elif direction in ("2", "cr"):
        sense, sense_name = -1.0, "CR"
    else:
        raise SystemExit("Invalid rotation direction.")
    angle = float(input("Angle in degrees: "))
    px, py, pivot_name = read_pivot("Pivot")
    return (
        about_point(rotation_matrix(sense * angle), px, py),
        f"{sense_name} rotation of {angle:g} deg about {pivot_name}",
    )


def read_reflection():
    print("\nReflect over")
    print("  1. X axis")
    print("  2. Y axis")
    choice = input("Choice: ").strip()
    if choice == "1":
        axis, axis_name = "x", "X axis"
    elif choice == "2":
        axis, axis_name = "y", "Y axis"
    else:
        raise SystemExit("Invalid reflection choice.")
    px, py, pivot_name = read_pivot("About")
    return (
        about_point(reflection_matrix(axis), px, py),
        f"Reflection over {axis_name} about {pivot_name}",
    )


def read_shearing():
    print("\nShearing type")
    print("  1. Along X  (x' = x + shx*y)")
    print("  2. Along Y  (y' = y + shy*x)")
    print("  3. Both     (enter shx and shy)")
    choice = input("Choice: ").strip()
    if choice == "1":
        shx = float(input("shx: "))
        shy = 0.0
        detail = f"along X with shx={shx:g}"
    elif choice == "2":
        shy = float(input("shy: "))
        shx = 0.0
        detail = f"along Y with shy={shy:g}"
    elif choice == "3":
        shx = float(input("shx: "))
        shy = float(input("shy: "))
        detail = f"with shx={shx:g}, shy={shy:g}"
    else:
        raise SystemExit("Invalid shearing choice.")
    px, py, pivot_name = read_pivot("Reference")
    return (
        about_point(shearing_matrix(shx, shy), px, py),
        f"Shearing {detail} about {pivot_name}",
    )


def read_transformation():
    print("\nChoose a transformation (applied via shader uniform)")
    print("  1. Translation")
    print("  2. Rotation")
    print("  3. Scaling")
    print("  4. Reflection")
    print("  5. Shearing")
    choice = input("Choice: ").strip()

    if choice == "1":
        tx = float(input("tx: "))
        ty = float(input("ty: "))
        # NDC space is roughly [-1,1]; keep values small (e.g. 0.2)
        return translation_matrix(tx, ty), f"Translation by ({tx:g}, {ty:g})"

    if choice == "2":
        return read_rotation()

    if choice == "3":
        sx = float(input("sx: "))
        sy = float(input("sy: "))
        px, py, pivot_name = read_pivot("Fixed")
        return (
            about_point(scaling_matrix(sx, sy), px, py),
            f"Scaling by ({sx:g}, {sy:g}) about {pivot_name}",
        )

    if choice == "4":
        return read_reflection()

    if choice == "5":
        return read_shearing()

    raise SystemExit("Invalid transformation choice.")


# ------------------------------------------------------------------
# Shader / GL setup
# ------------------------------------------------------------------

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


def bind_triangle_attribs():
    stride = 5 * 4
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, stride, None)
    glEnableVertexAttribArray(1)
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, c_void_p(8))


def draw_hud_text():
    """Bitmap HUD (fixed-function overlay; works in GLUT compatibility)."""
    from OpenGL.GL import (
        GL_MODELVIEW,
        GL_PROJECTION,
        glColor3f,
        glLoadIdentity,
        glMatrixMode,
        glPopMatrix,
        glPushMatrix,
        glRasterPos2f,
    )
    from OpenGL.GLU import gluOrtho2D

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    def text(x, y, s, font=GLUT_BITMAP_HELVETICA_12):
        glRasterPos2f(x, y)
        for ch in s:
            glutBitmapCharacter(font, ord(ch))

    glColor3f(1.0, 0.9, 0.4)
    text(20, WIN_H - 30, "Lab 8: Shaders + 2D Transforms", GLUT_BITMAP_HELVETICA_18)
    glColor3f(0.85, 0.85, 0.85)
    title = transform_name if len(transform_name) <= 60 else transform_name[:57] + "..."
    text(20, WIN_H - 55, title)
    glColor3f(0.45, 0.6, 1.0)
    text(20, WIN_H - 80, "dim blue = original (identity)")
    glColor3f(0.95, 0.45, 0.45)
    text(20, WIN_H - 100, "bright = transformed (uModel)")
    glColor3f(0.55, 0.55, 0.55)
    text(20, 30, "o: toggle original   Esc: quit")

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def init_gl():
    global program, vbo, loc_model, loc_tint

    for label, val in (
        ("Renderer", glGetString(GL_RENDERER)),
        ("OpenGL", glGetString(GL_VERSION)),
        ("GLSL", glGetString(GL_SHADING_LANGUAGE_VERSION)),
    ):
        if isinstance(val, bytes):
            val = val.decode("utf-8", errors="replace")
        print(f"  {label}: {val}")
    print()

    glClearColor(0.05, 0.05, 0.08, 1.0)
    program = create_program(VERTEX_SHADER, FRAGMENT_SHADER)
    glUseProgram(program)
    loc_model = glGetUniformLocation(program, "uModel")
    loc_tint = glGetUniformLocation(program, "uTint")

    data = array.array("f", TRIANGLE)
    raw = data.tobytes()
    vbo = int(glGenBuffers(1))
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, len(raw), raw, GL_STATIC_DRAW)
    bind_triangle_attribs()


def display():
    glClear(GL_COLOR_BUFFER_BIT)
    glUseProgram(program)
    bind_triangle_attribs()

    if show_original:
        glUniformMatrix4fv(loc_model, 1, GL_FALSE, mat4_identity())
        glUniform3f(loc_tint, 0.35, 0.45, 0.85)
        glDrawArrays(GL_TRIANGLES, 0, 3)

    glUniformMatrix4fv(loc_model, 1, GL_FALSE, model_mat4)
    glUniform3f(loc_tint, 1.0, 1.0, 1.0)
    glDrawArrays(GL_TRIANGLES, 0, 3)

    draw_hud_text()
    glutSwapBuffers()


def reshape(w, h):
    glViewport(0, 0, max(1, w), max(1, h))


def keyboard(key, _x, _y):
    global show_original
    if isinstance(key, bytes):
        key = key.decode("utf-8")
    if key in ("o", "O"):
        show_original = not show_original
        from OpenGL.GLUT import glutPostRedisplay
        glutPostRedisplay()
    elif key == "\x1b":
        glutLeaveMainLoop()


def main():
    global model_mat4, transform_name, transform_mat3

    print("=" * 50)
    print(" Lab 8: Vertex & Fragment Shaders + Transforms")
    print("=" * 50)
    print("Triangle is shaded with GLSL. Choose a homogeneous")
    print("2D transform; it is uploaded as mat4 uModel.\n")
    print("Tip: NDC coords are about [-1, 1]. Try tx=0.3, scale=1.5,")
    print("     rotate 45 about origin, reflect Y, shear shx=0.4.\n")

    transform_mat3, transform_name = read_transformation()
    model_mat4 = mat3_to_mat4_column_major(transform_mat3)

    print(f"\n{transform_name}")
    print("Homogeneous 3x3 matrix (CPU):")
    print_matrix(transform_mat3)
    print("Uploaded to GPU as mat4 uModel (column-major).")
    print("\nWindow controls: o = toggle original, Esc = quit\n")

    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(WIN_W, WIN_H)
    glutCreateWindow(b"Lab 8: Shaders + 2D Transforms")

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
