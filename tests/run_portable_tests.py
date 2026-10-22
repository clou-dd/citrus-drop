"""Optional developer tests: .NET 8 SDK, Pillow, reportlab, pypdf and Poppler."""
import argparse
from pathlib import Path
import os
import shlex
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw
from pypdf import PdfReader
from reportlab.pdfgen import canvas


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--poppler-dir", type=Path, help="Windows directory containing pdftoppm.exe and pdftotext.exe")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    subprocess.run(["dotnet", "build", str(root / "tests/CitrusDrop.PortableTests.csproj"), "-c", "Release"], check=True)
    with tempfile.TemporaryDirectory(prefix="CitrusPdfTests_") as temporary:
        work = Path(temporary)
        fixtures = work / "fixtures"
        fixtures.mkdir()
        results = work / "한글 공백 & $ 결과"
        tools = args.poppler_dir
        if os.name == "nt":
            if tools is None:
                raise SystemExit("Use --poppler-dir with the complete Poppler bin directory.")
            tools = tools.resolve()
        else:
            tools = work / "tools"
            tools.mkdir()
            for name in ("pdftoppm", "pdftotext"):
                executable = shutil.which(name)
                if executable is None:
                    raise SystemExit("Missing test dependency: " + name)
                wrapper = tools / (name + ".exe")
                wrapper.write_text("#!/bin/sh\nexec " + shlex.quote(executable) + ' "$@"\n', encoding="utf-8")
                wrapper.chmod(0o755)
        for name, size, color, label in (
            ("landscape.jpg", (800, 400), "#ffe3bc", "PAGE ONE / LANDSCAPE"),
            ("portrait.jpg", (400, 800), "#bfe6f3", "PAGE TWO / PORTRAIT"),
        ):
            image = Image.new("RGB", size, color)
            drawing = ImageDraw.Draw(image)
            drawing.rectangle((25, 25, size[0] - 25, size[1] - 25), outline="black", width=4)
            drawing.text((45, 70), label, fill="black")
            image.save(fixtures / name, quality=95)
        text = fixtures / "text.pdf"
        document = canvas.Canvas(str(text))
        document.drawString(70, 750, "Citrus PDF text fixture")
        document.save()
        test_dll = root / "tests/bin/Release/net8.0/CitrusDrop.PortableTests.dll"
        subprocess.run([
            "dotnet", str(test_dll), str(results), str(tools),
            str(fixtures / "landscape.jpg"), str(fixtures / "portrait.jpg"), str(text),
        ], check=True, timeout=120)
        pdf = PdfReader(results / "한글 공백 & $ PDF.pdf")
        assert len(pdf.pages) == 2
        assert pdf.pages[0].mediabox.width > pdf.pages[0].mediabox.height
        assert pdf.pages[1].mediabox.width < pdf.pages[1].mediabox.height
        for folder in results.glob("*_pages*"):
            for path in folder.iterdir():
                with Image.open(path) as image:
                    image.verify()
        print("PASS: independent PDF page-count/orientation and image-decoder checks")


if __name__ == "__main__":
    main()
