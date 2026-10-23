/// <summary>
/// Lab 10 — 3D Viewing Pipeline (Unity)
/// =======================================
/// Demonstrates every stage of the real-time 3D viewing pipeline:
///   Model Space → World Space → Eye/Camera Space
///   → Clip Space → NDC → Screen Space
///
/// Shows LIVE matrices from Unity's GPU pipeline alongside a split
/// Perspective / Orthographic viewport for visual comparison.
///
/// SETUP (re-use the CGVR_Lab9 Unity project):
///   1. Open your existing Unity project in Unity Hub.
///   2. In the Project panel: right-click Assets → Create → C# Script
///   3. Name it exactly "Lab10Controller" and paste this code in.
///   4. Open File → New Scene → save it (e.g. "Lab10").
///   5. Click Main Camera in the Hierarchy.
///   6. Inspector → Add Component → "Lab10Controller" → Press ▶ Play.
///
/// CONTROLS
/// ─────────────────────────────────────────────────
///   ← → ↑ ↓      Orbit camera around scene
///   + / -         Zoom in / out
///   F / G         Widen / Narrow field of view
///   V             Toggle split view  (Perspective | Orthographic)
///   1 / 2 / 3     Select object — updates pipeline data panel
///   H             Show / hide pipeline panel
/// </summary>
using UnityEngine;

[RequireComponent(typeof(Camera))]
public class Lab10Controller : MonoBehaviour
{
    // ── Scene definition ──────────────────────────────────────────────────
    static readonly (PrimitiveType t, string n, Vector3 p, Color c)[] PRIMS =
    {
        (PrimitiveType.Cube,     "Cube",     new Vector3(-3.5f, 0.50f,  2f), new Color(0.90f, 0.28f, 0.28f)),
        (PrimitiveType.Sphere,   "Sphere",   new Vector3( 0.0f, 0.50f,  0f), new Color(0.28f, 0.58f, 1.00f)),
        (PrimitiveType.Cylinder, "Cylinder", new Vector3( 3.5f, 1.00f, -2f), new Color(1.00f, 0.78f, 0.28f)),
    };

    // ── Inspector ─────────────────────────────────────────────────────────
    [Header("Orbit Camera")]
    public float orbitSpeed = 60f;
    public float zoomSpeed  = 5f;

    // ── Runtime state ─────────────────────────────────────────────────────
    Camera       mainCam;
    Camera       sideCam;
    GameObject[] sceneObjs;

    int  selIdx    = 1;      // default: Sphere
    bool splitView = true;
    bool showPanel = true;

    float orbitYaw   = 25f;
    float orbitPitch = 28f;
    float orbitDist  = 11f;
    readonly Vector3 pivot = new Vector3(0f, 0.5f, 0f);

    // GUI styles (lazy-init on first OnGUI call)
    GUIStyle stTitle, stStageHdr, stBody, stTiny;
    bool     stylesReady;

    // ─────────────────────────────────────────────────────────────────────
    void Awake()
    {
        // Disable any other Lab controllers attached to this camera
        // (e.g. Lab9Controller running in the same scene)
        foreach (var mb in GetComponents<MonoBehaviour>())
        {
            if (mb == this) continue;
            string t = mb.GetType().Name;
            if (t.StartsWith("Lab") && t != "Lab10Controller")
            {
                mb.enabled = false;
                Debug.Log($"[Lab10] Disabled conflicting controller: {t}");
            }
        }

        // Destroy stray objects left over from other scene scripts
        foreach (string n in new[] { "Floor", "Sun", "Cube", "Sphere",
                                     "Capsule", "Cylinder" })
        {
            var found = GameObject.Find(n);
            while (found != null) { Destroy(found); found = GameObject.Find(n); }
        }

        BuildScene();
    }

    void Start()
    {
        mainCam = GetComponent<Camera>();
        mainCam.clearFlags      = CameraClearFlags.SolidColor;
        mainCam.backgroundColor = new Color(0.07f, 0.07f, 0.10f);
        mainCam.fieldOfView     = 60f;

        // ── Orthographic side camera ──────────────────────────────────────
        var go  = new GameObject("Lab10_OrthoCamera");
        sideCam = go.AddComponent<Camera>();
        sideCam.clearFlags      = CameraClearFlags.SolidColor;
        sideCam.backgroundColor = new Color(0.05f, 0.06f, 0.09f);
        sideCam.orthographic    = true;
        sideCam.depth           = mainCam.depth + 1;

        ApplyViewports();
        SyncOrbit();
    }

