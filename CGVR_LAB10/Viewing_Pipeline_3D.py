"""
3D Viewing Pipeline — OpenGL Lab 10
=====================================
Implements the full MVP + Viewport pipeline and visualises every stage:

  Model Space ──[Model Matrix ]──► World Space
  World Space ──[View  Matrix ]──► Eye / Camera Space
  Eye Space   ──[Proj  Matrix ]──► Clip Space
  Clip Space  ──[÷ w (P-div) ]──► NDC  Space  [-1, 1]³
  NDC Space   ──[Viewport Map ]──► Screen Space  [px]

Press 'v' to enable split-view: left = Perspective, right = Orthographic.
The left panel shows the actual matrices for each stage, updated live.

Requires: pip install PyOpenGL PyOpenGL_accelerate

Controls
--------
  Arrow keys   orbit camera  (← → = azimuth,  ↑ ↓ = elevation)
  [ / ]        zoom in / out
  W / S        rotate main cube  (pitch)
  A / D        rotate main cube  (yaw)
  o            toggle Perspective ↔ Orthographic
  v            toggle split-view (Perspective | Orthographic)
  + / -        FOV (perspective) or ortho size
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
    GL_LINES,
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
    glLineWidth,
    glLinkProgram,
    glLoadIdentity,
    glLoadMatrixf,
    glMatrixMode,
    glPopMatrix,
    glPushMatrix,
    glRasterPos2f,
    glShaderSource,
    glUniformMatrix4fv,
    glUseProgram,
    glVertex2f,
    glVertex3f,
    glVertexAttribPointer,
    glViewport,
    GL_RENDERER,
    GL_SHADING_LANGUAGE_VERSION,
    GL_VERSION,
)
from OpenGL.GLU import gluOrtho2D
from OpenGL.GLUT import (
    GLUT_BITMAP_HELVETICA_10,
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
WIN_W, WIN_H = 1200, 700
PANEL_W      = 400

# ---------------------------------------------------------------------------
# Shaders — simple per-vertex colour, explicit Model × View × Proj
# ---------------------------------------------------------------------------
VERTEX_SHADER = """
#version 120
attribute vec3 aPos;
attribute vec3 aColor;
uniform mat4 uModel;
uniform mat4 uView;
uniform mat4 uProj;
varying vec3 vColor;
void main() {
    gl_Position = uProj * uView * uModel * vec4(aPos, 1.0);
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

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
cam_azimuth   = 35.0     # degrees — horizontal orbit
cam_elevation = 22.0     # degrees — vertical orbit
cam_dist      = 7.0

use_persp     = True
fov_deg       = 45.0
ortho_size    = 3.5

cube_rot_x    = 0.0
cube_rot_y    = 0.0

split_view    = False
show_panel    = True

mouse_dragging = False
mouse_last_x   = 0
mouse_last_y   = 0

# GL handles
program     = None
vbo = ibo   = None
loc_model = loc_view = loc_proj = -1

# Cached matrices (recomputed each frame, shared with panel draw)
_view_mat = None
_proj_mat = None
_eye_pos  = (0.0, 0.0, 7.0)

# ---------------------------------------------------------------------------
# Cube geometry — 6 faces × 4 verts, interleaved [x,y,z, r,g,b]
# ---------------------------------------------------------------------------
def build_cube(half=0.6):
    corners = [
        (-half,-half,-half),( half,-half,-half),( half, half,-half),(-half, half,-half),
        (-half,-half, half),( half,-half, half),( half, half, half),(-half, half, half),
    ]
    face_corners = [
        (0,1,2,3), (4,7,6,5), (0,4,5,1), (3,2,6,7), (0,3,7,4), (1,5,6,2),
    ]
    face_colors = [
        (0.90,0.28,0.28), (0.28,0.80,0.38), (0.30,0.52,1.00),
        (1.00,0.82,0.28), (0.76,0.32,0.92), (0.28,0.88,0.88),
    ]
    verts, idxs = [], []
    base = 0
    for (f0,f1,f2,f3), (cr,cg,cb) in zip(face_corners, face_colors):
        for vi in (f0, f1, f2, f3):
            verts.extend(list(corners[vi]) + [cr, cg, cb])
        idxs.extend([base, base+1, base+2, base, base+2, base+3])
        base += 4
    return verts, idxs

# ---------------------------------------------------------------------------
# Column-major matrix math
# ---------------------------------------------------------------------------
def mat4_identity():
    return [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]

def mat4_mul(a, b):
    out = [0.0]*16
    for col in range(4):
        for row in range(4):
            for k in range(4):
                out[col*4+row] += a[k*4+row] * b[col*4+k]
    return out

def mat4_rotate_x(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return [1,0,0,0, 0,c,s,0, 0,-s,c,0, 0,0,0,1]

def mat4_rotate_y(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return [c,0,-s,0, 0,1,0,0, s,0,c,0, 0,0,0,1]

def mat4_translate_v(tx, ty, tz):
    m = mat4_identity()
    m[12], m[13], m[14] = tx, ty, tz
    return m

def mat4_scale_u(s):
    m = mat4_identity()
    m[0] = m[5] = m[10] = s
    return m

def mat4_lookat(eye, center, up):
    """Standard GLM-style LookAt, column-major output."""
    ex, ey, ez = eye
    cx, cy, cz = center
    upx, upy, upz = up

    fx, fy, fz = cx-ex, cy-ey, cz-ez
    fl = math.sqrt(fx*fx+fy*fy+fz*fz)
    if fl < 1e-10:
        fx, fy, fz = 0.0, 0.0, -1.0
    else:
        fx, fy, fz = fx/fl, fy/fl, fz/fl

    sx = fy*upz - fz*upy
    sy = fz*upx - fx*upz
    sz = fx*upy - fy*upx
    sl = math.sqrt(sx*sx+sy*sy+sz*sz)
    if sl < 1e-10:
        sx, sy, sz = 1.0, 0.0, 0.0
    else:
        sx, sy, sz = sx/sl, sy/sl, sz/sl

    ux = sy*fz - sz*fy
    uy = sz*fx - sx*fz
    uz = sx*fy - sy*fx

    t0 = -(sx*ex + sy*ey + sz*ez)
    t1 = -(ux*ex + uy*ey + uz*ez)
    t2 =   fx*ex + fy*ey + fz*ez   # = dot(forward, eye)

    return [
        sx, ux, -fx, 0,   # col 0
        sy, uy, -fy, 0,   # col 1
        sz, uz, -fz, 0,   # col 2
        t0, t1,  t2, 1,   # col 3
    ]

def mat4_perspective(fovy_deg, aspect, near, far):
    f  = 1.0 / math.tan(math.radians(fovy_deg) / 2.0)
    nf = 1.0 / (near - far)
    return [
        f/aspect, 0, 0,  0,
        0,        f, 0,  0,
        0, 0, (far+near)*nf,    -1,
        0, 0, 2*far*near*nf,     0,
    ]

def mat4_ortho(l, r, b, t, n, f):
    return [
        2/(r-l), 0,       0,        0,
        0,       2/(t-b), 0,        0,
        0,       0,      -2/(f-n),  0,
        -(r+l)/(r-l), -(t+b)/(t-b), -(f+n)/(f-n), 1,
    ]

def get_eye():
    az = math.radians(cam_azimuth)
    el = math.radians(cam_elevation)
    x  = cam_dist * math.sin(az) * math.cos(el)
    y  = cam_dist * math.sin(el)
    z  = cam_dist * math.cos(az) * math.cos(el)
    return (x, y, z)

def compute_matrices(aspect):
    eye  = get_eye()
    view = mat4_lookat(eye, (0,0,0), (0,1,0))
    if use_persp:
        proj = mat4_perspective(fov_deg, aspect, 0.1, 100.0)
    else:
        s    = ortho_size
        proj = mat4_ortho(-s*aspect, s*aspect, -s, s, 0.1, 100.0)
    return view, proj, eye

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
        raise RuntimeError(f"{label} error:\n{log}")
    return sh

def create_program(vs_src, fs_src):
    vs   = compile_shader(vs_src, GL_VERTEX_SHADER,   "Vertex")
    fs   = compile_shader(fs_src, GL_FRAGMENT_SHADER, "Fragment")
    prog = glCreateProgram()
    glAttachShader(prog, vs)
    glAttachShader(prog, fs)
    glBindAttribLocation(prog, 0, "aPos")
    glBindAttribLocation(prog, 1, "aColor")
    glLinkProgram(prog)
    if not int(glGetProgramiv(prog, GL_LINK_STATUS)):
        log = glGetProgramInfoLog(prog)
        if isinstance(log, bytes):
            log = log.decode("utf-8", errors="replace")
        raise RuntimeError(f"Link error:\n{log}")
    glDeleteShader(vs)
    glDeleteShader(fs)
    return prog

STRIDE = 6 * 4   # 6 floats × 4 bytes

def bind_attribs():
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, STRIDE, None)
    glEnableVertexAttribArray(1)
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, STRIDE, c_void_p(12))

# ---------------------------------------------------------------------------
# GL initialisation
# ---------------------------------------------------------------------------
def init_gl():
    global program, vbo, ibo, loc_model, loc_view, loc_proj

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

    program   = create_program(VERTEX_SHADER, FRAGMENT_SHADER)
    loc_model = glGetUniformLocation(program, "uModel")
    loc_view  = glGetUniformLocation(program, "uView")
    loc_proj  = glGetUniformLocation(program, "uProj")

    verts, idxs = build_cube()
    v_raw = array.array("f", verts).tobytes()
    i_raw = array.array("I", idxs).tobytes()

    bufs = glGenBuffers(2)
    vbo  = int(bufs[0])
    ibo  = int(bufs[1])

    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, len(v_raw), v_raw, GL_STATIC_DRAW)

    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ibo)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(i_raw), i_raw, GL_STATIC_DRAW)

    glBindBuffer(GL_ARRAY_BUFFER, 0)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

