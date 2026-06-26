"""Create a simple app icon placeholder."""
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont

    size = 512
    img = Image.new("RGBA", (size, size), (13, 17, 23, 255))
    draw = ImageDraw.Draw(img)
    draw.ellipse([64, 64, 448, 448], fill=(35, 134, 54, 255))
    draw.text((180, 200), "RICK", fill=(255, 255, 255, 255))
    out = Path(__file__).parent / "app_icon.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print(f"Icon saved to {out}")
except ImportError:
    print("Pillow not available")
