"""Render SVG diagrams at their exact viewBox size with Chromium."""
from pathlib import Path
import sys
from xml.etree import ElementTree as ET

from playwright.sync_api import sync_playwright


def render(svg_path: Path) -> Path:
    root = ET.parse(svg_path).getroot()
    _, _, width, height = map(float, root.attrib["viewBox"].split())
    size = (int(width), int(height))
    png_path = svg_path.with_suffix(".png")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": size[0], "height": size[1]}, device_scale_factor=1)
        page.goto(svg_path.resolve().as_uri())
        page.locator("svg").screenshot(path=str(png_path))
        browser.close()
    return png_path


if __name__ == "__main__":
    for name in sys.argv[1:]:
        print(render(Path(name)))
