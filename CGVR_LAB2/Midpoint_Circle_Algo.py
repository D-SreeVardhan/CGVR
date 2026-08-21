"""
Midpoint Circle Algorithm - iterative plot (OpenGL)
----------------------------------------------------
Requires: pip install PyOpenGL PyOpenGL_accelerate

Enter center (xc, yc) and radius r in the terminal.
The OpenGL window plots the circle point-by-point on a coordinate grid.
"""

import math

from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
    GL_LINES,
    GL_LINE_LOOP,
    GL_MODELVIEW,
    GL_POINTS,
    GL_PROJECTION,
    glBegin,
    glClear,
    glClearColor,
    glColor3f,
    glEnd,
    glLineWidth,
    glLoadIdentity,
    glMatrixMode,
    glPointSize,
    glRasterPos2f,
    glVertex2f,
)
from OpenGL.GLU import gluOrtho2D
from OpenGL.GLUT import (
    GLUT_BITMAP_HELVETICA_10,
    GLUT_BITMAP_HELVETICA_12,
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
    glutMouseWheelFunc,
    glutPostRedisplay,
    glutSpecialFunc,
    glutSwapBuffers,
    glutTimerFunc,
)

WIN_W, WIN_H = 700, 700


# ------------------------------------------------------------------
# Midpoint Circle Algorithm
# ------------------------------------------------------------------

def midpoint_circle(xc, yc, r):
    """Return unique raster points for a circle using the midpoint method."""
    x = 0
    y = r
    decision = 1 - r
    points = []
    seen = set()

    def add_octants(px, py):
        for point in (
            (xc + px, yc + py),
            (xc - px, yc + py),
            (xc + px, yc - py),
            (xc - px, yc - py),
            (xc + py, yc + px),
            (xc - py, yc + px),
            (xc + py, yc - px),
            (xc - py, yc - px),
        ):
            if point not in seen:
                seen.add(point)
                points.append(point)

    add_octants(x, y)

    while x < y:
        x += 1
        if decision < 0:
            decision += 2 * x + 1
        else:
            y -= 1
            decision += 2 * (x - y) + 1
        add_octants(x, y)

    return points


def order_by_angle(points, xc, yc):
    """Sort points around the center for a clean outline (visual only)."""
    return sorted(points, key=lambda p: math.atan2(p[1] - yc, p[0] - xc))


# ------------------------------------------------------------------
# Terminal input
# ------------------------------------------------------------------

def get_input():
    print("=" * 50)
    print(" Midpoint Circle Algorithm")
    print("=" * 50)
    xc = int(input("Center xc: "))
    yc = int(input("Center yc: "))
    while True:
        r = int(input("Radius r: "))
        if r >= 0:
            break
        print("Radius cannot be negative.")
    return xc, yc, r


# ------------------------------------------------------------------
# OpenGL plumbing
# ------------------------------------------------------------------

circle_points = []       # algorithm order (octant expansion)
outline_points = []      # angular order for outline
current_index = 0
xc_val = yc_val = r_val = 0

view_half = 300.0
center_x, center_y = 0.0, 0.0
MIN_ZOOM = 20.0
MAX_ZOOM = 2000.0
DEFAULT_VIEW_HALF = 300.0


def fit_view_to_circle(xc, yc, r):
    """Center the camera on the circle with modest padding."""
    global view_half, center_x, center_y, DEFAULT_VIEW_HALF
    center_x, center_y = float(xc), float(yc)
    padding = max(8, int(r * 0.35) + 4)
    half = float(r + padding)
    view_half = max(MIN_ZOOM, half)
    DEFAULT_VIEW_HALF = view_half


def apply_projection():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(
        center_x - view_half,
        center_x + view_half,
        center_y - view_half,
        center_y + view_half,
    )
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def zoom(factor):
    global view_half
    view_half = max(MIN_ZOOM, min(MAX_ZOOM, view_half * factor))
    print(f"[zoom] view_half = {view_half:.1f}")
    apply_projection()
    glutPostRedisplay()


def pan(dx_frac, dy_frac):
    global center_x, center_y
    step = view_half * 0.2
    center_x += dx_frac * step
    center_y += dy_frac * step
    print(f"[pan] center = ({center_x:.1f}, {center_y:.1f})")
    apply_projection()
    glutPostRedisplay()


def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_10):
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))


def grid_step():
    raw = (view_half * 2) / 10.0
    if raw <= 0:
        return 1.0
    magnitude = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 5, 10):
        step = m * magnitude
        if step >= raw:
            return step
    return raw


def draw_grid(step):
    glColor3f(0.15, 0.15, 0.15)
    x_lo, x_hi = center_x - view_half, center_x + view_half
    y_lo, y_hi = center_y - view_half, center_y + view_half
    glBegin(GL_LINES)
    v = math.ceil(x_lo / step) * step
    while v <= x_hi:
        glVertex2f(v, y_lo)
        glVertex2f(v, y_hi)
        v += step
    v = math.ceil(y_lo / step) * step
    while v <= y_hi:
        glVertex2f(x_lo, v)
        glVertex2f(x_hi, v)
        v += step
    glEnd()


