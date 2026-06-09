"""Render OM PDF pages and rebuild Order Management panel in index.html."""
from __future__ import annotations

import re
from pathlib import Path

import fitz

from om_detailed_content import OM_SECTIONS

ROOT = Path(r'e:\Study')
PDF = ROOT / 'Order Orchestration EG v1.0 (3).pdf'
HTML = ROOT / 'index.html'
OUT = ROOT / 'assets' / 'om' / 'pdf-pages'
ZOOM = 1.5

# Each page assigned to one section (1-based page numbers)
PAGE_SECTION: dict[int, str] = {}

SECTIONS = [
    ('om-overview', '1. OM Overview & TOC', 2, 10),
    ('om-decomp', '2. Order Decomposition', 128, 131),
    ('om-decomp-orch', '3. Decomposition vs Orchestration', 7, 8),
    ('om-plan-def', '4. Swimlanes & Plan Definitions', 9, 16),
    ('om-generate', '5. Generate Orchestration Plans', 17, 22),
    ('om-item-types', '6. Orchestration Item Types', 12, 13),
    ('om-scenarios', '7. Scenarios & Dependencies', 15, 16),
    ('om-dependencies', '8. Dependency Definitions', 49, 55),
    ('om-manual', '9. Manual Tasks & Queues', 23, 36),
    ('om-auto', '10. Auto Tasks', 38, 44),
    ('om-callouts', '11. Systems & Callouts', 58, 84),
    ('om-fallout', '12. Fallout & Retry Policies', 86, 105),
    ('om-push', '13. Push Events', 110, 122),
    ('om-macd-1to1', '14. MACD 1:1 Decomposition', 125, 162),
    ('om-macd-disconnect', '15. MACD Disconnect', 163, 175),
    ('om-macd-1tom', '16. MACD 1:M Decomposition', 178, 202),
    ('om-cancel', '17. In-Flight Cancellation', 204, 218),
    ('om-rollback', '18. Rollback Groups & Smart Freeze', 220, 251),
    ('om-challenge', '19. Advanced Orchestration Challenge', 258, 269),
    ('om-ref', '20. Quick Reference', None, None),
]

DECOMP_OVERRIDE = {128, 129, 130, 131, 155, 156, 181, 199}
EXCLUDE_PAGES = {1, 2, 3, 4, 5, 6}

# Build page map from ranges (later ranges override on conflict — order matters)
for sid, _title, start, end in SECTIONS:
    if start is None:
        continue
    for p in range(start, end + 1):
        PAGE_SECTION[p] = sid

for p in DECOMP_OVERRIDE:
    PAGE_SECTION[p] = 'om-decomp'

# Fill gaps so every PDF page appears in exactly one section
prev_sid = 'om-overview'
for p in range(1, 271):
    if p in PAGE_SECTION:
        prev_sid = PAGE_SECTION[p]
    else:
        PAGE_SECTION[p] = prev_sid

for p in DECOMP_OVERRIDE:
    PAGE_SECTION[p] = 'om-decomp'

SIDEBAR = [
    ('om-overview', '1. OM Overview'),
    ('om-decomp', '2. Order Decomposition'),
    ('om-decomp-orch', '3. Decomp vs Orchestration'),
    ('om-plan-def', '4. Swimlanes & Plans'),
    ('om-generate', '5. Generate Plans'),
    ('om-item-types', '6. Item Types'),
    ('om-scenarios', '7. Scenarios'),
    ('om-dependencies', '8. Dependencies'),
    ('om-manual', '9. Manual Tasks'),
    ('om-auto', '10. Auto Tasks'),
    ('om-callouts', '11. Callouts'),
    ('om-fallout', '12. Fallout Management'),
    ('om-push', '13. Push Events'),
    ('om-macd-1to1', '14. MACD 1:1'),
    ('om-macd-disconnect', '15. MACD Disconnect'),
    ('om-macd-1tom', '16. MACD 1:M'),
    ('om-cancel', '17. Cancellation'),
    ('om-rollback', '18. Rollback Groups'),
    ('om-challenge', '19. Advanced Challenge'),
    ('om-ref', 'Quick Reference'),
]

SECTION_CONTENT: dict[str, str] = {}


def render_pages(pdf: fitz.Document) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    mat = fitz.Matrix(ZOOM, ZOOM)
    for i in range(len(pdf)):
        page_num = i + 1
        out_path = OUT / f'page-{page_num:04d}.png'
        if out_path.exists():
            continue
        pix = pdf[i].get_pixmap(matrix=mat, alpha=False)
        pix.save(str(out_path))
        if page_num % 50 == 0:
            print(f'  rendered page {page_num}/{len(pdf)}')


