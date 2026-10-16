"""
Phong Illumination Model — OpenGL Lab 7
========================================
Renders a 3D sphere with the Phong illumination model implemented entirely
in GLSL shaders.  Toggle each of the three components (ambient / diffuse /
specular) on and off, adjust shininess, and compare Phong (per-fragment)
against Gouraud (per-vertex) shading with a single key-press.

Requires: pip install PyOpenGL PyOpenGL_accelerate

Controls
--------
  1 / 2 / 3    toggle Ambient / Diffuse / Specular
  g            switch Phong ↔ Gouraud shading mode
  + / -        double / halve shininess  (n)
  Arrow keys   move light  (← → = X,  ↑ ↓ = Y)
  [ / ]        push / pull light along Z
  Mouse drag   orbit the sphere
  r            reset everything
  p            toggle info panel
  Esc          quit
"""

import array
import math
import sys
from ctypes import c_void_p

from OpenGL.GL import (
    GL_ARRAY_BUFFER,
    GL_COLOR_BUFFER_BIT,
    GL_COMPILE_STATUS,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_ELEMENT_ARRAY_BUFFER,
    GL_FALSE,
    GL_FLOAT,
    GL_FRAGMENT_SHADER,
    GL_LESS,
    GL_LINK_STATUS,
    GL_MODELVIEW,
    GL_PROJECTION,
    GL_QUADS,
    GL_STATIC_DRAW,
    GL_TRIANGLES,
    GL_UNSIGNED_INT,
    GL_VERTEX_SHADER,
    glAttachShader,
    glBegin,
    glBindAttribLocation,
    glBindBuffer,
    glBufferData,
    glClear,
    glClearColor,
    glClearDepth,
    glColor3f,
    glCompileShader,
    glCreateProgram,
    glCreateShader,
    glDeleteShader,
    glDepthFunc,
    glDisable,
    glDisableVertexAttribArray,
    glDrawElements,
    glEnable,
    glEnableVertexAttribArray,
    glEnd,
    glGenBuffers,
    glGetProgramInfoLog,
    glGetProgramiv,
    glGetShaderInfoLog,
    glGetShaderiv,
    glGetString,
    glGetUniformLocation,
    glLinkProgram,
    glLoadIdentity,
    glMatrixMode,
    glPopMatrix,
    glPushMatrix,
    glRasterPos2f,
    glShaderSource,
    glUniform1f,
    glUniform1i,
    glUniform3f,
    glUniformMatrix3fv,
    glUniformMatrix4fv,
    glUseProgram,
    glVertex2f,
    glVertexAttribPointer,
    glViewport,
    GL_RENDERER,
    GL_SHADING_LANGUAGE_VERSION,
    GL_VERSION,
)
from OpenGL.GLU import gluOrtho2D
from OpenGL.GLUT import (
    GLUT_BITMAP_HELVETICA_12,
    GLUT_BITMAP_HELVETICA_18,
    GLUT_DEPTH,
    GLUT_DOUBLE,
    GLUT_DOWN,
    GLUT_KEY_DOWN,
    GLUT_KEY_LEFT,
    GLUT_KEY_RIGHT,
    GLUT_KEY_UP,
    GLUT_LEFT_BUTTON,
    GLUT_RGB,
    GLUT_UP,
    glutBitmapCharacter,
    glutCreateWindow,
    glutDisplayFunc,
    glutInit,
    glutInitDisplayMode,
    glutInitWindowSize,
    glutKeyboardFunc,
    glutMainLoop,
    glutMotionFunc,
    glutMouseFunc,
    glutPostRedisplay,
    glutReshapeFunc,
    glutSpecialFunc,
    glutSwapBuffers,
)

try:
    from OpenGL.GLUT import glutLeaveMainLoop
except ImportError:
    def glutLeaveMainLoop():
        sys.exit(0)

# ---------------------------------------------------------------------------
WIN_W, WIN_H = 1100, 700
PANEL_W      = 390

