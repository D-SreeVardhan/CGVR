"""
Z-Buffer Hidden Surface Removal - OpenGL
-----------------------------------------
Requires: pip install PyOpenGL PyOpenGL_accelerate

Scene: five overlapping coloured quads at different Z depths.
Press 'z' to toggle the Z-buffer on / off and see the visual difference.
Use arrow keys to orbit the scene; '+'/'-' to zoom.
"""

import math
import sys

from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_FILL,
    GL_FRONT_AND_BACK,
    GL_LESS,
    GL_MODELVIEW,
    GL_PROJECTION,
    GL_QUADS,
    glBegin,
    glClear,
    glClearColor,
    glClearDepth,
    glColor3f,
    glDepthFunc,
    glDisable,
    glEnable,
    glEnd,
    glLoadIdentity,
    glMatrixMode,
    glPolygonMode,
    glPopMatrix,
    glPushMatrix,
    glRasterPos2f,
    glRotatef,
    glVertex3f,
    glViewport,
)
from OpenGL.GLU import gluLookAt, gluOrtho2D, gluPerspective
from OpenGL.GLUT import (
    GLUT_BITMAP_HELVETICA_12,
    GLUT_BITMAP_HELVETICA_18,
    GLUT_DEPTH,
    GLUT_DOUBLE,
    GLUT_KEY_DOWN,
    GLUT_KEY_LEFT,
    GLUT_KEY_RIGHT,
    GLUT_KEY_UP,
    GLUT_RGB,
    glutBitmapCharacter,
    glutCreateWindow,
    glutDisplayFunc,
    glutInit,
    glutInitDisplayMode,
    glutInitWindowSize,
    glutKeyboardFunc,
    glutLeaveMainLoop,
    glutMainLoop,
    glutPostRedisplay,
    glutReshapeFunc,
    glutSpecialFunc,
    glutSwapBuffers,
)

try:
    from OpenGL.GLUT import glutMouseWheelFunc
    _HAS_WHEEL = True
except ImportError:
    _HAS_WHEEL = False

WIN_W, WIN_H = 1000, 700

# ------------------------------------------------------------------
# Scene data — 5 overlapping quads at different Z depths
# Each tuple: (r, g, b, half-size, z-depth, x-offset, y-offset)
# ------------------------------------------------------------------
QUADS = [
    (0.95, 0.30, 0.30, 0.60,  0.0,  0.00,  0.00),   # red    — front
    (0.30, 0.55, 1.00, 0.50, -0.4,  0.20,  0.20),   # blue
    (0.30, 0.90, 0.40, 0.50, -0.8, -0.20,  0.30),   # green
    (0.95, 0.85, 0.25, 0.45, -1.2,  0.10, -0.25),   # yellow
    (0.80, 0.35, 0.95, 0.40, -1.6, -0.10, -0.15),   # purple — back
]

QUAD_LABELS = [
    (0.95, 0.30, 0.30, "Red     z= 0.0  (front)"),
    (0.30, 0.55, 1.00, "Blue    z=-0.4"),
    (0.30, 0.90, 0.40, "Green   z=-0.8"),
    (0.95, 0.85, 0.25, "Yellow  z=-1.2"),
    (0.80, 0.35, 0.95, "Purple  z=-1.6  (back)"),
]

zbuffer_on = True
orbit_x    = 25.0    # pitch (degrees)
orbit_y    = -20.0   # yaw   (degrees)
zoom_dist  = 5.0
show_panel = True


# ------------------------------------------------------------------
# Drawing helpers
# ------------------------------------------------------------------

def draw_quad(r, g, b, half, z, ox, oy):
    glColor3f(r, g, b)
    glBegin(GL_QUADS)
    glVertex3f(ox - half, oy - half, z)
    glVertex3f(ox + half, oy - half, z)
    glVertex3f(ox + half, oy + half, z)
    glVertex3f(ox - half, oy + half, z)
    glEnd()


def draw_text_2d(x, y, text, font=GLUT_BITMAP_HELVETICA_12):
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))


