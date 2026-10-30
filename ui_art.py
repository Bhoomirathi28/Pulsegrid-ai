"""Decorative folk-art side panels for the light theme.

ORIGINAL flat drawings (no faces, people or deities): one <symbol> per motif, placed with <use>.
Purely visual: a fixed layer behind the page, aria-hidden, ignored by the pointer."""
import math

INK, GOLD, VERM, LEAF, PEACOCK, ROSE, CREAM = "#1B2246", "#E9A93B", "#C8452B", "#2E7D4F", "#1F6F78", "#C85A7C", "#FFFDF8"
S = f'stroke="{INK}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"'
DOTS = f'fill="none" stroke="{CREAM}" stroke-width="2.6" stroke-linecap="round" stroke-dasharray="0.1 6"'


def _rot(a, cx, cy):
    return f'transform="rotate({a} {cx} {cy})"'


def _symbol(id_, vb, body):
    return f'<symbol id="pgm-{id_}" viewBox="{vb}">{body}</symbol>'


def _leaf(x, y, a, s=1.0, fill=LEAF):
    return (f'<path d="M0 0 C6 -9 19 -9 26 0 C19 9 6 9 0 0Z" fill="{fill}" {S} '
            f'transform="translate({x} {y}) rotate({a}) scale({s})"/>')


def _flower_dot(x, y, r=8):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{GOLD}" {S}/><circle cx="{x}" cy="{y}" r="{r / 2.2:.1f}" fill="{VERM}"/>'


def sym_lotus():
    p = ""
    for a, f, ry in ((-62, ROSE, 36), (62, ROSE, 36), (-32, VERM, 38), (32, VERM, 38), (0, GOLD, 42)):
        p += f'<ellipse cx="60" cy="50" rx="12" ry="{ry}" fill="{f}" {S} {_rot(a, 60, 92)}/>'
    p += f'<path d="M28 88 Q60 108 92 88 Q60 96 28 88Z" fill="{LEAF}" {S}/><path d="M60 14 L60 56" {S} stroke-width="1.4" fill="none"/>'
    p += f'<path d="M38 90 Q60 100 82 90" {DOTS}/>'
    return _symbol("lotus", "0 0 120 110", p)


def sym_marigold():
    p = "".join(f'<circle cx="{50 + 31 * math.cos(math.radians(a)):.1f}" cy="{50 + 31 * math.sin(math.radians(a)):.1f}" r="11" fill="{GOLD}" {S}/>'
                for a in range(0, 360, 30))
    p += "".join(f'<circle cx="{50 + 19 * math.cos(math.radians(a)):.1f}" cy="{50 + 19 * math.sin(math.radians(a)):.1f}" r="8" fill="{VERM}" {S}/>'
                 for a in range(15, 375, 45))
    p += f'<circle cx="50" cy="50" r="8" fill="{GOLD}" {S}/><circle cx="50" cy="50" r="2.6" fill="{INK}"/>'
    return _symbol("marigold", "0 0 100 100", p)


def sym_hibiscus():
    p = "".join(f'<ellipse cx="50" cy="26" rx="17" ry="25" fill="{ROSE}" {S} {_rot(a, 50, 50)}/>' for a in range(0, 360, 72))
    p += f'<circle cx="50" cy="50" r="8" fill="{VERM}" {S}/><path d="M50 50 L66 20" {S} fill="none"/>'
    p += "".join(f'<circle cx="{x}" cy="{y}" r="3" fill="{GOLD}" {S} stroke-width="1.4"/>' for x, y in ((66, 20), (60, 26), (72, 26)))
    return _symbol("hibiscus", "0 0 100 100", p)


def sym_jasmine():
    p = ""
    for cx, cy in ((22, 22), (46, 34), (28, 48)):
        p += "".join(f'<ellipse cx="{cx}" cy="{cy - 8}" rx="4.6" ry="8" fill="{CREAM}" {S} stroke-width="1.5" {_rot(a, cx, cy)}/>' for a in range(0, 360, 72))
        p += f'<circle cx="{cx}" cy="{cy}" r="2.6" fill="{GOLD}"/>'
    return _symbol("jasmine", "0 0 64 64", p)


def sym_vine():
    p = f'<path d="M30 0 C62 40 -2 80 30 120 C62 160 -2 200 30 240 C60 275 30 290 30 300" fill="none" {S}/>'
    for y, side in ((20, 1), (60, -1), (100, 1), (140, -1), (180, 1), (220, -1), (262, 1)):
        p += _leaf(30 + side * 6, y, -35 if side > 0 else 215, 1.15)
    for y, sgn in ((44, 1), (130, 1), (210, -1)):
        x = 30 + sgn * 24
        p += f'<path d="M{x} {y} c{10 * sgn} -8 {20 * sgn} 2 {13 * sgn} 11 c{-4 * sgn} 5 {-11 * sgn} 2 {-8 * sgn} -3" fill="none" {S}/>'
    return _symbol("vine", "0 0 60 300", p)


