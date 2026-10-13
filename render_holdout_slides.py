import csv
import os
import re
from PIL import Image, ImageDraw, ImageFont

CSV_PATH = "Holdout Slide Rows CSV.csv"
OUTPUT_DIR = "holdout_slides"


def render_slide_image(row: dict, output_path: str):
    width, height = 1280, 720
    # Clean modern dark canvas matching Canva presentation aesthetic
    image = Image.new("RGB", (width, height), color="#0F172A")
    draw = ImageDraw.Draw(image)

    try:
        title_font = ImageFont.truetype("arial.ttf", 40)
        subtitle_font = ImageFont.truetype("arial.ttf", 24)
        body_font = ImageFont.truetype("arial.ttf", 20)
        meta_font = ImageFont.truetype("arial.ttf", 16)
    except Exception:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
        meta_font = ImageFont.load_default()

    # Header Card
    draw.rectangle([60, 40, 1220, 130], fill="#1E293B", outline="#334155", width=2)
    draw.text((80, 60), row["slide_title"], fill="#F8FAFC", font=title_font)
    draw.text((1020, 68), f"ID: {row['slide_id']} | {row.get('deck_name', '')}", fill="#94A3B8", font=meta_font)

    # Visual / Chart Container Box
    draw.rectangle([60, 160, 780, 660], fill="#1E293B", outline="#3B82F6", width=2)
    visual_type_title = row.get("visual_type", "VISUAL").replace("_", " ").upper()
    draw.text((90, 185), f"Visual Component: {visual_type_title}", fill="#60A5FA", font=subtitle_font)

    # Format chart data summary text with word wrapping
    summary_text = row["chart_data_summary"]
    words = summary_text.split()
    lines = []
    current_line = []
    for w in words:
        current_line.append(w)
        if len(" ".join(current_line)) > 42:
            lines.append(" ".join(current_line))
            current_line = []
    if current_line:
        lines.append(" ".join(current_line))

    y_offset = 235
    for line in lines:
        draw.text((90, y_offset), line, fill="#E2E8F0", font=body_font)
        y_offset += 30

    # Body Notes / Points Container Box
    draw.rectangle([820, 160, 1220, 660], fill="#1E293B", outline="#334155", width=2)
    draw.text((850, 185), "Key Points & Details", fill="#38BDF8", font=subtitle_font)

    raw_bullets = re.split(r"[;|]", row["body_text"])
    bullets = [b.strip() for b in raw_bullets if b.strip()]
    b_offset = 240
    for b in bullets:
        # Wrap long bullets if needed
        b_words = b.split()
        b_lines = []
        cur_b = []
        for bw in b_words:
            cur_b.append(bw)
            if len(" ".join(cur_b)) > 26:
                b_lines.append(" ".join(cur_b))
                cur_b = []
        if cur_b:
            b_lines.append(" ".join(cur_b))

        for idx, bl in enumerate(b_lines):
            prefix = "• " if idx == 0 else "  "
            draw.text((850, b_offset), f"{prefix}{bl}", fill="#CBD5E1", font=body_font)
            b_offset += 28
        b_offset += 16

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    image.save(output_path)
    print(f"Rendered: {output_path}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs("slides", exist_ok=True)
    with open(CSV_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row["image_filename"]
            out_path1 = os.path.join(OUTPUT_DIR, filename)
            out_path2 = os.path.join("slides", filename)
            render_slide_image(row, out_path1)
            render_slide_image(row, out_path2)


if __name__ == "__main__":
    main()