    // ── Scene builder ─────────────────────────────────────────────────────
    void BuildScene()
    {
        sceneObjs = new GameObject[PRIMS.Length];
        for (int i = 0; i < PRIMS.Length; i++)
        {
            var (t, n, p, c) = PRIMS[i];
            var go = GameObject.CreatePrimitive(t);
            go.name = n;
            go.transform.position = p;
            Paint(go, c);
            sceneObjs[i] = go;
        }

        // Floor
        var floor = GameObject.CreatePrimitive(PrimitiveType.Plane);
        floor.name = "Floor";
        floor.transform.localScale = new Vector3(2f, 1f, 2f);
        Paint(floor, new Color(0.15f, 0.15f, 0.17f));

        // Directional light
        var sunGO = new GameObject("Sun");
        var lt    = sunGO.AddComponent<Light>();
        lt.type      = LightType.Directional;
        lt.intensity = 1.15f;
        lt.color     = new Color(1f, 0.95f, 0.86f);
        sunGO.transform.rotation = Quaternion.Euler(52f, -38f, 0f);
        RenderSettings.ambientLight = new Color(0.14f, 0.14f, 0.17f);
    }

    // ── Per-frame ─────────────────────────────────────────────────────────
    void Update()
    {
        HandleInput();
        SyncOrbit();
    }

    void HandleInput()
    {
        // Orbit
        if (Input.GetKey(KeyCode.LeftArrow))  orbitYaw  -= orbitSpeed * Time.deltaTime;
        if (Input.GetKey(KeyCode.RightArrow)) orbitYaw  += orbitSpeed * Time.deltaTime;
        if (Input.GetKey(KeyCode.UpArrow))
            orbitPitch = Mathf.Clamp(orbitPitch - orbitSpeed * Time.deltaTime, -80f, 80f);
        if (Input.GetKey(KeyCode.DownArrow))
            orbitPitch = Mathf.Clamp(orbitPitch + orbitSpeed * Time.deltaTime, -80f, 80f);

        // Zoom (scroll wheel + keys)
        orbitDist -= Input.GetAxis("Mouse ScrollWheel") * zoomSpeed * 2f;
        if (Input.GetKey(KeyCode.Equals)) orbitDist -= zoomSpeed * Time.deltaTime;
        if (Input.GetKey(KeyCode.Minus))  orbitDist += zoomSpeed * Time.deltaTime;
        orbitDist = Mathf.Clamp(orbitDist, 3f, 26f);

        // Field of view
        if (Input.GetKey(KeyCode.F))
            mainCam.fieldOfView = Mathf.Clamp(mainCam.fieldOfView + 30f * Time.deltaTime, 10f, 120f);
        if (Input.GetKey(KeyCode.G))
            mainCam.fieldOfView = Mathf.Clamp(mainCam.fieldOfView - 30f * Time.deltaTime, 10f, 120f);

        // Toggles
        if (Input.GetKeyDown(KeyCode.V)) { splitView = !splitView; ApplyViewports(); }
        if (Input.GetKeyDown(KeyCode.H)) showPanel  = !showPanel;

        // Object select
        if (Input.GetKeyDown(KeyCode.Alpha1)) selIdx = 0;
        if (Input.GetKeyDown(KeyCode.Alpha2)) selIdx = 1;
        if (Input.GetKeyDown(KeyCode.Alpha3)) selIdx = 2;
    }

    void SyncOrbit()
    {
        var rot    = Quaternion.Euler(orbitPitch, orbitYaw, 0f);
        var offset = rot * new Vector3(0f, 0f, -orbitDist);
        mainCam.transform.position = pivot + offset;
        mainCam.transform.LookAt(pivot);

        // Side camera mirrors main camera pose but uses orthographic projection
        sideCam.transform.SetPositionAndRotation(
            mainCam.transform.position, mainCam.transform.rotation);
        // Scale ortho size to match the perspective frustum height at the pivot
        sideCam.orthographicSize =
            orbitDist * Mathf.Tan(mainCam.fieldOfView * 0.5f * Mathf.Deg2Rad);
    }

    void ApplyViewports()
    {
        if (splitView)
        {
            mainCam.rect    = new Rect(0f,   0f, 0.5f, 1f);
            sideCam.rect    = new Rect(0.5f, 0f, 0.5f, 1f);
            sideCam.enabled = true;
        }
        else
        {
            mainCam.rect    = new Rect(0f, 0f, 1f, 1f);
            sideCam.enabled = false;
        }
    }

    // ── GUI ───────────────────────────────────────────────────────────────
    void OnGUI()
    {
        EnsureStyles();
        DrawTopBar();
        if (showPanel)   DrawPipelinePanel();
        if (splitView)   DrawBottomLabels();
    }