# ---------------------------------------------------------------------------
# Draw 3D scene in a given viewport
# ---------------------------------------------------------------------------
def draw_scene(vp_x, vp_y, vp_w, vp_h, view_mat, proj_mat):
    glViewport(vp_x, vp_y, vp_w, vp_h)
    glEnable(GL_DEPTH_TEST)

    # ── Shaded cubes ─────────────────────────────────────────────────────
    glUseProgram(program)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ibo)
    bind_attribs()

    glUniformMatrix4fv(loc_view, 1, GL_FALSE, view_mat)
    glUniformMatrix4fv(loc_proj, 1, GL_FALSE, proj_mat)

    # Main cube (user-rotated)
    model_a = mat4_mul(mat4_rotate_y(cube_rot_y), mat4_rotate_x(cube_rot_x))
    glUniformMatrix4fv(loc_model, 1, GL_FALSE, model_a)
    glDrawElements(GL_TRIANGLES, 36, GL_UNSIGNED_INT, None)

    # Cube B — right, smaller
    model_b = mat4_mul(mat4_translate_v(2.4, 0.0, 0.0), mat4_scale_u(0.38))
    glUniformMatrix4fv(loc_model, 1, GL_FALSE, model_b)
    glDrawElements(GL_TRIANGLES, 36, GL_UNSIGNED_INT, None)

    # Cube C — left-back
    model_c = mat4_mul(mat4_translate_v(-2.1, 0.0,-1.6), mat4_scale_u(0.52))
    glUniformMatrix4fv(loc_model, 1, GL_FALSE, model_c)
    glDrawElements(GL_TRIANGLES, 36, GL_UNSIGNED_INT, None)

    glDisableVertexAttribArray(0)
    glDisableVertexAttribArray(1)
    glBindBuffer(GL_ARRAY_BUFFER, 0)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

    # ── Grid + Axes (fixed-function) ─────────────────────────────────────
    glUseProgram(0)
    glMatrixMode(GL_PROJECTION)
    glLoadMatrixf(proj_mat)
    glMatrixMode(GL_MODELVIEW)
    glLoadMatrixf(view_mat)

    # Floor grid at y = -0.6
    glColor3f(0.18, 0.18, 0.20)
    glLineWidth(1.0)
    glBegin(GL_LINES)
    for i in range(-6, 7):
        glVertex3f(i,  -0.6, -6);  glVertex3f(i,  -0.6,  6)
        glVertex3f(-6, -0.6,  i);  glVertex3f( 6, -0.6,  i)
    glEnd()

    # Coordinate axes
    glLineWidth(2.5)
    glBegin(GL_LINES)
    glColor3f(0.92, 0.22, 0.22); glVertex3f(0,0,0); glVertex3f(3,0,0)   # X red
    glColor3f(0.22, 0.88, 0.22); glVertex3f(0,0,0); glVertex3f(0,3,0)   # Y green
    glColor3f(0.25, 0.45, 0.95); glVertex3f(0,0,0); glVertex3f(0,0,3)   # Z blue
    glEnd()
    glLineWidth(1.0)


