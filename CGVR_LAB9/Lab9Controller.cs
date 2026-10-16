/// <summary>
/// Lab 9 — Simple Interactive 3D Scene (Unity)
/// =============================================
/// SETUP (one-time):
///   1. Create a new Unity project — 3D Core (Built-in Render Pipeline).
///   2. In the Project window: right-click Assets → Create → C# Script → "Lab9Controller".
///   3. Replace the file contents with this code and save.
///   4. Click "Main Camera" in the Hierarchy panel.
///   5. Inspector → Add Component → search "Lab9Controller" → add it.
///   6. Press ▶ Play.
///
/// The script builds the entire scene at runtime — no manual GameObject setup needed.
///
/// CONTROLS
/// ─────────────────────────────────────────────────
///   Tab          Switch between Camera and Interact mode
///   ─ Camera mode ──────────────────────────────────
///   WASD         Move (forward / back / strafe)
///   Mouse        Look around
///   Q / E        Move down / up
///   Shift        Sprint
///   ─ Interact mode ────────────────────────────────
///   Left-click   Select an object  (highlighted amber)
///   Arrows       Translate  (X / Z)
///   PgUp / PgDn  Translate  (Y)
///   I / K        Rotate  (pitch)
///   J / L        Rotate  (yaw)
///   + / -        Scale  up / down
///   Backspace    Deselect
/// </summary>
using UnityEngine;

[RequireComponent(typeof(Camera))]
[RequireComponent(typeof(CharacterController))]
public class Lab9Controller : MonoBehaviour
{
    // ── Scene layout ─────────────────────────────────────────────────────
    static readonly (PrimitiveType type, string label, Vector3 pos, Color col)[] OBJECTS =
    {
        (PrimitiveType.Cube,     "Cube",     new Vector3(-3f, 0.50f,  0f), new Color(0.90f, 0.28f, 0.28f)),
        (PrimitiveType.Sphere,   "Sphere",   new Vector3( 0f, 0.50f,  0f), new Color(0.28f, 0.55f, 1.00f)),
        (PrimitiveType.Capsule,  "Capsule",  new Vector3( 3f, 1.00f,  0f), new Color(0.28f, 0.85f, 0.40f)),
        (PrimitiveType.Cylinder, "Cylinder", new Vector3( 0f, 0.50f, -3f), new Color(1.00f, 0.80f, 0.28f)),
    };

    // ── Inspector-exposed settings ────────────────────────────────────────
    [Header("Camera")]
    public float moveSpeed        = 6f;
    public float sprintMultiplier = 2.5f;
    public float sensitivity      = 2f;

    [Header("Object Interaction")]
    public Color highlightColor = new Color(1f, 0.78f, 0.10f);   // amber
    public float translateSpeed = 4f;
    public float rotateSpeed    = 80f;
    public float scaleSpeed     = 1.5f;

    // ── Private state ─────────────────────────────────────────────────────
    float  pitch, yaw;
    bool   cameraMode = true;

    Camera             cam;
    CharacterController cc;
    float              verticalVelocity = 0f;

    GameObject selected;
    Renderer   selRend;
    Color      origColor;

    // No Shader.Find needed — clone the primitive's default material instead

    // ─────────────────────────────────────────────────────────────────────
    void Awake() => BuildScene();

    void Start()
    {
        cam = GetComponent<Camera>();
        cam.clearFlags      = CameraClearFlags.SolidColor;
        cam.backgroundColor = new Color(0.07f, 0.07f, 0.10f);

        // Eye level = 2 m above ground; CC capsule bottom flush with y = 0
        transform.SetPositionAndRotation(
            new Vector3(0f, 2.0f, -10f),
            Quaternion.Euler(10f, 0f, 0f));
        pitch = 10f;

        // CharacterController — prevents clipping through ground & objects
        cc            = GetComponent<CharacterController>();
        cc.height     = 2.0f;                          // full body height
        cc.radius     = 0.4f;                          // capsule radius
        cc.center     = new Vector3(0f, -1.0f, 0f);   // bottom touches y = 0
        cc.stepOffset = 0.4f;                          // climbs small steps
        cc.slopeLimit = 55f;                           // max walkable slope

        LockCursor(true);
    }

