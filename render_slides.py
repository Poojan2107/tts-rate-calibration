import csv
import os
from PIL import Image, ImageDraw, ImageFont

CSV_PATH = "Canva Create Pipeline Slides Dataset.csv"
OUTPUT_DIR = "slides"
SELECTED_SLIDE_IDS = ["slide-01", "slide-02", "slide-03"]


def render_slide_image(row: dict, output_path: str):
    width, height = 1280, 720
    # Create canvas with clean slate / modern gradient background
    image = Image.new("RGB", (width, height), color="#0F172A")
    draw = ImageDraw.Draw(image)

    # Use default bitmap font or truetype if available
    try:
        title_font = ImageFont.truetype("arial.ttf", 44)
        subtitle_font = ImageFont.truetype("arial.ttf", 26)
        body_font = ImageFont.truetype("arial.ttf", 22)
        meta_font = ImageFont.truetype("arial.ttf", 18)
    except Exception:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
        meta_font = ImageFont.load_default()

    # Header Card
    draw.rectangle([60, 40, 1220, 130], fill="#1E293B", outline="#334155", width=2)
    draw.text((80, 60), row["slide_title"], fill="#F8FAFC", font=title_font)
    draw.text((1050, 68), f"ID: {row['slide_id']}", fill="#94A3B8", font=meta_font)

    # Visual / Chart Container Box
    draw.rectangle([60, 160, 780, 660], fill="#1E293B", outline="#3B82F6", width=2)
    draw.text((90, 185), f"Visual Component: {row['visual_type'].upper()}", fill="#60A5FA", font=subtitle_font)

    # Format chart data summary text with simple word wrapping
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

    y_offset = 240
    for line in lines:
        draw.text((90, y_offset), line, fill="#E2E8F0", font=body_font)
        y_offset += 34

    # Body Notes / Points Container Box
    draw.rectangle([820, 160, 1220, 660], fill="#1E293B", outline="#334155", width=2)
    draw.text((850, 185), "Key Points & Details", fill="#38BDF8", font=subtitle_font)

    bullets = [b.strip() for b in row["body_text"].split("|")]
    b_offset = 245
    for b in bullets:
        draw.text((850, b_offset), f"• {b}", fill="#CBD5E1", font=body_font)
        b_offset += 55

    image.save(output_path)
    print(f"Rendered: {output_path}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(CSV_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["slide_id"] in SELECTED_SLIDE_IDS:
                filename = row["image_filename"]
                output_path = os.path.join(OUTPUT_DIR, filename)
                render_slide_image(row, output_path)


if __name__ == "__main__":
    main()
