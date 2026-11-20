"""Generate the five black-and-white CarbonWise system diagrams.

Fallback for environments without Graphviz/PlantUML. Pillow is already in the
backend dev environment. Output: docs/diagrams/*.png at 300 DPI.

Design constraints: white background, black strokes/text only, no colour.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT
FONT_REGULAR = r"C:\Windows\Fonts\arial.ttf"
FONT_BOLD = r"C:\Windows\Fonts\arialbd.ttf"
DPI = (300, 300)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REGULAR, size)


def canvas(width: int, height: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (width, height), "white")
    return image, ImageDraw.Draw(image)


def header(draw: ImageDraw.ImageDraw, width: int, title: str, subtitle: str) -> None:
    draw.text((90, 70), title, font=font(44, True), fill="black")
    draw.text((92, 132), subtitle, font=font(22), fill="black")
    draw.line((90, 178, width - 90, 178), fill="black", width=3)


def footer(draw: ImageDraw.ImageDraw, width: int, height: int, text: str) -> None:
    draw.line((90, height - 70, width - 90, height - 70), fill="black", width=1)
    draw.text((90, height - 52), text, font=font(16), fill="black")
    draw.text((width - 360, height - 52), "CarbonWise v1.0", font=font(16), fill="black")


def rounded(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    lines: tuple[str, ...] = (),
    *,
    title_size: int = 26,
    body_size: int = 19,
    radius: int = 14,
    fill: str = "white",
    width: int = 3,
    header_fill: str | None = None,
    align: str = "center",
    pad: int = 16,
) -> None:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=radius, outline="black", fill=fill, width=width)
    title_font = font(title_size, True)
    body_font = font(body_size)
    if header_fill:
        header_h = title_size + 24
        draw.rounded_rectangle(
            (x0, y0, x1, y0 + header_h), radius=radius, fill=header_fill, outline="black", width=width
        )
        draw.rectangle((x0, y0 + header_h - radius, x1, y0 + header_h), fill=header_fill)
        draw.text(
            ((x0 + x1) / 2, y0 + header_h / 2),
            title,
            font=title_font,
            fill="white",
            anchor="mm",
            align="center",
        )
        text_y = y0 + header_h + pad
    else:
        draw.multiline_text(
            ((x0 + x1) / 2, y0 + pad + title_size / 2),
            title,
            font=title_font,
            fill="black",
            anchor="ma" if align == "center" else "la",
            align="center",
            spacing=4,
        )
        text_y = y0 + pad + title_size * (title.count("\n") + 1) + 22
    if lines:
        draw.multiline_text(
            ((x0 + x1) / 2, text_y),
            "\n".join(lines),
            font=body_font,
            fill="black",
            anchor="ma",
            align="center",
            spacing=6,
        )


def label(draw: ImageDraw.ImageDraw, xy: tuple[float, float], text: str, *, size: int = 17) -> None:
    f = font(size)
    lines = text.split("\n")
    widths, heights = [], []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=f)
        widths.append(bbox[2] - bbox[0])
        heights.append(bbox[3] - bbox[1])
    w = max(widths) + 12
    h = sum(heights) + 8 * len(lines) + 6
    x, y = xy
    draw.rectangle((x - w / 2, y - h / 2, x + w / 2, y + h / 2), fill="white")
    draw.multiline_text((x, y), text, font=f, fill="black", anchor="mm", align="center", spacing=4)


def arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    text: str | None = None,
    width: int = 3,
    head: int = 22,
    label_at: float = 0.5,
    label_offset: tuple[float, float] = (0, 0),
) -> None:
    draw.line((start, end), fill="black", width=width)
    sx, sy = start
    ex, ey = end
    dx, dy = ex - sx, ey - sy
    length = max((dx * dx + dy * dy) ** 0.5, 1e-6)
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    tip = (ex, ey)
    base = (ex - ux * head, ey - uy * head)
    left = (base[0] + px * head * 0.45, base[1] + py * head * 0.45)
    right = (base[0] - px * head * 0.45, base[1] - py * head * 0.45)
    draw.polygon([tip, left, right], fill="black")
    if text:
        lx = sx + dx * label_at + label_offset[0]
        ly = sy + dy * label_at + label_offset[1]
        label(draw, (lx, ly), text)


def orthogonal(
    draw: ImageDraw.ImageDraw,
    points: list[tuple[float, float]],
    *,
    text: str | None = None,
    width: int = 3,
) -> None:
    for a, b in zip(points, points[1:]):
        draw.line((a, b), fill="black", width=width)
    # Arrowhead on the final segment.
    sx, sy = points[-2]
    ex, ey = points[-1]
    dx, dy = ex - sx, ey - sy
    length = max((dx * dx + dy * dy) ** 0.5, 1e-6)
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    tip = (ex, ey)
    base = (ex - ux * 20, ey - uy * 20)
    draw.polygon(
        [tip, (base[0] + px * 9, base[1] + py * 9), (base[0] - px * 9, base[1] - py * 9)],
        fill="black",
    )
    if text:
        mid = points[len(points) // 2]
        label(draw, (mid[0], mid[1] - 24), text)


def context_diagram() -> None:
    w, h = 2400, 1700
    image, d = canvas(w, h)
    header(d, w, "1. Context Diagram", "CarbonWise — system boundary, actors, and external data flows")
    cx, cy = 1200, 860
    d.ellipse((930, 640, 1470, 1080), outline="black", fill="white", width=5)
    d.ellipse((955, 665, 1445, 1055), outline="black", width=1)
    d.multiline_text(
        (cx, cy - 40),
        "CarbonWise\nEmissions Analysis &\nReduction Planning",
        font=font(30, True),
        fill="black",
        anchor="mm",
        align="center",
        spacing=8,
    )
    d.multiline_text(
        (cx, cy + 100),
        "Backend owns every\ncalculated emission value",
        font=font(17),
        fill="black",
        anchor="mm",
        align="center",
        spacing=4,
    )

    rounded(d, (120, 330, 560, 510), "Individual /\nhousehold user", ("records, goals, consent",), title_size=25)
    rounded(d, (120, 1140, 560, 1340), "Organization user", ("profile, shared records,\nreports, plans",), title_size=25)
    rounded(d, (1840, 330, 2280, 530), "Admin / content editor", ("catalog, factors, content,\nAI settings, audit",), title_size=25)
    rounded(
        d,
        (1840, 1140, 2280, 1360),
        "OpenRouter API",
        ("openrouter/free only\nno training · no key on device",),
        title_size=25,
    )

    arrow(d, (560, 410), (965, 690), text="profile, activity data,\nfeedback", label_offset=(-40, 30))
    arrow(d, (1010, 640), (560, 370), text="kg CO2e, reports,\ngoals, plans", label_offset=(-60, -40))
    arrow(d, (560, 1235), (960, 1020), text="org profile,\nshared activity", label_offset=(-40, 35))
    arrow(d, (1020, 1065), (560, 1285), text="org reports,\nplan progress", label_offset=(-60, 45))
    arrow(d, (1840, 420), (1435, 680), text="catalog, factors,\ncontent, AI policy", label_offset=(60, 20))
    arrow(d, (1450, 700), (1840, 350), text="usage, audit log,\nflagged output", label_offset=(55, -30))
    arrow(d, (1445, 940), (1840, 1210), text="redacted prompts\n(no bills, no PII)", label_offset=(60, 30))
    arrow(d, (1840, 1300), (1450, 1010), text="JSON text only\n(no emission values)", label_offset=(70, 25))

    footer(d, w, h, "External entities and top-level data flows only. See DFD-0 and DFD-1 for detail.")
    image.save(OUT / "01-context.png", dpi=DPI)


def dfd0_diagram() -> None:
    w, h = 2400, 1700
    image, d = canvas(w, h)
    header(d, w, "2. Data Flow Diagram — Level 0", "One process: the CarbonWise platform")
    d.rounded_rectangle((880, 620, 1520, 1080), radius=26, outline="black", fill="white", width=5)
    d.rounded_rectangle((900, 640, 1500, 1060), radius=20, outline="black", width=1)
    d.multiline_text(
        (1200, 760),
        "0\nCarbonWise\nPlatform",
        font=font(34, True),
        fill="black",
        anchor="mm",
        align="center",
        spacing=6,
    )
    d.multiline_text(
        (1200, 910),
        "Auth · catalog · records · documents\nreports · goals · plans · AI · admin",
        font=font(18),
        fill="black",
        anchor="mm",
        align="center",
        spacing=6,
    )
    d.multiline_text(
        (1200, 1010),
        "Emission calculation is deterministic\ninside this process.",
        font=font(16),
        fill="black",
        anchor="mm",
        align="center",
        spacing=4,
    )

    rounded(d, (110, 330, 560, 520), "Individual /\nhousehold user", ("records, goals",), title_size=25)
    rounded(d, (110, 1120, 560, 1330), "Organization user", ("shared records, plans",), title_size=25)
    rounded(d, (1840, 330, 2290, 540), "Admin / content editor", ("catalog, content, AI config",), title_size=25)
    rounded(d, (1840, 1120, 2290, 1360), "OpenRouter API", ("stateless text generation",), title_size=25)

    arrow(d, (560, 400), (940, 680), text="activity + profile", label_offset=(-30, 20))
    arrow(d, (980, 650), (560, 370), text="calculated results", label_offset=(-30, -30))
    arrow(d, (560, 1210), (930, 1030), text="org data", label_offset=(-20, 30))
    arrow(d, (980, 1060), (560, 1300), text="reports", label_offset=(-20, 30))
    arrow(d, (1840, 430), (1460, 700), text="catalog + content", label_offset=(40, 25))
    arrow(d, (1460, 720), (1840, 380), text="audit + usage", label_offset=(40, -25))
    arrow(d, (1460, 980), (1840, 1210), text="redacted prompt", label_offset=(40, 30))
    arrow(d, (1840, 1300), (1460, 1030), text="text only", label_offset=(40, 30))

    footer(d, w, h, "Level 0 shows the platform as a single process; DFD-1 decomposes it into nine processes.")
    image.save(OUT / "02-dfd-level-0.png", dpi=DPI)


def dfd1_diagram() -> None:
    w, h = 3500, 2300
    image, d = canvas(w, h)
    header(
        d,
        w,
        "3. Data Flow Diagram — Level 1",
        "Nine processes, seven data stores, actors, and the external AI service",
    )

    def process_box(x: int, y: int, number: str, name: str, body: str) -> None:
        d.rounded_rectangle((x, y, x + 540, y + 220), radius=16, outline="black", fill="white", width=4)
        d.text((x + 270, y + 68), f"{number}  {name}", font=font(25, True), fill="black", anchor="mm")
        d.text((x + 270, y + 140), body, font=font(19), fill="black", anchor="mm")

    def store(x: int, y: int, number: str, name: str) -> None:
        d.line((x, y, x + 500, y), fill="black", width=4)
        d.line((x, y, x, y + 120), fill="black", width=4)
        d.line((x, y + 120, x + 500, y + 120), fill="black", width=4)
        d.line((x + 500, y, x + 500, y + 120), fill="black", width=4)
        d.text((x + 18, y + 14), number, font=font(24, True), fill="black")
        d.text((x + 18, y + 62), name, font=font(21), fill="black")

    # Actors (left)
    rounded(d, (80, 300, 420, 860), "Individual /\nhousehold user", ("records, goals,\nreports, chat",), title_size=23)
    rounded(d, (80, 960, 420, 1260), "Organization\nuser", ("org profile,\nshared plans",), title_size=23)
    rounded(d, (80, 1320, 420, 1540), "Admin /\ncontent editor", ("catalog, content,\naudit",), title_size=23)

    # Process grid: three columns, three rows
    process_box(700, 320, "1.0", "Auth & profile", "sign-in · refresh · preferences")
    process_box(1500, 320, "2.0", "Catalog & factors", "categories · units · sources")
    process_box(2300, 320, "5.0", "Reports & export", "periods · categories · CSV")
    process_box(700, 680, "3.0", "Records & calculation", "snapshot factor → integer grams")
    process_box(1500, 680, "4.0", "Documents & extraction", "upload · consent · vision")
    process_box(2300, 680, "6.0", "Goals, plans & alternatives", "baseline · actions · savings")
    process_box(700, 1040, "9.0", "Admin console", "users · content · audit")
    process_box(1500, 1040, "7.0", "Engagement & notifications", "challenges · badges · alerts")
    process_box(2300, 1040, "8.0", "AI assistant & insights", "redacted prompt → text")

    # Data stores (bottom, grouped by the process that owns them)
    store(700, 1380, "D1", "users & profiles")
    store(1500, 1380, "D2", "catalog & factors")
    store(700, 1680, "D3", "consumption records")
    store(1500, 1680, "D4", "documents")
    store(2300, 1680, "D5", "goals, plans & actions")
    store(1500, 1960, "D6", "engagement & notifications")
    store(2300, 1960, "D7", "AI metadata & audit")

    rounded(d, (3000, 1090, 3400, 1270), "OpenRouter API", ("openrouter/free · stateless",), title_size=23)

    # Actor → process flows
    arrow(d, (420, 400), (700, 400), text="credentials / profile", label_offset=(0, -26))
    orthogonal(d, [(420, 620), (620, 620), (620, 790), (700, 790)], text="activity + bills")
    orthogonal(d, [(420, 1100), (620, 1100), (620, 960), (2180, 960), (2180, 850), (2300, 850)])
    label(d, (900, 930), "org goals & plans")
    orthogonal(d, [(420, 1430), (620, 1430), (620, 1180), (700, 1180)], text="admin actions")
    # User chat flow routed above the process grid and down the right-hand lane.
    orthogonal(d, [(420, 350), (620, 350), (620, 260), (2920, 260), (2920, 1080), (2840, 1080)])
    label(d, (1750, 240), "chat prompts & feedback")

    # Process ↔ data store flows, routed through empty lanes to avoid boxes.
    arrow(d, (970, 540), (620, 540), width=2)
    arrow(d, (970, 540), (560, 540), width=2)
    orthogonal(d, [(560, 540), (560, 1440), (700, 1440)])
    label(d, (610, 1320), "users")
    arrow(d, (1240, 790), (1500, 790), text="draft", label_offset=(0, -24), width=2)
    orthogonal(d, [(1500, 760), (1340, 760), (1340, 1740), (1500, 1740)])
    label(d, (1420, 1640), "draft bills")
    arrow(d, (970, 900), (660, 900), width=2)
    orthogonal(d, [(660, 900), (660, 1740), (700, 1740)])
    label(d, (648, 1600), "records")
    orthogonal(d, [(2040, 540), (2180, 540), (2180, 1440), (2000, 1440)], text="factors")
    orthogonal(d, [(2570, 900), (2920, 900), (2920, 1740), (2800, 1740)], text="plan actions")
    orthogonal(d, [(1770, 1260), (2100, 1260), (2100, 2020), (2000, 2020)], text="alerts")
    orthogonal(d, [(2570, 1260), (2960, 1260), (2960, 2020), (2800, 2020)], text="AI logs")

    # Process-to-process flows
    arrow(d, (1240, 430), (1500, 430), text="session", label_offset=(0, -24), width=2)
    arrow(d, (1770, 540), (1240, 700), text="factors", label_offset=(-20, -20), width=2)
    arrow(d, (1500, 790), (1240, 790), text="draft", label_offset=(0, -24), width=2)
    orthogonal(d, [(1240, 740), (1340, 740), (1340, 600), (2280, 600), (2280, 540)])
    label(d, (1820, 578), "aggregates")
    orthogonal(d, [(1240, 850), (1340, 850), (1340, 940), (2180, 940), (2180, 800), (2300, 800)])
    label(d, (1750, 918), "baseline")
    orthogonal(d, [(2570, 900), (2570, 960), (1950, 960), (1950, 1040)])
    label(d, (2300, 938), "actions")

    # External AI service
    arrow(d, (2840, 1150), (3000, 1150), text="redacted prompt", label_offset=(0, -24), width=2)
    arrow(d, (3000, 1210), (2840, 1210), text="text only", label_offset=(0, 24), width=2)

    d.text(
        (700, 2140),
        "5.0 reads D3. 9.0 edits D2 and D7. AI output is validated JSON text; process 3 alone calculates and snapshots emission values.",
        font=font(18),
        fill="black",
    )
    footer(d, w, h, "Data stores D1–D7. AI receives redacted prompts and never returns or invents emission values.")
    image.save(OUT / "03-dfd-level-1.png", dpi=DPI)


def use_case_diagram() -> None:
    w, h = 2400, 1900
    image, d = canvas(w, h)
    header(d, w, "4. Use Case Diagram", "Guest, individual/household, organization user, admin, and OpenRouter")
    d.rectangle((420, 245, 2020, 1745), outline="black", fill="white", width=4)
    d.text((450, 265), "CarbonWise v1 — authenticated product boundary", font=font(24, True), fill="black")

    def ellipse(cx: int, cy: int, text: str, rx: int = 210, ry: int = 48) -> None:
        d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), outline="black", fill="white", width=3)
        d.multiline_text((cx, cy), text, font=font(19), fill="black", anchor="mm", align="center", spacing=3)

    # Guest
    ellipse(1250, 380, "Register / sign in /\nread public content")
    # Individual / household user
    ellipse(1250, 570, "Track activity & upload bills")
    ellipse(1250, 730, "Dashboard, reports & CSV export")
    ellipse(1250, 890, "Goals, plans & alternatives")
    ellipse(1250, 1050, "Chat assistant & AI insights")
    ellipse(1250, 1210, "Challenges, badges &\nprivate leaderboard")
    # Organization user
    ellipse(1250, 1400, "Organization profile,\nshared reports & plans")
    # Admin
    ellipse(820, 1580, "Administer users, catalog,\nfactors & documents")
    ellipse(1620, 1580, "Manage content, challenges,\nAI monitor & audit")

    # Actors
    rounded(d, (80, 305, 350, 430), "Guest", title_size=25)
    rounded(d, (80, 500, 350, 1270), "Individual /\nhousehold user", title_size=24)
    rounded(d, (80, 1335, 350, 1465), "Organization\nuser", title_size=23)
    rounded(d, (80, 1515, 350, 1645), "Admin /\ncontent editor", title_size=23)
    rounded(d, (2100, 990, 2350, 1120), "OpenRouter\nAPI (external)", title_size=22)

    # Associations
    arrow(d, (350, 368), (1040, 380), width=2)
    d.line((350, 885, 1040, 885), fill="black", width=2)
    for cy in (570, 730, 890, 1050, 1210):
        d.line((350, 885, 1040, cy), fill="black", width=2)
    arrow(d, (350, 1400), (1040, 1400), width=2)
    arrow(d, (350, 1580), (610, 1580), width=2)
    d.line((350, 1530, 1620, 1530), fill="black", width=2)
    d.line((1620, 1530, 1620, 1532), fill="black", width=2)
    # External service participates only in the assistant use case.
    d.line((1460, 1050, 2100, 1050), fill="black", width=2)
    d.text((1650, 1018), "text-only JSON", font=font(17), fill="black")

    d.text(
        (450, 1695),
        "The guest path is unauthenticated; every other use case requires a JWT session. Admin is a separate cookie session.",
        font=font(17),
        fill="black",
    )
    footer(d, w, h, "OpenRouter is an external actor: it receives redacted prompts and returns text, never emission values.")
    image.save(OUT / "04-use-case.png", dpi=DPI)


def erd_diagram() -> None:
    w, h = 3600, 2700
    image, d = canvas(w, h)
    header(d, w, "5. Entity Relationship Diagram", "SQLite schema · 29 tables · integer grams CO2e · UTC timestamps")

    entity_font = font(21, True)
    body_font = font(16)
    columns = [80, 650, 1220, 1790, 2360, 2930]
    col_w = 500
    rows = [300, 650, 1000, 1350, 1700, 2050]
    row_h = 280

    boxes: dict[str, tuple[int, int]] = {}
    specs: dict[str, tuple[int, int, list[str]]] = {}

    def entity(col: int, row: int, name: str, attrs: list[str]) -> None:
        specs[name] = (col, row, attrs)
        x = columns[col]
        y = rows[row]
        boxes[name] = (x, y)
        d.rounded_rectangle((x, y, x + col_w, y + row_h), radius=10, outline="black", fill="white", width=3)
        d.rectangle((x, y, x + col_w, y + 44), fill="black")
        d.text((x + 14, y + 10), name, font=entity_font, fill="white")
        for index, attr in enumerate(attrs[:7]):
            d.text((x + 16, y + 58 + index * 30), attr, font=body_font, fill="black")

    entity(0, 0, "organizations", ["id PK", "name_en / name_ar", "slug UQ", "org_type", "is_active"])
    entity(1, 0, "users", ["id PK", "email UQ", "organization_id FK", "account_type", "locale / timezone", "is_active"])
    entity(2, 0, "user_profiles", ["id PK", "user_id FK UQ", "household_size", "leaderboard_opt_in", "default_period"])
    entity(3, 0, "refresh_tokens", ["id PK", "user_id FK", "token_hash UQ", "expires_at", "revoked_at"])
    entity(4, 0, "admins", ["id PK", "email UQ", "role", "is_active", "last_login_at"])
    entity(5, 0, "admin_audit_logs", ["id PK", "admin_id FK", "action", "entity / entity_id", "created_at"])

    entity(0, 1, "emission_categories", ["id PK", "slug UQ", "name_en / name_ar", "unit", "is_active"])
    entity(1, 1, "emission_factors", ["id PK", "category_id FK", "factor_grams", "source", "year", "is_active"])
    entity(2, 1, "alternatives", ["id PK", "category_id FK", "title_en / title_ar", "saving_percent", "source"])
    entity(3, 1, "saved_alternatives", ["id PK", "user_id FK", "alternative_id FK", "status", "created_at"])
    entity(4, 1, "articles", ["id PK", "slug UQ", "title_en / title_ar", "body_en / body_ar", "published_at"])
    entity(5, 1, "app_settings", ["id PK", "key UQ", "value", "updated_at"])

    entity(1, 2, "consumption_records", ["id PK", "user_id FK", "factor_id FK", "quantity / unit", "factor_grams_snapshot", "emissions_grams", "status"])
    entity(2, 2, "documents", ["id PK", "user_id FK", "record_id FK", "original_filename", "status", "ai_consent"])
    entity(3, 2, "goals", ["id PK", "user_id FK", "target_percent", "baseline_grams", "start/end_date", "status"])
    entity(4, 2, "reduction_plans", ["id PK", "user_id FK", "goal_id FK", "source", "summary_en / summary_ar"])
    entity(5, 2, "plan_actions", ["id PK", "plan_id FK", "title / description", "priority", "estimated_saving_grams", "status"])

    entity(0, 3, "challenges", ["id PK", "slug UQ", "title_en / title_ar", "target_value", "points", "status"])
    entity(1, 3, "challenge_participants", ["id PK", "challenge_id FK", "user_id FK", "progress_value", "status"])
    entity(2, 3, "points_ledger", ["id PK", "user_id FK", "points", "reason", "created_at"])
    entity(3, 3, "badges", ["id PK", "slug UQ", "title_en / title_ar", "points", "criteria"])
    entity(4, 3, "user_badges", ["id PK", "user_id FK", "badge_id FK", "awarded_at"])
    entity(5, 3, "notifications", ["id PK", "user_id FK", "title_en / title_ar", "body_en / body_ar", "read_at"])

    entity(0, 4, "notification_preferences", ["id PK", "user_id FK UQ", "email_enabled", "push_enabled", "weekly_digest"])
    entity(1, 4, "ai_conversations", ["id PK", "user_id FK", "locale", "created_at"])
    entity(2, 4, "ai_messages", ["id PK", "conversation_id FK", "role", "content", "created_at"])
    entity(3, 4, "ai_usage", ["id PK", "user_id FK", "feature", "tokens", "status", "created_at"])
    entity(4, 4, "ai_flagged_responses", ["id PK", "user_id FK", "reason", "redacted_text", "created_at"])
    entity(5, 4, "ai_cache", ["id PK", "cache_key UQ", "response_json", "expires_at"])

    # Connection layer: drawn before labels/boxes so lines disappear under boxes.
    def link(a: str, b: str) -> None:
        ax, ay = boxes[a]
        bx, by = boxes[b]
        points = [
            (ax + col_w / 2, ay + row_h / 2),
            (bx + col_w / 2, by + row_h / 2),
        ]
        d.line(points, fill="black", width=2)
        d.text((points[0][0] + 8, points[0][1] + 4), "1", font=font(15), fill="black")
        d.text((points[1][0] - 22, points[1][1] - 22), "N", font=font(15), fill="black")

    pairs = [
        ("organizations", "users"),
        ("users", "user_profiles"),
        ("users", "refresh_tokens"),
        ("admins", "admin_audit_logs"),
        ("emission_categories", "emission_factors"),
        ("emission_factors", "consumption_records"),
        ("users", "consumption_records"),
        ("consumption_records", "documents"),
        ("users", "goals"),
        ("goals", "reduction_plans"),
        ("reduction_plans", "plan_actions"),
        ("users", "saved_alternatives"),
        ("alternatives", "saved_alternatives"),
        ("challenges", "challenge_participants"),
        ("challenge_participants", "points_ledger"),
        ("badges", "user_badges"),
        ("users", "user_badges"),
        ("users", "notifications"),
        ("users", "notification_preferences"),
        ("users", "ai_conversations"),
        ("ai_conversations", "ai_messages"),
        ("users", "ai_usage"),
        ("users", "ai_flagged_responses"),
    ]
    for a, b in pairs:
        if a in boxes and b in boxes:
            link(a, b)

    # Redraw boxes over connector lines so the diagram reads as a clean schema.
    for name, (col, row, attrs) in specs.items():
        entity(col, row, name, attrs)

    # Relationship legend
    d.text((80, 2330), "Key relationships", font=font(24, True), fill="black")
    legend = (
        "organizations 1:N users · users 1:1 user_profiles · users 1:N refresh_tokens\n"
        "emission_categories 1:N emission_factors · emission_factors 1:N consumption_records\n"
        "users 1:N consumption_records / documents / goals / reduction_plans / notifications\n"
        "goals 1:N reduction_plans · reduction_plans 1:N plan_actions\n"
        "users N:M challenges via challenge_participants · users N:M badges via user_badges\n"
        "users 1:N ai_conversations · ai_conversations 1:N ai_messages"
    )
    d.multiline_text((80, 2370), legend, font=font(18), fill="black", spacing=8)
    footer(d, w, h, "All timestamps UTC; emission values are integer grams CO2e. Cache and join tables included.")
    image.save(OUT / "05-erd.png", dpi=DPI)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    context_diagram()
    dfd0_diagram()
    dfd1_diagram()
    use_case_diagram()
    erd_diagram()
    for path in sorted(OUT.glob("*.png")):
        print(f"generated {path.name} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
