"""
Composite 2D Transformations (Homogeneous Matrices) - OpenGL
-------------------------------------------------------------
Requires: pip install PyOpenGL PyOpenGL_accelerate

Enter a shape, then chain Translation / Rotation / Scaling / Reflection.
Matrices are multiplied into one composite matrix and applied once.
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


# ------------------------------------------------------------------
# Homogeneous matrix helpers
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


def transform_points(matrix, points):
    transformed = []
    for x, y in points:
        new_x = matrix[0][0] * x + matrix[0][1] * y + matrix[0][2]
        new_y = matrix[1][0] * x + matrix[1][1] * y + matrix[1][2]
        w = matrix[2][0] * x + matrix[2][1] * y + matrix[2][2]
        transformed.append((clean(new_x / w), clean(new_y / w)))
    return transformed


def print_matrix(matrix):
    for row in matrix:
        print("  ".join(f"{clean(value):7.2f}" for value in row))


# ------------------------------------------------------------------
# Terminal input (same 4 ops as Lab 3, chainable)
# ------------------------------------------------------------------

def read_shape():
    print("=" * 50)
    print(" Composite 2D Transformations")
    print("=" * 50)
    print("Enter the shape (1 or more vertices / points).")
    count = int(input("Number of vertices: "))
    if count < 1:
        raise SystemExit("Need at least 1 point.")

    points = []
    for i in range(count):
        x = float(input(f"  x{i + 1}: "))
        y = float(input(f"  y{i + 1}: "))
        points.append((x, y))
    return points


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
        sense = 1.0
        sense_name = "CCR"
    elif direction in ("2", "cr"):
        sense = -1.0
        sense_name = "CR"
    else:
        raise SystemExit("Invalid rotation direction.")

    angle = float(input("Angle in degrees: "))
    px, py, pivot_name = read_pivot("Pivot")
    signed_angle = sense * angle

    return (
        about_point(rotation_matrix(signed_angle), px, py),
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


def read_one_transformation(index):
    print(f"\n--- Transformation #{index} ---")
    print("  1. Translation")
    print("  2. Rotation")
    print("  3. Scaling")
    print("  4. Reflection")
    choice = input("Choice: ").strip()

    if choice == "1":
        tx = float(input("tx: "))
        ty = float(input("ty: "))
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

    raise SystemExit("Invalid transformation choice.")


def read_composite_sequence():
    """
    Build composite M = Mn * ... * M2 * M1
    so the first entered transform is applied first to the shape.
    """
    print("\nHow many transformations to compose? (2 or more recommended)")
    count = int(input("Count: "))
    if count < 1:
        raise SystemExit("Need at least 1 transformation.")

    composite = identity_matrix()
    step_names = []
    step_matrices = []

    for i in range(1, count + 1):
        matrix, name = read_one_transformation(i)
        print(f"\n--- T{i} matrix ({name}) ---")
        print_matrix(matrix)

        # Left-multiply so later transforms wrap earlier ones:
        # final = Mn * ... * M1
        composite = multiply_matrices(matrix, composite)
        step_names.append(f"T{i}: {name}")
        step_matrices.append(matrix)

        print(f"\nAfter composing T{i}:  M := T{i} * M")
        print("Current composite M:")
        print_matrix(composite)

    title = " then ".join(f"T{i}" for i in range(1, count + 1))
    return composite, title, step_names, step_matrices


# ------------------------------------------------------------------
# OpenGL plumbing
# ------------------------------------------------------------------

original_points = []
transformed_points = []
transform_name = ""
step_labels = []
transform_matrix = None
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


def draw_polyline(points, r, g, b, width=2.0, dashed=False):
    if len(points) < 2:
        return
    glColor3f(r, g, b)
    glLineWidth(width)
    if dashed:
        glEnable(GL_LINE_STIPPLE)
        glLineStipple(2, 0x00FF)
    mode = GL_LINE_LOOP if len(points) > 2 else GL_LINES
    glBegin(mode)
    if len(points) == 2:
        glVertex2f(points[0][0], points[0][1])
        glVertex2f(points[1][0], points[1][1])
    else:
        for x, y in points:
            glVertex2f(x, y)
    glEnd()
    if dashed:
        glDisable(GL_LINE_STIPPLE)


def draw_vertices(points, r, g, b):
    glColor3f(r, g, b)
    glPointSize(6)
    glBegin(GL_POINTS)
    for x, y in points:
        glVertex2f(x, y)
    glEnd()

    if not show_vertex_labels:
        return

    off = view_half * 0.025
    for x, y in points:
        draw_text(x + off, y + off, f"({x:g}, {y:g})")


def format_matrix_rows(matrix):
    rows = []
    for row in matrix:
        cells = "  ".join(f"{clean(v):7.3f}" for v in row)
        rows.append(f"[ {cells} ]")
    return rows


def draw_screen_text(x, y, text, font=GLUT_BITMAP_HELVETICA_12):
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))


def draw_math_panel():
    """Fixed right-side panel: steps, composite M, and P' values."""
    if not show_math_panel or transform_matrix is None:
        return

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
    line = 16

    glColor3f(1.0, 0.9, 0.4)
    draw_screen_text(tx, ty, "CALCULATION / OUTPUT", GLUT_BITMAP_HELVETICA_18)
    ty -= line * 1.3

    glColor3f(0.5, 0.85, 1.0)
    draw_screen_text(tx, ty, "Order: M = Tn ... T2 T1", GLUT_BITMAP_HELVETICA_12)
    ty -= line
    glColor3f(0.85, 0.85, 0.85)
    draw_screen_text(tx, ty, f"Applied: {transform_name}", GLUT_BITMAP_HELVETICA_10)
    ty -= line * 1.1

    for label in step_labels[:5]:
        short = label if len(label) <= 42 else label[:39] + "..."
        glColor3f(0.75, 0.75, 0.8)
        draw_screen_text(tx, ty, short, GLUT_BITMAP_HELVETICA_10)
        ty -= line
    if len(step_labels) > 5:
        draw_screen_text(tx, ty, f"... +{len(step_labels) - 5} more (see terminal)", GLUT_BITMAP_HELVETICA_10)
        ty -= line
    ty -= line * 0.3

    glColor3f(0.5, 0.85, 1.0)
    draw_screen_text(tx, ty, "Composite matrix M:", GLUT_BITMAP_HELVETICA_12)
    ty -= line
    glColor3f(0.95, 0.95, 0.95)
    for row in format_matrix_rows(transform_matrix):
        draw_screen_text(tx, ty, row, GLUT_BITMAP_HELVETICA_12)
        ty -= line
    ty -= line * 0.3

    glColor3f(0.5, 0.85, 1.0)
    draw_screen_text(tx, ty, "P' = M * [x  y  1]^T", GLUT_BITMAP_HELVETICA_12)
    ty -= line * 1.1

    glColor3f(0.75, 0.75, 0.75)
    draw_screen_text(tx, ty, "Original  ->  Transformed", GLUT_BITMAP_HELVETICA_12)
    ty -= line

    for (x, y), (nx, ny) in zip(original_points, transformed_points):
        if ty < panel_y + 50:
            glColor3f(0.6, 0.6, 0.6)
            draw_screen_text(tx, ty, "... (see terminal for all)", GLUT_BITMAP_HELVETICA_10)
            break
        glColor3f(0.9, 0.9, 0.9)
        draw_screen_text(
            tx,
            ty,
            f"({x:g}, {y:g})  ->  ({nx:g}, {ny:g})",
            GLUT_BITMAP_HELVETICA_12,
        )
        ty -= line

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
    draw_text(x, y, f"Composite: {transform_name}", font=GLUT_BITMAP_HELVETICA_18)
    glColor3f(0.35, 0.55, 1.0)
    draw_text(x, y - step, "blue dashed = original", font=GLUT_BITMAP_HELVETICA_12)
    glColor3f(0.95, 0.3, 0.3)
    draw_text(x, y - 2 * step, "red solid = composite result", font=GLUT_BITMAP_HELVETICA_12)