def draw_axes(step):
    glColor3f(0.6, 0.6, 0.6)
    x_lo, x_hi = center_x - view_half, center_x + view_half
    y_lo, y_hi = center_y - view_half, center_y + view_half
    glBegin(GL_LINES)
    glVertex2f(x_lo, 0)
    glVertex2f(x_hi, 0)
    glVertex2f(0, y_lo)
    glVertex2f(0, y_hi)
    glEnd()

    glColor3f(0.7, 0.7, 0.7)
    label_offset = step * 0.08
    v = math.ceil(x_lo / step) * step
    while v <= x_hi:
        if v != 0:
            label = str(int(v)) if v == int(v) else f"{v:.2g}"
            draw_text(v - label_offset, -label_offset - 6, label)
        v += step
    v = math.ceil(y_lo / step) * step
    while v <= y_hi:
        if v != 0:
            label = str(int(v)) if v == int(v) else f"{v:.2g}"
            draw_text(label_offset * 0.5, v - label_offset, label)
        v += step
    draw_text(label_offset * 0.5, -label_offset - 6, "0")


def display():
    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()

    step = grid_step()
    draw_grid(step)
    draw_axes(step)

    visible = circle_points[:current_index]
    visible_set = set(visible)

    # Outline of points revealed so far (angular order)
    if len(visible) >= 2:
        partial_outline = [p for p in outline_points if p in visible_set]
        if len(partial_outline) >= 2:
            glColor3f(0.95, 0.25, 0.25)
            glLineWidth(1.5)
            glBegin(GL_LINE_LOOP)
            for x, y in partial_outline:
                glVertex2f(x, y)
            glEnd()

    # Raster points from the midpoint algorithm
    glColor3f(0.25, 0.55, 1.0)
    glPointSize(4)
    glBegin(GL_POINTS)
    for x, y in visible:
        glVertex2f(x, y)
    glEnd()

    # Radius line: center -> rightmost circumference point (xc + r, yc)
    rim_x, rim_y = xc_val + r_val, yc_val
    glColor3f(1.0, 0.85, 0.2)
    glLineWidth(2.0)
    glBegin(GL_LINES)
    glVertex2f(xc_val, yc_val)
    glVertex2f(rim_x, rim_y)
    glEnd()
    mid_x = (xc_val + rim_x) / 2.0
    mid_y = yc_val + max(0.8, view_half * 0.025)
    glColor3f(1.0, 0.9, 0.45)
    draw_text(mid_x, mid_y, f"r = {r_val}", font=GLUT_BITMAP_HELVETICA_12)

    # Center marker + label only
    glColor3f(0.2, 0.95, 0.35)
    glPointSize(7)
    glBegin(GL_POINTS)
    glVertex2f(xc_val, yc_val)
    glEnd()
    glColor3f(0.85, 0.95, 0.85)
    off = view_half * 0.03
    draw_text(
        xc_val + off,
        yc_val - off * 1.4,
        f"center ({xc_val}, {yc_val})",
        font=GLUT_BITMAP_HELVETICA_12,
    )

    glutSwapBuffers()


def timer(_value):
    global current_index
    if current_index < len(circle_points):
        # Reveal one octant-batch step visually: advance a few points per tick
        # so larger radii finish in a reasonable time.
        step = 1 if len(circle_points) <= 120 else max(1, len(circle_points) // 80)
        current_index = min(len(circle_points), current_index + step)
        glutPostRedisplay()
    glutTimerFunc(35, timer, 0)


def keyboard(key, _x, _y):
    global view_half, center_x, center_y, current_index
    if isinstance(key, bytes):
        key = key.decode("utf-8")
    if key in ("+", "="):
        zoom(0.8)
    elif key in ("-", "_"):
        zoom(1.25)
    elif key in ("r", "R"):
        view_half = DEFAULT_VIEW_HALF
        center_x, center_y = float(xc_val), float(yc_val)
        apply_projection()
        glutPostRedisplay()
    elif key in ("a", "A"):
        current_index = 0
        glutPostRedisplay()
    elif key in ("q", "Q", "\x1b"):
        glutLeaveMainLoop()


def special_keys(key, _x, _y):
    if key == GLUT_KEY_UP:
        pan(0, 1)
    elif key == GLUT_KEY_DOWN:
        pan(0, -1)
    elif key == GLUT_KEY_LEFT:
        pan(-1, 0)
    elif key == GLUT_KEY_RIGHT:
        pan(1, 0)


def mouse_wheel(_wheel, direction, _x, _y):
    zoom(0.9 if direction > 0 else 1.1)


def init():
    glClearColor(0.0, 0.0, 0.0, 1.0)
    apply_projection()


def main():
    global circle_points, outline_points, xc_val, yc_val, r_val

    xc, yc, r = get_input()
    xc_val, yc_val, r_val = xc, yc, r

    circle_points = midpoint_circle(xc, yc, r)
    outline_points = order_by_angle(circle_points, xc, yc)
    fit_view_to_circle(xc, yc, r)

    print(f"\nPlotting {len(circle_points)} unique points (r = {r})...")
    print("Midpoint circle points:")
    for x, y in circle_points:
        print(x, y)
    print(f"\nTotal points: {len(circle_points)}")
    print("\nClick the window for keyboard focus, then:")
    print("  '+' / '-'    -> zoom in / out")
    print("  Arrow keys   -> pan")
    print("  'a' -> replay animation")
    print("  'r' -> reset view, 'q' -> quit\n")

    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(WIN_W, WIN_H)
    glutCreateWindow(b"Midpoint Circle - OpenGL")
    init()
    glutDisplayFunc(display)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_keys)
    try:
        glutMouseWheelFunc(mouse_wheel)
    except Exception:
        pass
    glutTimerFunc(35, timer, 0)
    glutMainLoop()


if __name__ == "__main__":
    main()
