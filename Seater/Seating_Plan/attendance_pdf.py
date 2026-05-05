from io import BytesIO
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont


PAGE_SIZE = (1240, 1754)
MARGIN = 72
TEXT_COLOR = "#1f2937"
ACCENT_COLOR = "#0e4d92"
LINE_COLOR = "#d8e3f1"
CARD_BG = "#edf5ff"
HEADER_BG = "#dce9ff"


def load_font(size, bold=False):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica.ttc",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


TITLE_FONT = load_font(34, bold=True)
SECTION_FONT = load_font(24, bold=True)
BODY_FONT = load_font(18)
SMALL_FONT = load_font(16)
BOLD_FONT = load_font(18, bold=True)
PRINT_FONT = load_font(21, bold=True)
PRINT_HEADER_FONT = load_font(20, bold=True)


def make_page():
    image = Image.new("RGB", PAGE_SIZE, "white")
    return image, ImageDraw.Draw(image)


def measure(draw, text, font):
    left, top, right, bottom = draw.textbbox((0, 0), str(text), font=font)
    return right - left, bottom - top


def wrap_text(draw, text, font, max_width):
    words = str(text).split()
    if not words:
        return [""]

    lines = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        width, _ = measure(draw, candidate, font)
        if width <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def draw_title(draw, text, y):
    draw.text((MARGIN, y), text, font=TITLE_FONT, fill=ACCENT_COLOR)
    _, height = measure(draw, text, TITLE_FONT)
    return y + height + 8


def draw_subtitle(draw, text, y):
    draw.text((MARGIN, y), text, font=SMALL_FONT, fill="#5b6b84")
    _, height = measure(draw, text, SMALL_FONT)
    return y + height + 20


def draw_section(draw, title, y):
    draw.text((MARGIN, y), title, font=SECTION_FONT, fill=ACCENT_COLOR)
    _, height = measure(draw, title, SECTION_FONT)
    y += height + 10
    draw.line((MARGIN, y, PAGE_SIZE[0] - MARGIN, y), fill=LINE_COLOR, width=2)
    return y + 16


def draw_cards(draw, y, cards):
    gap = 18
    width = (PAGE_SIZE[0] - (2 * MARGIN) - (gap * 2)) // 3
    height = 128
    for index, card in enumerate(cards):
        row = index // 3
        col = index % 3
        x0 = MARGIN + col * (width + gap)
        y0 = y + row * (height + gap)
        x1 = x0 + width
        y1 = y0 + height
        draw.rounded_rectangle((x0, y0, x1, y1), radius=18, fill=CARD_BG, outline="#bdd2ef", width=2)
        draw.text((x0 + 22, y0 + 20), card["label"], font=SMALL_FONT, fill="#355070")
        draw.text((x0 + 22, y0 + 56), str(card["value"]), font=TITLE_FONT, fill=ACCENT_COLOR)
    rows = (len(cards) + 2) // 3
    return y + rows * height + max(0, rows - 1) * gap + 12


def draw_table_header(draw, y, headers, widths):
    x = MARGIN
    draw.rounded_rectangle((MARGIN, y, MARGIN + sum(widths), y + 46), radius=12, fill=HEADER_BG, outline="#c8d8f0")
    for header, width in zip(headers, widths):
        draw.text((x + 12, y + 12), header, font=BOLD_FONT, fill=TEXT_COLOR)
        x += width
    return y + 46


def draw_table_row(draw, y, row, widths):
    x_positions = [MARGIN]
    for width in widths[:-1]:
        x_positions.append(x_positions[-1] + width)
    wrapped_cells = []
    line_count = 1
    for value, width in zip(row, widths):
        lines = wrap_text(draw, value, SMALL_FONT, width - 20)
        wrapped_cells.append(lines)
        line_count = max(line_count, len(lines))
    height = max(38, line_count * 22 + 16)
    draw.rectangle((MARGIN, y, MARGIN + sum(widths), y + height), outline=LINE_COLOR, width=1)
    for index, lines in enumerate(wrapped_cells):
        text_y = y + 8
        for line in lines:
            draw.text((x_positions[index] + 12, text_y), line, font=SMALL_FONT, fill=TEXT_COLOR)
            text_y += 22
    return y + height


