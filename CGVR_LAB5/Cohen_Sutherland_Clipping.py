"""
Cohen–Sutherland Line Clipping Algorithm - OpenGL
-------------------------------------------------
Requires: pip install PyOpenGL PyOpenGL_accelerate

Enter a clip window and a line. The program computes region outcodes,
clips with Cohen–Sutherland, and shows original vs clipped segment.
"""

import math

from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
    GL_LINE_LOOP,
    GL_LINE_STIPPLE,
    GL_LINES,
    GL_MODELVIEW,
    GL_POINTS,
    GL_PROJECTION,
    GL_QUADS,
    glBegin,
    glClear,
    glClearColor,
    glColor3f,
    glColor4f,
    glDisable,
    glEnable,
    glEnd,
    glLineStipple,
    glLineWidth,
    glLoadIdentity,
    glMatrixMode,
    glPointSize,
    glPopMatrix,
    glPushMatrix,
    glRasterPos2f,
    glVertex2f,
)
from OpenGL.GLU import gluOrtho2D
from OpenGL.GLUT import (
    GLUT_BITMAP_HELVETICA_10,
    GLUT_BITMAP_HELVETICA_12,
    GLUT_BITMAP_HELVETICA_18,
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
)

WIN_W, WIN_H = 1100, 700

# Region-code bit masks (TBRL)
INSIDE = 0  # 0000
LEFT = 1    # 0001
RIGHT = 2   # 0010
BOTTOM = 4  # 0100
TOP = 8     # 1000


# ------------------------------------------------------------------
# Cohen–Sutherland algorithm
# ------------------------------------------------------------------

def compute_outcode(x, y, xmin, ymin, xmax, ymax):
    code = INSIDE
    if x < xmin:
        code |= LEFT
    elif x > xmax:
        code |= RIGHT
    if y < ymin:
        code |= BOTTOM
    elif y > ymax:
        code |= TOP
    return code


def outcode_bits(code):
    """Return 4-bit string TBRL and human-readable region labels."""
    bits = f"{(code >> 3) & 1}{(code >> 2) & 1}{(code >> 1) & 1}{code & 1}"
    labels = []
    if code == INSIDE:
        labels.append("INSIDE")
    else:
        if code & TOP:
            labels.append("TOP")
        if code & BOTTOM:
            labels.append("BOTTOM")
        if code & RIGHT:
            labels.append("RIGHT")
        if code & LEFT:
            labels.append("LEFT")
    return bits, "+".join(labels)


def clean(value):
    if abs(value) < 1e-9:
        return 0.0
    return round(value, 6)


def cohen_sutherland_clip(x1, y1, x2, y2, xmin, ymin, xmax, ymax):
    """
    Clip line (x1,y1)-(x2,y2) to the window.
    Returns (cx1, cy1, cx2, cy2, status) where status is
    'accept', 'reject', or 'clipped'.
    """
    code1 = compute_outcode(x1, y1, xmin, ymin, xmax, ymax)
    code2 = compute_outcode(x2, y2, xmin, ymin, xmax, ymax)
    ox1, oy1, ox2, oy2 = x1, y1, x2, y2
    accept = False

    while True:
        if code1 == 0 and code2 == 0:
            accept = True
            break
        if code1 & code2:
            break

        code_out = code1 if code1 != 0 else code2
        x, y = 0.0, 0.0

        if code_out & TOP:
            x = x1 + (x2 - x1) * (ymax - y1) / (y2 - y1)
            y = ymax
        elif code_out & BOTTOM:
            x = x1 + (x2 - x1) * (ymin - y1) / (y2 - y1)
            y = ymin
        elif code_out & RIGHT:
            y = y1 + (y2 - y1) * (xmax - x1) / (x2 - x1)
            x = xmax
        elif code_out & LEFT:
            y = y1 + (y2 - y1) * (xmin - x1) / (x2 - x1)
            x = xmin

        if code_out == code1:
            x1, y1 = x, y
            code1 = compute_outcode(x1, y1, xmin, ymin, xmax, ymax)
        else:
            x2, y2 = x, y
            code2 = compute_outcode(x2, y2, xmin, ymin, xmax, ymax)

    if not accept:
        return None, "reject"

    cx1, cy1 = clean(x1), clean(y1)
    cx2, cy2 = clean(x2), clean(y2)
    same = (
        abs(cx1 - clean(ox1)) < 1e-9
        and abs(cy1 - clean(oy1)) < 1e-9
        and abs(cx2 - clean(ox2)) < 1e-9
        and abs(cy2 - clean(oy2)) < 1e-9
    )
    status = "accept" if same else "clipped"
    return (cx1, cy1, cx2, cy2), status