def fig_grid(pages: list[int], heading: str) -> str:
    if not pages:
        return ''
    figures = []
    for p in sorted(set(pages)):
        src = f'assets/om/pdf-pages/page-{p:04d}.png'
        figures.append(
            f'        <figure class="doc-screenshot" id="om-page-{p:04d}">\n'
            f'          <a href="{src}" target="_blank" rel="noopener">'
            f'<img loading="lazy" src="{src}" alt="Order Orchestration EG page {p}"></a>\n'
            f'          <figcaption><strong>PDF page {p}.</strong> Order Orchestration Exercise Guide</figcaption>\n'
            f'        </figure>'
        )
    return (
        f'\n      <h3>{heading}</h3>\n'
        f'      <div class="pdf-fig-grid">\n'
        + '\n'.join(figures)
        + '\n      </div>\n'
    )


def pages_for(section_id: str) -> list[int]:
    return sorted(
        p for p, s in PAGE_SECTION.items()
        if s == section_id and p not in EXCLUDE_PAGES
    )


def build_panel() -> str:
    sidebar = '\n'.join(f'    <a href="#{sid}">{label}</a>' for sid, label in SIDEBAR)

    section_ids = [
        'om-overview', 'om-decomp', 'om-decomp-orch', 'om-plan-def', 'om-generate',
        'om-item-types', 'om-scenarios', 'om-dependencies', 'om-manual', 'om-auto',
        'om-callouts', 'om-fallout', 'om-push', 'om-macd-1to1', 'om-macd-disconnect',
        'om-macd-1tom', 'om-cancel', 'om-rollback', 'om-challenge', 'om-ref',
    ]
    fig_headings = {
        'om-overview': 'PDF Screenshots — Overview & Table of Contents',
        'om-decomp': 'PDF Screenshots — Decomposition Models & Configuration',
        'om-decomp-orch': 'PDF Screenshots — Decomposition vs Orchestration',
        'om-plan-def': 'PDF Screenshots — Plan Definitions & Swimlanes',
        'om-generate': 'PDF Screenshots — Generating Orchestration Plans',
        'om-item-types': 'PDF Screenshots — Item Types & State Flow',
        'om-scenarios': 'PDF Screenshots — Orchestration Scenarios',
        'om-dependencies': 'PDF Screenshots — Dependency Definitions',
        'om-manual': 'PDF Screenshots — Manual Tasks & Queues',
        'om-auto': 'PDF Screenshots — Auto Tasks',
        'om-callouts': 'PDF Screenshots — Systems, Callouts & Installation Plan',
        'om-fallout': 'PDF Screenshots — Fallout & Retry Policies',
        'om-push': 'PDF Screenshots — Push Events',
        'om-macd-1to1': 'PDF Screenshots — MACD 1:1 (Exercise 6-9)',
        'om-macd-disconnect': 'PDF Screenshots — MACD Disconnect (Exercise 6-10)',
        'om-macd-1tom': 'PDF Screenshots — MACD 1:M & Streaming TV (Exercise 6-11)',
        'om-cancel': 'PDF Screenshots — In-Flight Cancellation (Exercise 6-12)',
        'om-rollback': 'PDF Screenshots — Rollback Groups & Smart Freeze (Exercise 6-13)',
        'om-challenge': 'PDF Screenshots — Advanced Challenge (Exercise 6-14)',
    }

    sections_html = []
    for sid in section_ids:
        body = OM_SECTIONS[sid]
        if sid != 'om-ref':
            body += fig_grid(pages_for(sid), fig_headings.get(sid, 'PDF Screenshots'))
        sections_html.append(f'    <section id="{sid}">\n{body}\n    </section>')

    main = '\n\n'.join(sections_html)
    return f'''<!-- ===================== ORDER MANAGEMENT PANEL ===================== -->
<div id="panel-om" class="module-panel">
<div class="layout">
  <nav class="sidebar" data-panel="om">
    <h3>Order Management</h3>
{sidebar}
  </nav>
  <main class="main">

{main}

  </main>
</div>
</div><!-- end panel-om -->
'''


def replace_panel(html: str, new_panel: str) -> str:
    pattern = r'<!-- ===================== ORDER MANAGEMENT PANEL ===================== -->.*?<!-- end panel-om -->'
    m = re.search(pattern, html, re.S)
    if not m:
        raise SystemExit('OM panel not found in index.html')
    return html[: m.start()] + new_panel + html[m.end() :]


def main() -> None:
    print('Opening PDF...')
    pdf = fitz.open(PDF)
    print(f'Rendering {len(pdf)} pages to {OUT}...')
    render_pages(pdf)
    print('Building OM panel HTML...')
    panel = build_panel()
    html = HTML.read_text(encoding='utf-8')
    html = replace_panel(html, panel)
    HTML.write_text(html, encoding='utf-8')
    print(f'Updated {HTML}')
    print(f'Pages mapped: {len(PAGE_SECTION)}')
    for sid, label in SIDEBAR:
        n = len(pages_for(sid))
        if n:
            print(f'  {sid}: {n} pages')


if __name__ == '__main__':
    main()
