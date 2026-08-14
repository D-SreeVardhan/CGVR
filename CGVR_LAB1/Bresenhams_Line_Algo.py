"""
DDA / Bresenham Line Drawing - iterative plot
----------------------------------------------
Requires: pip install PyOpenGL PyOpenGL_accelerate

Enter the start point, end point, and choose an algorithm in the
terminal. The OpenGL window will then plot the line point-by-point.
"""

import math

from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
    GL_LINES,
    GL_LINE_STRIP,
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

WIN_W, WIN_H = 600, 600


# ------------------------------------------------------------------
# Line Drawing Algorithms (return the list of points to plot, in order)
# ------------------------------------------------------------------

def dda_line(x1, y1, x2, y2):
    points = []
    dx = x2 - x1
    dy = y2 - y1
    steps = int(max(abs(dx), abs(dy)))
    if steps == 0:
        return [(x1, y1)]
    x_inc = dx / steps
    y_inc = dy / steps
    x, y = x1, y1
    for _ in range(steps + 1):
        points.append((round(x), round(y)))
        x += x_inc
        y += y_inc
    return points


def bresenham_line(x1, y1, x2, y2):
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
    points = []
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x2 > x1 else -1
    sy = 1 if y2 > y1 else -1
    x, y = x1, y1

    if dx > dy:
        err = dx / 2.0
        while x != x2:
            points.append((x, y))
            err -= dy
            if err < 0:
                y += sy
                err += dx
            x += sx
    else:
        err = dy / 2.0
        while y != y2:
            points.append((x, y))
            err -= dx
            if err < 0:
                x += sx
                err += dy
            y += sy
    points.append((x2, y2))
    return points


# ------------------------------------------------------------------
# Terminal input
# ------------------------------------------------------------------

def get_input():
    print("=" * 50)
    print(" DDA / Bresenham Line Drawing")
    print("=" * 50)
    x1 = int(input("Start X: "))
    y1 = int(input("Start Y: "))
    x2 = int(input("End X: "))
    y2 = int(input("End Y: "))

    while True:
        algo = input("Algorithm - (a)DDA or (b)resenham [Bresenham]: ").strip().lower()
        if algo in ('a', 'dda'):
            algo = 'dda'
            break
        elif algo in ('b', 'bresenham'):
            algo = 'bresenham'
            break
        print("Please enter 'a' or 'b'.")

    return x1, y1, x2, y2, algo


# ------------------------------------------------------------------
# OpenGL plumbing
# ------------------------------------------------------------------

line_points = []   # full list of points to plot
current_index = 0  # how many points have been drawn so far
show_labels = True


# --- zoom / pan state ---
view_half = 300.0   # current half-width/height of the view volume
center_x, center_y = 0.0, 0.0   # current view center (for panning)
MIN_ZOOM = 20.0
MAX_ZOOM = 2000.0


def apply_projection():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(center_x - view_half, center_x + view_half,
               center_y - view_half, center_y + view_half)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def zoom(factor):
    global view_half
    view_half = max(MIN_ZOOM, min(MAX_ZOOM, view_half * factor))
    print(f"[zoom] view_half = {view_half:.1f}")
    apply_projection()
    glutPostRedisplay()


def pan(dx_frac, dy_frac):
    """Move the view center by a fraction of the current view size."""
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
    """Pick a 'nice' grid spacing (1/2/5 x10^n) so ~10 lines fit the view."""
    raw = (view_half * 2) / 10.0
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
        glVertex2f(v, y_lo); glVertex2f(v, y_hi)
        v += step
    v = math.ceil(y_lo / step) * step
    while v <= y_hi:
        glVertex2f(x_lo, v); glVertex2f(x_hi, v)
        v += step
    glEnd()