# ------------------------------------------------------------------
# Terminal input
# ------------------------------------------------------------------

def read_input():
    print("=" * 50)
    print(" Cohen–Sutherland Line Clipping")
    print("=" * 50)

    print("\nClip window (axis-aligned rectangle)")
    xmin = float(input("  xmin: "))
    ymin = float(input("  ymin: "))
    xmax = float(input("  xmax: "))
    ymax = float(input("  ymax: "))
    if xmin >= xmax or ymin >= ymax:
        raise SystemExit("Need xmin < xmax and ymin < ymax.")

    print("\nLine endpoints")
    x1 = float(input("  x1: "))
    y1 = float(input("  y1: "))
    x2 = float(input("  x2: "))
    y2 = float(input("  y2: "))

    return xmin, ymin, xmax, ymax, x1, y1, x2, y2


# ------------------------------------------------------------------
# OpenGL plumbing
# ------------------------------------------------------------------

clip_window = (0.0, 0.0, 0.0, 0.0)  # xmin, ymin, xmax, ymax
line_original = (0.0, 0.0, 0.0, 0.0)
line_clipped = None  # (cx1, cy1, cx2, cy2) or None
clip_status = "reject"
code1_info = ("0000", "INSIDE")
code2_info = ("0000", "INSIDE")
show_vertex_labels = True
show_math_panel = True

view_half = 300.0
center_x, center_y = 0.0, 0.0
MIN_ZOOM = 20.0
MAX_ZOOM = 2000.0
DEFAULT_VIEW_HALF = 300.0
DEFAULT_CENTER = (0.0, 0.0)


def fit_view(points):
    global view_half, center_x, center_y, DEFAULT_VIEW_HALF, DEFAULT_CENTER
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span = max(max_x - min_x, max_y - min_y, 4.0)
    padding = span * 0.35 + 2.0
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0
    view_half = max(MIN_ZOOM, span / 2.0 + padding)
    DEFAULT_VIEW_HALF = view_half
    DEFAULT_CENTER = (center_x, center_y)


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


def draw_clip_window():
    xmin, ymin, xmax, ymax = clip_window
    glColor3f(0.2, 0.85, 0.35)
    glLineWidth(2.0)
    glBegin(GL_LINE_LOOP)
    glVertex2f(xmin, ymin)
    glVertex2f(xmax, ymin)
    glVertex2f(xmax, ymax)
    glVertex2f(xmin, ymax)
    glEnd()
    off = view_half * 0.02
    glColor3f(0.45, 0.95, 0.55)
    draw_text(xmin + off, ymax + off, "clip window", GLUT_BITMAP_HELVETICA_12)


def draw_line_segment(x1, y1, x2, y2, r, g, b, width=2.0, dashed=False):
    glColor3f(r, g, b)
    glLineWidth(width)
    if dashed:
        glEnable(GL_LINE_STIPPLE)
        glLineStipple(2, 0x00FF)
    glBegin(GL_LINES)
    glVertex2f(x1, y1)
    glVertex2f(x2, y2)
    glEnd()
    if dashed:
        glDisable(GL_LINE_STIPPLE)

    glPointSize(6)
    glBegin(GL_POINTS)
    glVertex2f(x1, y1)
    glVertex2f(x2, y2)
    glEnd()

    if show_vertex_labels:
        off = view_half * 0.025
        draw_text(x1 + off, y1 + off, f"({clean(x1):g}, {clean(y1):g})")
        draw_text(x2 + off, y2 + off, f"({clean(x2):g}, {clean(y2):g})")


def draw_screen_text(x, y, text, font=GLUT_BITMAP_HELVETICA_12):
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))


