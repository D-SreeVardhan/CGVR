/// <summary>
/// Lab 8 — Vertex and Fragment Shaders (Unity URP)
/// =================================================
/// A regular icosahedron (20 faces, 30 edges, 12 vertices) drawn by a
/// custom two-stage shader with three interactive fragment modes.
///
///   Vertex shader   — transforms every corner, passes per-vertex color
///                     and the face normal into the rasterizer.
///   Fragment shader — reads interpolated values and writes one of:
///                       0  pure vertex gradient
///                       1  gradient + dark edges + white vertex dots
///                       2  N·L lighting + specular + edges + vertex dots
///
/// SETUP
///   1. Put Lab8Shader.shader in Assets/Resources/.
///   2. Put this file in Assets/ as Lab8Controller.cs.
///   3. Select Main Camera → Add Component → Lab8Controller.
///   4. Press Play.
///
/// CONTROLS
///   Left-drag / Arrow keys  Rotate
///   Scroll / + -            Scale
///   M                       Cycle fragment mode
///   Space                   Pause / resume auto-spin
///   R                       Reset
/// </summary>
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;

[RequireComponent(typeof(Camera))]
public class Lab8Controller : MonoBehaviour
{
    [Header("Motion")]
    public float mouseSens   = 0.32f;
    public float keySpeed    = 75f;
    public float scaleSpeed  = 0.60f;
    public float autoSpinSpd = 10f;

    // ── State ─────────────────────────────────────────────────────────────
    Transform gem;
    Material  mat;
    int       mode;
    float     yaw    = 25f;
    float     pitch  = 18f;
    float     scale  = 1f;
    float     idle;
    bool      autoSpin = true;

    // ── GUI styles ────────────────────────────────────────────────────────
    GUIStyle stTitle, stBody, stDim, stAccent;
    bool     stylesReady;

    static readonly Color Ink   = new Color(0.93f, 0.90f, 0.84f);
    static readonly Color Amber = new Color(0.96f, 0.65f, 0.18f);
    static readonly Color Muted = new Color(0.55f, 0.52f, 0.48f);

    static readonly string[] ModeName = { "VERTEX GRADIENT", "GRADIENT + EDGES", "LIT + EDGES" };
    static readonly string[] FragLine =
    {
        "pixel = interpolated vColor\n(raw rasterizer output)",
        "pixel = vColor, dark at edges\nwhite dot at each vertex",
        "pixel = N·L + specular\nedges and vertex dots overlaid",
    };

    // ─────────────────────────────────────────────────────────────────────
    void Awake()
    {
        foreach (string n in new[] { "Icosahedron", "Gem", "Triangle" })
            DestroyAll(n);
        BuildScene();
    }

    void Start()
    {
        var cam = GetComponent<Camera>();
        cam.orthographic    = false;
        cam.fieldOfView     = 36f;
        cam.nearClipPlane   = 0.05f;
        cam.farClipPlane    = 40f;
        cam.clearFlags      = CameraClearFlags.SolidColor;
        cam.backgroundColor = new Color(0.09f, 0.08f, 0.07f);

        // Offset camera left so the right portion of screen shows the gem
        transform.SetPositionAndRotation(
            new Vector3(-1.1f, 0.25f, -4.8f), Quaternion.identity);
        transform.LookAt(new Vector3(0.55f, 0f, 0f));
        Apply();
    }

    // ── Scene builder ─────────────────────────────────────────────────────
    void BuildScene()
    {
        var shader = Resources.Load<Shader>("Lab8Shader");
        if (shader == null)
        {
            Debug.LogError("[Lab 8] Lab8Shader.shader must be in Assets/Resources/");
            return;
        }
        mat = new Material(shader);
        mat.SetFloat("_Mode", 0f);

        var go = new GameObject("Icosahedron");
        go.AddComponent<MeshFilter>().sharedMesh   = BuildIcosahedron();
        go.AddComponent<MeshRenderer>().sharedMaterial = mat;
        gem = go.transform;
    }