def display():
    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()

    step = grid_step()
    draw_grid(step)
    draw_axes(step)

    draw_polyline(original_points, 0.35, 0.55, 1.0, width=2.0, dashed=True)
    draw_vertices(original_points, 0.35, 0.55, 1.0)

    draw_polyline(transformed_points, 0.95, 0.25, 0.25, width=2.5, dashed=False)
    draw_vertices(transformed_points, 0.95, 0.25, 0.25)

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
    global original_points, transformed_points, transform_name, step_labels, transform_matrix

    original_points = read_shape()
    matrix, transform_name, step_labels, _step_matrices = read_composite_sequence()
    transform_matrix = matrix
    transformed_points = transform_points(matrix, original_points)

    print("\n========== COMPOSITE RESULT ==========")
    print(f"Order (applied first -> last): {transform_name}")
    print("Composition rule: M = Tn * ... * T2 * T1")
    print("Each point: P' = M * [x  y  1]^T")
    for label in step_labels:
        print(f"  {label}")
    print("\nFinal composite homogeneous matrix M:")
    print_matrix(matrix)
    print("\nOriginal -> Transformed:")
    for (x, y), (nx, ny) in zip(original_points, transformed_points):
        print(f"  ({x:g}, {y:g}) -> ({nx:g}, {ny:g})")

    fit_view(original_points + transformed_points)

    print("\nClick the window for keyboard focus, then:")
    print("  '+' / '-'    -> zoom in / out")
    print("  Arrow keys   -> pan")
    print("  'l' -> toggle vertex labels")
    print("  'm' -> toggle math panel")
    print("  'r' -> reset view, 'q' -> quit\n")

    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(WIN_W, WIN_H)
    glutCreateWindow(b"Composite 2D Transformations - OpenGL")
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