def draw_math_panel():
    if not show_math_panel:
        return

    xmin, ymin, xmax, ymax = clip_window
    x1, y1, x2, y2 = line_original

    panel_x = WIN_W - 380
    panel_w = 370
    panel_y = 20
    panel_h = WIN_H - 40

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glColor4f(0.08, 0.08, 0.1, 1.0)
    glBegin(GL_QUADS)
    glVertex2f(panel_x, panel_y)
    glVertex2f(panel_x + panel_w, panel_y)
    glVertex2f(panel_x + panel_w, panel_y + panel_h)
    glVertex2f(panel_x, panel_y + panel_h)
    glEnd()

    glColor3f(0.45, 0.45, 0.5)
    glBegin(GL_LINES)
    glVertex2f(panel_x, panel_y)
    glVertex2f(panel_x, panel_y + panel_h)
    glEnd()

    tx = panel_x + 12
    ty = panel_y + panel_h - 26
    line = 17

    glColor3f(1.0, 0.9, 0.4)
    draw_screen_text(tx, ty, "CALCULATION / OUTPUT", GLUT_BITMAP_HELVETICA_18)
    ty -= line * 1.4

    glColor3f(0.5, 0.85, 1.0)
    draw_screen_text(tx, ty, "Cohen-Sutherland", GLUT_BITMAP_HELVETICA_12)
    ty -= line
    glColor3f(0.85, 0.85, 0.85)
    draw_screen_text(tx, ty, "Outcodes: TBRL (Top Bottom Right Left)", GLUT_BITMAP_HELVETICA_10)
    ty -= line * 1.2

    glColor3f(0.5, 0.85, 1.0)
    draw_screen_text(tx, ty, "Clip window:", GLUT_BITMAP_HELVETICA_12)
    ty -= line
    glColor3f(0.9, 0.9, 0.9)
    draw_screen_text(
        tx, ty,
        f"[{xmin:g}, {xmax:g}] x [{ymin:g}, {ymax:g}]",
        GLUT_BITMAP_HELVETICA_12,
    )
    ty -= line * 1.2

    glColor3f(0.5, 0.85, 1.0)
    draw_screen_text(tx, ty, "Region outcodes:", GLUT_BITMAP_HELVETICA_12)
    ty -= line
    glColor3f(0.35, 0.55, 1.0)
    b1, l1 = code1_info
    draw_screen_text(tx, ty, f"P1 ({x1:g},{y1:g}): {b1}  {l1}", GLUT_BITMAP_HELVETICA_12)
    ty -= line
    b2, l2 = code2_info
    draw_screen_text(tx, ty, f"P2 ({x2:g},{y2:g}): {b2}  {l2}", GLUT_BITMAP_HELVETICA_12)
    ty -= line * 1.2

    glColor3f(0.5, 0.85, 1.0)
    draw_screen_text(tx, ty, "Result:", GLUT_BITMAP_HELVETICA_12)
    ty -= line
    if clip_status == "accept":
        glColor3f(0.3, 0.95, 0.4)
        draw_screen_text(tx, ty, "TRIVIAL ACCEPT (fully inside)", GLUT_BITMAP_HELVETICA_12)
    elif clip_status == "reject":
        glColor3f(0.95, 0.35, 0.35)
        draw_screen_text(tx, ty, "TRIVIAL REJECT (fully outside)", GLUT_BITMAP_HELVETICA_12)
    else:
        glColor3f(1.0, 0.85, 0.3)
        draw_screen_text(tx, ty, "CLIPPED (partially visible)", GLUT_BITMAP_HELVETICA_12)
    ty -= line * 1.2

    glColor3f(0.5, 0.85, 1.0)
    draw_screen_text(tx, ty, "Original  ->  Clipped", GLUT_BITMAP_HELVETICA_12)
    ty -= line
    glColor3f(0.9, 0.9, 0.9)
    draw_screen_text(tx, ty, f"({x1:g}, {y1:g}) -- ({x2:g}, {y2:g})", GLUT_BITMAP_HELVETICA_12)
    ty -= line
    if line_clipped is None:
        glColor3f(0.95, 0.4, 0.4)
        draw_screen_text(tx, ty, "-> (discarded)", GLUT_BITMAP_HELVETICA_12)
    else:
        cx1, cy1, cx2, cy2 = line_clipped
        glColor3f(0.95, 0.35, 0.35)
        draw_screen_text(
            tx, ty,
            f"-> ({cx1:g}, {cy1:g}) -- ({cx2:g}, {cy2:g})",
            GLUT_BITMAP_HELVETICA_12,
        )

    ty = panel_y + 28
    glColor3f(0.55, 0.55, 0.55)
    draw_screen_text(tx, ty, "m: toggle math panel", GLUT_BITMAP_HELVETICA_10)

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_hud():
    x = center_x - view_half * 0.92
    y = center_y + view_half * 0.88
    step = view_half * 0.055

    glColor3f(0.95, 0.95, 0.95)
    draw_text(x, y, "Cohen-Sutherland Line Clipping", GLUT_BITMAP_HELVETICA_18)
    glColor3f(0.2, 0.85, 0.35)
    draw_text(x, y - step, "green = clip window", GLUT_BITMAP_HELVETICA_12)
    glColor3f(0.35, 0.55, 1.0)
    draw_text(x, y - 2 * step, "blue dashed = original line", GLUT_BITMAP_HELVETICA_12)
    glColor3f(0.95, 0.3, 0.3)
    draw_text(x, y - 3 * step, "red solid = clipped segment", GLUT_BITMAP_HELVETICA_12)