def sym_peacock():
    p = ""
    for a in (-84, -62, -40, -18, 4, 26):
        p += (f'<g transform="translate(78 126) rotate({a})"><path d="M0 0 C-12 -28 -12 -62 0 -84 C12 -62 12 -28 0 0Z" fill="{LEAF}" {S}/>'
              f'<ellipse cx="0" cy="-66" rx="7.5" ry="10" fill="{GOLD}" {S}/><ellipse cx="0" cy="-66" rx="3.6" ry="5.2" fill="{PEACOCK}"/>'
              f'<path d="M0 -12 L0 -48" {DOTS}/></g>')
    p += f'<ellipse cx="104" cy="128" rx="30" ry="19" fill="{PEACOCK}" {S}/><path d="M86 126 Q104 136 122 124" {DOTS}/>'
    p += f'<path d="M122 116 C140 108 132 90 134 76 L142 76 C142 96 152 110 132 126Z" fill="{PEACOCK}" {S}/>'
    p += f'<circle cx="138" cy="70" r="9" fill="{PEACOCK}" {S}/><path d="M146 68 L158 72 L146 75Z" fill="{GOLD}" {S}/><circle cx="141" cy="68" r="2" fill="{CREAM}"/>'
    p += "".join(f'<path d="M138 62 L{x} {y}" {S} fill="none"/><circle cx="{x}" cy="{y}" r="3" fill="{VERM}" {S} stroke-width="1.4"/>'
                 for x, y in ((130, 46), (138, 42), (146, 46)))
    p += f'<path d="M100 146 L96 172 M112 146 L114 172 M92 172 L102 172 M110 172 L120 172" {S} fill="none"/>'
    return _symbol("peacock", "0 0 170 180", p)


def sym_bird():
    p = (f'<path d="M16 30 L1 16 L6 34 Z" fill="{PEACOCK}" {S}/><ellipse cx="30" cy="30" rx="17" ry="11" fill="{VERM}" {S}/>'
         f'<circle cx="46" cy="19" r="7.5" fill="{VERM}" {S}/><path d="M52 17 L61 21 L52 24Z" fill="{GOLD}" {S}/>'
         f'<circle cx="48" cy="17" r="1.8" fill="{CREAM}"/><path d="M20 30 Q32 18 40 32 Q30 38 20 30Z" fill="{GOLD}" {S}/>'
         f'<circle cx="30" cy="30" r="1.6" fill="{INK}"/><path d="M28 40 L28 49 M34 40 L35 49" {S} fill="none"/>')
    return _symbol("bird", "0 0 64 52", p)


def sym_birdpair():
    p = (f'<path d="M4 84 C40 70 80 70 116 84" fill="none" {S}/>'
         + _leaf(24, 78, -150, 0.8) + _leaf(96, 78, -30, 0.8) + _flower_dot(60, 74, 6)
         + '<use href="#pgm-bird" x="4" y="26" width="52" height="42"/>'
         + '<g transform="translate(116 0) scale(-1 1)"><use href="#pgm-bird" x="4" y="26" width="52" height="42"/></g>')
    return _symbol("birdpair", "0 0 120 96", p)


def sym_elephant():
    p = (f'<path d="M38 100 L38 62 C38 38 80 34 112 38 C146 42 152 56 152 74 L152 100Z" fill="{ROSE}" {S}/>'
         + "".join(f'<path d="M{x} 98 L{x} 132 Q{x + 9} 138 {x + 18} 132 L{x + 18} 98Z" fill="{ROSE}" {S}/>'
                   f'<path d="M{x + 1} 128 L{x + 17} 128" {DOTS}/>' for x in (46, 72, 118, 136))
         + f'<path d="M38 66 Q28 80 32 98" fill="none" {S}/><circle cx="32" cy="100" r="3" fill="{GOLD}" {S}/>'
         f'<path d="M150 50 C170 38 198 50 198 76 C198 86 192 96 186 96 C192 110 196 124 186 134 C178 140 170 134 174 126 '
         f'C178 116 174 106 166 98 C156 96 148 80 150 50Z" fill="{ROSE}" {S}/>'
         f'<ellipse cx="156" cy="72" rx="11" ry="19" fill="{GOLD}" {S} {_rot(10, 156, 72)}/>'
         f'<path d="M181 84 Q205 90 200 112" fill="none" stroke="{CREAM}" stroke-width="5" stroke-linecap="round"/>'
         f'<path d="M181 84 Q205 90 200 112" fill="none" {S} stroke-width="1.4"/>'
         f'<circle cx="177" cy="62" r="2.6" fill="{INK}"/><path d="M156 44 Q172 34 190 46" {DOTS}/>'
         f'<path d="M58 40 L128 40 L134 82 Q96 92 52 82Z" fill="{GOLD}" {S}/>'
         f'<path d="M64 48 L124 48 L128 76 Q96 84 60 76Z" fill="{VERM}" {S} stroke-width="1.4"/>'
         f'<path d="M66 54 L122 54 M66 70 Q96 76 124 70" {DOTS}/><circle cx="94" cy="62" r="6" fill="{GOLD}" {S} stroke-width="1.4"/>'
         + "".join(f'<circle cx="{x}" cy="84" r="5" fill="{PEACOCK}" {S} stroke-width="1.4"/>' for x in (66, 80, 94, 108, 122)))
    return _symbol("elephant", "0 0 210 142", p)


