# DA-to-DE roadmap diagram

Source: `roadmap.html`; faithful, mixed-audience flowchart; fit canvas 1400 × 1440. All 24 Mermaid nodes, four stage containers and 25 edges are retained. The “還不用” branch goes directly to the portfolio/interview endpoint; only Spark and Kafka pass through Lakehouse. No labels merged or dropped.

Palette follows the existing knowledge-base diagrams (passive-components/diagram_kit.py). Stage zones keep the faithful import readable; only the decision is accented. Shapes distinguish start/end, actions and the decision.

Prerequisite: install the diagram-design plugin/skill (https://github.com/cathrynlavery/diagram-design). Set `$DIAGRAM_DESIGN_SKILL_DIR` to the installed skill directory (the directory containing `SKILL.md` and `scripts/`).

Export from the repository root:

```sh
python3 "$DIAGRAM_DESIGN_SKILL_DIR/scripts/export_svg.py" docs/assets/diagrams/da-to-de-roadmap/roadmap.html docs/assets/diagrams/da-to-de-roadmap/roadmap.svg --system-fonts
python3 scripts/darken_diagrams.py docs/assets/diagrams/da-to-de-roadmap/roadmap.svg
```

The SVG stays light; the PNG is the site's dark rendition. Offline font stack: Geist, Noto Sans CJK TC, Microsoft JhengHei, sans-serif. This export environment resolves Chinese to Microsoft JhengHei; Noto Sans CJK TC was not found by fontconfig. PNG pixels preserve the verified glyphs.
