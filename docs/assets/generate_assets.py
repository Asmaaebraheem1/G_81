"""Generate CarbonWise's original flat-illustration asset set.

The project ships no third-party stock photography. Every asset is original
vector-style artwork produced by this script, so the licence is clean and the
palette stays consistent in both LTR and RTL layouts. Images contain no text.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

S = 2  # supersampling factor
W, H = 1600, 900

CREAM = "#F7F3EA"
INK = "#12332A"
DEEP = "#0B3D2E"
GREEN = "#1F7A5C"
LIME = "#7BC96F"
MINT = "#CDE8D5"
SKY = "#DCEEF2"
SAND = "#EAD9BE"
CORAL = "#E07A5F"
SUN = "#F2CC8F"
WHITE = "#FFFFFF"
STEEL = "#9DB4AE"

ROOT = Path(__file__).resolve().parents[2]
TARGETS = [
    ROOT / "mobile" / "assets" / "images",
    ROOT / "backend" / "app" / "static" / "assets" / "images",
]


class Pen:
    def __init__(self) -> None:
        self.image = Image.new("RGB", (W * S, H * S), CREAM)
        self.d = ImageDraw.Draw(self.image)

    def _box(self, box):
        return tuple(int(v * S) for v in box)

    def rect(self, box, fill, outline=None, width=0):
        self.d.rectangle(self._box(box), fill=fill, outline=outline, width=int(width * S))

    def rrect(self, box, radius, fill, outline=None, width=0):
        self.d.rounded_rectangle(
            self._box(box), radius=radius * S, fill=fill, outline=outline, width=int(width * S)
        )

    def ellipse(self, box, fill, outline=None, width=0):
        self.d.ellipse(self._box(box), fill=fill, outline=outline, width=int(width * S))

    def poly(self, points, fill, outline=None):
        pts = [(int(x * S), int(y * S)) for x, y in points]
        self.d.polygon(pts, fill=fill, outline=outline)

    def line(self, points, fill=INK, width=4):
        pts = [(int(x * S), int(y * S)) for x, y in points]
        self.d.line(pts, fill=fill, width=int(width * S), joint="curve")

    def arc(self, box, start, end, fill=INK, width=4):
        self.d.arc(self._box(box), start=start, end=end, fill=fill, width=int(width * S))

    def leaf(self, cx, cy, length=120, angle=45, fill=LIME, stem=True):
        import math

        rad = math.radians(angle)
        ux, uy = math.cos(rad), math.sin(rad)
        px, py = -uy, ux
        tip = (cx + ux * length / 2, cy + uy * length / 2)
        base = (cx - ux * length / 2, cy - uy * length / 2)
        left = (cx + px * length * 0.28, cy + py * length * 0.28)
        right = (cx - px * length * 0.28, cy - py * length * 0.28)
        self.poly([tip, left, base, right], fill)
        if stem:
            self.line([base, tip], fill=DEEP, width=max(2, length // 40))

    def sun(self, cx, cy, radius=90):
        self.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), SUN)

    def cloud(self, cx, cy, scale=1.0, fill=WHITE):
        self.ellipse((cx - 90 * scale, cy - 28 * scale, cx - 20 * scale, cy + 36 * scale), fill)
        self.ellipse((cx - 42 * scale, cy - 55 * scale, cx + 42 * scale, cy + 30 * scale), fill)
        self.ellipse((cx + 10 * scale, cy - 25 * scale, cx + 85 * scale, cy + 38 * scale), fill)
        self.rrect((cx - 90 * scale, cy + 8 * scale, cx + 85 * scale, cy + 38 * scale), 16 * scale, fill)

    def hill(self, y, amp, fill):
        points = [(-20, H + 20)]
        for x in range(-20, W + 60, 40):
            import math

            points.append((x, y + math.sin(x / 170) * amp))
        points.append((W + 20, H + 20))
        self.poly(points, fill)

    def tree(self, x, ground, size=1.0, canopy=LIME):
        self.rect((x - 10 * size, ground - 80 * size, x + 10 * size, ground), "#7A5230")
        self.ellipse((x - 70 * size, ground - 210 * size, x + 70 * size, ground - 70 * size), canopy)
        self.ellipse((x - 45 * size, ground - 250 * size, x + 40 * size, ground - 150 * size), canopy)

    def turbine(self, x, ground, height=330, scale=1.0):
        self.poly(
            [(x - 8 * scale, ground), (x + 8 * scale, ground), (x + 4 * scale, ground - height), (x - 4 * scale, ground - height)],
            STEEL,
        )
        hub = (x, ground - height)
        self.ellipse((hub[0] - 12 * scale, hub[1] - 12 * scale, hub[0] + 12 * scale, hub[1] + 12 * scale), DEEP)
        import math

        for angle in (-90, 30, 150):
            rad = math.radians(angle)
            end = (hub[0] + math.cos(rad) * 115 * scale, hub[1] + math.sin(rad) * 115 * scale)
            self.line([hub, end], fill=STEEL, width=9 * scale)

    def solar_panel(self, x, y, w, h, tilt=10):
        self.poly([(x, y + tilt), (x + w, y), (x + w + 20, y + h), (x + 20, y + h + tilt)], "#2F6F8F")
        for i in range(1, 4):
            self.line([(x + w * i / 4, y + tilt * (1 - i / 4)), (x + 20 + w * i / 4, y + h + tilt * (1 - i / 4))], fill=SKY, width=3)
        self.line([(x + 10, y + h * 0.55), (x + w + 10, y + h * 0.55)], fill=SKY, width=3)
        self.line([(x + 12, y + h + tilt), (x + 8, y + h + 70)], fill=STEEL, width=8)
        self.line([(x + w - 25, y + h), (x + w - 20, y + h + 70)], fill=STEEL, width=8)

    def house(self, x, ground, w=300, h=220, roof=GREEN):
        self.rect((x, ground - h, x + w, ground), SAND)
        self.poly([(x - 30, ground - h), (x + w / 2, ground - h - 120), (x + w + 30, ground - h)], DEEP)
        self.poly([(x + 20, ground - h + 10), (x + w / 2, ground - h - 80), (x + w - 20, ground - h + 10)], roof)
        self.rect((x + 40, ground - h + 70, x + 110, ground - 40), SKY)
        self.rect((x + w - 100, ground - 75, x + w - 40, ground), GREEN)

    def person(self, x, ground, shirt=GREEN, skin="#C98E6B", scale=1.0):
        self.ellipse((x - 20 * scale, ground - 170 * scale, x + 20 * scale, ground - 130 * scale), skin)
        self.rrect((x - 30 * scale, ground - 130 * scale, x + 30 * scale, ground - 55 * scale), 14 * scale, shirt)
        self.line([(x - 15 * scale, ground - 60 * scale), (x - 24 * scale, ground)], fill=INK, width=9 * scale)
        self.line([(x + 15 * scale, ground - 60 * scale), (x + 24 * scale, ground)], fill=INK, width=9 * scale)
        self.line([(x - 28 * scale, ground - 110 * scale), (x - 56 * scale, ground - 80 * scale)], fill=shirt, width=9 * scale)
        self.line([(x + 28 * scale, ground - 110 * scale), (x + 56 * scale, ground - 80 * scale)], fill=shirt, width=9 * scale)

    def bike(self, x, ground, scale=1.0):
        r = 48 * scale
        for cx in (x - 70 * scale, x + 70 * scale):
            self.ellipse((cx - r, ground - 2 * r, cx + r, ground), None, outline=INK, width=5 * scale)
        self.line([(x - 70 * scale, ground - r), (x - 10 * scale, ground - r), (x + 20 * scale, ground - 2 * r), (x + 70 * scale, ground - r)], fill=INK, width=5 * scale)
        self.line([(x - 10 * scale, ground - r), (x + 35 * scale, ground - 2 * r)], fill=INK, width=5 * scale)
        self.line([(x - 35 * scale, ground - 2 * r), (x + 28 * scale, ground - 2 * r)], fill=INK, width=5 * scale)
        self.line([(x + 35 * scale, ground - 2 * r), (x + 55 * scale, ground - 2.4 * r)], fill=INK, width=5 * scale)

    def plane(self, cx, cy, scale=1.0):
        self.poly(
            [(cx - 220 * scale, cy), (cx + 180 * scale, cy - 30 * scale), (cx + 220 * scale, cy - 5 * scale), (cx + 200 * scale, cy + 25 * scale), (cx - 120 * scale, cy + 35 * scale)],
            WHITE,
            outline=STEEL,
        )
        self.poly([(cx - 40 * scale, cy + 5 * scale), (cx + 40 * scale, cy + 140 * scale), (cx + 100 * scale, cy + 140 * scale), (cx + 60 * scale, cy + 8 * scale)], WHITE, outline=STEEL)
        self.poly([(cx - 100 * scale, cy - 15 * scale), (cx - 40 * scale, cy - 120 * scale), (cx + 10 * scale, cy - 120 * scale), (cx - 10 * scale, cy - 12 * scale)], WHITE, outline=STEEL)
        self.poly([(cx - 220 * scale, cy), (cx - 170 * scale, cy - 35 * scale), (cx - 130 * scale, cy - 32 * scale), (cx - 160 * scale, cy + 5 * scale)], CORAL)
        self.ellipse((cx + 80 * scale, cy - 20 * scale, cx + 140 * scale, cy + 8 * scale), SKY)

    def drop(self, cx, cy, r=150):
        self.poly([(cx, cy - r * 1.55), (cx + r * 0.92, cy + r * 0.30), (cx + r * 0.55, cy + r), (cx - r * 0.55, cy + r), (cx - r * 0.92, cy + r * 0.30)], "#4FA3C7")
        self.ellipse((cx - r * 0.45, cy + r * 0.05, cx + r * 0.15, cy + r * 0.55), "#8FD0E8")

    def bin(self, x, ground, w=150, h=210, fill=GREEN):
        self.poly([(x, ground - h), (x + w, ground - h), (x + w - 16, ground), (x + 16, ground)], fill)
        self.rrect((x - 10, ground - h - 26, x + w + 10, ground - h + 4), 8, DEEP)
        for i in range(1, 4):
            self.line([(x + w * i / 4, ground - h + 20), (x + w * i / 4 - 4, ground - 20)], fill=WHITE, width=3)

    def chart(self, baseline=700):
        values = (170, 250, 210, 330, 420)
        for index, value in enumerate(values):
            x = 520 + index * 130
            self.rrect((x, baseline - value, x + 70, baseline), 10, GREEN if index < 3 else LIME)

    def badge(self, cx, cy, r=110, fill=WHITE, icon=LIME):
        self.ellipse((cx - r, cy - r, cx + r, cy + r), fill)
        self.arc((cx - r + 18, cy - r + 18, cx + r - 18, cy + r - 18), 20, 340, fill=icon, width=10)

    def save(self, name: str) -> None:
        out = self.image.resize((W, H), Image.LANCZOS).convert("RGB")
        for folder in TARGETS:
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / f"{name}.webp"
            out.save(path, "WEBP", quality=86, method=6)
            print(f"wrote {path.relative_to(ROOT)} ({path.stat().st_size} bytes)")


def base(p: Pen) -> None:
    p.rect((0, 0, W, H), CREAM)
    p.ellipse((1050, -240, 1750, 460), SKY)
    p.sun(1330, 170, 95)


def hero() -> None:
    p = Pen()
    base(p)
    p.sun(260, 180, 105)
    p.hill(640, 26, MINT)
    p.hill(720, 30, GREEN)
    p.hill(810, 18, DEEP)
    p.turbine(420, 720, 360, 1.05)
    p.turbine(620, 750, 280, 0.85)
    p.turbine(170, 760, 250, 0.75)
    p.solar_panel(1030, 610, 380, 150, 12)
    p.house(1180, 780, 260, 180)
    p.cloud(820, 180, 0.8)
    p.cloud(520, 120, 0.55)
    p.leaf(940, 330, 120, -35, LIME)
    p.save("hero-renewable-energy")


def onboarding_climate() -> None:
    p = Pen()
    base(p)
    p.ellipse((360, 170, 960, 770), SKY)
    p.ellipse((410, 220, 910, 720), "#4FA3C7")
    # simplified continents
    p.poly([(500, 320), (590, 290), (650, 350), (620, 430), (540, 460), (490, 400)], LIME)
    p.poly([(660, 470), (760, 440), (840, 500), (820, 610), (730, 650), (650, 580)], LIME)
    p.poly([(450, 500), (510, 480), (540, 560), (500, 640), (430, 610)], GREEN)
    p.leaf(1020, 300, 150, -35, GREEN)
    p.leaf(1120, 420, 130, 20, LIME)
    p.leaf(950, 520, 110, 60, LIME)
    p.hill(780, 16, MINT)
    p.save("onboarding-climate")


def onboarding_transport() -> None:
    p = Pen()
    base(p)
    # skyline
    for x, w, h in [(160, 110, 230), (280, 90, 300), (380, 140, 210), (530, 100, 340), (640, 120, 260)]:
        p.rrect((x, 620 - h, x + w, 620), 6, SAND)
        for wy in range(620 - h + 30, 590, 55):
            p.rect((x + 20, wy, x + w - 20, wy + 22), SKY)
    p.rect((0, 620, W, 900), "#D8CDBB")
    p.rect((0, 730, W, 900), "#C7BBA6")
    p.line([(120, 800), (1480, 800)], fill=WHITE, width=8)
    for x in range(160, 1460, 120):
        p.line([(x, 800), (x + 50, 800)], fill=SUN, width=8)
    p.bike(1130, 825, 1.2)
    p.person(1130, 820, CORAL, scale=1.15)
    p.tree(250, 700, 0.9, LIME)
    p.tree(1420, 700, 0.8, GREEN)
    p.sun(1370, 160, 80)
    p.cloud(600, 160, 0.7)
    p.save("onboarding-transport")


def onboarding_energy() -> None:
    p = Pen()
    base(p)
    p.hill(760, 18, MINT)
    p.house(520, 760, 430, 300, LIME)
    p.solar_panel(760, 520, 210, 85, 8)
    p.sun(1180, 240, 95)
    p.leaf(300, 430, 130, -40, GREEN)
    p.leaf(390, 540, 100, 20, LIME)
    p.tree(1050, 760, 0.9, GREEN)
    p.tree(1420, 770, 0.7, LIME)
    p.save("onboarding-energy")


def empty_records() -> None:
    p = Pen()
    base(p)
    p.rrect((520, 180, 1080, 800), 24, WHITE, INK, 4)
    p.rrect((610, 240, 990, 330), 12, MINT)
    p.rect((610, 240, 680, 330), GREEN)
    for y in (390, 480, 570, 660):
        p.line([(610, y), (800, y)], fill=STEEL, width=8)
        p.ellipse((860, y - 18, 896, y + 18), None, outline=GREEN, width=5)
    p.leaf(1150, 300, 140, -30, LIME)
    p.leaf(1230, 430, 110, 30, GREEN)
    p.ellipse((260, 560, 440, 740), SUN)
    p.save("empty-records")


def empty_reports() -> None:
    p = Pen()
    base(p)
    p.rrect((420, 150, 1220, 790), 26, WHITE, INK, 4)
    p.line([(500, 700), (1130, 700)], fill=INK, width=6)
    p.line([(500, 700), (500, 250)], fill=INK, width=6)
    p.chart(690)
    p.line([(530, 470), (700, 360), (880, 400), (1080, 260)], fill=CORAL, width=8)
    p.ellipse((1070, 250, 1090, 270), CORAL)
    p.leaf(1280, 260, 120, -35, LIME)
    p.leaf(1280, 620, 100, 35, GREEN)
    p.ellipse((240, 260, 380, 400), MINT)
    p.save("empty-reports")


def empty_challenges() -> None:
    p = Pen()
    base(p)
    p.hill(780, 14, MINT)
    p.tree(800, 780, 1.25, GREEN)
    p.poly([(790, 560), (810, 560), (810, 400), (790, 400)], INK)
    p.poly([(810, 410), (950, 450), (810, 500)], CORAL)
    p.person(470, 790, GREEN, scale=1.0)
    p.person(1130, 790, CORAL, scale=1.0)
    p.person(300, 810, LIME, scale=0.8)
    p.person(1300, 810, GREEN, scale=0.8)
    p.sun(1310, 180, 80)
    p.cloud(420, 170, 0.7)
    p.save("empty-challenges")


def category_electricity() -> None:
    p = Pen()
    base(p)
    p.hill(760, 12, MINT)
    p.solar_panel(430, 400, 560, 230, 16)
    p.ellipse((1040, 500, 1220, 680), WHITE)
    p.poly(
        [(1120, 520), (1060, 600), (1105, 600), (1085, 665), (1160, 575), (1115, 575)],
        GREEN,
    )
    p.sun(1180, 230, 100)
    p.leaf(280, 560, 110, -35, LIME)
    p.save("category-electricity")


def category_transport() -> None:
    p = Pen()
    base(p)
    p.rect((0, 680, W, 900), "#D8CDBB")
    p.rrect((520, 300, 1100, 680), 26, GREEN)
    p.rect((560, 350, 1060, 500), SKY)
    for x in (600, 740, 880, 1020):
        p.rect((x, 350, x + 70, 500), WHITE)
    p.ellipse((600, 640, 690, 730), INK)
    p.ellipse((930, 640, 1020, 730), INK)
    p.rect((560, 520, 1060, 550), LIME)
    p.bike(300, 760, 1.0)
    p.sun(1300, 170, 80)
    p.save("category-transport")


def category_flights() -> None:
    p = Pen()
    base(p)
    p.cloud(380, 260, 1.2)
    p.cloud(1180, 420, 1.4)
    p.cloud(760, 700, 1.0)
    p.plane(760, 400, 1.25)
    p.line([(980, 540), (1180, 650)], fill=LIME, width=6)
    p.leaf(1220, 680, 90, 30, LIME)
    p.save("category-flights")


def category_water() -> None:
    p = Pen()
    base(p)
    p.drop(800, 390, 190)
    for y in (700, 760, 820):
        p.arc((380, y - 70, 1220, y + 70), 200, 340, fill="#4FA3C7", width=6)
    p.leaf(1180, 250, 120, -35, LIME)
    p.leaf(360, 600, 110, 30, GREEN)
    p.save("category-water")


def category_waste() -> None:
    p = Pen()
    base(p)
    p.bin(480, 780, 170, 240, GREEN)
    p.bin(710, 780, 170, 240, LIME)
    p.bin(940, 780, 170, 240, SAND)
    p.arc((660, 250, 900, 490), 40, 330, fill=GREEN, width=12)
    import math

    angle = math.radians(330)
    cx, cy, rx, ry = 780, 370, 120, 120
    tip = (cx + rx * math.cos(angle), cy + ry * math.sin(angle))
    tangent = (-math.sin(angle), math.cos(angle))
    normal = (math.cos(angle), math.sin(angle))
    length = 30
    p.poly(
        [
            tip,
            (tip[0] - tangent[0] * length + normal[0] * 12, tip[1] - tangent[1] * length + normal[1] * 12),
            (tip[0] - tangent[0] * length - normal[0] * 12, tip[1] - tangent[1] * length - normal[1] * 12),
        ],
        GREEN,
    )
    p.leaf(1120, 260, 120, -35, LIME)
    p.save("category-waste")


def category_household() -> None:
    p = Pen()
    base(p)
    p.hill(780, 12, MINT)
    p.house(540, 780, 420, 290, GREEN)
    p.solar_panel(780, 570, 160, 70, 8)
    p.badge(1120, 430, 120, WHITE, GREEN)
    p.leaf(1120, 430, 110, -45, GREEN)
    p.leaf(300, 540, 110, -35, LIME)
    p.save("category-household")


def challenge_community() -> None:
    p = Pen()
    base(p)
    p.hill(790, 14, MINT)
    p.person(430, 800, GREEN)
    p.person(620, 820, LIME, scale=0.9)
    p.person(1170, 800, CORAL)
    p.leaf(800, 620, 180, -50, LIME)
    p.line([(800, 780), (800, 620)], fill="#7A5230", width=10)
    p.ellipse((710, 760, 890, 800), "#7A5230")
    p.sun(1320, 180, 80)
    p.save("challenge-community")


def content_climate() -> None:
    p = Pen()
    base(p)
    p.poly([(380, 640), (800, 700), (800, 260), (380, 210)], WHITE)
    p.poly([(1220, 640), (800, 700), (800, 260), (1220, 210)], WHITE)
    p.line([(800, 260), (800, 700)], fill=INK, width=5)
    p.ellipse((560, 320, 760, 520), SKY)
    p.poly([(590, 400), (650, 370), (720, 430), (680, 470), (610, 450)], LIME)
    p.leaf(1010, 400, 150, -45, GREEN)
    p.leaf(980, 540, 110, 25, LIME)
    p.sun(1250, 180, 80)
    p.save("content-climate")


def main() -> None:
    for maker in (
        hero,
        onboarding_climate,
        onboarding_transport,
        onboarding_energy,
        empty_records,
        empty_reports,
        empty_challenges,
        category_electricity,
        category_transport,
        category_flights,
        category_water,
        category_waste,
        category_household,
        challenge_community,
        content_climate,
    ):
        maker()


if __name__ == "__main__":
    main()
