from pathlib import Path

from PIL import Image, ImageDraw

folder = Path(__file__).resolve().parents[1] / "markitdown_es" / "assets"
folder.mkdir(parents=True, exist_ok=True)
image = Image.new("RGBA", (256, 256))
draw = ImageDraw.Draw(image)
draw.rounded_rectangle((0, 0, 255, 255), radius=48, fill="#16394b")
draw.line(
    [(48, 176), (48, 80), (88, 128), (128, 80), (128, 176)], fill="white", width=16, joint="curve"
)
draw.line([(184, 80), (184, 168)], fill="#89d9df", width=16)
draw.polygon([(156, 148), (212, 148), (184, 184)], fill="#89d9df")
image.save(folder / "app.png")
image.save(
    folder / "app.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
)