def _fish():
    scales = "".join(f'<path d="M{x} {y - 6} Q{x + 6} {y} {x} {y + 6}" fill="none" stroke="{INK}" stroke-width="1.4" stroke-linecap="round"/>'
                     for x, y in ((40, 50), (40, 40), (40, 60), (52, 50), (52, 40), (52, 60), (64, 50)))
    return (f'<path d="M84 50 L112 32 Q106 50 112 68Z" fill="{PEACOCK}" {S}/>'
            f'<path d="M8 50 Q46 8 88 50 Q46 92 8 50Z" fill="{GOLD}" {S}/>' + scales +
            f'<circle cx="24" cy="46" r="5" fill="{CREAM}" {S} stroke-width="1.4"/><circle cx="24" cy="46" r="1.8" fill="{INK}"/>'
            f'<path d="M30 30 Q46 22 58 30" {DOTS}/>')


def sym_fishpair():
    return _symbol("fishpair", "0 0 120 200",
                   f'<g transform="scale(1 .82)">{_fish()}</g>'
                   f'<g transform="translate(120 200) rotate(180) scale(1 .82)">{_fish()}</g>')


def sym_paisley():
    p = (f'<path d="M40 4 C72 14 78 56 54 82 C36 100 8 86 14 62 C18 46 38 48 40 62 C41 70 32 72 32 64 C30 76 50 74 54 58 C58 34 40 28 40 4Z" fill="{PEACOCK}" {S}/>'
         f'<path d="M40 14 C60 24 62 52 46 70" {DOTS}/>')
    p += "".join(f'<circle cx="{x}" cy="{y}" r="3.2" fill="{GOLD}" {S} stroke-width="1.2"/>' for x, y in ((34, 40), (46, 28), (52, 50), (26, 74)))
    return _symbol("paisley", "0 0 80 100", p)


def sym_sun():
    rays = "".join(f'<path d="M50 4 L58 22 L42 22Z" fill="{VERM}" {S} stroke-width="1.6" {_rot(a, 50, 50)}/>' for a in range(0, 360, 30))
    p = (rays + f'<circle cx="50" cy="50" r="27" fill="{GOLD}" {S}/><circle cx="50" cy="50" r="17" fill="{VERM}" {S}/>'
         f'<circle cx="50" cy="50" r="22" {DOTS}/><circle cx="50" cy="50" r="5" fill="{GOLD}"/>')
    return _symbol("sun", "0 0 100 100", p)


def sym_kolam():
    d = "".join(f'<circle cx="{30 + dx * 14}" cy="{30 + dy * 14}" r="3" fill="{INK}"/>' for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx + dy) % 2 == 0)
    return _symbol("kolam", "0 0 60 60", f'<polygon points="30,6 54,30 30,54 6,30" fill="none" stroke="{GOLD}" stroke-width="2.4"/>' + d)


