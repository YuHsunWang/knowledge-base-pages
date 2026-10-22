# Backend learning series diagrams

Sources: `overview.html`, `fastapi-request-flow.html`, `render-deploy-flow.html`, drawn with the diagram-design skill (https://github.com/cathrynlavery/diagram-design). Palette follows `../da-to-de-roadmap/` (passive-components/diagram_kit.py). Canvas 1280 wide.

The FastAPI flow puts the API-key dependency before body validation: verified on FastAPI 0.159.1 (bad key + bad body returns 401, good key + bad body returns 422).

Export from the repository root, with `$DIAGRAM_DESIGN_SKILL_DIR` set to the installed skill directory:

```sh
for f in overview fastapi-request-flow render-deploy-flow; do
  python3 "$DIAGRAM_DESIGN_SKILL_DIR/scripts/export_svg.py" docs/assets/diagrams/backend-series/$f.html docs/assets/diagrams/backend-series/$f.svg --system-fonts
done
python3 scripts/darken_diagrams.py docs/assets/diagrams/backend-series/*.svg
```

The SVG stays light; the PNG is the site's dark rendition.
