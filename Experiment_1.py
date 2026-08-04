"""
Experiment 1: Bresenham's Line Drawing Algorithm and Bresenham's (Midpoint)
Circle Algorithm using Python OpenGL (PyOpenGL + GLUT)

The rendered frame is automatically saved once at startup as a PNG image:
    output/exp1_bresenham_line_circle.png

Requirements:
    pip install PyOpenGL PyOpenGL_accelerate Pillow

Run:
    python Experiment_1.py
    python Experiment_1.py --output custom/screenshot.png

Controls (while the window is focused):
    s  -> save a PNG snapshot of the current frame
    q  -> quit
    Esc -> quit
"""

import argparse
import os

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from PIL import Image

# Default output path for the rendered snapshot
DEFAULT_OUTPUT = os.path.join("output", "exp1_bresenham_line_circle.png")

# Window / framebuffer size (matches gluOrtho2D(0, 500, 0, 500))
WINDOW_WIDTH = 500
WINDOW_HEIGHT = 500


# ---------------------------------------------------------
# Setup
# ---------------------------------------------------------
def init():
    glClearColor(1.0, 1.0, 1.0, 1.0)   # white background
    glColor3f(0.0, 0.0, 0.0)           # black drawing color
    glPointSize(2)                     # pixel size (make points visible)
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)   # 2D coordinate system


def plot_point(x, y):
    glBegin(GL_POINTS)
    glVertex2i(int(x), int(y))
    glEnd()


# ---------------------------------------------------------
# Bresenham's Line Drawing Algorithm
# ---------------------------------------------------------
def bresenham_line(x1, y1, x2, y2):
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)

    sx = 1 if x2 > x1 else -1   # step direction for x
    sy = 1 if y2 > y1 else -1   # step direction for y

    x, y = x1, y1

    if dx > dy:
        # slope <= 1: step along x
        p = 2 * dy - dx
        for _ in range(dx + 1):
            plot_point(x, y)
            x += sx
            if p >= 0:
                y += sy
                p -= 2 * dx
            p += 2 * dy
    else:
        # slope > 1: step along y
        p = 2 * dx - dy
        for _ in range(dy + 1):
            plot_point(x, y)
            y += sy
            if p >= 0:
                x += sx
                p -= 2 * dy
            p += 2 * dx


# ---------------------------------------------------------
# Bresenham's (Midpoint) Circle Drawing Algorithm
# ---------------------------------------------------------
def plot_circle_points(xc, yc, x, y):
    # plot all 8 symmetric points of the circle
    glBegin(GL_POINTS)
    glVertex2i(xc + x, yc + y)
    glVertex2i(xc - x, yc + y)
    glVertex2i(xc + x, yc - y)
    glVertex2i(xc - x, yc - y)
    glVertex2i(xc + y, yc + x)
    glVertex2i(xc - y, yc + x)
    glVertex2i(xc + y, yc - x)
    glVertex2i(xc - y, yc - x)
    glEnd()


def bresenham_circle(xc, yc, r):
    x = 0
    y = r
    d = 3 - 2 * r   # initial decision parameter

    plot_circle_points(xc, yc, x, y)

    while x < y:
        if d < 0:
            d += 4 * x + 6
        else:
            d += 4 * (x - y) + 10
            y -= 1
        x += 1
        plot_circle_points(xc, yc, x, y)


# ---------------------------------------------------------
# Frame capture -> PNG
# ---------------------------------------------------------
def save_screenshot(filepath):
    """
    Read the rendered framebuffer and write it as a PNG file.

    OpenGL's pixel origin is the bottom-left corner, while PNG images
    count rows from the top, so the buffer is flipped vertically.
    """
    # Read the RGBA framebuffer (single buffer: GLUT_SINGLE | GLUT_RGB)
    glPixelStorei(GL_PACK_ALIGNMENT, 1)
    buffer = glReadPixels(
        0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, GL_RGBA, GL_UNSIGNED_BYTE
    )

    # Convert the raw bytes into a PIL image and flip it vertically
    image = Image.frombytes(
        "RGBA", (WINDOW_WIDTH, WINDOW_HEIGHT), buffer, "raw", "RGBA", 0, -1
    )
    # Convert to RGB for a compact PNG (background is plain white anyway)
    image = image.convert("RGB")

    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    image.save(filepath, "PNG")
    print(f"[saved] {filepath}")


# ---------------------------------------------------------
# Display callback
# ---------------------------------------------------------
def display():
    glClear(GL_COLOR_BUFFER_BIT)
    glColor3f(0.0, 0.0, 0.0)

    # Example: draw a line from (50,50) to (400,300)
    bresenham_line(50, 50, 400, 300)

    # Example: draw a circle centered at (250,250) with radius 100
    bresenham_circle(250, 250, 100)

    glFlush()


# ---------------------------------------------------------
# Keyboard callback
# ---------------------------------------------------------
def keyboard(key, x, y):
    if key == b"s":          # save screenshot
        save_screenshot(OUTPUT_PATH)
    elif key in (b"q", b"\x1b"):   # q or Esc -> quit
        glutLeaveMainLoop()


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Bresenham Line and Circle - saves a PNG snapshot"
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"PNG output path (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()

    global OUTPUT_PATH
    OUTPUT_PATH = args.output

    glutInit()
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Experiment 1: Bresenham Line and Circle - OpenGL")
    init()
    glutDisplayFunc(display)
    glutKeyboardFunc(keyboard)
    display()                    # render the frame once
    save_screenshot(OUTPUT_PATH)           # auto-export the frame as PNG
    glutMainLoop()


if __name__ == "__main__":
    main()