    // ── Scene builder (runtime) ───────────────────────────────────────────
    void BuildScene()
    {
        // Floor plane
        var floor = GameObject.CreatePrimitive(PrimitiveType.Plane);
        floor.name = "Floor";
        floor.transform.localScale = new Vector3(3f, 1f, 3f);
        Paint(floor, new Color(0.22f, 0.22f, 0.24f));

        // Coloured interactive primitives
        foreach (var (type, label, pos, col) in OBJECTS)
        {
            var go = GameObject.CreatePrimitive(type);
            go.name              = label;
            go.transform.position = pos;
            Paint(go, col);
        }

        // Directional "sun" light
        var sun = new GameObject("Sun");
        var lt  = sun.AddComponent<Light>();
        lt.type      = LightType.Directional;
        lt.intensity = 1.1f;
        lt.color     = new Color(1f, 0.96f, 0.88f);
        sun.transform.rotation = Quaternion.Euler(50f, -30f, 0f);

        // Dim ambient fill
        RenderSettings.ambientLight = new Color(0.18f, 0.18f, 0.20f);
    }

    static void Paint(GameObject go, Color col)
    {
        var rend = go.GetComponent<Renderer>();
        // Clone the primitive's own default material — works on any render pipeline
        var mat  = new Material(rend.sharedMaterial);
        SetMatColor(mat, col);
        rend.material = mat;
    }

    // ── Per-frame update ──────────────────────────────────────────────────
    void Update()
    {
        // Tab toggles mode
        if (Input.GetKeyDown(KeyCode.Tab))
        {
            cameraMode = !cameraMode;
            if (cameraMode) Deselect();   // clear selection when switching to camera
            LockCursor(cameraMode);
        }

        if (cameraMode) CameraUpdate();
        else            InteractUpdate();
    }

    // ── Camera movement ───────────────────────────────────────────────────
    void CameraUpdate()
    {
        // Mouse look
        yaw   += Input.GetAxis("Mouse X") * sensitivity;
        pitch -= Input.GetAxis("Mouse Y") * sensitivity;
        pitch  = Mathf.Clamp(pitch, -85f, 85f);
        transform.rotation = Quaternion.Euler(pitch, yaw, 0f);

        float spd = Input.GetKey(KeyCode.LeftShift)
                  ? moveSpeed * sprintMultiplier : moveSpeed;

        // Horizontal movement stays on the ground plane (yaw-relative, pitch ignored)
        // so WASD never "dives into" the ground when looking down
        var move = Quaternion.Euler(0f, yaw, 0f) * new Vector3(
            Input.GetAxis("Horizontal"), 0f,
            Input.GetAxis("Vertical"));

        // Gravity accumulates when airborne; snap to ground with small downward force
        if (cc.isGrounded)
            verticalVelocity = -2f;
        else
            verticalVelocity += Physics.gravity.y * Time.deltaTime;

        // Q/E override vertical (climb / descend manually)
        float qe = (Input.GetKey(KeyCode.E) ? 1f : 0f)
                 - (Input.GetKey(KeyCode.Q) ? 1f : 0f);

        var velocity = move * spd + Vector3.up * (qe != 0f ? qe * spd : verticalVelocity);

        // CharacterController.Move() respects all colliders — no more clipping
        cc.Move(velocity * Time.deltaTime);
    }

    // ── Object interaction ────────────────────────────────────────────────
    void InteractUpdate()
    {
        // Click to select
        if (Input.GetMouseButtonDown(0))
        {
            var ray = cam.ScreenPointToRay(Input.mousePosition);
            if (Physics.Raycast(ray, out RaycastHit hit, 200f)
                && hit.collider.name != "Floor")
                Select(hit.collider.gameObject);
            else
                Deselect();
        }

        if (selected == null) return;

        float    dt = Time.deltaTime;
        Transform t  = selected.transform;

        // Translate  (arrow keys + PgUp/PgDn)
        var move = Vector3.zero;
        if (Input.GetKey(KeyCode.LeftArrow))  move.x -= 1f;
        if (Input.GetKey(KeyCode.RightArrow)) move.x += 1f;
        if (Input.GetKey(KeyCode.UpArrow))    move.z += 1f;
        if (Input.GetKey(KeyCode.DownArrow))  move.z -= 1f;
        if (Input.GetKey(KeyCode.PageUp))     move.y += 1f;
        if (Input.GetKey(KeyCode.PageDown))   move.y -= 1f;
        t.position += move * translateSpeed * dt;

        // Rotate  (I/K = pitch,  J/L = yaw)
        if (Input.GetKey(KeyCode.I)) t.Rotate( Vector3.right, rotateSpeed * dt, Space.World);
        if (Input.GetKey(KeyCode.K)) t.Rotate(-Vector3.right, rotateSpeed * dt, Space.World);
        if (Input.GetKey(KeyCode.J)) t.Rotate(-Vector3.up,    rotateSpeed * dt, Space.World);
        if (Input.GetKey(KeyCode.L)) t.Rotate( Vector3.up,    rotateSpeed * dt, Space.World);

        // Scale  (+/-)
        float sc = (Input.GetKey(KeyCode.Equals) ? 1f : 0f)
                 - (Input.GetKey(KeyCode.Minus)  ? 1f : 0f);
        t.localScale = Vector3.Max(
            t.localScale + Vector3.one * sc * scaleSpeed * dt,
            Vector3.one * 0.10f);

        // Deselect
        if (Input.GetKeyDown(KeyCode.Backspace)) Deselect();
    }

