// Lab 8 — Vertex shader + Fragment shader (URP / HLSL)
//
// VERTEX SHADER  runs once per corner of every triangle.
//   Receives: object-space position, surface normal, per-vertex color,
//             and a barycentric coordinate  (1,0,0) / (0,1,0) / (0,0,1).
//   Outputs:  clip-space position, world normal, color, bary — all
//             handed to the rasterizer for interpolation.
//
// RASTERIZER (fixed): blends the vertex outputs across the triangle.
//
// FRAGMENT SHADER  runs once per pixel.
//   Reads the interpolated values and writes one of three effects:
//   Mode 0 — pure vertex gradient (raw rasterizer interpolation)
//   Mode 1 — gradient + dark edge lines + white vertex dots
//   Mode 2 — per-pixel N·L lighting + specular + edges + vertex dots
Shader "CGVR/Lab8VertexFragment"
{
    Properties
    {
        _Mode ("Mode", Float) = 0
    }

    SubShader
    {
        Tags
        {
            "RenderType"       = "Opaque"
            "RenderPipeline"   = "UniversalPipeline"
            "Queue"            = "Geometry"
        }

        Pass
        {
            Name "Lab8"
            Tags { "LightMode" = "UniversalForward" }
            Cull Off        // show both sides (icosahedron is convex, ZWrite sorts it)
            ZWrite On

            HLSLPROGRAM
            #pragma vertex   vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            CBUFFER_START(UnityPerMaterial)
                float _Mode;
            CBUFFER_END

            // ── Vertex input ────────────────────────────────────────────
            struct Attributes
            {
                float3 positionOS : POSITION;
                float3 normalOS   : NORMAL;
                float4 color      : COLOR;
                float3 bary       : TEXCOORD0;   // barycentric: set in C#
            };

            // ── Rasterizer payload ──────────────────────────────────────
            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 normalWS   : TEXCOORD0;
                float3 bary       : TEXCOORD1;
                float4 color      : COLOR;
            };

            // ── Vertex shader ───────────────────────────────────────────
            Varyings vert(Attributes IN)
            {
                Varyings OUT;
                OUT.positionCS = TransformObjectToHClip(IN.positionOS);
                OUT.normalWS   = TransformObjectToWorldNormal(IN.normalOS);
                OUT.color      = IN.color;
                OUT.bary       = IN.bary;
                return OUT;
            }

            // ── Fragment shader ─────────────────────────────────────────
            half4 frag(Varyings IN) : SV_Target
            {
                float3 b    = IN.bary;
                float  minB = min(min(b.x, b.y), b.z);   // → 0 at edges
                float  maxB = max(max(b.x, b.y), b.z);   // → 1 at vertices

                // Edge line:   dark where any bary coord is near zero
                float edge  = 1.0 - smoothstep(0.0, 0.038, minB);
                // Vertex dot:  bright where one bary coord dominates
                float vtx   = smoothstep(0.87, 0.95, maxB);

                // ── Mode 0: pure gradient ───────────────────────────────
                if (_Mode < 0.5)
                    return IN.color;

                // ── Mode 1: gradient + edges + vertex dots ──────────────
                if (_Mode < 1.5)
                {
                    half3 col = IN.color.rgb;
                    col = lerp(col, half3(0.03, 0.03, 0.03), edge * 0.92);
                    col = lerp(col, half3(1.00, 1.00, 1.00), vtx);
                    return half4(col, 1);
                }

                // ── Mode 2: N·L lighting + edges + vertex dots ──────────
                float3 N    = normalize(IN.normalWS);
                float3 L    = normalize(float3(0.55, 0.82, -0.40));
                float3 camF = float3(0, 0, 1);            // approx view dir
                float3 H    = normalize(L + camF);
                float  ndl  = saturate(dot(N, L));
                float  spec = pow(saturate(dot(N, H)), 48.0) * 0.50;
                half3  lit  = IN.color.rgb * (0.16 + 0.84 * ndl) + spec;
                lit = lerp(lit, half3(0.03, 0.03, 0.03), edge * 0.92);
                lit = lerp(lit, half3(1.00, 1.00, 1.00), vtx);
                return half4(lit, 1);
            }
            ENDHLSL
        }
    }
    FallBack Off
}
