import glfw
import math
import time
from OpenGL.GL import *


def main():
    if not glfw.init():
        raise Exception("GLFW could not be initialized")

    width, height = 800, 600
    window = glfw.create_window(width, height, "Bouncing Triangle", None, None)

    if not window:
        glfw.terminate()
        raise Exception("GLFW window could not be created")

    glfw.make_context_current(window)

    # Position and velocity for bouncing motion (in normalized -1..1 space)
    pos_x, pos_y = 0.0, 0.0
    vel_x, vel_y = 0.6, 0.45  # units per second

    triangle_half_size = 0.15  # rough bounding radius for bounce collision

    start_time = time.time()
    last_time = start_time

    while not glfw.window_should_close(window):
        glfw.poll_events()

        now = time.time()
        dt = now - last_time
        last_time = now
        elapsed = now - start_time

        # --- Update position (bounce off the edges) ---
        pos_x += vel_x * dt
        pos_y += vel_y * dt

        if pos_x + triangle_half_size > 1.0 or pos_x - triangle_half_size < -1.0:
            vel_x *= -1
            pos_x = max(min(pos_x, 1.0 - triangle_half_size), -1.0 + triangle_half_size)

        if pos_y + triangle_half_size > 1.0 or pos_y - triangle_half_size < -1.0:
            vel_y *= -1
            pos_y = max(min(pos_y, 1.0 - triangle_half_size), -1.0 + triangle_half_size)

        # --- Clear screen ---
        glClearColor(0.08, 0.08, 0.1, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # --- Draw the triangle ---
        glPushMatrix()
        glTranslatef(pos_x, pos_y, 0.0)
        glRotatef(elapsed * 90.0, 0.0, 0.0, 1.0)  # spin 90 degrees/sec

        glBegin(GL_TRIANGLES)

        # Cycle each vertex's color over time, offset from each other
        r1 = (math.sin(elapsed * 2.0) + 1.0) / 2.0
        g1 = (math.sin(elapsed * 2.0 + 2.0) + 1.0) / 2.0
        b1 = (math.sin(elapsed * 2.0 + 4.0) + 1.0) / 2.0
        glColor3f(r1, g1, b1)
        glVertex2f(0.0, triangle_half_size)

        r2 = (math.sin(elapsed * 2.0 + 2.0) + 1.0) / 2.0
        g2 = (math.sin(elapsed * 2.0 + 4.0) + 1.0) / 2.0
        b2 = (math.sin(elapsed * 2.0) + 1.0) / 2.0
        glColor3f(r2, g2, b2)
        glVertex2f(-triangle_half_size, -triangle_half_size)

        r3 = (math.sin(elapsed * 2.0 + 4.0) + 1.0) / 2.0
        g3 = (math.sin(elapsed * 2.0) + 1.0) / 2.0
        b3 = (math.sin(elapsed * 2.0 + 2.0) + 1.0) / 2.0
        glColor3f(r3, g3, b3)
        glVertex2f(triangle_half_size, -triangle_half_size)

        glEnd()

        glPopMatrix()

        glfw.swap_buffers(window)

    glfw.terminate()


if __name__ == "__main__":
    main()