// Additive fresnel overlay drawn on top of the selected component.
Shader "CarDesigner/SelectionRim"
{
    Properties
    {
        _Color ("Color", Color) = (0.89, 0.64, 0.23, 1)
        _Power ("Rim Power", Range(0.5, 8)) = 3.2
        _Fill ("Fill", Range(0, 1)) = 0.035
        _Pulse ("Pulse Speed", Range(0, 10)) = 3.5
    }

    SubShader
    {
        Tags { "RenderType" = "Transparent" "Queue" = "Transparent+10" "RenderPipeline" = "UniversalPipeline" }

        Pass
        {
            Name "SelectionRim"
            Tags { "LightMode" = "UniversalForward" }

            Blend One One
            ZWrite Off
            ZTest LEqual
            Offset -1, -1
            Cull Back

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            CBUFFER_START(UnityPerMaterial)
                half4 _Color;
                half _Power;
                half _Fill;
                half _Pulse;
            CBUFFER_END

            struct Attributes
            {
                float4 positionOS : POSITION;
                float3 normalOS : NORMAL;
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 normalWS : TEXCOORD0;
                float3 viewDirWS : TEXCOORD1;
            };

            Varyings vert(Attributes input)
            {
                Varyings output;
                VertexPositionInputs positions = GetVertexPositionInputs(input.positionOS.xyz);
                output.positionCS = positions.positionCS;
                output.normalWS = TransformObjectToWorldNormal(input.normalOS);
                output.viewDirWS = GetWorldSpaceViewDir(positions.positionWS);
                return output;
            }

            half4 frag(Varyings input) : SV_Target
            {
                half facing = saturate(dot(normalize(input.normalWS), normalize(input.viewDirWS)));
                half rim = pow(1.0h - facing, _Power);
                half pulse = 0.78h + 0.22h * sin(_Time.y * _Pulse);
                return half4(_Color.rgb * (rim + _Fill) * pulse, 1.0h);
            }
            ENDHLSL
        }
    }
}
