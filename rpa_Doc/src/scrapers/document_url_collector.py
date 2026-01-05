import json
import os
import re
from urllib.parse import urljoin
from playwright.sync_api import Page
from src.config.settings import FILE_PATHS, SCRAPER_CONFIG

MONTHS_FILE = FILE_PATHS["months"]
OUTPUT_FILE = FILE_PATHS["month_document_urls"]
DOC_PATTERN = re.compile(r"/\d+\.html$")


def collect_from_special_table(page: Page):
    """
    อ่าน table โครงสร้างพิเศษของ RD
    1 เรื่อง = 2 <tr>
    """
    links = []
    collected_urls = set()

    container = page.locator("div[id^='c'] table tbody")
    rows = container.locator("tr").all()

    i = 0
    while i < len(rows):
        row = rows[i]

        if row.locator("span:has-text('เรื่อง')").count() > 0:
            a = row.locator("a").first
            title = a.inner_text().strip()
            href = a.get_attribute("href")

            if title and href and DOC_PATTERN.search(href):
                full_url = urljoin(page.url, href)
                if full_url not in collected_urls:
                    collected_urls.add(full_url)
                    links.append({
                        "title": title,
                        "url": full_url
                    })
            i += 2
        else:
            i += 1

    return links


def collect_all_document_links(page: Page, month_url: str):
    """
    เก็บลิงก์เอกสารทั้งหมดของ 1 เดือน (รวม pagination)
    """
    links = []
    collected_urls = set()
    visited_pages = set()

    page.goto(month_url, timeout=SCRAPER_CONFIG["page_timeout"])
    page.wait_for_load_state("domcontentloaded")

    while True:
        if page.url in visited_pages:
            break
        visited_pages.add(page.url)

        try:
            page.wait_for_selector("table", timeout=SCRAPER_CONFIG["selector_timeout"])
        except Exception:
            print(f"[WARN] No table found on {page.url} (Might be empty or slow)")
            break

        # โครงสร้าง table พิเศษ (RD)
        special_links = collect_from_special_table(page)
        for item in special_links:
            if item["url"] not in collected_urls:
                collected_urls.add(item["url"])
                links.append(item)

        # fallback table ทั่วไป (กันกรณีบางหน้า layout ต่าง)
        rows = page.locator("table tr").all()
        for row in rows:
            tds = row.locator("td").all()
            if len(tds) < 2:
                continue

            anchors = tds[1].locator("a").all()
            for a in anchors:
                try:
                    title = a.inner_text().strip()
                    href = a.get_attribute("href")

                    if not title or not href or not DOC_PATTERN.search(href):
                        continue

                    full_url = urljoin(page.url, href)
                    if full_url not in collected_urls:
                        collected_urls.add(full_url)
                        links.append({
                            "title": title,
                            "url": full_url
                        })
                except Exception:
                    continue

        # pagination
        pager_links = page.locator("p.text-right a, div[align='right'] a").all()
        next_page = None

        for a in pager_links:
            txt = a.inner_text().strip()
            href = a.get_attribute("href")

            if txt.isdigit() and href:
                candidate = urljoin(page.url, href)
                if candidate not in visited_pages:
                    next_page = candidate
                    break

        if next_page:
            page.goto(next_page, timeout=SCRAPER_CONFIG["page_timeout"])
            page.wait_for_load_state("domcontentloaded")
        else:
            break

    return links


def run_collect_month_urls(page: Page):
    """
    Main task: เก็บลิงก์เอกสารจากทุกเดือน
    """
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(MONTHS_FILE, "r", encoding="utf-8") as f:
        months = json.load(f)

    results = []
    total_months = 0
    total_documents = 0

    for m in months:
        total_months += 1
        print(f"[INFO] Processing {m['year']} {m['month']}")

        links = collect_all_document_links(page, m["url"])
        print(f"[INFO] Found {len(links)} documents")

        total_documents += len(links)

        results.append({
            "year": m["year"],
            "month": m["month"],
            "month_no": m["month_no"],
            "month_url": m["url"],
            "total_documents": len(links),
            "documents": links
        })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("[SUMMARY]")
    print(f"Processed months : {total_months}")
    print(f"Total documents : {total_documents}")
    print(f"Output file     : {OUTPUT_FILE}")