# ---------------------------------------------------------------------------
# Panel drawing helpers
# ---------------------------------------------------------------------------
def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_12):
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))


def draw_mat4_rows(m, tx, ty, line_h):
    """Render a column-major 4×4 matrix as 4 text rows. Returns new ty."""
    for r in range(4):
        vals  = [m[c * 4 + r] for c in range(4)]
        s     = "|%6.2f %6.2f %6.2f %6.2f|" % tuple(vals)
        glColor3f(0.70, 0.70, 0.70)
        draw_text(tx, ty, s, GLUT_BITMAP_HELVETICA_10)
        ty -= line_h
    return ty


def draw_panel(view_mat, proj_mat, eye):
    if not show_panel:
        return

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Background
    glColor3f(0.08, 0.08, 0.10)
    glBegin(GL_QUADS)
    glVertex2f(0,       0);      glVertex2f(PANEL_W, 0)
    glVertex2f(PANEL_W, WIN_H);  glVertex2f(0,       WIN_H)
    glEnd()

    # Right-edge accent line
    from OpenGL.GL import GL_LINES as _GL_LINES
    glColor3f(0.28, 0.28, 0.32)
    glBegin(_GL_LINES)
    glVertex2f(PANEL_W, 0); glVertex2f(PANEL_W, WIN_H)
    glEnd()

    tx   = 16
    ty   = WIN_H - 28
    line = 19
    sm   = 16   # small line height (for matrix rows)

    # ── Title ─────────────────────────────────────────────────────────────
    glColor3f(1.0, 0.88, 0.35)
    draw_text(tx, ty, "3D Viewing Pipeline", GLUT_BITMAP_HELVETICA_18)
    ty -= line + 4
    glColor3f(0.42, 0.42, 0.48)
    draw_text(tx, ty, "Model\u2192World \u2192Eye \u2192Clip \u2192NDC \u2192Screen")
    ty -= line + 8

    # ── Stage 1 ───────────────────────────────────────────────────────────
    glColor3f(0.40, 0.80, 1.00)
    draw_text(tx, ty, "1  Model Space \u2192 World Space")
    ty -= line
    glColor3f(0.58, 0.58, 0.62)
    draw_text(tx + 10, ty, "Model = R\u02b8 * R\u02d0 * S  (user rotation)")
    ty -= sm
    model_a = mat4_mul(mat4_rotate_y(cube_rot_y), mat4_rotate_x(cube_rot_x))
    ty = draw_mat4_rows(model_a, tx + 10, ty, sm)
    ty -= 6

    # ── Stage 2 ───────────────────────────────────────────────────────────
    glColor3f(0.40, 0.80, 1.00)
    draw_text(tx, ty, "2  World Space \u2192 Eye Space")
    ty -= line
    glColor3f(0.58, 0.58, 0.62)
    ex, ey, ez = eye
    draw_text(tx + 10, ty, f"Eye  ({ex:+.2f}, {ey:+.2f}, {ez:+.2f})")
    ty -= sm
    draw_text(tx + 10, ty, "At   ( 0.00,  0.00,  0.00)")
    ty -= sm
    ty = draw_mat4_rows(view_mat, tx + 10, ty, sm)
    ty -= 6

    # ── Stage 3 ───────────────────────────────────────────────────────────
    glColor3f(0.40, 0.80, 1.00)
    draw_text(tx, ty, "3  Eye Space \u2192 Clip Space")
    ty -= line
    glColor3f(0.58, 0.58, 0.62)
    if use_persp:
        vp_w = (WIN_W - PANEL_W) // (2 if split_view else 1)
        aspect = vp_w / WIN_H
        draw_text(tx + 10, ty, f"PERSPECTIVE  FOV={fov_deg:.0f}\u00b0  a={aspect:.2f}")
        ty -= sm
        draw_text(tx + 10, ty,  "near=0.1  far=100")
    else:
        draw_text(tx + 10, ty, f"ORTHOGRAPHIC  size={ortho_size:.1f}")
        ty -= sm
        draw_text(tx + 10, ty,  "near=0.1  far=100")
    ty -= sm
    ty = draw_mat4_rows(proj_mat, tx + 10, ty, sm)
    ty -= 6

    # ── Stage 4 ───────────────────────────────────────────────────────────
    glColor3f(0.40, 0.80, 1.00)
    draw_text(tx, ty, "4  Clip Space \u2192 NDC  (perspective divide)")
    ty -= line
    glColor3f(0.58, 0.58, 0.62)
    for s in ("x_ndc = x_clip / w_clip",
              "y_ndc = y_clip / w_clip",
              "z_ndc = z_clip / w_clip    \u2208 [-1, 1]"):
        draw_text(tx + 10, ty, s)
        ty -= sm
    ty -= 4

    # ── Stage 5 ───────────────────────────────────────────────────────────
    glColor3f(0.40, 0.80, 1.00)
    draw_text(tx, ty, "5  NDC \u2192 Screen  (viewport map)")
    ty -= line
    glColor3f(0.58, 0.58, 0.62)
    vp_w_disp = WIN_W - PANEL_W
    for s in (f"x_s = (x_ndc + 1) \u00d7 {vp_w_disp}/2  + {PANEL_W}",
               f"y_s = (y_ndc + 1) \u00d7 {WIN_H}/2",
               f"Viewport: {vp_w_disp} \u00d7 {WIN_H} px"):
        draw_text(tx + 10, ty, s)
        ty -= sm
    ty -= 6

    # ── Projection mode indicator ──────────────────────────────────────────
    mode  = "PERSPECTIVE" if use_persp else "ORTHOGRAPHIC"
    mcol  = (0.35, 1.0, 0.55) if use_persp else (1.0, 0.85, 0.35)
    glColor3f(*mcol)
    draw_text(tx, ty, f"Mode: {mode}  [o]     Split: {'ON' if split_view else 'OFF'}  [v]")
    ty -= line + 4

    # ── Controls ──────────────────────────────────────────────────────────
    glColor3f(0.42, 0.42, 0.48)
    draw_text(tx, ty, "Controls:")
    ty -= line
    for ctrl in (
        "Arrows   orbit camera",
        "[ / ]    zoom in / out",
        "W/S A/D  rotate main cube",
        "o        toggle projection",
        "v        split view",
        "+ / -    FOV / ortho size",
        "r        reset   p  panel   Esc quit",
    ):
        glColor3f(0.48, 0.48, 0.52)
        draw_text(tx + 10, ty, ctrl)
        ty -= sm

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


