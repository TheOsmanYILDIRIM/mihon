//!PARAM strength
//!DESC White reduction (0 = off)
//!DEFAULT 0.35
//!MINIMUM 0
//!MAXIMUM 0.6

//!DESC Selective white reduction
//!HOOK MAIN
//!BIND HOOKED
//!COMPUTE 8 8
@group(0) @binding(0) var tex: texture_2d<f32>;
@group(0) @binding(1) var outputTexture: texture_storage_2d<rgba16float, write>;
override strength: f32;

@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3<u32>) {
    if (any(id.xy >= textureDimensions(outputTexture))) {
        return;
    }
    let c = textureLoad(tex, id.xy, 0);
    let hi = max(c.r, max(c.g, c.b));
    let lo = min(c.r, min(c.g, c.b));
    let neutral = 1.0 - smoothstep(0.02, 0.12, hi - lo);
    let bright = smoothstep(0.55, 1.0, lo);
    let delta = min(lo, strength * neutral * bright);
    textureStore(outputTexture, id.xy, vec4<f32>(c.rgb - vec3<f32>(delta), c.a));
}