# ---------------------------------------------------------------------------
# GLSL — Phong shading (lighting computed per-fragment)
# ---------------------------------------------------------------------------
VERTEX_PHONG = """
#version 120
attribute vec3 aPos;
attribute vec3 aNorm;

uniform mat4 uModel;
uniform mat4 uView;
uniform mat4 uProj;
uniform mat3 uNormalMat;

varying vec3 vNormal;
varying vec3 vFragPos;

void main() {
    vec4 worldPos = uModel * vec4(aPos, 1.0);
    vFragPos      = worldPos.xyz;
    vNormal       = normalize(uNormalMat * aNorm);
    gl_Position   = uProj * uView * worldPos;
}
"""

FRAGMENT_PHONG = """
#version 120
varying vec3 vNormal;
varying vec3 vFragPos;

uniform vec3  uLightPos;
uniform vec3  uViewPos;
uniform vec3  uLightColor;
uniform vec3  uObjColor;
uniform float uKa;
uniform float uKd;
uniform float uKs;
uniform float uShininess;
uniform int   uAmbOn;
uniform int   uDiffOn;
uniform int   uSpecOn;
uniform int   uIsLight;

void main() {
    if (uIsLight == 1) {
        gl_FragColor = vec4(uLightColor, 1.0);
        return;
    }

    vec3 N  = normalize(vNormal);
    vec3 L  = normalize(uLightPos - vFragPos);
    vec3 V  = normalize(uViewPos  - vFragPos);
    vec3 R  = reflect(-L, N);           /* R = 2(N.L)N - L */

    /* Ia = Ka * La */
    vec3 Ia = uKa * uLightColor * uObjColor;

    /* Id = Kd * max(N.L, 0) * Ld */
    float NdotL = max(dot(N, L), 0.0);
    vec3 Id = uKd * NdotL * uLightColor * uObjColor;

    /* Is = Ks * max(R.V, 0)^n * Ls */
    float RdotV = max(dot(R, V), 0.0);
    vec3 Is = uKs * pow(RdotV, uShininess) * uLightColor;

    vec3 result = vec3(0.0);
    if (uAmbOn  == 1) result += Ia;
    if (uDiffOn == 1) result += Id;
    if (uSpecOn == 1) result += Is;

    gl_FragColor = vec4(result, 1.0);
}
"""

# ---------------------------------------------------------------------------
# GLSL — Gouraud shading (lighting computed per-vertex, interpolated)
# ---------------------------------------------------------------------------
VERTEX_GOURAUD = """
#version 120
attribute vec3 aPos;
attribute vec3 aNorm;

uniform mat4 uModel;
uniform mat4 uView;
uniform mat4 uProj;
uniform mat3 uNormalMat;
uniform vec3  uLightPos;
uniform vec3  uViewPos;
uniform vec3  uLightColor;
uniform vec3  uObjColor;
uniform float uKa;
uniform float uKd;
uniform float uKs;
uniform float uShininess;
uniform int   uAmbOn;
uniform int   uDiffOn;
uniform int   uSpecOn;
uniform int   uIsLight;

varying vec3 vColor;

void main() {
    vec4 worldPos = uModel * vec4(aPos, 1.0);

    if (uIsLight == 1) {
        vColor = uLightColor;
    } else {
        vec3 N  = normalize(uNormalMat * aNorm);
        vec3 L  = normalize(uLightPos - worldPos.xyz);
        vec3 V  = normalize(uViewPos  - worldPos.xyz);
        vec3 R  = reflect(-L, N);

        vec3 Ia = uKa * uLightColor * uObjColor;
        float NdotL = max(dot(N, L), 0.0);
        vec3 Id = uKd * NdotL * uLightColor * uObjColor;
        float RdotV = max(dot(R, V), 0.0);
        vec3 Is = uKs * pow(RdotV, uShininess) * uLightColor;

        vColor = vec3(0.0);
        if (uAmbOn  == 1) vColor += Ia;
        if (uDiffOn == 1) vColor += Id;
        if (uSpecOn == 1) vColor += Is;
    }

    gl_Position = uProj * uView * worldPos;
}
"""

FRAGMENT_GOURAUD = """
#version 120
varying vec3 vColor;
void main() {
    gl_FragColor = vec4(vColor, 1.0);
}
"""

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
light_pos   = [2.0, 3.0, 2.0]
light_color = [1.0, 1.0, 1.0]
obj_color   = [1.0, 0.50, 0.31]   # coral