# ---------------------------------------------------------------------------
# GLUT callbacks
# ---------------------------------------------------------------------------
def display():
    global _view_mat, _proj_mat, _eye_pos

    # Full clear
    glViewport(0, 0, WIN_W, WIN_H)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    scene_x = PANEL_W
    scene_w = WIN_W - PANEL_W

    if split_view:
        half_w = scene_w // 2

        # Left: Perspective
        p_view, p_proj, eye = compute_matrices(half_w / WIN_H)
        p_proj_forced = mat4_perspective(fov_deg, half_w / WIN_H, 0.1, 100.0)
        draw_scene(scene_x, 0, half_w, WIN_H, p_view, p_proj_forced)

        # Right: Orthographic
        s     = ortho_size
        asp   = half_w / WIN_H
        o_proj = mat4_ortho(-s*asp, s*asp, -s, s, 0.1, 100.0)
        draw_scene(scene_x + half_w, 0, half_w, WIN_H, p_view, o_proj)

        # Cache the active (left) matrices for panel
        _view_mat = p_view
        _proj_mat = p_proj_forced
        _eye_pos  = eye

    else:
        view, proj, eye = compute_matrices(scene_w / WIN_H)
        draw_scene(scene_x, 0, scene_w, WIN_H, view, proj)
        _view_mat = view
        _proj_mat = proj
        _eye_pos  = eye

    # 2-D overlay
    glViewport(0, 0, WIN_W, WIN_H)
    glDisable(GL_DEPTH_TEST)
    glUseProgram(0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    draw_panel(_view_mat, _proj_mat, _eye_pos)

    # Split-view labels
    if split_view:
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, WIN_W, 0, WIN_H)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        half_w = (WIN_W - PANEL_W) // 2
        glColor3f(0.35, 1.0, 0.55)
        draw_text(PANEL_W + 6, WIN_H - 22,
                  f"PERSPECTIVE   FOV={fov_deg:.0f}\u00b0", GLUT_BITMAP_HELVETICA_12)
        glColor3f(1.0, 0.85, 0.35)
        draw_text(PANEL_W + half_w + 6, WIN_H - 22,
                  f"ORTHOGRAPHIC  size={ortho_size:.1f}", GLUT_BITMAP_HELVETICA_12)

        # Divider line between the two views
        glColor3f(0.30, 0.30, 0.35)
        from OpenGL.GL import GL_LINES as _L
        glBegin(_L)
        glVertex2f(PANEL_W + half_w, 0)
        glVertex2f(PANEL_W + half_w, WIN_H)
        glEnd()

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    glutSwapBuffers()