    void EnsureStyles()
    {
        if (stylesReady) return;
        stylesReady = true;
        stTitle    = MkStyle(16, FontStyle.Bold,   new Color(1.00f, 0.82f, 0.28f));
        stStageHdr = MkStyle(10, FontStyle.Bold,   new Color(0.90f, 0.90f, 0.90f));
        stBody     = MkStyle( 9, FontStyle.Normal, new Color(0.82f, 0.92f, 0.82f));
        stTiny     = MkStyle( 9, FontStyle.Normal, new Color(0.65f, 0.72f, 0.65f));
    }

    static GUIStyle MkStyle(int sz, FontStyle fs, Color col)
    {
        var s = new GUIStyle(GUI.skin.label) { fontSize = sz, fontStyle = fs };
        s.normal.textColor = col;
        return s;
    }

    // ── Top bar ───────────────────────────────────────────────────────────
    void DrawTopBar()
    {
        Rect(0, 0, Screen.width, 28f, new Color(0, 0, 0, 0.65f));

        var rich = MkStyle(13, FontStyle.Normal, Color.white);
        rich.richText = true;
        string modeStr = splitView
            ? "<color=#88FF88>PERSPECTIVE</color>  ◄  [V]  ►  <color=#88CCFF>ORTHOGRAPHIC</color>   [H] panel"
            : "<color=#88FF88>FULL PERSPECTIVE VIEW</color>   [V] split   [H] panel";
        GUI.Label(new UnityEngine.Rect(8f, 5f, 700f, 20f), modeStr, rich);

        GUI.Label(new UnityEngine.Rect(Screen.width - 430f, 5f, 430f, 20f),
            "[←→↑↓] Orbit    [+/-] Zoom    [F/G] FOV    [1/2/3] Object", stTiny);
    }

    // ── Pipeline panel ────────────────────────────────────────────────────
    void DrawPipelinePanel()
    {
        const float PX = 8f, PY = 36f, PW = 270f;

        var sel = selIdx < sceneObjs.Length ? sceneObjs[selIdx] : null;

        // ── Compute pipeline values ───────────────────────────────────────
        Matrix4x4 mMat = sel != null ? sel.transform.localToWorldMatrix : Matrix4x4.identity;
        Matrix4x4 vMat = mainCam.worldToCameraMatrix;
        Matrix4x4 pMat = mainCam.projectionMatrix;

        Vector3   worldPos = sel != null ? sel.transform.position : Vector3.zero;
        Vector3   eyePos   = vMat.MultiplyPoint(worldPos);
        Vector4   clip     = pMat * (vMat * mMat * new Vector4(0, 0, 0, 1));
        Vector3   ndc      = clip.w != 0f
                             ? new Vector3(clip.x / clip.w, clip.y / clip.w, clip.z / clip.w)
                             : Vector3.zero;
        Vector3   screen   = sel != null ? mainCam.WorldToScreenPoint(worldPos) : Vector3.zero;

        // ── Background panel ──────────────────────────────────────────────
        float panelH = 26f + 5f * (58f + 8f) + 10f;
        Rect(PX - 4, PY - 4, PW + 8, panelH, new Color(0, 0, 0, 0.72f));

        float y = PY;

        // Title
        GUI.Label(new UnityEngine.Rect(PX, y, PW, 20f), "3D VIEWING PIPELINE", stTitle);
        y += 20f;
        GUI.Label(new UnityEngine.Rect(PX, y, PW, 13f),
            $"Object: {(sel?.name ?? "—")}   [1] Cube  [2] Sphere  [3] Cylinder", stTiny);
        y += 14f;

        // ── Stage 1 — Model → World ───────────────────────────────────────
        y = DrawStage(PX, y, PW,
            "① MODEL → WORLD  (Model Matrix)",
            new Color(1.00f, 0.55f, 0.32f),
            sel != null
                ? $"pos   {Fmt(worldPos)}\n" +
                  $"rot   {Fmt(sel.transform.eulerAngles)}\n" +
                  $"scale {Fmt(sel.transform.localScale)}"
                : "no object selected",
            lines: 3);

        // ── Stage 2 — World → Eye ─────────────────────────────────────────
        y = DrawStage(PX, y, PW,
            "② WORLD → EYE  (View / LookAt)",
            new Color(0.35f, 0.80f, 1.00f),
            $"cam pos  {Fmt(mainCam.transform.position)}\n" +
            $"eye pos  {Fmt(eyePos)}",
            lines: 2);

        // ── Stage 3 — Eye → Clip (Projection) ────────────────────────────
        string projType = mainCam.orthographic
            ? "Orthographic"
            : $"Perspective  FOV={mainCam.fieldOfView:F0}°";

        y = DrawStage(PX, y, PW,
            $"③ EYE → CLIP  ({projType})",
            new Color(0.38f, 1.00f, 0.52f),
            MatRow(pMat, 0) + "\n" +
            MatRow(pMat, 1) + "\n" +
            MatRow(pMat, 2) + "\n" +
            MatRow(pMat, 3),
            lines: 4);

        // ── Stage 4 — Clip → NDC ─────────────────────────────────────────
        y = DrawStage(PX, y, PW,
            "④ CLIP → NDC  (÷ w, perspective divide)",
            new Color(0.88f, 0.55f, 1.00f),
            $"clip  ({clip.x:F3}, {clip.y:F3}, {clip.z:F3},  w={clip.w:F3})\n" +
            $"ndc   ({ndc.x:F3}, {ndc.y:F3}, {ndc.z:F3})",
            lines: 2);

        // ── Stage 5 — NDC → Screen ───────────────────────────────────────
        DrawStage(PX, y, PW,
            "⑤ NDC → SCREEN  (Viewport Mapping)",
            new Color(1.00f, 1.00f, 0.42f),
            $"viewport  {(int)mainCam.pixelRect.width} × {(int)mainCam.pixelRect.height} px\n" +
            $"screen    ({screen.x:F0}, {screen.y:F0})   depth = {screen.z:F3}",
            lines: 2);
    }