Ka, Kd, Ks = 0.20, 1.00, 0.80
shininess   = 32.0

amb_on     = True
diff_on    = True
spec_on    = True
use_phong  = True    # False → Gouraud
show_panel = True

orbit_x  = 0.0
orbit_y  = 0.0
cam_dist = 4.0

mouse_dragging = False
mouse_last_x   = 0
mouse_last_y   = 0

prog_phong   = None
prog_gouraud = None
locs_phong   = {}
locs_gouraud = {}
sphere_vbo   = None
sphere_ibo   = None
sphere_count = 0

UNIFORM_NAMES = [
    "uModel", "uView", "uProj", "uNormalMat",
    "uLightPos", "uViewPos", "uLightColor", "uObjColor",
    "uKa", "uKd", "uKs", "uShininess",
    "uAmbOn", "uDiffOn", "uSpecOn", "uIsLight",
]

# ---------------------------------------------------------------------------
# Sphere geometry — interleaved [x, y, z, nx, ny, nz]
# ---------------------------------------------------------------------------

def build_sphere(radius=1.0, stacks=56, slices=56):
    verts = []
    for i in range(stacks + 1):
        phi  = math.pi * i / stacks
        sp, cp = math.sin(phi), math.cos(phi)
        for j in range(slices + 1):
            theta = 2.0 * math.pi * j / slices
            st, ct = math.sin(theta), math.cos(theta)
            x, y, z  = radius * sp * ct, radius * cp, radius * sp * st
            verts.extend([x, y, z, sp * ct, cp, sp * st])

    idxs = []
    for i in range(stacks):
        for j in range(slices):
            a = i * (slices + 1) + j
            b = a + 1
            c = (i + 1) * (slices + 1) + j
            d = c + 1
            idxs.extend([a, c, b, b, c, d])

    return verts, idxs

# ---------------------------------------------------------------------------
# Column-major matrix math
# ---------------------------------------------------------------------------

def mat4_identity():
    return [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]

def mat4_mul(a, b):
    out = [0.0] * 16
    for col in range(4):
        for row in range(4):
            for k in range(4):
                out[col * 4 + row] += a[k * 4 + row] * b[col * 4 + k]
    return out