    void Select(GameObject go)
    {
        Deselect();
        selected = go;
        selRend  = go.GetComponent<Renderer>();
        if (selRend != null)
        {
            // Read original colour from whichever property the shader uses
            origColor = selRend.material.HasProperty("_BaseColor")
                ? selRend.material.GetColor("_BaseColor")
                : selRend.material.color;
            SetMatColor(selRend.material, highlightColor);
        }
        Debug.Log($"[Lab 9] Selected: {go.name}  pos = {go.transform.position:F2}");
    }

    void Deselect()
    {
        if (selected != null && selRend != null)
            SetMatColor(selRend.material, origColor);
        selected = null;
        selRend  = null;
    }

    static void SetMatColor(Material mat, Color col)
    {
        if (mat.HasProperty("_Color"))     mat.SetColor("_Color",     col);
        if (mat.HasProperty("_BaseColor")) mat.SetColor("_BaseColor", col);
    }

    // ── On-screen HUD ─────────────────────────────────────────────────────
    void OnGUI()
    {
        var big  = new GUIStyle(GUI.skin.label) { fontSize = 16, fontStyle = FontStyle.Bold };
        var norm = new GUIStyle(GUI.skin.label) { fontSize = 13 };

        string modeStr = cameraMode
            ? "CAMERA MODE  \u2014  Tab \u2192 Interact"
            : "INTERACT MODE  \u2014  Tab \u2192 Camera";

        // Drop-shadow
        GUI.color = new Color(0f, 0f, 0f, 0.6f);
        GUI.Label(new Rect(12f, 12f, 700f, 26f), modeStr, big);

        // Label
        GUI.color = cameraMode
            ? new Color(0.35f, 1.00f, 0.55f)   // green  = camera
            : new Color(1.00f, 0.80f, 0.30f);   // amber  = interact
        GUI.Label(new Rect(11f, 11f, 700f, 26f), modeStr, big);

        GUI.color = Color.white;

        if (cameraMode)
        {
            GUI.Label(new Rect(11f, 35f, 800f, 22f),
                "WASD: move   Mouse: look   Q/E: up/down   Shift: sprint", norm);
        }
        else if (selected != null)
        {
            var p = selected.transform.position;
            var r = selected.transform.eulerAngles;
            var s = selected.transform.localScale;

            GUI.color = highlightColor;
            GUI.Label(new Rect(11f, 35f, 700f, 24f), $"\u25ba  {selected.name}", big);

            GUI.color = Color.white;
            GUI.Label(new Rect(11f, 57f, 860f, 22f),
                $"  Pos ({p.x:F2}, {p.y:F2}, {p.z:F2})   " +
                $"Rot ({r.x:F0}\u00b0, {r.y:F0}\u00b0, {r.z:F0}\u00b0)   " +
                $"Scale {s.x:F2}", norm);
            GUI.Label(new Rect(11f, 77f, 860f, 22f),
                "  Arrows: translate   I/J/K/L: rotate   +/-: scale   Backspace: deselect", norm);
        }
        else
        {
            GUI.color = new Color(0.75f, 0.75f, 0.75f);
            GUI.Label(new Rect(11f, 35f, 700f, 22f),
                "Click on an object to select it", norm);
        }
    }

    // ── Cursor helper ─────────────────────────────────────────────────────
    void LockCursor(bool locked)
    {
        Cursor.lockState = locked ? CursorLockMode.Locked : CursorLockMode.None;
        Cursor.visible   = !locked;
    }
}