    // ── Update ────────────────────────────────────────────────────────────
    void Update()
    {
        if (gem == null) return;

        var kb = Keyboard.current;
        var ms = Mouse.current;
        bool acted = false;

        // Mouse drag
        if (ms != null && ms.leftButton.isPressed)
        {
            var d = ms.delta.ReadValue();
            if (d.sqrMagnitude > 0.5f)
            {
                yaw   += d.x * mouseSens;
                pitch -= d.y * mouseSens;
                pitch  = Mathf.Clamp(pitch, -88f, 88f);
                acted  = true;
            }
        }

        // Scroll zoom
        if (ms != null)
        {
            float sc = ms.scroll.ReadValue().y;
            if (Mathf.Abs(sc) > 0.01f)
            {
                scale = Mathf.Clamp(scale + sc * 0.002f, 0.25f, 2.6f);
                acted = true;
            }
        }

        if (kb != null)
        {
            // Arrow keys → rotate
            if (kb.leftArrowKey.isPressed)  { yaw   -= keySpeed * Time.deltaTime; acted = true; }
            if (kb.rightArrowKey.isPressed) { yaw   += keySpeed * Time.deltaTime; acted = true; }
            if (kb.upArrowKey.isPressed)    { pitch -= keySpeed * Time.deltaTime; acted = true; }
            if (kb.downArrowKey.isPressed)  { pitch += keySpeed * Time.deltaTime; acted = true; }
            pitch = Mathf.Clamp(pitch, -88f, 88f);

            // +/- scale
            float grow = (kb.equalsKey.isPressed || kb.numpadPlusKey.isPressed  ? 1f : 0f)
                       - (kb.minusKey.isPressed  || kb.numpadMinusKey.isPressed ? 1f : 0f);
            if (grow != 0f)
            {
                scale = Mathf.Clamp(scale + grow * scaleSpeed * Time.deltaTime, 0.25f, 2.6f);
                acted = true;
            }

            // Mode / reset / auto-spin
            if (kb.mKey.wasPressedThisFrame)
            {
                mode = (mode + 1) % ModeName.Length;
                mat.SetFloat("_Mode", mode);
            }
            if (kb.rKey.wasPressedThisFrame)
            {
                yaw = 25f; pitch = 18f; scale = 1f; acted = true;
            }
            if (kb.spaceKey.wasPressedThisFrame) autoSpin = !autoSpin;
        }

        idle = acted ? 0f : idle + Time.deltaTime;
        if (autoSpin && idle > 2f) yaw += autoSpinSpd * Time.deltaTime;

        Apply();
    }

    void Apply()
    {
        if (gem == null) return;
        gem.rotation   = Quaternion.Euler(pitch, yaw, 0f);
        gem.localScale = Vector3.one * scale;
    }

    // ── GUI ───────────────────────────────────────────────────────────────
    void OnGUI()
    {
        EnsureStyles();

        const float PX = 12f, PY = 12f, PW = 298f;
        DrawRect(PX - 8, PY - 8, PW + 16, 308f, new Color(0.07f, 0.06f, 0.05f, 0.88f));

        float cy = PY;
        GUI.Label(new Rect(PX, cy, PW, 22f), "VERTEX  +  FRAGMENT SHADERS", stTitle);
        cy += 26f;

        stAccent.normal.textColor = Amber;
        GUI.Label(new Rect(PX, cy, PW, 18f), "M   " + ModeName[mode], stAccent);
        cy += 22f;

        cy = Section(PX, cy, PW, "VERTEX SHADER", "once per corner (12 vertices, 20 faces)",
            "clipPos   = MVP × position\nnormalWS  = ObjectToWorldNormal()\nvColor    = vertex color (HSV gradient)");

        cy = Section(PX, cy, PW, "FRAGMENT SHADER", "once per pixel", FragLine[mode]);

        GUI.Label(new Rect(PX, cy, PW, 28f),
            $"pitch {pitch:F0}°   yaw {yaw:F0}°   scale {scale:F2}\n" +
            (autoSpin && idle > 2f ? "auto-spinning  Space = stop" : "Space = auto-spin"),
            stDim);
        cy += 32f;

        GUI.Label(new Rect(PX, cy, PW, 20f),
            "Drag / Arrows rotate   Scroll / +- scale   R reset",
            stDim);
    }

    float Section(float x, float y, float w, string head, string sub, string code)
    {
        float h = 72f;
        DrawRect(x,       y, w,  h,  new Color(0.15f, 0.13f, 0.11f, 0.95f));
        DrawRect(x,       y, 3f, h,  Amber);
        GUI.Label(new Rect(x + 10f, y +  3f, w - 14f, 16f), head, stAccent);
        GUI.Label(new Rect(x + 10f, y + 19f, w - 14f, 13f), sub,  stDim);
        GUI.Label(new Rect(x + 10f, y + 32f, w - 14f, 38f), code, stBody);
        return y + h + 6f;
    }

    // ── Style helpers ─────────────────────────────────────────────────────
    void EnsureStyles()
    {
        if (stylesReady) return;
        stylesReady = true;
        stTitle  = Sty(15, FontStyle.Bold,   Ink);
        stBody   = Sty(11, FontStyle.Normal, Ink);
        stDim    = Sty(10, FontStyle.Normal, Muted);
        stAccent = Sty(12, FontStyle.Bold,   Amber);
    }