def mat4_rotate_x(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return [1,0,0,0, 0,c,s,0, 0,-s,c,0, 0,0,0,1]

def mat4_rotate_y(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return [c,0,-s,0, 0,1,0,0, s,0,c,0, 0,0,0,1]

def mat4_perspective(fovy_deg, aspect, near, far):
    f  = 1.0 / math.tan(math.radians(fovy_deg) / 2.0)
    nf = 1.0 / (near - far)
    return [
        f / aspect, 0, 0,  0,
        0,          f, 0,  0,
        0,          0, (far + near) * nf, -1,
        0,          0, 2 * far * near * nf, 0,
    ]

def mat4_view(cam_z):
    """Camera fixed at (0, 0, cam_z) looking at origin."""
    m = mat4_identity()
    m[14] = -cam_z
    return m

def mat4_translate_v(tx, ty, tz):
    m = mat4_identity()
    m[12], m[13], m[14] = tx, ty, tz
    return m

def mat4_scale_u(s):
    m = mat4_identity()
    m[0] = m[5] = m[10] = s
    return m

def mat3_from_mat4(m):
    """Upper-left 3×3 of a column-major 4×4."""
    return [m[0], m[1], m[2],
            m[4], m[5], m[6],
            m[8], m[9], m[10]]

def fv(lst):
    """Return a plain Python list — PyOpenGL_accelerate accepts lists for uniforms."""
    return list(lst)

# ---------------------------------------------------------------------------
# Shader helpers
# ---------------------------------------------------------------------------

def compile_shader(source, stype, label):
    sh = glCreateShader(stype)
    glShaderSource(sh, [source])
    glCompileShader(sh)
    if not int(glGetShaderiv(sh, GL_COMPILE_STATUS)):
        log = glGetShaderInfoLog(sh)
        if isinstance(log, bytes):
            log = log.decode("utf-8", errors="replace")
        raise RuntimeError(f"{label} compile error:\n{log}")
    return sh

def create_program(vs_src, fs_src):
    vs   = compile_shader(vs_src, GL_VERTEX_SHADER,   "Vertex")
    fs   = compile_shader(fs_src, GL_FRAGMENT_SHADER, "Fragment")
    prog = glCreateProgram()
    glAttachShader(prog, vs)
    glAttachShader(prog, fs)
    glBindAttribLocation(prog, 0, "aPos")
    glBindAttribLocation(prog, 1, "aNorm")
    glLinkProgram(prog)
    if not int(glGetProgramiv(prog, GL_LINK_STATUS)):
        log = glGetProgramInfoLog(prog)
        if isinstance(log, bytes):
            log = log.decode("utf-8", errors="replace")
        raise RuntimeError(f"Program link error:\n{log}")
    glDeleteShader(vs)
    glDeleteShader(fs)
    return prog

def get_locs(prog):
    return {name: glGetUniformLocation(prog, name) for name in UNIFORM_NAMES}

# ---------------------------------------------------------------------------
# GL initialisation
# ---------------------------------------------------------------------------
STRIDE = 6 * 4   # 6 floats × 4 bytes per vertex

def init_gl():
    global prog_phong, prog_gouraud, locs_phong, locs_gouraud
    global sphere_vbo, sphere_ibo, sphere_count

    for label, sym in (
        ("Renderer", GL_RENDERER),
        ("OpenGL",   GL_VERSION),
        ("GLSL",     GL_SHADING_LANGUAGE_VERSION),
    ):
        val = glGetString(sym)
        if isinstance(val, bytes):
            val = val.decode("utf-8", errors="replace")
        print(f"  {label}: {val}")
    print()

    glClearColor(0.06, 0.06, 0.08, 1.0)
    glClearDepth(1.0)
    glDepthFunc(GL_LESS)

    prog_phong   = create_program(VERTEX_PHONG,   FRAGMENT_PHONG)
    prog_gouraud = create_program(VERTEX_GOURAUD, FRAGMENT_GOURAUD)
    locs_phong   = get_locs(prog_phong)
    locs_gouraud = get_locs(prog_gouraud)

    verts, idxs  = build_sphere(radius=1.0, stacks=56, slices=56)
    sphere_count = len(idxs)

    v_raw = array.array("f", verts).tobytes()
    i_raw = array.array("I", idxs).tobytes()

    bufs = glGenBuffers(2)
    sphere_vbo = int(bufs[0])
    sphere_ibo = int(bufs[1])

    glBindBuffer(GL_ARRAY_BUFFER, sphere_vbo)
    glBufferData(GL_ARRAY_BUFFER, len(v_raw), v_raw, GL_STATIC_DRAW)

    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, sphere_ibo)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(i_raw), i_raw, GL_STATIC_DRAW)

    glBindBuffer(GL_ARRAY_BUFFER, 0)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

def bind_sphere_attribs():
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, STRIDE, None)
    glEnableVertexAttribArray(1)
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, STRIDE, c_void_p(12))

# ---------------------------------------------------------------------------
# Uniform upload
# ---------------------------------------------------------------------------

def upload_uniforms(L, model, view, proj, normal_mat, is_light=False):
    glUniformMatrix4fv(L["uModel"],     1, GL_FALSE, fv(model))
    glUniformMatrix4fv(L["uView"],      1, GL_FALSE, fv(view))
    glUniformMatrix4fv(L["uProj"],      1, GL_FALSE, fv(proj))
    glUniformMatrix3fv(L["uNormalMat"], 1, GL_FALSE, fv(normal_mat))
    glUniform3f(L["uLightPos"],   *light_pos)
    glUniform3f(L["uViewPos"],    0.0, 0.0, cam_dist)
    glUniform3f(L["uLightColor"], *light_color)
    glUniform3f(L["uObjColor"],   *obj_color)
    glUniform1f(L["uKa"],         Ka)
    glUniform1f(L["uKd"],         Kd)
    glUniform1f(L["uKs"],         Ks)
    glUniform1f(L["uShininess"],  shininess)
    glUniform1i(L["uAmbOn"],      1 if amb_on  else 0)
    glUniform1i(L["uDiffOn"],     1 if diff_on else 0)
    glUniform1i(L["uSpecOn"],     1 if spec_on else 0)
    glUniform1i(L["uIsLight"],    1 if is_light else 0)

