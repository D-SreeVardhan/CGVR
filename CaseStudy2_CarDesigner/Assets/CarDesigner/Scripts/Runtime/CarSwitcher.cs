using System;
using UnityEngine;

namespace CarDesigner
{
    /// <summary>
    /// Holds one or more car configurations. Only the active car is visible; all others are hidden.
    /// DesignerUI reads the active rig and paint through this component.
    /// </summary>
    [DisallowMultipleComponent]
    public class CarSwitcher : MonoBehaviour
    {
        [Serializable]
        public struct Slot
        {
            public string displayName;
            public CarRig rig;
            public CarPaint paint;
        }

        [SerializeField] Slot[] slots = Array.Empty<Slot>();
        [SerializeField] int activeIndex;

        public event Action<int> SlotChanged;

        public int Count => slots.Length;
        public int ActiveIndex => activeIndex;

        public CarRig ActiveRig => slots.Length > 0 && activeIndex < slots.Length ? slots[activeIndex].rig : null;
        public CarPaint ActivePaint => slots.Length > 0 && activeIndex < slots.Length ? slots[activeIndex].paint : null;
        public string ActiveName => slots.Length > 0 && activeIndex < slots.Length ? slots[activeIndex].displayName : "";

        public string SlotName(int index) => index >= 0 && index < slots.Length ? slots[index].displayName : "";

        void Awake()
        {
            ApplyVisibility();
        }

        public void SwitchTo(int index)
        {
            if (index < 0 || index >= slots.Length || index == activeIndex) return;
            activeIndex = index;
            ApplyVisibility();
            SlotChanged?.Invoke(activeIndex);
        }

        void ApplyVisibility()
        {
            for (int i = 0; i < slots.Length; i++)
            {
                if (slots[i].rig != null)
                    slots[i].rig.gameObject.SetActive(i == activeIndex);
            }
        }
    }
}
