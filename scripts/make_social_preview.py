"""Build the repository social preview from real Form Studio screenshots."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "social-preview.png"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = (
        ["C:/Windows/Fonts/segoeuib.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
        if bold
        else ["C:/Windows/Fonts/segoeui.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    )
    for name in names:
        if Path(name).exists():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()


def card(canvas: Image.Image, source: str, box: tuple[int, int, int, int]) -> None:
    left, top, width, height = box
    shot = Image.open(ROOT / "docs" / "designs" / f"{source}.png").convert("RGB")
    shot = ImageOps.fit(shot, (width, height), Image.Resampling.LANCZOS, centering=(0.5, 0.18))
    mask = Image.new("L", (width, height), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, width - 1, height - 1), radius=18, fill=255)
    shadow = Image.new("RGBA", (width + 30, height + 30), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((12, 12, width + 10, height + 10), radius=22, fill=(0, 0, 0, 75))
    canvas.alpha_composite(shadow, (left - 7, top - 4))
    canvas.paste(shot, (left, top), mask)
    ImageDraw.Draw(canvas).rounded_rectangle(
        (left, top, left + width - 1, top + height - 1), radius=18, outline="#76818e", width=2
    )


def main() -> None:
    image = Image.new("RGBA", (1280, 640), "#111820")
    draw = ImageDraw.Draw(image)
    draw.ellipse((-130, 370, 480, 980), fill="#183933")
    draw.ellipse((750, -280, 1450, 410), fill="#1b2b44")

    draw.rounded_rectangle((68, 66, 211, 100), radius=17, fill="#c9f5d5")
    draw.text((87, 72), "OPEN SOURCE", fill="#163b2d", font=font(16, bold=True))
    draw.text((68, 136), "FORM /", fill="#ffffff", font=font(78, bold=True))
    draw.text((68, 216), "STUDIO", fill="#c9f5d5", font=font(78, bold=True))
    draw.text((70, 330), "Build websites without code.", fill="#f3f6f3", font=font(29))
    draw.text((70, 377), "10 designs. One powerful editor.", fill="#afbac3", font=font(23))
    draw.rounded_rectangle((68, 480, 510, 552), radius=16, outline="#62756f", width=2)
    draw.text((88, 499), "FastAPI   ·   TypeScript   ·   AGPL-3.0", fill="#d9e6e1", font=font(18))

    card(image, "noir", (731, 86, 390, 254))
    card(image, "studio", (625, 257, 390, 254))
    card(image, "garden", (865, 315, 333, 216))
    image.convert("RGB").save(OUT, optimize=True)
    print(OUT)


if __name__ == "__main__":
    main()
