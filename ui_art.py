"""Decorative folk-style side art for the light theme. Original flat shapes, no faces or figures.

Purely visual: a fixed layer behind the page content, aria-hidden, ignored by the pointer."""
import math

INK, GOLD, VERM, LEAF, PEACOCK, ROSE = "#1B2246", "#E9A93B", "#C8452B", "#2E7D4F", "#1F6F78", "#C85A7C"
_S = f'stroke="{INK}" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"'


def _lotus(cx, cy, s=1.0):
    petals = ""
    for ang, fill in ((-62, ROSE), (62, ROSE), (-32, VERM), (32, VERM), (0, GOLD)):
        petals += (f'<ellipse cx="0" cy="-34" rx="12" ry="34" fill="{fill}" {_S} '
                   f'transform="rotate({ang})"/>')
    return (f'<g transform="translate({cx} {cy}) scale({s})">{petals}'
            f'<path d="M-30 6 Q0 26 30 6" fill="none" {_S}/><circle cx="0" cy="2" r="4" fill="{INK}"/></g>')


def _marigold(cx, cy, s=1.0):
    ring = "".join(
        f'<circle cx="{26 * math.cos(math.radians(a)):.1f}" cy="{26 * math.sin(math.radians(a)):.1f}" r="11" fill="{GOLD}" {_S}/>'
        for a in range(0, 360, 40))
    return (f'<g transform="translate({cx} {cy}) scale({s})">{ring}'
            f'<circle r="15" fill="{VERM}" {_S}/><circle r="5" fill="{GOLD}"/></g>')


def _paisley(cx, cy, s=1.0, rot=0, fill=PEACOCK):
    return (f'<g transform="translate({cx} {cy}) rotate({rot}) scale({s})">'
            f'<path d="M0 -46 C34 -40 40 8 14 34 C-6 52 -34 38 -30 14 C-27 -6 -8 -4 -4 10 '
            f'C-2 20 -14 22 -14 14" fill="{fill}" {_S}/>'
            f'<circle cx="8" cy="-8" r="4" fill="{GOLD}"/><circle cx="14" cy="8" r="3" fill="{GOLD}"/>'
            f'<circle cx="2" cy="-22" r="3" fill="{GOLD}"/></g>')


def _vine(x0, y0, length, s=1.0):
    """A wavy stem with alternating leaves, running downward."""
    out, y, side = f'<path d="M{x0} {y0} ', 0, 1
    segs = int(length // 60)
    d = ""
    for i in range(segs):
        d += f"q{26 * (1 if i % 2 == 0 else -1)} 30 0 60 "
    out += d + f'" fill="none" {_S}/>'
    for i in range(segs):
        yy = y0 + 30 + i * 60
        xx = x0 + (13 if i % 2 == 0 else -13)
        sd = 1 if i % 2 == 0 else -1
        out += (f'<path d="M{xx} {yy} q{26 * sd} -18 {40 * sd} 4 q{-14 * sd} 20 {-40 * sd} -4z" '
                f'fill="{LEAF}" {_S}/>')
    return out


def _kolam(cx, cy):
    dots = "".join(f'<circle cx="{cx + dx * 16}" cy="{cy + dy * 16}" r="3.4" fill="{INK}"/>'
                   for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx + dy) % 2 == 0)
    return (f'<polygon points="{cx},{cy - 22} {cx + 22},{cy} {cx},{cy + 22} {cx - 22},{cy}" fill="none" '
            f'stroke="{GOLD}" stroke-width="2.4"/>' + dots)


def _panel_svg() -> str:
    parts = [
        _vine(150, 0, 900),
        _lotus(150, 130, 1.1), _marigold(70, 250, 0.95), _paisley(228, 330, 1.2, 12, PEACOCK),
        _kolam(110, 440), _marigold(230, 520, 0.8), _lotus(90, 640, 1.0),
        _paisley(220, 720, 1.1, -18, VERM), _kolam(180, 810), _marigold(70, 850, 0.7),
    ]
    return ('<svg viewBox="0 0 300 900" preserveAspectRatio="xMidYMin slice" '
            'xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' + "".join(parts) + "</svg>")


ART_CSS = """
<style>
.pg-art{position:fixed;top:0;bottom:0;width:22vw;max-width:340px;z-index:0;pointer-events:none;opacity:.2;overflow:hidden;}
.pg-art svg{width:100%;height:100%;display:block;}
.pg-art.l{left:0;-webkit-mask-image:linear-gradient(to right,#000 20%,transparent 100%);mask-image:linear-gradient(to right,#000 20%,transparent 100%);}
.pg-art.r{right:0;-webkit-mask-image:linear-gradient(to left,#000 20%,transparent 100%);mask-image:linear-gradient(to left,#000 20%,transparent 100%);}
.pg-art.r svg{transform:scaleX(-1);}
.stApp [data-testid="stMainBlockContainer"], .block-container{position:relative;z-index:1;}
@media (max-width:900px){.pg-art{display:none;}}
</style>
"""


def art_html() -> str:
    svg = _panel_svg()
    return (ART_CSS + f'<div class="pg-art l" aria-hidden="true">{svg}</div>'
            f'<div class="pg-art r" aria-hidden="true">{svg}</div>')
