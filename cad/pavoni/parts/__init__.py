"""One module per assembly. Each exposes build(ctx) -> {part_id: [Solid, ...]}
with one solid per instance, in world coordinates (mm)."""

MODULES = ["boiler", "base", "mount", "heating", "group", "lever", "portafilter", "sight_glass", "steam", "safety_valve", "electrical"]
