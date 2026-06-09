"""Move CPQ PDF figures from #cpq-figures into relevant topic sections."""
import re
from pathlib import Path

HTML = Path(r'e:\Study\index.html')

FIG_GROUP_TO_SECTION = {
    'cpq-fig-order-capture-pricing-flow': 'cpq-flow',
    'cpq-fig-vlocity-cart-cards': 'cpq-cart',
    'cpq-fig-asset-based-ordering-abo': 'cpq-macd',
    'cpq-fig-order-quote-manager-legacy': 'cpq-cart',
    'cpq-fig-pricing-hooks-matrices': 'cpq-pricing',
    'cpq-fig-context-rules-framework': 'cpq-rules',
    'cpq-fig-advanced-rules-framework': 'cpq-rules',
    'cpq-fig-promotions-discounts': 'cpq-promotions',  # split below by fig num
    'cpq-fig-change-of-plans-multiplay': 'cpq-change-plans',
}

# Figures routed outside their group default
FIG_NUM_SECTION = {
    88: 'cpq-pricing',  # Price Book Entry Edit Page
    11: 'cpq-cards',    # Assets cards VF page
}


def figure_section(fig_num: int, group_id: str) -> str:
    if fig_num in FIG_NUM_SECTION:
        return FIG_NUM_SECTION[fig_num]
    if group_id == 'cpq-fig-promotions-discounts' and fig_num >= 89:
        return 'cpq-promotions'
    if group_id == 'cpq-fig-promotions-discounts' and fig_num == 88:
        return 'cpq-pricing'
    return FIG_GROUP_TO_SECTION[group_id]


def screen_section(page: int) -> str:
    if page <= 9:
        return 'cpq-overview'
    if 275 <= page <= 297:
        return 'cpq-pricing'
    if 386 <= page <= 400:
        return 'cpq-cost-margin'
    if page == 559:
        return 'cpq-promotions'
    if 569 <= page <= 576:
        return 'cpq-flow-mgmt'
    if 578 <= page <= 599:
        return 'cpq-promotions'
    if 600 <= page <= 620:
        return 'cpq-discounts'
    if 628 <= page <= 644:
        return 'cpq-change-plans'
    if 651 <= page <= 663:
        return 'cpq-multisite'
    if page >= 675:
        return 'cpq-hooks'
    return 'cpq-overview'


def parse_figures_section(html: str) -> tuple[str, dict[str, list[str]]]:
    start = html.find('    <section id="cpq-figures">')
    end = html.find('    </section>\n\n    <section id="cpq-macd">')
    if start == -1 or end == -1:
        raise SystemExit('cpq-figures section not found')

    block = html[start:end + len('    </section>')]
    rest = html[:start] + html[end + len('    </section>\n\n'):]

    buckets: dict[str, list[str]] = {}
    current_group = None

    # Split by h3 tags
    parts = re.split(r'(<h3[^>]*id="([^"]+)"[^>]*>.*?</h3>)', block, flags=re.S)
    i = 0
    while i < len(parts):
        part = parts[i]
        if i + 1 < len(parts) and parts[i].startswith('<h3'):
            h3_html = parts[i]
            group_id = parts[i + 1]
            i += 2
            content = parts[i] if i < len(parts) else ''
            i += 1

            if group_id in ('cpq-pdf-figures', 'cpq-pdf-screens'):
                # handle screens separately
                if group_id == 'cpq-pdf-screens':
                    for fig in re.findall(r'(<figure class="doc-screenshot"[\s\S]*?</figure>)', content):
                        m = re.search(r'screen-page-(\d+)\.png', fig)
                        if m:
                            page = int(m.group(1))
                            sec = screen_section(page)
                            buckets.setdefault(sec, []).append(fig.strip())
                continue

            title_match = re.search(r'<h3[^>]*>(.*?)</h3>', h3_html, re.S)
            title = re.sub(r'<[^>]+>', '', title_match.group(1)) if title_match else group_id

            for fig in re.findall(r'(<figure class="doc-screenshot"[\s\S]*?</figure>)', content):
                fig = fig.strip()
                m = re.search(r'id="fig-(\d+)"', fig)
                fig_num = int(m.group(1)) if m else 0
                sec = figure_section(fig_num, group_id)
                heading = f'      <h3>PDF Figures — {title}</h3>\n      <div class="pdf-fig-grid">\n'
                # Store with metadata for dedupe heading per section+title
                buckets.setdefault(sec, [])
                # Avoid duplicate figures in same bucket
                if fig not in buckets[sec]:
                    buckets[sec].append(('__HEADING__', title, heading))
                    buckets[sec].append(fig)
        else:
            i += 1

    return rest, buckets


def build_insertions(buckets: dict[str, list]) -> dict[str, str]:
    out = {}
    for sec, items in buckets.items():
        chunks = []
        current_title = None
        grid_open = False
        for item in items:
            if isinstance(item, tuple) and item[0] == '__HEADING__':
                title = item[1]
                if title != current_title:
                    if grid_open:
                        chunks.append('      </div>\n')
                    chunks.append(f'      <h3>PDF Screenshots — {title}</h3>\n      <div class="pdf-fig-grid">\n')
                    current_title = title
                    grid_open = True
            else:
                if not grid_open:
                    chunks.append('      <h3>PDF Screenshots</h3>\n      <div class="pdf-fig-grid">\n')
                    grid_open = True
                chunks.append('        ' + item.replace('\n', '\n        ') + '\n')
        if grid_open:
            chunks.append('      </div>\n')
        if chunks:
            out[sec] = '\n' + ''.join(chunks)
    return out


def insert_into_sections(html: str, insertions: dict[str, str]) -> str:
    for sec_id, content in insertions.items():
        marker = f'    <section id="{sec_id}">'
        start = html.find(marker)
        if start == -1:
            print(f'WARN: section {sec_id} not found')
            continue
        close = html.find('    </section>', start)
        if close == -1:
            continue
        html = html[:close] + content + '\n' + html[close:]
    return html


def main():
    html = HTML.read_text(encoding='utf-8')
    html, buckets = parse_figures_section(html)
    insertions = build_insertions(buckets)
    html = insert_into_sections(html, insertions)

    html = html.replace('    <a href="#cpq-figures">CPQ PDF Screens (94 Figs)</a>\n', '')

    # Clean duplicate heading logic - rebuild with simpler approach
    HTML.write_text(html, encoding='utf-8')
    total_figs = sum(
        1 for sec in buckets.values()
        for x in sec if not (isinstance(x, tuple) and x[0] == '__HEADING__')
    )
    print(f'Distributed {total_figs} figures/screens to {len(insertions)} sections')
    print('Sections:', ', '.join(sorted(insertions.keys())))
    print('cpq-figures removed:', 'cpq-figures' not in html)


if __name__ == '__main__':
    main()