def draw_axes(step):
    glColor3f(0.6, 0.6, 0.6)
    x_lo, x_hi = center_x - view_half, center_x + view_half
    y_lo, y_hi = center_y - view_half, center_y + view_half
    glBegin(GL_LINES)
    glVertex2f(x_lo, 0); glVertex2f(x_hi, 0)
    glVertex2f(0, y_lo); glVertex2f(0, y_hi)
    glEnd()

    # tick labels
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


def draw_point_labels():
    n = len(line_points)
    if n == 0:
        return

    # Offsets scale with zoom level so labels stay close to their point
    off = view_half * 0.02
    start_off = view_half * 0.06

    # Avoid clutter on long lines - label every point if few, else thin them out
    label_every = 1 if n <= 30 else max(1, n // 30)

    glColor3f(1.0, 1.0, 0.4)
    for i, (x, y) in enumerate(line_points[:current_index]):
        if i == 0 or i == n - 1 or i % label_every == 0:
            draw_text(x + off, y + off, f"({x},{y})", font=GLUT_BITMAP_HELVETICA_10)

    # Always make sure start/end are clearly labeled once reached
    sx, sy = line_points[0]
    if current_index >= 1:
        glColor3f(1.0, 0.6, 0.2)
        draw_text(sx + off, sy - start_off, "start")
    if current_index >= n:
        ex, ey = line_points[-1]
        glColor3f(1.0, 0.6, 0.2)
        draw_text(ex + off, ey - start_off, "end")


def display():
    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()

    step = grid_step()
    draw_grid(step)
    draw_axes(step)

    # the line drawn so far, connected so it reads as a proper line/graph
    glColor3f(0.2, 0.6, 1.0)
    glLineWidth(1.0)
    glBegin(GL_LINE_STRIP)
    for (x, y) in line_points[:current_index]:
        glVertex2f(x, y)
    glEnd()

    # highlight each plotted pixel as a point on top
    glColor3f(0.0, 1.0, 0.3)
    glPointSize(3)
    glBegin(GL_POINTS)
    for (x, y) in line_points[:current_index]:
        glVertex2f(x, y)
    glEnd()

    if show_labels:
        draw_point_labels()

    glutSwapBuffers()


def timer(_value):
    global current_index
    if current_index < len(line_points):
        current_index += 1
        glutPostRedisplay()
    glutTimerFunc(30, timer, 0)


def keyboard(key, _x, _y):
    if isinstance(key, bytes):
        key = key.decode('utf-8')
    if key in ('+', '='):
        zoom(0.8)          # zoom in
    elif key in ('-', '_'):
        zoom(1.25)         # zoom out
    elif key in ('r', 'R'):
        global view_half, center_x, center_y
        view_half = 300.0
        center_x, center_y = 0.0, 0.0
        apply_projection()
        glutPostRedisplay()
    elif key in ('q', 'Q'):
        glutLeaveMainLoop()
    elif key in ('l', 'L'):
        global show_labels
        show_labels = not show_labels
        glutPostRedisplay()


def special_keys(key, _x, _y):
    # Arrow keys pan the view around after zooming in
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
    global line_points

    x1, y1, x2, y2, algo = get_input()

    if algo == 'dda':
        line_points = dda_line(x1, y1, x2, y2)
    else:
        line_points = bresenham_line(x1, y1, x2, y2)

    print(f"\nPlotting {len(line_points)} points using {algo.upper()}...")
    print("Click inside the window first to give it keyboard focus, then:")
    print("  '+' / '-'    -> zoom in / out")
    print("  Arrow keys   -> pan around")
    print("  'r' -> reset view, 'l' -> toggle labels, 'q' -> quit\n")

    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(WIN_W, WIN_H)
    glutCreateWindow(b"Line Drawing")
    init()
    glutDisplayFunc(display)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_keys)
    try:
        glutMouseWheelFunc(mouse_wheel)  # freeglut only; ignored if unsupported
    except Exception:
        pass
    glutTimerFunc(30, timer, 0)
    glutMainLoop()


if __name__ == "__main__":
    main()