def display():
    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()

    step = grid_step()
    draw_grid(step)
    draw_axes(step)
    draw_clip_window()

    x1, y1, x2, y2 = line_original
    draw_line_segment(x1, y1, x2, y2, 0.35, 0.55, 1.0, width=2.0, dashed=True)

    if line_clipped is not None:
        cx1, cy1, cx2, cy2 = line_clipped
        draw_line_segment(cx1, cy1, cx2, cy2, 0.95, 0.25, 0.25, width=2.5, dashed=False)

    draw_hud()
    draw_math_panel()
    glutSwapBuffers()


def keyboard(key, _x, _y):
    global view_half, center_x, center_y, show_vertex_labels, show_math_panel
    if isinstance(key, bytes):
        key = key.decode("utf-8")
    if key in ("+", "="):
        zoom(0.8)
    elif key in ("-", "_"):
        zoom(1.25)
    elif key in ("r", "R"):
        view_half = DEFAULT_VIEW_HALF
        center_x, center_y = DEFAULT_CENTER
        apply_projection()
        glutPostRedisplay()
    elif key in ("l", "L"):
        show_vertex_labels = not show_vertex_labels
        glutPostRedisplay()
    elif key in ("m", "M"):
        show_math_panel = not show_math_panel
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
    global clip_window, line_original, line_clipped, clip_status, code1_info, code2_info

    xmin, ymin, xmax, ymax, x1, y1, x2, y2 = read_input()
    clip_window = (xmin, ymin, xmax, ymax)
    line_original = (x1, y1, x2, y2)

    c1 = compute_outcode(x1, y1, xmin, ymin, xmax, ymax)
    c2 = compute_outcode(x2, y2, xmin, ymin, xmax, ymax)
    code1_info = outcode_bits(c1)
    code2_info = outcode_bits(c2)

    clipped, clip_status = cohen_sutherland_clip(x1, y1, x2, y2, xmin, ymin, xmax, ymax)
    line_clipped = clipped

    print("\n========== CLIP RESULT ==========")
    print(f"Window: xmin={xmin:g}, ymin={ymin:g}, xmax={xmax:g}, ymax={ymax:g}")
    print(f"Line:   ({x1:g}, {y1:g}) -- ({x2:g}, {y2:g})")
    print(f"Outcode P1: {code1_info[0]} ({code1_info[1]})")
    print(f"Outcode P2: {code2_info[0]} ({code2_info[1]})")
    print(f"Status: {clip_status.upper()}")
    if clipped is None:
        print("Clipped: (discarded — fully outside)")
    else:
        cx1, cy1, cx2, cy2 = clipped
        print(f"Clipped: ({cx1:g}, {cy1:g}) -- ({cx2:g}, {cy2:g})")

    points = [(xmin, ymin), (xmax, ymax), (x1, y1), (x2, y2)]
    if clipped is not None:
        points.extend([(clipped[0], clipped[1]), (clipped[2], clipped[3])])
    fit_view(points)

    print("\nClick the window for keyboard focus, then:")
    print("  '+' / '-'    -> zoom in / out")
    print("  Arrow keys   -> pan")
    print("  'l' -> toggle endpoint labels")
    print("  'm' -> toggle math panel")
    print("  'r' -> reset view, 'q' -> quit\n")

    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(WIN_W, WIN_H)
    glutCreateWindow(b"Cohen-Sutherland Line Clipping - OpenGL")
    init()
    glutDisplayFunc(display)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_keys)
    try:
        glutMouseWheelFunc(mouse_wheel)
    except Exception:
        pass
    glutMainLoop()


if __name__ == "__main__":
    main()