# ---------------------------------------------------------------------------
# Panel drawing
# ---------------------------------------------------------------------------

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_12):
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))

def draw_panel():
    if not show_panel:
        return

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Panel background
    glColor3f(0.09, 0.09, 0.11)
    glBegin(GL_QUADS)
    glVertex2f(0,       0)
    glVertex2f(PANEL_W, 0)
    glVertex2f(PANEL_W, WIN_H)
    glVertex2f(0,       WIN_H)
    glEnd()

    # Thin accent line on the right edge of the panel
    from OpenGL.GL import glLineWidth, glBegin as gB, glEnd as gE, GL_LINES
    glColor3f(0.30, 0.30, 0.35)
    glLineWidth(1.0)
    gB(GL_LINES)
    glVertex2f(PANEL_W, 0)
    glVertex2f(PANEL_W, WIN_H)
    gE()
    glLineWidth(1.0)

    tx   = 18
    ty   = WIN_H - 30
    line = 21

    # ── Title ─────────────────────────────────────────────────────────────
    glColor3f(1.0, 0.88, 0.35)
    draw_text(tx, ty, "Phong Illumination Model", GLUT_BITMAP_HELVETICA_18)
    ty -= line + 4

    glColor3f(0.55, 0.55, 0.60)
    draw_text(tx, ty, "I  =  Ia  +  Id  +  Is")
    ty -= int(line * 1.6)

    # ── Ambient ───────────────────────────────────────────────────────────
    glColor3f(*((.35, .95, .50) if amb_on else (.50, .50, .50)))
    draw_text(tx, ty, f"[1]  Ambient   {'ON ' if amb_on else 'OFF'}")
    ty -= line
    glColor3f(0.80, 0.80, 0.80)
    draw_text(tx + 14, ty, "Ia = Ka * La")
    ty -= line
    draw_text(tx + 14, ty, f"Ka = {Ka:.2f}")
    ty -= int(line * 1.4)

    # ── Diffuse ───────────────────────────────────────────────────────────
    glColor3f(*((.35, .65, 1.00) if diff_on else (.50, .50, .50)))
    draw_text(tx, ty, f"[2]  Diffuse   {'ON ' if diff_on else 'OFF'}")
    ty -= line
    glColor3f(0.80, 0.80, 0.80)
    draw_text(tx + 14, ty, "Id = Kd * max(N\xb7L, 0) * Ld")
    ty -= line
    draw_text(tx + 14, ty, f"Kd = {Kd:.2f}")
    ty -= int(line * 1.4)

    # ── Specular ──────────────────────────────────────────────────────────
    glColor3f(*((1.00, .55, .30) if spec_on else (.50, .50, .50)))
    draw_text(tx, ty, f"[3]  Specular  {'ON ' if spec_on else 'OFF'}")
    ty -= line
    glColor3f(0.80, 0.80, 0.80)
    draw_text(tx + 14, ty, "Is = Ks * max(R\xb7V, 0)^n * Ls")
    ty -= line
    draw_text(tx + 14, ty, f"Ks = {Ks:.2f}     n (shininess) = {shininess:.0f}")
    ty -= int(line * 1.6)

    # ── Vector legend ─────────────────────────────────────────────────────
    glColor3f(0.50, 0.85, 1.00)
    draw_text(tx, ty, "Vectors:")
    ty -= line
    glColor3f(0.80, 0.80, 0.80)
    for legend in (
        "N  = surface normal",
        "L  = normalize(lightPos - fragPos)",
        "V  = normalize(viewPos  - fragPos)",
        "R  = reflect(-L, N)",
        "      = 2(N\xb7L)N - L",
    ):
        draw_text(tx + 14, ty, legend)
        ty -= line
    ty -= int(line * 0.6)

    # ── Scene info ────────────────────────────────────────────────────────
    glColor3f(0.50, 0.85, 1.00)
    draw_text(tx, ty, "Scene:")
    ty -= line
    glColor3f(0.80, 0.80, 0.80)
    lx, ly, lz = light_pos
    draw_text(tx + 14, ty, f"Light   ({lx:+.1f}, {ly:+.1f}, {lz:+.1f})  \u25cf")
    ty -= line
    draw_text(tx + 14, ty, f"Camera  ( 0.0,  0.0, {cam_dist:.1f})")
    ty -= line
    r, g, b = obj_color
    draw_text(tx + 14, ty, f"Object  coral ({r:.2f}, {g:.2f}, {b:.2f})")
    ty -= int(line * 1.4)

    # ── Shading mode ──────────────────────────────────────────────────────
    mode_label = "Phong  (per-fragment)" if use_phong else "Gouraud (per-vertex) "
    glColor3f(*((0.35, 1.00, 0.60) if use_phong else (1.00, 0.85, 0.35)))
    draw_text(tx, ty, f"Shading: {mode_label}  [g]")
    ty -= int(line * 1.6)

    # ── Controls ──────────────────────────────────────────────────────────
    glColor3f(0.45, 0.45, 0.50)
    draw_text(tx, ty, "Controls:")
    ty -= line
    for ctrl in (
        "1/2/3     toggle Ambient / Diffuse / Specular",
        "+  /  -   shininess \xd72  /  \xf72",
        "Arrows    move light  (X / Y axis)",
        "[  /  ]   move light  (Z axis)",
        "Drag      orbit sphere",
        "r         reset   p  panel   Esc  quit",
    ):
        glColor3f(0.55, 0.55, 0.60)
        draw_text(tx + 10, ty, ctrl)
        ty -= line

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# ---------------------------------------------------------------------------
# GLUT callbacks
# ---------------------------------------------------------------------------

