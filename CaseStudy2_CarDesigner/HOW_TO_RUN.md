# Atelier Car Designer — How to Run

CS4104 Case Study 2 · Industrial Design & Architecture  
Desu Sree Vardhan · 1RUA24CSE7004 · Section C

This folder is a complete Unity project. Unzip it, add it to Unity Hub, and press Play. You do **not** need the original author’s `Library` folder — Unity rebuilds that on first open.

---

## What you need

| Requirement | Details |
|---|---|
| **Unity Hub** | [Download](https://unity.com/download) |
| **Unity Editor** | **6000.6.6f1** (Unity 6) — this is the version the project was built with |
| **Modules** | Windows / macOS Build Support (whichever OS you are on). URP is already in `Packages/` |
| **Disk** | ~2 GB free for the first import (Unity generates a local `Library/` folder) |
| **OS** | macOS, Windows, or Linux |

If 6000.6.6f1 is not listed, open Unity Hub → **Installs → Install Editor → Archive**, or install any nearby Unity 6 release (6000.0 / 6000.2 / 6000.3) and let Hub upgrade the project when prompted.

---

## Open and play (5 minutes)

1. Unzip `CaseStudy2_AtelierCarDesigner.zip`. You should see a folder containing `Assets`, `Packages`, `ProjectSettings`, and this file.
2. Open **Unity Hub → Projects → Add → Add project from disk**.
3. Select the unzipped folder (the one that contains `Assets`).
4. Click the project. First open takes a few minutes while Unity imports meshes, shaders, and packages. Wait until the progress bar finishes — do **not** enter Safe Mode if a warning appears; click **Ignore** and let the import complete.
5. In the Project window open  
   `Assets / CarDesigner / Scenes / CarStudio`
6. Double-click `CarStudio` so it is the open scene.
7. Press the **Play** button (▶) at the top of the Editor.

The studio UI is built at runtime. If the Game view looks empty, click the **Game** tab (not Scene) and set the scale slider to **1x**.

---

## Controls

| Input | Action |
|---|---|
| Left-drag | Orbit camera |
| Right-drag / middle-drag | Pan |
| Scroll wheel | Zoom |
| Click a part on the car, or pick it from the left list | Select that component |
| Double-click a part | Frame the camera on it |
| Inspector sliders | Translate (mm), rotate (°), scale |
| **CASE PRESET** | Scale 1.5 · Rotate 45° · Translate +50 mm (the assignment transform) |
| Finish swatches | Recolour the body |
| OPEN DOORS / EXPLODED VIEW / FRAME / RESET ALL | Bottom bar |
| SPORTS COUPE button (if shown) | Switch the active prototype |

---

## Folder map

```
CaseStudy2_AtelierCarDesigner/
├── HOW_TO_RUN.md              ← this file
├── CaseStudy2_Report.docx     ← case-study write-up (paste-ready)
├── Assets/                    ← scene, models, scripts, URP settings
│   └── CarDesigner/
│       ├── Scenes/CarStudio.unity
│       ├── Models/            ← FBX car meshes + textures
│       └── Scripts/           ← C# (CarPart, CarRig, DesignerUI, …)
├── Packages/                  ← URP, Input System (resolved by Unity)
├── ProjectSettings/           ← editor version, quality, input, build scene
└── output/                    ← reference screenshots
```

Do not delete `.meta` files. Unity uses them to keep scene references intact.

---

## Use a different car (same scripts)

The C# does **not** bake in one mesh. Any FBX with separate body / wheel / door meshes can drive `CarRig` + `CarPart` + `DesignerUI`. Each teammate can demo a different car.

### Free models to download (pick one)

| Car | Download | Why it works |
|---|---|---|
| **Kenney Car Kit** (sedan, hatchback, taxi, police, truck…) | [kenney.nl/assets/car-kit](https://kenney.nl/assets/car-kit) · CC0 · FBX | 40+ vehicles, **wheels are separate files** — easiest swap. Each person picks a different vehicle from the same zip. |
| **Free Low Poly Car** (Unity Asset Store) | [assetstore.unity.com — Free Low Poly Car](https://assetstore.unity.com/packages/3d/vehicles/land/free-low-poly-car-329692) · free · FBX | URP-ready, separated wheels, body / glass / lights as their own materials. |
| **Kay Lousberg Hatchback** | [poly.pizza/m/BG0KAhmGDt](https://poly.pizza/m/BG0KAhmGDt) · CC0 · FBX | Single hatchback, clean hierarchy, good if you want one extra daily-driver look. |

Prefer models whose **wheels, body, and doors are separate meshes**. A single welded mesh still runs, but you cannot select a rim or apply the CASE PRESET to one wheel.

### Wire it up (do not copy or rewrite scripts)

1. Drop the `.fbx` into `Assets/CarDesigner/Models/`. In the Inspector: **Scale Factor = 1**, uncheck **Use File Scale**, Apply.
2. Drag the FBX into the `CarStudio` scene. If it is tiny or huge, set the root scale (try `1` or `0.01` until the car is about 4 m long).
3. On the **empty root** of that car: **Add Component → Car Rig**.
4. On **every mesh child** (body, each wheel, each door…): **Add Component → Car Part** and **Mesh Collider** (assign the same mesh). Set `Car Part → Category`:
   - body shell → **Body**
   - each wheel → **Wheel**
   - each door → **Door**
   - glass → **Glass**
   - seats / wheel / dash → **Interior**
5. Select **Studio Systems** in the Hierarchy. On `Car Switcher`, add a slot: Display Name, Rig = your new `CarRig`, Paint = existing `CarPaint` (or duplicate `CarPaint.mat` for a second colour set).
6. Press Play. The top bar should show the new car name; FRAME, CASE PRESET, paint, doors, explode all use the same scripts.

Do **not** change `CarPart.cs`, `CarRig.cs`, or `DesignerUI.cs`. Those already apply `p′ = c + t + R·(s·(p − c))` to whatever mesh is selected.

---

## If something goes wrong

| Symptom | Fix |
|---|---|
| Hub says “missing editor version” | Install **6000.6.6f1**, or open with another Unity 6 and confirm the upgrade |
| Safe Mode / compile errors on first open | Wait for package restore (`Window → Package Manager`). Then close and reopen the project |
| Empty Game view / missing scripts | Open `CarStudio.unity` before pressing Play. Do not move files out of `Assets/` |
| Pink materials | URP is missing — `Window → Package Manager` should list **Universal RP 17.6**. If not, Hub did not restore packages; check internet and reopen |
| Very low resolution | Game view scale is below 1x — drag it to **1x**. Turn off **Low Resolution Aspect Ratios** in the Game view menu |
| UI buttons do nothing | Click inside the Game view first so it has focus |

---

## Report

`CaseStudy2_Report.docx` is the written case study (geometric modelling, T·R·S matrix, clipping / hidden-surface removal). Screenshots from a working Play session are also in `output/`.
