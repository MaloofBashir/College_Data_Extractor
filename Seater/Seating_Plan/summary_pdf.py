from io import BytesIO
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont


PAGE_SIZE = (1240, 1754)
MARGIN = 72
LINE_COLOR = "#d7dfeb"
TEXT_COLOR = "#1f2937"
ACCENT_COLOR = "#124c9c"
CARD_BG = "#eef4ff"
TABLE_HEADER_BG = "#dbe8ff"


def load_font(size, bold=False, mono=False):
    font_candidates = []
    if mono:
        font_candidates.extend(
            [
                "/System/Library/Fonts/Supplemental/Courier New Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Courier New.ttf",
                "/Library/Fonts/Courier New Bold.ttf" if bold else "/Library/Fonts/Courier New.ttf",
            ]
        )
    else:
        font_candidates.extend(
            [
                "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
                "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
                "/System/Library/Fonts/Supplemental/Helvetica.ttc",
            ]
        )

    for candidate in font_candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue

    return ImageFont.load_default()


TITLE_FONT = load_font(34, bold=True)
SECTION_FONT = load_font(24, bold=True)
BODY_FONT = load_font(19)
SMALL_FONT = load_font(16)
BOLD_FONT = load_font(19, bold=True)
MONO_FONT = load_font(18, mono=True)


def measure_text(draw, text, font):
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return right - left, bottom - top


def wrap_to_width(draw, text, font, max_width):
    if not text:
        return [""]

    words = str(text).split()
    lines = []
    current = ""

    for word in words:
        candidate = word if not current else f"{current} {word}"
        width, _ = measure_text(draw, candidate, font)
        if width <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines or [str(text)]


def make_page():
    image = Image.new("RGB", PAGE_SIZE, "white")
    return image, ImageDraw.Draw(image)


def draw_wrapped_text(draw, text, x, y, font, max_width, fill=TEXT_COLOR, line_gap=8):
    lines = wrap_to_width(draw, text, font, max_width)
    _, line_height = measure_text(draw, "Ag", font)

    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height + line_gap

    return y


def draw_section_title(draw, title, y):
    draw.text((MARGIN, y), title, font=SECTION_FONT, fill=ACCENT_COLOR)
    _, height = measure_text(draw, title, SECTION_FONT)
    y += height + 10
    draw.line((MARGIN, y, PAGE_SIZE[0] - MARGIN, y), fill=LINE_COLOR, width=2)
    return y + 18


def draw_metric_cards(draw, y, cards):
    card_gap = 18
    card_width = (PAGE_SIZE[0] - (2 * MARGIN) - (card_gap * 2)) // 3
    card_height = 132

    for index, card in enumerate(cards):
        row = index // 3
        col = index % 3
        x0 = MARGIN + col * (card_width + card_gap)
        y0 = y + row * (card_height + card_gap)
        x1 = x0 + card_width
        y1 = y0 + card_height
        draw.rounded_rectangle((x0, y0, x1, y1), radius=18, fill=CARD_BG, outline="#b8cdf0", width=2)
        draw.text((x0 + 24, y0 + 22), card["label"], font=SMALL_FONT, fill="#355070")
        draw.text((x0 + 24, y0 + 58), card["value"], font=TITLE_FONT, fill=ACCENT_COLOR)

    rows = (len(cards) + 2) // 3
    return y + rows * card_height + max(0, rows - 1) * card_gap + 16


def draw_table_header(draw, y, headers, column_widths, row_height=34, header_font=BOLD_FONT):
    x_positions = [MARGIN]
    for width in column_widths[:-1]:
        x_positions.append(x_positions[-1] + width)

    total_width = sum(column_widths)
    header_bottom = y + row_height + 12
    draw.rounded_rectangle(
        (MARGIN, y, MARGIN + total_width, header_bottom),
        radius=12,
        fill=TABLE_HEADER_BG,
        outline="#c2d4f1",
    )

    for index, header in enumerate(headers):
        draw.text((x_positions[index] + 12, y + 10), header, font=header_font, fill=TEXT_COLOR)

    return header_bottom


def draw_table_row(draw, y, row, column_widths, row_height=34, font=SMALL_FONT):
    x_positions = [MARGIN]
    for width in column_widths[:-1]:
        x_positions.append(x_positions[-1] + width)

    total_width = sum(column_widths)
    line_count = 1
    wrapped_cells = []

    for value, width in zip(row, column_widths):
        wrapped = wrap_to_width(draw, value, font, width - 20)
        wrapped_cells.append(wrapped)
        line_count = max(line_count, len(wrapped))

    box_height = max(row_height, line_count * 24 + 16)
    draw.rectangle((MARGIN, y, MARGIN + total_width, y + box_height), outline=LINE_COLOR, width=1)

    for index, wrapped_lines in enumerate(wrapped_cells):
        text_y = y + 8
        for line in wrapped_lines:
            draw.text((x_positions[index] + 12, text_y), line, font=font, fill=TEXT_COLOR)
            text_y += 24

    return y + box_height


def draw_table(draw, y, headers, rows, column_widths, row_height=34, font=SMALL_FONT, header_font=BOLD_FONT):
    current_y = draw_table_header(draw, y, headers, column_widths, row_height=row_height, header_font=header_font)
    for row in rows:
        current_y = draw_table_row(draw, current_y, row, column_widths, row_height=row_height, font=font)

    return current_y + 12


def append_page(pages, image):
    pages.append(image.convert("RGB"))


def generate_summary_pdf(summary):
    pages = []
    image, draw = make_page()
    y = MARGIN

    title = "Result Pass Percentage Summary"
    draw.text((MARGIN, y), title, font=TITLE_FONT, fill=ACCENT_COLOR)
    _, title_height = measure_text(draw, title, TITLE_FONT)
    y += title_height + 8
    y = draw_wrapped_text(
        draw,
        f"Generated on {datetime.now().strftime('%d %b %Y, %I:%M %p')}",
        MARGIN,
        y,
        SMALL_FONT,
        PAGE_SIZE[0] - (2 * MARGIN),
        fill="#5b6b84",
        line_gap=4,
    )
    y += 18

    cards = [
        {"label": "Total Students", "value": str(summary["total_students"])},
        {"label": "Passed", "value": str(summary["overall_passed"])},
        {"label": "Failed", "value": str(summary["overall_not_passed"])},
        {"label": "Overall Pass %", "value": f'{summary["overall_pass_percentage"]}%'},
    ]
    y = draw_metric_cards(draw, y, cards)

    y = draw_section_title(draw, "Subject-wise Performance", y)
    subject_rows = [
        [
            item["subject"],
            item["subject_name"],
            str(item["appeared"]),
            str(item["passed"]),
            f'{item["pass_percentage"]}%',
        ]
        for item in summary["subjects"]
    ]
    y = draw_table(
        draw,
        y,
        ["Code", "Subject", "Total Students", "Passed", "Pass %"],
        subject_rows,
        [140, 420, 180, 140, 140],
    )
    append_page(pages, image)

    pdf_buffer = BytesIO()
    pages[0].save(pdf_buffer, format="PDF", save_all=True, append_images=pages[1:])
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()