def sym_tree():
    p = f'<path d="M100 330 C92 270 108 230 100 170 C95 130 102 100 100 56" fill="none" {S} stroke-width="3.4"/>'
    branches = [((100, 262), (66, 252), (36, 228), (22, 196)), ((100, 214), (70, 204), (46, 180), (38, 146)),
                ((100, 166), (78, 152), (62, 128), (58, 96)), ((100, 120), (84, 108), (76, 90), (78, 70))]
    for (x0, y0), (cx, cy), (c2x, c2y), (x1, y1) in branches:
        for sgn in (1, -1):
            def f(x):
                return 100 + sgn * (x - 100)
            p += f'<path d="M{f(x0)} {y0} C{f(cx)} {cy} {f(c2x)} {c2y} {f(x1)} {y1}" fill="none" {S}/>'
            p += _flower_dot(f(x1), y1 - 4, 9)
            for t, ang in ((0.45, -50), (0.72, -20)):
                lx = (1 - t) * f(x0) + t * f(x1)
                ly = (1 - t) * y0 + t * y1
                p += _leaf(round(lx, 1), round(ly, 1), (ang if sgn > 0 else 180 - ang) + (20 if t > .5 else -20), 1.1)
    p += f'<circle cx="100" cy="42" r="16" fill="{GOLD}" {S}/><circle cx="100" cy="42" r="8" fill="{VERM}" {S}/>'
    p += "".join(f'<circle cx="{100 + 24 * math.cos(math.radians(a)):.1f}" cy="{42 + 24 * math.sin(math.radians(a)):.1f}" r="3" fill="{GOLD}" {S} stroke-width="1.2"/>'
                 for a in range(0, 360, 45))
    p += f'<ellipse cx="100" cy="334" rx="62" ry="13" fill="{GOLD}" {S}/><path d="M52 334 Q100 346 148 334" {DOTS}/>'
    p += _leaf(60, 322, -150, 1.1) + _leaf(140, 322, -30, 1.1)
    return _symbol("tree", "0 0 200 350", p)


SYMBOLS = [sym_lotus(), sym_marigold(), sym_hibiscus(), sym_jasmine(), sym_vine(), sym_peacock(), sym_bird(), sym_birdpair(),
           sym_elephant(), sym_fishpair(), sym_paisley(), sym_sun(), sym_kolam(), sym_tree()]


def _u(id_, x, y, w, h):
    return f'<use href="#pgm-{id_}" x="{x}" y="{y}" width="{w}" height="{h}"/>'


def _panel(items: str) -> str:
    return ('<svg viewBox="0 0 300 900" preserveAspectRatio="xMidYMin slice" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
            + items + "</svg>")


def _left() -> str:
    """Tree of life with peacock, lotus and vines."""
    return _panel(
        _u("vine", -20, 0, 54, 270) + _u("vine", -14, 560, 54, 270) + _u("marigold", 228, 18, 52, 52) + _u("kolam", 236, 78, 40, 40)
        + _u("sun", 202, 112, 66, 66) + _u("peacock", 56, 70, 190, 202)
        + _u("tree", 20, 280, 262, 450) + _u("jasmine", 232, 330, 50, 50) + _u("hibiscus", 16, 300, 62, 62)
        + _u("lotus", 66, 742, 170, 156) + _u("kolam", 12, 842, 46, 46) + _u("marigold", 242, 800, 46, 46))


def _right() -> str:
    """Elephant, marigolds, folk birds, fish and paisleys."""
    return _panel(
        _u("marigold", 18, 14, 48, 48) + _u("kolam", 74, 20, 36, 36) + _u("elephant", 30, 72, 262, 178)
        + _u("marigold", 40, 262, 60, 60) + _u("marigold", 206, 290, 50, 50) + _u("paisley", 110, 256, 58, 72)
        + _u("birdpair", 56, 354, 190, 150) + _u("jasmine", 14, 400, 52, 52)
        + _u("fishpair", 98, 520, 96, 160) + _u("paisley", 14, 560, 62, 78) + _u("paisley", 212, 600, 62, 78)
        + _u("hibiscus", 30, 704, 74, 74) + _u("sun", 198, 720, 74, 74) + _u("kolam", 14, 820, 44, 44) + _u("marigold", 236, 826, 52, 52))


ART_CSS = """
<style>
.pg-art{position:fixed;top:0;bottom:0;width:22vw;max-width:340px;z-index:0;pointer-events:none;opacity:.18;overflow:hidden;}
.pg-art svg{width:100%;height:100%;display:block;}
.pg-art.l{left:0;-webkit-mask-image:linear-gradient(to right,#000 35%,transparent 100%);mask-image:linear-gradient(to right,#000 35%,transparent 100%);}
.pg-art.r{right:0;-webkit-mask-image:linear-gradient(to left,#000 35%,transparent 100%);mask-image:linear-gradient(to left,#000 35%,transparent 100%);}
.pg-sprite{position:absolute;width:0;height:0;overflow:hidden;}
.stApp [data-testid="stMainBlockContainer"], .block-container{position:relative;z-index:1;}
@media (max-width:900px){.pg-art{display:none;}}
</style>
"""


def art_html() -> str:
    sprite = f'<svg class="pg-sprite" aria-hidden="true"><defs>{"".join(SYMBOLS)}</defs></svg>'
    return (ART_CSS + sprite + f'<div class="pg-art l" aria-hidden="true">{_left()}</div>'
            f'<div class="pg-art r" aria-hidden="true">{_right()}</div>')
