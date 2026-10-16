# CGVR Lab 9

## Simple Interactive 3D Scene — Unity

Creates a runtime 3D scene with four coloured primitive objects, FPS camera movement, and full object interaction (translate / rotate / scale).

---

## Unity Setup (one-time, ~5 minutes)

### Step 1 — Install Unity Editor

1. Open **Unity Hub**
2. Click **Installs** → **Install Editor**
3. Choose **Unity 6** (6000.x LTS) — tested and working
4. Check **Mac Build Support** only — uncheck everything else
5. Click **Install** and wait

### Step 2 — Create a New Project

1. Unity Hub → **Projects** → **New project**
2. Template: **Universal 3D** (URP) — the script is pipeline-agnostic
3. Give it any name (e.g. `CGVR_Lab9`) and choose a location
4. Click **Create project**

### Step 3 — Fix Input Handling (Unity 6 only)

Unity 6 URP projects default to the new Input System. The script uses the classic `Input` class, so:

1. **Edit → Project Settings → Player → Other Settings**
2. Set **Active Input Handling → Both**
3. Unity will restart — click **Apply**

### Step 4 — Add the Script

1. In the **Project** panel: right-click `Assets` → **Create → C# Script**
2. Name it exactly `Lab9Controller` (no spaces, capital L and C)
3. Open the file and **replace all contents** with `Lab9Controller.cs`
4. Save (`⌘ S`)

### Step 5 — Attach to Camera

1. In the **Hierarchy**: click **Main Camera**
2. **Inspector → Add Component** → search `Lab9Controller` → add it
3. Press **▶ Play**

The scene builds itself at runtime — no manual GameObject setup needed.

---

## Scene Contents (created at runtime)

| Object | Shape | Colour |
|--------|-------|--------|
| Floor | Plane (30×30) | Dark grey |
| Cube | Box | Red |
| Sphere | Sphere | Blue |
| Capsule | Capsule | Green |
| Cylinder | Cylinder | Yellow |
| Sun | Directional light | Warm white |

---

## Controls

### Camera Mode (default — green HUD)

| Key | Action |
|-----|--------|
| `WASD` | Move forward / back / strafe |
| Mouse | Look around |
| `Q` / `E` | Move down / up |
| `Left Shift` | Sprint |
| `Tab` | Switch to Interact mode |

### Interact Mode (amber HUD)

| Key | Action |
|-----|--------|
| **Left-click** | Select object (turns amber) |
| Arrow keys | Translate X / Z |
| `PgUp` / `PgDn` | Translate Y (up / down) |
| `I` / `K` | Rotate pitch |
| `J` / `L` | Rotate yaw |
| `+` / `-` | Scale up / down |
| `Backspace` | Deselect |
| `Tab` | Switch back to Camera mode |

The HUD shows the selected object's live **Position**, **Rotation**, and **Scale** values.

---

## Output

| File | Description |
|------|-------------|
| `Lab9_CameraMode.png` | Camera mode — first-person view of all objects |
| `Lab9_InteractMode.png` | Walking closer to the scene |
| `Lab9_ObjectSelected.png` | Object selected with amber highlight |
| `Lab9_Overview.png` | Wide overview of the full scene |
| `Screen Recording 2026-10-16 at 4.43.33 PM.mov` | Full gameplay demo video |

---

## Files

| File | Description |
|------|-------------|
| `Lab9Controller.cs` | All-in-one Unity C# script (scene + camera + interaction) |
| `README.md` | Setup guide and controls |
| `output/` | Screenshots and demo recording |