def display():
    # Clear full window
    glViewport(0, 0, WIN_W, WIN_H)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # 3-D viewport (right of panel)
    vp_x = PANEL_W
    vp_w = WIN_W - PANEL_W
    glViewport(vp_x, 0, vp_w, WIN_H)
    glEnable(GL_DEPTH_TEST)

    prog = prog_phong   if use_phong else prog_gouraud
    L    = locs_phong   if use_phong else locs_gouraud
    glUseProgram(prog)

    # Matrices
    model      = mat4_mul(mat4_rotate_y(orbit_y), mat4_rotate_x(orbit_x))
    normal_mat = mat3_from_mat4(model)
    aspect     = vp_w / WIN_H
    proj       = mat4_perspective(45.0, aspect, 0.1, 100.0)
    view       = mat4_view(cam_dist)

    # Bind sphere buffers
    glBindBuffer(GL_ARRAY_BUFFER,         sphere_vbo)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, sphere_ibo)
    bind_sphere_attribs()

    # Draw main sphere
    upload_uniforms(L, model, view, proj, normal_mat, is_light=False)
    glDrawElements(GL_TRIANGLES, sphere_count, GL_UNSIGNED_INT, None)

    # Draw light-source indicator (tiny sphere at light_pos)
    ident     = mat4_identity()
    ident_m3  = mat3_from_mat4(ident)
    light_mod = mat4_mul(mat4_translate_v(*light_pos), mat4_scale_u(0.07))
    upload_uniforms(L, light_mod, view, proj, ident_m3, is_light=True)
    glDrawElements(GL_TRIANGLES, sphere_count, GL_UNSIGNED_INT, None)

    # Cleanup
    glDisableVertexAttribArray(0)
    glDisableVertexAttribArray(1)
    glBindBuffer(GL_ARRAY_BUFFER, 0)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

    # 2-D panel overlay
    glViewport(0, 0, WIN_W, WIN_H)
    glDisable(GL_DEPTH_TEST)
    glUseProgram(0)
    draw_panel()

    glutSwapBuffers()


def reshape(w, h):
    global WIN_W, WIN_H
    WIN_W, WIN_H = max(1, w), max(1, h)
    glViewport(0, 0, WIN_W, WIN_H)