    // Draws one pipeline stage box; returns the Y position after the box.
    float DrawStage(float x, float y, float w,
                    string header, Color accent, string body, int lines)
    {
        // Connector arrow
        GUI.color = new Color(0.42f, 0.42f, 0.42f);
        GUI.Label(new UnityEngine.Rect(x + 6f, y, w, 10f), "  ▼", stTiny);
        y += 8f;

        float lineH = 11f;
        float boxH  = 17f + lines * lineH + 3f;

        // Tinted background
        Rect(x, y, w, boxH, new Color(accent.r * 0.11f, accent.g * 0.11f, accent.b * 0.11f, 0.88f));
        // Accent bar on the left
        Rect(x, y, 3f, boxH, new Color(accent.r, accent.g, accent.b, 0.95f));

        // Header text
        var sh = MkStyle(10, FontStyle.Bold, accent);
        GUI.Label(new UnityEngine.Rect(x + 6f, y + 2f, w - 6f, 14f), header, sh);

        // Body text
        GUI.Label(new UnityEngine.Rect(x + 6f, y + 16f, w - 6f, lines * lineH + 2f), body, stBody);

        GUI.color = Color.white;
        return y + boxH + 2f;
    }

    // ── Bottom labels ─────────────────────────────────────────────────────
    void DrawBottomLabels()
    {
        float hw = Screen.width * 0.5f;
        float by = Screen.height - 26f;
        Rect(0f, by, Screen.width, 26f, new Color(0f, 0f, 0f, 0.62f));

        var sP = MkStyle(13, FontStyle.Bold, new Color(0.52f, 1.00f, 0.58f));
        sP.alignment = TextAnchor.MiddleCenter;
        GUI.Label(new UnityEngine.Rect(0f, by + 4f, hw, 18f),
            $"PERSPECTIVE   FOV {mainCam.fieldOfView:F0}°", sP);

        var sO = MkStyle(13, FontStyle.Bold, new Color(0.45f, 0.80f, 1.00f));
        sO.alignment = TextAnchor.MiddleCenter;
        GUI.Label(new UnityEngine.Rect(hw, by + 4f, hw, 18f),
            $"ORTHOGRAPHIC   size {sideCam.orthographicSize:F1}", sO);
    }

    // ── Utilities ─────────────────────────────────────────────────────────
    static void Rect(float x, float y, float w, float h, Color col)
    {
        GUI.color = col;
        GUI.DrawTexture(new UnityEngine.Rect(x, y, w, h), Texture2D.whiteTexture);
        GUI.color = Color.white;
    }

    static string Fmt(Vector3 v)  => $"({v.x:F2}, {v.y:F2}, {v.z:F2})";
    static string MatRow(Matrix4x4 m, int r) =>
        $" [{m[r,0]:F2} {m[r,1]:F2} {m[r,2]:F2} {m[r,3]:F2}]";

    static void Paint(GameObject go, Color col)
    {
        var rend = go.GetComponent<Renderer>();
        var mat  = new Material(rend.sharedMaterial);
        SetMatColor(mat, col);
        rend.material = mat;
    }

    static void SetMatColor(Material mat, Color col)
    {
        if (mat.HasProperty("_Color"))     mat.SetColor("_Color",     col);
        if (mat.HasProperty("_BaseColor")) mat.SetColor("_BaseColor", col);
    }
}