def reshape(w, h):
    global WIN_W, WIN_H
    WIN_W, WIN_H = max(1, w), max(1, h)
    glViewport(0, 0, WIN_W, WIN_H)


def keyboard(key, _x, _y):
    global fov_deg, ortho_size, use_persp, split_view, show_panel
    global cube_rot_x, cube_rot_y, cam_azimuth, cam_elevation, cam_dist

    if isinstance(key, bytes):
        key = key.decode("utf-8")

    if key in ("w", "W"):
        cube_rot_x = (cube_rot_x + 5.0) % 360
    elif key in ("s", "S"):
        cube_rot_x = (cube_rot_x - 5.0) % 360
    elif key in ("a", "A"):
        cube_rot_y = (cube_rot_y - 5.0) % 360
    elif key in ("d", "D"):
        cube_rot_y = (cube_rot_y + 5.0) % 360
    elif key in ("o", "O"):
        use_persp = not use_persp
        print(f"Projection: {'Perspective' if use_persp else 'Orthographic'}")
    elif key in ("v", "V"):
        split_view = not split_view
        print(f"Split view: {'ON' if split_view else 'OFF'}")
    elif key in ("+", "="):
        if use_persp:
            fov_deg = min(120.0, fov_deg + 5.0)
        else:
            ortho_size = min(10.0, ortho_size + 0.5)
    elif key in ("-", "_"):
        if use_persp:
            fov_deg = max(10.0, fov_deg - 5.0)
        else:
            ortho_size = max(0.5, ortho_size - 0.5)
    elif key == "[":
        cam_dist = max(2.0, cam_dist - 0.5)
    elif key == "]":
        cam_dist = min(20.0, cam_dist + 0.5)
    elif key in ("r", "R"):
        cam_azimuth, cam_elevation, cam_dist = 35.0, 22.0, 7.0
        fov_deg, ortho_size = 45.0, 3.5
        cube_rot_x = cube_rot_y = 0.0
        use_persp = True
        split_view = False
        print("Reset.")
    elif key in ("p", "P"):
        show_panel = not show_panel
    elif key == "\x1b":
        glutLeaveMainLoop()
        return

    glutPostRedisplay()