def keyboard(key, _x, _y):
    global Ka, Kd, Ks, shininess
    global amb_on, diff_on, spec_on, use_phong, show_panel
    global orbit_x, orbit_y

    if isinstance(key, bytes):
        key = key.decode("utf-8")

    if key == "1":
        amb_on  = not amb_on
        print(f"Ambient:  {'ON' if amb_on  else 'OFF'}")
    elif key == "2":
        diff_on = not diff_on
        print(f"Diffuse:  {'ON' if diff_on else 'OFF'}")
    elif key == "3":
        spec_on = not spec_on
        print(f"Specular: {'ON' if spec_on else 'OFF'}")
    elif key in ("g", "G"):
        use_phong = not use_phong
        mode = "Phong (per-fragment)" if use_phong else "Gouraud (per-vertex)"
        print(f"Shading: {mode}")
    elif key in ("+", "="):
        shininess = min(256.0, shininess * 2.0)
        print(f"Shininess: {shininess:.0f}")
    elif key in ("-", "_"):
        shininess = max(1.0, shininess / 2.0)
        print(f"Shininess: {shininess:.0f}")
    elif key == "[":
        light_pos[2] -= 0.3
        print(f"Light: ({light_pos[0]:.1f}, {light_pos[1]:.1f}, {light_pos[2]:.1f})")
    elif key == "]":
        light_pos[2] += 0.3
        print(f"Light: ({light_pos[0]:.1f}, {light_pos[1]:.1f}, {light_pos[2]:.1f})")
    elif key in ("r", "R"):
        orbit_x, orbit_y = 0.0, 0.0
        light_pos[:] = [2.0, 3.0, 2.0]
        Ka, Kd, Ks   = 0.20, 1.00, 0.80
        shininess    = 32.0
        amb_on = diff_on = spec_on = True
        use_phong = True
        print("Reset.")
    elif key in ("p", "P"):
        show_panel = not show_panel
    elif key == "\x1b":
        glutLeaveMainLoop()
        return

    glutPostRedisplay()


def special_keys(key, _x, _y):
    step = 0.25
    if   key == GLUT_KEY_LEFT:  light_pos[0] -= step
    elif key == GLUT_KEY_RIGHT: light_pos[0] += step
    elif key == GLUT_KEY_UP:    light_pos[1] += step
    elif key == GLUT_KEY_DOWN:  light_pos[1] -= step
    print(f"Light: ({light_pos[0]:.1f}, {light_pos[1]:.1f}, {light_pos[2]:.1f})")
    glutPostRedisplay()


def mouse(button, state, x, y):
    global mouse_dragging, mouse_last_x, mouse_last_y
    if button == GLUT_LEFT_BUTTON:
        mouse_dragging = (state == GLUT_DOWN)
        mouse_last_x, mouse_last_y = x, y


def motion(x, y):
    global orbit_x, orbit_y, mouse_last_x, mouse_last_y
    if not mouse_dragging:
        return
    dx = x - mouse_last_x
    dy = y - mouse_last_y
    orbit_y  += dx * 0.5
    orbit_x  += dy * 0.5
    orbit_x   = max(-89.0, min(89.0, orbit_x))
    mouse_last_x, mouse_last_y = x, y
    glutPostRedisplay()

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    print("=" * 54)
    print(" Lab 7: Phong Illumination Model (OpenGL)")
    print("=" * 54)
    print("3D sphere with per-fragment Phong shading via GLSL.\n")
    print("  1 / 2 / 3   toggle Ambient / Diffuse / Specular")
    print("  g           Phong ↔ Gouraud shading mode")
    print("  + / -       shininess ×2 / ÷2")
    print("  Arrow keys  move light (X / Y)")
    print("  [ / ]       move light (Z)")
    print("  Mouse drag  orbit sphere")
    print("  r           reset   p  panel   Esc  quit\n")

    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIN_W, WIN_H)
    glutCreateWindow(b"Lab 7: Phong Illumination Model")

    try:
        init_gl()
    except Exception as exc:
        print("Shader init failed:", exc)
        sys.exit(1)

    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_keys)
    glutMouseFunc(mouse)
    glutMotionFunc(motion)
    glutMainLoop()


if __name__ == "__main__":
    main()