def append_page(pages, image):
    pages.append(image.convert("RGB"))


def draw_subject_roll_column(draw, x, y, width, height, subject_name, rolls, start_index=1, continued=False):
    header_height = 64
    row_height = 34
    serial_width = 58

    draw.rounded_rectangle((x, y, x + width, y + height), radius=16, fill="#fbfeff", outline="#c8d8f0", width=2)
    draw.rounded_rectangle((x, y, x + width, y + header_height), radius=16, fill=HEADER_BG, outline="#c8d8f0", width=2)
    heading = subject_name if not continued else f"{subject_name} (contd.)"
    draw.text((x + 14, y + 18), heading, font=PRINT_HEADER_FONT, fill=TEXT_COLOR)

    head_y = y + header_height + 12
    draw.text((x + 12, head_y), "S.No", font=BOLD_FONT, fill="#355070")
    draw.text((x + serial_width + 28, head_y), "Roll No", font=BOLD_FONT, fill="#355070")
    head_y += 30

    max_rows = max(1, (height - header_height - 52) // row_height)
    visible_rolls = rolls[:max_rows]
    for offset, roll in enumerate(visible_rolls):
        row_y = head_y + offset * row_height
        draw.line((x + 10, row_y + row_height, x + width - 10, row_y + row_height), fill=LINE_COLOR, width=1)
        draw.text((x + 12, row_y + 6), str(start_index + offset), font=PRINT_FONT, fill=TEXT_COLOR)
        draw.text((x + serial_width + 28, row_y + 6), str(roll), font=PRINT_FONT, fill=TEXT_COLOR)

    return max_rows


def generate_attendance_pdf(summary):
    pages = []
    centre_heading = f'Centre {summary.get("selected_centre") or "-"} Roll Numbers'
    selected_subject_text = ", ".join(summary["selected_subjects"]) if summary["selected_subjects"] else "All subjects in this centre"
    subjects = summary["filtered_subjects"]
    columns_per_page = 2
    column_gap = 26
    content_top = 210
    column_height = PAGE_SIZE[1] - content_top - MARGIN

    for batch_start in range(0, len(subjects), columns_per_page):
        batch = subjects[batch_start:batch_start + columns_per_page]
        roll_offsets = [0] * len(batch)
        serial_offsets = [1] * len(batch)

        while True:
            image, draw = make_page()
            y = MARGIN
            y = draw_title(draw, centre_heading, y)
            y = draw_subtitle(draw, f"Subjects: {selected_subject_text}", y)
            draw.text((MARGIN, y), "Roll numbers run top to bottom in each subject column, then move left to right.", font=SMALL_FONT, fill="#5b6b84")
            y += 30
            draw.text((MARGIN, y), f"Generated on {datetime.now().strftime('%d %b %Y, %I:%M %p')}", font=SMALL_FONT, fill="#5b6b84")

            total_width = PAGE_SIZE[0] - (2 * MARGIN) - ((len(batch) - 1) * column_gap)
            column_width = total_width // max(1, len(batch))
            has_more = False

            for index, item in enumerate(batch):
                x = MARGIN + index * (column_width + column_gap)
                remaining_rolls = item["roll_numbers"][roll_offsets[index]:]
                drawn_rows = draw_subject_roll_column(
                    draw,
                    x,
                    content_top,
                    column_width,
                    column_height,
                    item["subject"],
                    remaining_rolls,
                    start_index=serial_offsets[index],
                    continued=roll_offsets[index] > 0,
                )
                roll_offsets[index] += drawn_rows
                serial_offsets[index] += drawn_rows
                if roll_offsets[index] < len(item["roll_numbers"]):
                    has_more = True

            append_page(pages, image)
            if not has_more:
                break

    buffer = BytesIO()
    pages[0].save(buffer, format="PDF", save_all=True, append_images=pages[1:])
    buffer.seek(0)
    return buffer.getvalue()