def special_keys(key, _x, _y):
    global cam_azimuth, cam_elevation
    if   key == GLUT_KEY_LEFT:  cam_azimuth   -= 3.0
    elif key == GLUT_KEY_RIGHT: cam_azimuth   += 3.0
    elif key == GLUT_KEY_UP:    cam_elevation  = min(88.0, cam_elevation + 3.0)
    elif key == GLUT_KEY_DOWN:  cam_elevation  = max(-88.0, cam_elevation - 3.0)
    glutPostRedisplay()


def mouse(button, state, x, y):
    global mouse_dragging, mouse_last_x, mouse_last_y
    if button == GLUT_LEFT_BUTTON:
        mouse_dragging = (state == GLUT_DOWN)
        mouse_last_x, mouse_last_y = x, y


def motion(x, y):
    global cam_azimuth, cam_elevation, mouse_last_x, mouse_last_y
    if not mouse_dragging:
        return
    dx = x - mouse_last_x
    dy = y - mouse_last_y
    cam_azimuth   += dx * 0.4
    cam_elevation  = max(-88.0, min(88.0, cam_elevation - dy * 0.4))
    mouse_last_x, mouse_last_y = x, y
    glutPostRedisplay()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    print("=" * 58)
    print(" Lab 10: 3D Viewing Pipeline")
    print("=" * 58)
    print("Full MVP pipeline with live matrix display.\n")
    print("  Arrow keys  orbit camera")
    print("  [ / ]       zoom")
    print("  W/S A/D     rotate main cube")
    print("  o           toggle Perspective / Orthographic")
    print("  v           split view (Perspective | Orthographic)")
    print("  + / -       FOV or ortho size")
    print("  r           reset   p  panel   Esc  quit\n")

    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIN_W, WIN_H)
    glutCreateWindow(b"Lab 10: 3D Viewing Pipeline")

    try:
        init_gl()
    except Exception as exc:
        print("Init failed:", exc)
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
