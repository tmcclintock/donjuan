"""Shared tree icon drawing helpers for outdoor scene renderers."""


def draw_tree_icon(draw, x0: int, y0: int, tile_size: int, palette: dict) -> None:
    """Draw the shared stylized tree icon used by outdoor scene renderers."""
    t = tile_size
    draw.ellipse(
        [x0 + t * 0.35, y0 + t * 0.5, x0 + t * 0.65, y0 + t * 0.95],
        fill=palette["tree_trunk"],
    )
    draw.ellipse(
        [x0 + t * 0.08, y0 + t * 0.08, x0 + t * 0.92, y0 + t * 0.86],
        fill=palette["tree_canopy"],
    )
    draw.ellipse(
        [x0 + t * 0.2, y0 + t * 0.14, x0 + t * 0.72, y0 + t * 0.56],
        fill=palette["tree_canopy_hi"],
    )
