using System.Collections.Generic;
using System.IO;
using CarDesigner.UI;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem.UI;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace CarDesigner.EditorTools
{
    /// <summary>
    /// Generates the whole studio scene from the imported FBX so it can be rebuilt deterministically:
    /// import settings, materials, environment, car rig, camera, lighting, post-processing, UI and player settings.
    /// </summary>
    public static class StudioSceneBuilder
    {
        public const string Root = "Assets/CarDesigner";
        public const string ModelPath = Root + "/Models/SportCarInterior.fbx";
        public const string ScenePath = Root + "/Scenes/CarStudio.unity";
        const string ModelsFolder = Root + "/Models";
        const string MaterialsFolder = Root + "/Materials";
        const string SettingsFolder = Root + "/Settings";
        const string LitShader = "Universal Render Pipeline/Lit";
        const string UnlitShader = "Universal Render Pipeline/Unlit";
        const float TurntableTop = 0.04f;

        static readonly Color Backdrop = new Color32(0x13, 0x13, 0x15, 0xFF);

        static readonly Dictionary<string, (string label, PartCategory category)> PartMap =
            new Dictionary<string, (string, PartCategory)>
            {
                { "Chassis", ("Body Shell", PartCategory.Body) },
                { "Door_L", ("Door · Left", PartCategory.Door) },
                { "Door_R", ("Door · Right", PartCategory.Door) },
                { "Tire_FL", ("Wheel · Front Left", PartCategory.Wheel) },
                { "Tire_FR", ("Wheel · Front Right", PartCategory.Wheel) },
                { "Tire_RL", ("Wheel · Rear Left", PartCategory.Wheel) },
                { "Tire_RR", ("Wheel · Rear Right", PartCategory.Wheel) },
                { "MirrorL", ("Mirror · Left", PartCategory.Mirror) },
                { "MirrorR", ("Mirror · Right", PartCategory.Mirror) },
                { "Windows", ("Glasshouse", PartCategory.Glass) },
                { "WindowL", ("Side Glass · Left", PartCategory.Glass) },
                { "WindowR", ("Side Glass · Right", PartCategory.Glass) },
                { "Interior", ("Cabin Trim", PartCategory.Interior) },
                { "Seats", ("Seats", PartCategory.Interior) },
                { "Steering_Wheel", ("Steering Wheel", PartCategory.Interior) },
            };

        struct StudioMaterials
        {
            public Material Base, Paint, Glass, Rubber, Trim, Floor, Turntable, TurntableRim, Highlight;
            public Texture2D Palette;
            public Color PaletteKey;
        }

        [MenuItem("Car Designer/Rebuild Studio Scene", priority = 0)]
        public static void Build()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode)
            {
                Debug.LogWarning("CarDesigner: exit Play Mode before rebuilding the studio scene.");
                return;
            }
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;

            EnsureFolder(MaterialsFolder);
            EnsureFolder(SettingsFolder);
            EnsureFolder(Root + "/Scenes");

            ConfigureModelImport();
            StudioMaterials materials = CreateMaterials();

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            ConfigureRenderSettings();
            BuildEnvironment(materials);
            CarRig rig = BuildCar(materials);
            OrbitCamera orbit = BuildCamera(rig);
            BuildLights();
            BuildVolume();
            BuildSystems(rig, orbit, materials);

            EditorSceneManager.SaveScene(scene, ScenePath);
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };
            ConfigurePlayer();
            AssetDatabase.SaveAssets();

            Debug.Log($"CarDesigner: studio scene built at {ScenePath} (palette: {(materials.Palette != null ? materials.Palette.name : "none")}).");
        }

        [MenuItem("Car Designer/Capture Scene Preview", priority = 20)]
        public static void CapturePreviewMenu() => CapturePreview("StudioPreview.png");

        /// <summary>Command-line entry point: <c>-executeMethod CarDesigner.EditorTools.StudioSceneBuilder.BuildAndPreview</c>.</summary>
        public static void BuildAndPreview()
        {
            Build();
            CapturePreview("StudioPreview.png");
        }

        public static string OutputPath(string fileName)
        {
            string folder = Path.Combine(Directory.GetParent(Application.dataPath)!.FullName, "output");
            Directory.CreateDirectory(folder);
            return Path.Combine(folder, fileName);
        }

        public static void CapturePreview(string fileName)
        {
            OrbitCamera orbit = Object.FindAnyObjectByType<OrbitCamera>();
            if (orbit == null)
            {
                Debug.LogWarning("CarDesigner: no studio camera in the open scene.");
                return;
            }

            Camera cam = orbit.GetComponent<Camera>();
            const int width = 1920, height = 1080;
            var target = new RenderTexture(width, height, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
            RenderTexture previousTarget = cam.targetTexture, previousActive = RenderTexture.active;

            cam.targetTexture = target;
            cam.Render();
            RenderTexture.active = target;
            var image = new Texture2D(width, height, TextureFormat.RGB24, false);
            image.ReadPixels(new Rect(0, 0, width, height), 0, 0);
            image.Apply();

            cam.targetTexture = previousTarget;
            RenderTexture.active = previousActive;
            string path = OutputPath(fileName);
            File.WriteAllBytes(path, image.EncodeToPNG());
            Object.DestroyImmediate(image);
            Object.DestroyImmediate(target);
            Debug.Log($"CarDesigner: preview written to {path}");
        }

        // ───────────────────────────── import & materials ─────────────────────────────

        static void ConfigureModelImport()
        {
            var importer = (ModelImporter)AssetImporter.GetAtPath(ModelPath);
            if (importer == null) throw new FileNotFoundException("Car model missing", ModelPath);

            // The Blender export tags its metre-modelled geometry as centimetres; ignoring the file unit keeps it 1:1.
            importer.globalScale = 1f;
            importer.useFileScale = false;
            importer.bakeAxisConversion = true;
            importer.importCameras = false;
            importer.importLights = false;
            importer.importAnimation = false;
            importer.animationType = ModelImporterAnimationType.None;
            importer.isReadable = true;
            importer.meshCompression = ModelImporterMeshCompression.Off;
            importer.materialImportMode = ModelImporterMaterialImportMode.ImportViaMaterialDescription;
            importer.SaveAndReimport();
        }

        static StudioMaterials CreateMaterials()
        {
            var m = new StudioMaterials { Palette = FindPalette() };

            m.Base = Lit("CarBase", Color.white, 0.55f, 0.05f, m.Palette);
            m.Paint = m.Palette != null
                ? Lit("CarPaint", Color.white, 0.82f, 0.1f, m.Palette)
                : Lit("CarPaint", new Color32(0x8E, 0x2A, 0x1F, 0xFF), 0.82f, 0.1f);
            m.Rubber = Lit("Rubber", new Color32(0x1A, 0x1A, 0x1B, 0xFF), 0.22f);
            m.Trim = Lit("CabinTrim", new Color32(0x2B, 0x26, 0x22, 0xFF), 0.3f);
            m.Glass = Lit("Glass", new Color(0.07f, 0.075f, 0.08f, 0.55f), 0.95f);
            MakeTransparent(m.Glass);

            m.Floor = Lit("StudioFloor", new Color32(0x1E, 0x1E, 0x20, 0xFF), 0.32f);
            m.Turntable = Lit("Turntable", new Color32(0x2C, 0x2C, 0x2F, 0xFF), 0.55f, 0.2f);
            m.TurntableRim = LoadOrCreate("TurntableRim", Shader.Find(UnlitShader));
            m.TurntableRim.SetColor("_BaseColor", new Color32(0xE3, 0xA2, 0x3B, 0xFF));
            EditorUtility.SetDirty(m.TurntableRim);

            m.Highlight = LoadOrCreate("SelectionRim", Shader.Find("CarDesigner/SelectionRim"));
            m.Highlight.SetColor("_Color", new Color(0.95f, 0.66f, 0.28f, 1f));
            m.Highlight.SetFloat("_Power", 3.2f);
            m.Highlight.SetFloat("_Fill", 0.035f);
            EditorUtility.SetDirty(m.Highlight);

            if (m.Palette != null)
            {
                Mesh chassis = FindModelMesh("Chassis");
                m.PaletteKey = chassis != null ? DominantTexel(chassis, m.Palette) : Color.white;
                Debug.Log($"CarDesigner: body key colour #{ColorUtility.ToHtmlStringRGB(m.PaletteKey)}" +
                          (chassis != null ? "" : " (chassis mesh not found)"));
            }
            return m;
        }

        static Texture2D FindPalette()
        {
            foreach (string guid in AssetDatabase.FindAssets("t:Texture2D", new[] { ModelsFolder }))
            {
                string path = AssetDatabase.GUIDToAssetPath(guid);
                var importer = (TextureImporter)AssetImporter.GetAtPath(path);
                importer.isReadable = true;
                importer.mipmapEnabled = false;
                importer.textureCompression = TextureImporterCompression.Uncompressed;
                importer.filterMode = FilterMode.Bilinear;
                importer.SaveAndReimport();
                return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
            }
            return null;
        }

        static Mesh FindModelMesh(string objectName)
        {
            foreach (Object asset in AssetDatabase.LoadAllAssetsAtPath(ModelPath))
                if (asset is GameObject go && go.name == objectName && go.TryGetComponent(out MeshFilter filter))
                    return filter.sharedMesh;

            // A single-root FBX names its root (the chassis) after the file instead.
            var root = AssetDatabase.LoadAssetAtPath<GameObject>(ModelPath);
            return objectName == "Chassis" && root != null && root.TryGetComponent(out MeshFilter rootFilter)
                ? rootFilter.sharedMesh
                : null;
        }

        /// <summary>Area-weighted most common texel under the chassis UVs — the body paint colour to recolour.</summary>
        static Color DominantTexel(Mesh mesh, Texture2D palette)
        {
            Vector3[] vertices = mesh.vertices;
            Vector2[] uvs = mesh.uv;
            int[] triangles = mesh.triangles;
            if (uvs.Length == 0) return Color.white;

            var weights = new Dictionary<Color32, float>();
            var samples = new Dictionary<Color32, Color>();
            for (int i = 0; i < triangles.Length; i += 3)
            {
                int a = triangles[i], b = triangles[i + 1], c = triangles[i + 2];
                float area = Vector3.Cross(vertices[b] - vertices[a], vertices[c] - vertices[a]).magnitude;
                Vector2 uv = (uvs[a] + uvs[b] + uvs[c]) / 3f;
                Color texel = palette.GetPixelBilinear(uv.x, uv.y);
                var bucket = new Color32((byte)(Mathf.RoundToInt(texel.r * 15f) * 17), (byte)(Mathf.RoundToInt(texel.g * 15f) * 17),
                    (byte)(Mathf.RoundToInt(texel.b * 15f) * 17), 255);
                weights.TryGetValue(bucket, out float total);
                weights[bucket] = total + area;
                if (!samples.ContainsKey(bucket)) samples[bucket] = texel;
            }

            // Black trim and underside usually out-area the paint, so prefer chromatic swatches.
            Color32? best = HeaviestBucket(weights, samples, chromaticOnly: true) ??
                            HeaviestBucket(weights, samples, chromaticOnly: false);
            return best.HasValue ? samples[best.Value] : Color.white;
        }

        static Color32? HeaviestBucket(Dictionary<Color32, float> weights, Dictionary<Color32, Color> samples, bool chromaticOnly)
        {
            Color32? best = null;
            float bestWeight = -1f;
            foreach (KeyValuePair<Color32, float> entry in weights)
            {
                Color.RGBToHSV(samples[entry.Key], out _, out float saturation, out float value);
                if (chromaticOnly && (saturation < 0.3f || value < 0.2f)) continue;
                if (entry.Value <= bestWeight) continue;
                best = entry.Key;
                bestWeight = entry.Value;
            }
            return best;
        }

        static Material Lit(string name, Color color, float smoothness, float metallic = 0f, Texture texture = null)
        {
            Material material = LoadOrCreate(name, Shader.Find(LitShader));
            material.SetColor("_BaseColor", color);
            material.SetTexture("_BaseMap", texture);
            material.SetFloat("_Smoothness", smoothness);
            material.SetFloat("_Metallic", metallic);
            EditorUtility.SetDirty(material);
            return material;
        }

        static Material LoadOrCreate(string name, Shader shader)
        {
            string path = $"{MaterialsFolder}/{name}.mat";
            var material = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (material == null)
            {
                material = new Material(shader) { name = name };
                AssetDatabase.CreateAsset(material, path);
            }
            else if (material.shader != shader)
            {
                material.shader = shader;
            }
            return material;
        }

        static void MakeTransparent(Material material)
        {
            material.SetFloat("_Surface", 1f);
            material.SetFloat("_Blend", 0f);
            material.SetFloat("_SrcBlend", (float)BlendMode.SrcAlpha);
            material.SetFloat("_DstBlend", (float)BlendMode.OneMinusSrcAlpha);
            material.SetFloat("_SrcBlendAlpha", (float)BlendMode.One);
            material.SetFloat("_DstBlendAlpha", (float)BlendMode.OneMinusSrcAlpha);
            material.SetFloat("_ZWrite", 0f);
            material.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
            material.DisableKeyword("_ALPHAPREMULTIPLY_ON");
            material.SetOverrideTag("RenderType", "Transparent");
            material.renderQueue = (int)RenderQueue.Transparent;
            material.SetShaderPassEnabled("ShadowCaster", false);
            EditorUtility.SetDirty(material);
        }

        // ───────────────────────────── scene content ─────────────────────────────

        static void ConfigureRenderSettings()
        {
            RenderSettings.skybox = null;
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color32(0x72, 0x6D, 0x66, 0xFF);
            RenderSettings.ambientEquatorColor = new Color32(0x3E, 0x3B, 0x37, 0xFF);
            RenderSettings.ambientGroundColor = new Color32(0x12, 0x12, 0x12, 0xFF);
            RenderSettings.defaultReflectionMode = DefaultReflectionMode.Custom;
            RenderSettings.customReflectionTexture = StudioReflection();
            RenderSettings.reflectionIntensity = 0.9f;
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.Linear;
            RenderSettings.fogColor = Backdrop;
            RenderSettings.fogStartDistance = 16f;
            RenderSettings.fogEndDistance = 46f;
            DynamicGI.UpdateEnvironment();
        }

        /// <summary>
        /// Neutral studio reflection: warm softbox overhead, graphite walls with a bright band, dark floor.
        /// Replaces the default procedural sky, whose blue tint would otherwise appear in paint and glass.
        /// </summary>
        static Cubemap StudioReflection()
        {
            const int size = 32;
            string path = SettingsFolder + "/StudioReflection.cubemap";
            AssetDatabase.DeleteAsset(path);

            var cubemap = new Cubemap(size, TextureFormat.RGBA32, false) { name = "StudioReflection" };
            Color softbox = new Color32(0xC9, 0xC1, 0xB3, 0xFF);
            Color wallTop = new Color32(0x4A, 0x47, 0x42, 0xFF);
            Color wallBottom = new Color32(0x1E, 0x1D, 0x1C, 0xFF);
            Color band = new Color32(0x9C, 0x95, 0x8A, 0xFF);
            Color floor = new Color32(0x12, 0x12, 0x12, 0xFF);

            var pixels = new Color[size * size];
            foreach (CubemapFace face in new[] { CubemapFace.PositiveX, CubemapFace.NegativeX, CubemapFace.PositiveZ, CubemapFace.NegativeZ })
            {
                for (int y = 0; y < size; y++)
                {
                    float t = 1f - y / (size - 1f);
                    Color wall = Color.Lerp(wallBottom, wallTop, t);
                    bool inBand = t > 0.62f && t < 0.72f;
                    for (int x = 0; x < size; x++) pixels[y * size + x] = inBand ? band : wall;
                }
                cubemap.SetPixels(pixels, face);
            }

            for (int i = 0; i < pixels.Length; i++)
            {
                int x = i % size, y = i / size;
                float r = new Vector2(x - size * 0.5f, y - size * 0.5f).magnitude / (size * 0.5f);
                pixels[i] = Color.Lerp(softbox, wallTop, Mathf.SmoothStep(0.35f, 1f, r));
            }
            cubemap.SetPixels(pixels, CubemapFace.PositiveY);
            for (int i = 0; i < pixels.Length; i++) pixels[i] = floor;
            cubemap.SetPixels(pixels, CubemapFace.NegativeY);
            cubemap.Apply(false);

            AssetDatabase.CreateAsset(cubemap, path);
            return cubemap;
        }

        static void BuildEnvironment(StudioMaterials materials)
        {
            var environment = new GameObject("Studio Environment");

            GameObject floor = GameObject.CreatePrimitive(PrimitiveType.Plane);
            floor.name = "Floor";
            floor.transform.SetParent(environment.transform, false);
            floor.transform.localScale = new Vector3(8f, 1f, 8f);
            Object.DestroyImmediate(floor.GetComponent<Collider>());
            floor.GetComponent<Renderer>().sharedMaterial = materials.Floor;
            floor.isStatic = true;

            const float radius = 3.2f;
            MeshObject("Turntable", environment.transform, materials.Turntable,
                SaveMesh("TurntableDisc", DiscMesh(radius, TurntableTop, 160)), ShadowCastingMode.On);
            MeshObject("Turntable Rim", environment.transform, materials.TurntableRim,
                SaveMesh("TurntableRim", RingMesh(radius + 0.035f, radius + 0.06f, 0.003f, 160)), ShadowCastingMode.Off);
        }

        static void MeshObject(string name, Transform parent, Material material, Mesh mesh, ShadowCastingMode shadows)
        {
            var go = new GameObject(name, typeof(MeshFilter), typeof(MeshRenderer)) { isStatic = true };
            go.transform.SetParent(parent, false);
            go.GetComponent<MeshFilter>().sharedMesh = mesh;
            var meshRenderer = go.GetComponent<MeshRenderer>();
            meshRenderer.sharedMaterial = material;
            meshRenderer.shadowCastingMode = shadows;
        }

        static Mesh SaveMesh(string name, Mesh mesh)
        {
            string path = $"{SettingsFolder}/{name}.asset";
            AssetDatabase.DeleteAsset(path);
            mesh.name = name;
            AssetDatabase.CreateAsset(mesh, path);
            return mesh;
        }

        /// <summary>Flat-topped cylinder with a split edge so the rim shades crisply.</summary>
        static Mesh DiscMesh(float radius, float height, int segments)
        {
            var vertices = new List<Vector3> { new Vector3(0f, height, 0f) };
            var normals = new List<Vector3> { Vector3.up };
            var triangles = new List<int>();

            for (int i = 0; i <= segments; i++)
            {
                float a = i * Mathf.PI * 2f / segments;
                var dir = new Vector3(Mathf.Cos(a), 0f, Mathf.Sin(a));
                vertices.Add(dir * radius + Vector3.up * height);
                normals.Add(Vector3.up);
            }
            for (int i = 1; i <= segments; i++) triangles.AddRange(new[] { 0, i + 1, i });

            int side = vertices.Count;
            for (int i = 0; i <= segments; i++)
            {
                float a = i * Mathf.PI * 2f / segments;
                var dir = new Vector3(Mathf.Cos(a), 0f, Mathf.Sin(a));
                vertices.Add(dir * radius + Vector3.up * height);
                vertices.Add(dir * radius);
                normals.Add(dir);
                normals.Add(dir);
            }
            for (int i = 0; i < segments; i++)
            {
                int top = side + i * 2, bottom = top + 1, nextTop = top + 2, nextBottom = top + 3;
                triangles.AddRange(new[] { top, nextTop, bottom, bottom, nextTop, nextBottom });
            }

            var mesh = new Mesh();
            mesh.SetVertices(vertices);
            mesh.SetNormals(normals);
            mesh.SetTriangles(triangles, 0);
            mesh.RecalculateBounds();
            return mesh;
        }

        static Mesh RingMesh(float innerRadius, float outerRadius, float height, int segments)
        {
            var vertices = new List<Vector3>();
            var triangles = new List<int>();
            for (int i = 0; i <= segments; i++)
            {
                float a = i * Mathf.PI * 2f / segments;
                var dir = new Vector3(Mathf.Cos(a), 0f, Mathf.Sin(a));
                vertices.Add(dir * innerRadius + Vector3.up * height);
                vertices.Add(dir * outerRadius + Vector3.up * height);
            }
            for (int i = 0; i < segments; i++)
            {
                int inner = i * 2, outer = inner + 1, nextInner = inner + 2, nextOuter = inner + 3;
                triangles.AddRange(new[] { inner, nextInner, outer, outer, nextInner, nextOuter });
            }

            var mesh = new Mesh();
            mesh.SetVertices(vertices);
            mesh.SetTriangles(triangles, 0);
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();
            return mesh;
        }

        static CarRig BuildCar(StudioMaterials materials)
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(ModelPath);
            var model = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
            PrefabUtility.UnpackPrefabInstance(model, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            model.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
            model.transform.localScale = Vector3.one;
            // A single-root FBX makes that root (the chassis) the prefab root, renamed after the file.
            if (model.TryGetComponent(out MeshRenderer _)) model.name = "Chassis";

            // Every part becomes a direct child of an empty rig root, so all rest poses share one space.
            var car = new GameObject("Sports Coupe");
            MeshRenderer[] renderers = model.GetComponentsInChildren<MeshRenderer>(true);
            foreach (MeshRenderer r in renderers) r.transform.SetParent(car.transform, true);
            if (model.transform.parent != car.transform) Object.DestroyImmediate(model);
            else
                for (int i = model.transform.childCount - 1; i >= 0; i--)
                    Object.DestroyImmediate(model.transform.GetChild(i).gameObject);

            Bounds bounds = renderers[0].bounds;
            foreach (MeshRenderer r in renderers) bounds.Encapsulate(r.bounds);
            car.transform.position = new Vector3(-bounds.center.x, TurntableTop - bounds.min.y, -bounds.center.z);

            bool hasPalette = materials.Palette != null;
            foreach (MeshRenderer r in renderers)
            {
                (string label, PartCategory category) info = PartMap.TryGetValue(r.name, out var mapped)
                    ? mapped
                    : (ObjectNames.NicifyVariableName(r.name), PartCategory.Body);

                r.gameObject.AddComponent<CarPart>().Configure(info.label, info.category);
                r.gameObject.AddComponent<MeshCollider>().sharedMesh = r.GetComponent<MeshFilter>().sharedMesh;
                r.sharedMaterials = AssignMaterials(r.sharedMaterials, info.category, hasPalette, materials);
                if (info.category == PartCategory.Glass) r.shadowCastingMode = ShadowCastingMode.Off;
            }

            CarRig rig = car.AddComponent<CarRig>();
            rig.SetForwardAxis(DetectForward(car.transform));
            EditorUtility.SetDirty(rig);
            Debug.Log($"CarDesigner: car bounds {bounds.size.x:0.000} × {bounds.size.y:0.000} × {bounds.size.z:0.000} m, forward {DetectForward(car.transform)}.");
            return rig;
        }

        static Material[] AssignMaterials(Material[] imported, PartCategory category, bool hasPalette, StudioMaterials m)
        {
            var result = new Material[Mathf.Max(1, imported.Length)];
            for (int i = 0; i < result.Length; i++)
            {
                bool isGlassSlot = category == PartCategory.Glass ||
                                   (i < imported.Length && imported[i] != null && imported[i].name.Contains("Window"));
                bool paintable = category is PartCategory.Body or PartCategory.Door or PartCategory.Mirror;
                if (isGlassSlot) result[i] = m.Glass;
                else if (hasPalette) result[i] = paintable ? m.Paint : m.Base;
                else result[i] = category switch
                {
                    PartCategory.Body or PartCategory.Door or PartCategory.Mirror => m.Paint,
                    PartCategory.Wheel => m.Rubber,
                    PartCategory.Interior => m.Trim,
                    PartCategory.Glass => m.Glass,
                    _ => throw new System.ArgumentOutOfRangeException(nameof(category), category, null)
                };
            }
            return result;
        }

        /// <summary>Forward = along the car's long axis, from the rear axle towards the front axle.</summary>
        static Vector3 DetectForward(Transform car)
        {
            Vector3? Centre(string partName)
            {
                Transform t = car.Find(partName);
                return t != null ? car.InverseTransformPoint(t.GetComponent<Renderer>().bounds.center) : null;
            }

            Transform chassis = car.Find("Chassis");
            Vector3 size = chassis != null ? chassis.GetComponent<Renderer>().bounds.size : Vector3.forward;
            Vector3 longAxis = size.x > size.z ? Vector3.right : Vector3.forward;

            Vector3? fl = Centre("Tire_FL"), fr = Centre("Tire_FR"), rl = Centre("Tire_RL"), rr = Centre("Tire_RR");
            Vector3? steering = Centre("Steering_Wheel"), seats = Centre("Seats");
            float direction = 1f;
            if (fl.HasValue && fr.HasValue && rl.HasValue && rr.HasValue)
                direction = Vector3.Dot((fl.Value + fr.Value) - (rl.Value + rr.Value), longAxis);
            else if (steering.HasValue && seats.HasValue)
                direction = Vector3.Dot(steering.Value - seats.Value, longAxis);

            return longAxis * (direction < 0f ? -1f : 1f);
        }

        static OrbitCamera BuildCamera(CarRig rig)
        {
            var go = new GameObject("Studio Camera", typeof(Camera), typeof(AudioListener), typeof(OrbitCamera)) { tag = "MainCamera" };
            var cam = go.GetComponent<Camera>();
            cam.fieldOfView = 36f;
            cam.nearClipPlane = 0.05f;
            cam.farClipPlane = 120f;
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = Backdrop;
            cam.allowHDR = true;

            UniversalAdditionalCameraData data = cam.GetUniversalAdditionalCameraData();
            data.renderPostProcessing = true;
            data.antialiasing = AntialiasingMode.FastApproximateAntialiasing;

            Bounds bounds = CarBounds(rig);
            Vector3 forward = rig.transform.TransformDirection(ForwardOf(rig));
            Vector3 right = Vector3.Cross(Vector3.up, forward);
            Vector3 towardsCamera = (forward * 0.78f + right * 0.62f).normalized;
            float yaw = Mathf.Atan2(-towardsCamera.x, -towardsCamera.z) * Mathf.Rad2Deg;
            float length = Mathf.Max(bounds.size.x, bounds.size.z);

            var orbit = go.GetComponent<OrbitCamera>();
            orbit.Configure(new Vector3(bounds.center.x, bounds.min.y + bounds.size.y * 0.42f, bounds.center.z), yaw, 13f, length * 1.8f);
            return orbit;
        }

        static Vector3 ForwardOf(CarRig rig)
        {
            var serialized = new SerializedObject(rig);
            return serialized.FindProperty("forwardAxis").vector3Value;
        }

        static Bounds CarBounds(CarRig rig)
        {
            Renderer[] renderers = rig.GetComponentsInChildren<Renderer>();
            Bounds bounds = renderers[0].bounds;
            foreach (Renderer r in renderers) bounds.Encapsulate(r.bounds);
            return bounds;
        }

        static void BuildLights()
        {
            var lights = new GameObject("Studio Lights");

            Light key = DirectionalLight("Key Light", lights.transform, Quaternion.Euler(52f, -38f, 0f),
                new Color32(0xFF, 0xF0, 0xDC, 0xFF), 2.4f);
            key.shadows = LightShadows.Soft;
            key.shadowStrength = 0.85f;

            Light fill = DirectionalLight("Fill Light", lights.transform, Quaternion.Euler(24f, 148f, 0f),
                new Color32(0xE8, 0xE4, 0xDC, 0xFF), 0.8f);
            fill.shadows = LightShadows.None;

            Light rim = DirectionalLight("Rim Light", lights.transform, Quaternion.Euler(18f, 20f, 0f),
                new Color32(0xFF, 0xE2, 0xB8, 0xFF), 0.9f);
            rim.shadows = LightShadows.None;
        }

        static Light DirectionalLight(string name, Transform parent, Quaternion rotation, Color color, float intensity)
        {
            var go = new GameObject(name, typeof(Light));
            go.transform.SetParent(parent, false);
            go.transform.rotation = rotation;
            var light = go.GetComponent<Light>();
            light.type = LightType.Directional;
            light.color = color;
            light.intensity = intensity;
            return light;
        }

        static void BuildVolume()
        {
            string path = SettingsFolder + "/StudioVolume.asset";
            AssetDatabase.DeleteAsset(path);
            var profile = ScriptableObject.CreateInstance<VolumeProfile>();
            AssetDatabase.CreateAsset(profile, path);

            var tonemapping = profile.Add<Tonemapping>(true);
            tonemapping.mode.value = TonemappingMode.ACES;
            var adjustments = profile.Add<ColorAdjustments>(true);
            adjustments.postExposure.value = 0.6f;
            adjustments.contrast.value = 10f;
            adjustments.saturation.value = 0f;
            adjustments.colorFilter.overrideState = false;
            adjustments.hueShift.overrideState = false;
            var bloom = profile.Add<Bloom>(true);
            bloom.threshold.value = 1.1f;
            bloom.intensity.value = 0.3f;
            var vignette = profile.Add<Vignette>(true);
            vignette.intensity.value = 0.3f;
            vignette.smoothness.value = 0.45f;
            vignette.color.value = Color.black;

            foreach (VolumeComponent component in profile.components)
            {
                component.hideFlags = HideFlags.HideInInspector | HideFlags.HideInHierarchy;
                AssetDatabase.AddObjectToAsset(component, profile);
            }
            EditorUtility.SetDirty(profile);
            AssetDatabase.SaveAssets();

            var go = new GameObject("Studio Volume", typeof(Volume));
            var volume = go.GetComponent<Volume>();
            volume.isGlobal = true;
            volume.sharedProfile = profile;
        }

        static void BuildSystems(CarRig rig, OrbitCamera orbit, StudioMaterials materials)
        {
            var systems = new GameObject("Studio Systems");

            var selector = systems.AddComponent<PartSelector>();
            Set(selector, "viewCamera", orbit.GetComponent<Camera>());
            Set(selector, "orbit", orbit);
            Set(selector, "highlightMaterial", materials.Highlight);

            var paint = systems.AddComponent<CarPaint>();
            Set(paint, "rig", rig);
            Set(paint, "paintMaterial", materials.Paint);
            Set(paint, "palette", materials.Palette);
            var serialized = new SerializedObject(paint);
            serialized.FindProperty("paletteKey").colorValue = materials.PaletteKey;
            serialized.ApplyModifiedPropertiesWithoutUndo();

            // CarSwitcher wraps the single car produced by the scene builder.
            // When the user adds more cars in the Editor the switcher can hold them all.
            var switcher = systems.AddComponent<CarSwitcher>();
            var switcherSo = new SerializedObject(switcher);
            var slots = switcherSo.FindProperty("slots");
            slots.arraySize = 1;
            var slot = slots.GetArrayElementAtIndex(0);
            slot.FindPropertyRelative("displayName").stringValue = "Sports Coupe";
            slot.FindPropertyRelative("rig").objectReferenceValue = rig;
            slot.FindPropertyRelative("paint").objectReferenceValue = paint;
            switcherSo.ApplyModifiedPropertiesWithoutUndo();

            var ui = new GameObject("Designer UI").AddComponent<DesignerUI>();
            Set(ui, "switcher", switcher);
            Set(ui, "selector", selector);
            Set(ui, "orbit", orbit);

            var eventSystem = new GameObject("EventSystem", typeof(EventSystem), typeof(InputSystemUIInputModule));
            eventSystem.GetComponent<InputSystemUIInputModule>().AssignDefaultActions();
        }

        static void ConfigurePlayer()
        {
            PlayerSettings.companyName = "CGVR Studio";
            PlayerSettings.productName = "Atelier Car Designer";
            PlayerSettings.SetApplicationIdentifier(NamedBuildTarget.Android, "com.cgvr.atelier");
            PlayerSettings.defaultInterfaceOrientation = UIOrientation.AutoRotation;
            PlayerSettings.allowedAutorotateToPortrait = false;
            PlayerSettings.allowedAutorotateToPortraitUpsideDown = false;
            PlayerSettings.allowedAutorotateToLandscapeLeft = true;
            PlayerSettings.allowedAutorotateToLandscapeRight = true;
            PlayerSettings.SetScriptingBackend(NamedBuildTarget.Android, ScriptingImplementation.IL2CPP);
            PlayerSettings.Android.targetArchitectures = AndroidArchitecture.ARM64;
        }

        static void Set(Object target, string field, Object value)
        {
            var serialized = new SerializedObject(target);
            serialized.FindProperty(field).objectReferenceValue = value;
            serialized.ApplyModifiedPropertiesWithoutUndo();
        }

        static void EnsureFolder(string path)
        {
            if (AssetDatabase.IsValidFolder(path)) return;
            string parent = Path.GetDirectoryName(path)!.Replace('\\', '/');
            EnsureFolder(parent);
            AssetDatabase.CreateFolder(parent, Path.GetFileName(path));
        }
    }
}