def draw_info_panel():
    if not show_panel:
        return

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    tx = 20
    ty = WIN_H - 30
    line = 20

    glColor3f(1.0, 0.9, 0.4)
    draw_text_2d(tx, ty, "Z-Buffer Hidden Surface Removal", GLUT_BITMAP_HELVETICA_18)
    ty -= line + 4

    r, g, b = (0.3, 0.9, 0.4) if zbuffer_on else (0.95, 0.35, 0.35)
    glColor3f(r, g, b)
    state = "ENABLED" if zbuffer_on else "DISABLED"
    draw_text_2d(tx, ty, f"Z-Buffer: {state}  (press z to toggle)")
    ty -= line

    glColor3f(0.65, 0.65, 0.65)
    draw_text_2d(tx, ty, "Arrow keys: orbit   +/-: zoom   p: toggle panel   Esc: quit")
    ty -= int(line * 1.6)

    glColor3f(0.5, 0.85, 1.0)
    draw_text_2d(tx, ty, "Algorithm:")
    ty -= line
    glColor3f(0.85, 0.85, 0.85)
    for code_line in (
        "init depthBuffer[x][y] = INF  for all pixels",
        "for each polygon:",
        "    for each fragment (x, y, z):",
        "        if z < depthBuffer[x][y]:",
        "            colorBuffer[x][y] = fragment.color",
        "            depthBuffer[x][y] = z",
    ):
        draw_text_2d(tx, ty, f"  {code_line}")
        ty -= line

    ty -= 6
    glColor3f(0.5, 0.85, 1.0)
    draw_text_2d(tx, ty, "Quads (front to back):")
    ty -= line
    for r, g, b, label in QUAD_LABELS:
        glColor3f(r, g, b)
        draw_text_2d(tx, ty, f"  {label}")
        ty -= line

    if not zbuffer_on:
        ty -= 4
        glColor3f(1.0, 0.6, 0.2)
        draw_text_2d(
            tx, ty,
            "Z-Buffer OFF: painter's order ignored — last drawn (purple) wins!"
        )

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


# ------------------------------------------------------------------
# GLUT callbacks
# ------------------------------------------------------------------

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, WIN_W / WIN_H, 0.1, 100.0)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(0, 0, zoom_dist, 0, 0, 0, 0, 1, 0)

    glPushMatrix()
    glRotatef(orbit_x, 1, 0, 0)
    glRotatef(orbit_y, 0, 1, 0)

    if zbuffer_on:
        glEnable(GL_DEPTH_TEST)
    else:
        glDisable(GL_DEPTH_TEST)

    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    for quad in QUADS:
        r, g, b, half, z, ox, oy = quad
        draw_quad(r, g, b, half, z, ox, oy)

    glPopMatrix()

    draw_info_panel()
    glutSwapBuffers()


def reshape(w, h):
    global WIN_W, WIN_H
    WIN_W, WIN_H = max(1, w), max(1, h)
    glViewport(0, 0, WIN_W, WIN_H)


def keyboard(key, _x, _y):
    global zbuffer_on, show_panel, zoom_dist
    if isinstance(key, bytes):
        key = key.decode("utf-8")
    if key in ("z", "Z"):
        zbuffer_on = not zbuffer_on
        print(f"[Z-Buffer] {'ON' if zbuffer_on else 'OFF'}")
        glutPostRedisplay()
    elif key in ("p", "P"):
        show_panel = not show_panel
        glutPostRedisplay()
    elif key in ("+", "="):
        zoom_dist = max(1.5, zoom_dist - 0.3)
        glutPostRedisplay()
    elif key in ("-", "_"):
        zoom_dist = min(15.0, zoom_dist + 0.3)
        glutPostRedisplay()
    elif key == "\x1b":
        glutLeaveMainLoop()


def special_keys(key, _x, _y):
    global orbit_x, orbit_y
    if key == GLUT_KEY_UP:
        orbit_x = min(89.0, orbit_x + 3.0)
    elif key == GLUT_KEY_DOWN:
        orbit_x = max(-89.0, orbit_x - 3.0)
    elif key == GLUT_KEY_LEFT:
        orbit_y -= 3.0
    elif key == GLUT_KEY_RIGHT:
        orbit_y += 3.0
    glutPostRedisplay()


def mouse_wheel(_wheel, direction, _x, _y):
    global zoom_dist
    zoom_dist = max(1.5, min(15.0, zoom_dist + (-0.3 if direction > 0 else 0.3)))
    glutPostRedisplay()


def init_gl():
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glClearDepth(1.0)
    glDepthFunc(GL_LESS)


def main():
    print("=" * 52)
    print(" Lab 6: Z-Buffer Hidden Surface Removal")
    print("=" * 52)
    print("Five overlapping coloured quads at different depths.")
    print()
    print("  z          -> toggle Z-buffer on / off")
    print("  Arrow keys -> orbit the scene")
    print("  + / -      -> zoom in / out")
    print("  p          -> toggle info panel")
    print("  Esc        -> quit")
    print()
    print("Z-Buffer ON  : correct depth order (front quad visible).")
    print("Z-Buffer OFF : last-drawn quad (purple) always on top.")
    print()

    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIN_W, WIN_H)
    glutCreateWindow(b"Lab 6: Z-Buffer Hidden Surface Removal")
    init_gl()
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_keys)
    if _HAS_WHEEL:
        try:
            glutMouseWheelFunc(mouse_wheel)
        except Exception:
            pass
    glutMainLoop()


if __name__ == "__main__":
    main()
