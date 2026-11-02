using System;
using UnityEngine;
using UnityEngine.Rendering;

namespace CarDesigner
{
    /// <summary>Tap-to-select via physics raycast, with an additive rim overlay drawn on the selected part.</summary>
    public class PartSelector : MonoBehaviour
    {
        [SerializeField] Camera viewCamera;
        [SerializeField] OrbitCamera orbit;
        [SerializeField] Material highlightMaterial;
        [SerializeField] float maxPickDistance = 60f;

        RenderParams highlightParams;

        public CarPart Selected { get; private set; }
        public event Action<CarPart> SelectionChanged;

        void Awake()
        {
            highlightParams = new RenderParams(highlightMaterial)
            {
                shadowCastingMode = ShadowCastingMode.Off,
                receiveShadows = false
            };
        }

        void OnEnable()
        {
            orbit.Tapped += OnTap;
            orbit.DoubleTapped += OnDoubleTap;
        }

        void OnDisable()
        {
            orbit.Tapped -= OnTap;
            orbit.DoubleTapped -= OnDoubleTap;
        }

        public void Select(CarPart part)
        {
            if (part == Selected) return;
            Selected = part;
            SelectionChanged?.Invoke(part);
        }

        public void Frame(CarPart part)
        {
            Bounds bounds = part.WorldBounds;
            orbit.FocusOn(bounds.center, Mathf.Max(1.6f, bounds.size.magnitude * 2.2f));
        }

        void OnTap(Vector2 screenPosition) => Select(Pick(screenPosition));

        void OnDoubleTap(Vector2 screenPosition)
        {
            CarPart part = Pick(screenPosition);
            if (part == null)
            {
                orbit.ResetView();
                return;
            }
            Select(part);
            Frame(part);
        }

        CarPart Pick(Vector2 screenPosition)
        {
            Ray ray = viewCamera.ScreenPointToRay(screenPosition);
            return Physics.Raycast(ray, out RaycastHit hit, maxPickDistance)
                ? hit.collider.GetComponentInParent<CarPart>()
                : null;
        }

        void LateUpdate()
        {
            if (Selected == null || highlightMaterial == null) return;

            Mesh mesh = Selected.MeshFilter.sharedMesh;
            Matrix4x4 toWorld = Selected.transform.localToWorldMatrix;
            for (int i = 0; i < mesh.subMeshCount; i++)
                Graphics.RenderMesh(highlightParams, mesh, i, toWorld);
        }
    }
}
