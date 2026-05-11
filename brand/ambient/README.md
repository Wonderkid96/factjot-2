# Ambient loop slot

Drop a single seamless 60-second loop here as `desk.mov` (or `.mp4`). It layers
between the desk base and the case-file scenes at ~0.18 opacity, providing
atmospheric texture (dust, paper fibres, slow light shifts) without competing
with the foreground.

The slot is optional — if `desk.mov` is missing, the pipeline renders without
ambient and the desk stays solid.

Recommended specs:
- 1080×1920 (matches reel resolution; will object-fit cover otherwise)
- 60s loop, seamless
- Subtle slow motion — anything kinetic will compete with the scenes
- Mostly dark — bright areas will bleed through and wash out the desk