    static GUIStyle Sty(int sz, FontStyle fs, Color col)
    {
        var s = new GUIStyle(GUI.skin.label) { fontSize = sz, fontStyle = fs };
        s.normal.textColor = col;
        return s;
    }

    static void DrawRect(float x, float y, float w, float h, Color col)
    {
        var prev = GUI.color;
        GUI.color = col;
        GUI.DrawTexture(new Rect(x, y, w, h), Texture2D.whiteTexture);
        GUI.color = prev;
    }

    static void DestroyAll(string objectName)
    {
        var found = GameObject.Find(objectName);
        while (found != null) { Destroy(found); found = GameObject.Find(objectName); }
    }

    // ── Icosahedron mesh ──────────────────────────────────────────────────
    // 12 vertices on the unit sphere, 20 equilateral triangular faces.
    // Each face gets its own 3 vertices (flat normals, unique bary coords).
    // Vertex colors are computed from HSV mapped to the vertex's position:
    //   hue      = azimuthal angle around Y axis
    //   sat/val  = driven by elevation, giving a top-to-bottom gradient
    static Mesh BuildIcosahedron()
    {
        float phi = (1f + Mathf.Sqrt(5f)) / 2f;

        // 12 base positions (normalized to unit sphere)
        var B = new Vector3[]
        {
            new Vector3(-1,  phi,  0), new Vector3( 1,  phi,  0),  //  0  1  top pair
            new Vector3(-1, -phi,  0), new Vector3( 1, -phi,  0),  //  2  3  bottom pair
            new Vector3( 0, -1,  phi), new Vector3( 0,  1,  phi),  //  4  5
            new Vector3( 0, -1, -phi), new Vector3( 0,  1, -phi),  //  6  7
            new Vector3( phi,  0, -1), new Vector3( phi,  0,  1),  //  8  9
            new Vector3(-phi,  0, -1), new Vector3(-phi,  0,  1),  // 10 11
        };
        for (int i = 0; i < B.Length; i++) B[i] = B[i].normalized;

        // 20 faces — standard icosahedron table
        var F = new int[,]
        {
            {0,11,5},{0,5,1},{0,1,7},{0,7,10},{0,10,11},
            {1,5,9},{5,11,4},{11,10,2},{10,7,6},{7,1,8},
            {3,9,4},{3,4,2},{3,2,6},{3,6,8},{3,8,9},
            {4,9,5},{2,4,11},{6,2,10},{8,6,7},{9,8,1},
        };

        // Barycentric corners for edge/vertex detection
        var BC = new Vector3[]
        {
            new Vector3(1,0,0), new Vector3(0,1,0), new Vector3(0,0,1)
        };

        var verts = new List<Vector3>();
        var norms = new List<Vector3>();
        var cols  = new List<Color>();
        var bary  = new List<Vector3>();
        var tris  = new List<int>();

        for (int f = 0; f < 20; f++)
        {
            Vector3 a = B[F[f,0]], b = B[F[f,1]], c = B[F[f,2]];
            Color   ca = GemColor(a), cb = GemColor(b), cc = GemColor(c);

            // Flat face normal — ensure it points outward from the origin
            Vector3 n = Vector3.Cross(b - a, c - a);
            if (n.sqrMagnitude < 1e-8f) continue;
            n.Normalize();
            if (Vector3.Dot(n, (a + b + c) / 3f) < 0f) n = -n;

            int idx = verts.Count;
            verts.Add(a); verts.Add(b); verts.Add(c);
            norms.Add(n); norms.Add(n); norms.Add(n);
            cols.Add(ca); cols.Add(cb); cols.Add(cc);
            bary.Add(BC[0]); bary.Add(BC[1]); bary.Add(BC[2]);
            tris.Add(idx); tris.Add(idx + 1); tris.Add(idx + 2);
        }

        var mesh = new Mesh { name = "Icosahedron" };
        mesh.SetVertices(verts);
        mesh.SetNormals(norms);
        mesh.SetColors(cols);
        mesh.SetUVs(0, bary);
        mesh.SetTriangles(tris, 0);
        mesh.RecalculateBounds();
        return mesh;
    }

    // Color based on world-space position on the unit sphere:
    //   hue      = horizontal angle around Y axis (full rainbow spectrum)
    //   elevation drives both saturation and brightness (crown is brighter)
    static Color GemColor(Vector3 v)
    {
        float hue  = Mathf.Repeat(Mathf.Atan2(v.z, v.x) / (Mathf.PI * 2f), 1f);
        float elev = v.y * 0.5f + 0.5f;                    // 0 = bottom, 1 = top
        float sat  = Mathf.Lerp(0.72f, 0.98f, elev);
        float val  = Mathf.Lerp(0.48f, 1.00f, elev);
        return Color.HSVToRGB(hue, sat, val);
    }
}
