"""One module per assembly. Each exposes build(ctx) -> {part_id: [Solid, ...]}
with one solid per instance, in world coordinates (mm)."""

MODULES = ["boiler", "group"]
