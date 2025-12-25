import json
import os
from urllib.parse import urljoin
from playwright.sync_api import Page
from src.config.settings import FILE_PATHS, TH_MONTH_MAP, SCRAPER_CONFIG

def collect_months(page: Page):
    """
    Scrapes available months for each year collected in the previous stage.
    
    Args:
        page (Page): Playwright page object.
        
    Returns:
        None: Saves the results to a JSON file defined in settings.
    """
    output_file = FILE_PATHS["months"]
    year_file = FILE_PATHS["years"]
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    if not os.path.exists(year_file):
        print(f"❌ ไม่พบไฟล์ปี {year_file}")
        return

    with open(year_file, "r", encoding="utf-8") as f:
        years = json.load(f)

    months = []
    seen = set()

    for y in years:
        page.goto(y["url"])

        # Wait for the month sub-menu to load
        try:
            page.wait_for_selector(
                SCRAPER_CONFIG["month_selector"],
                timeout=SCRAPER_CONFIG["selector_timeout"]
            )
        except Exception:
            print(f"⚠️ ไม่พบข้อมูลเดือนสำหรับปี {y['year']}")
            continue

        month_links = page.locator(SCRAPER_CONFIG["month_selector"]).all()

        for a in month_links:
            month_name = a.inner_text().strip()
            month_no = TH_MONTH_MAP.get(month_name)

            # Skip if not a valid month name
            if not month_no:
                continue

            href = a.get_attribute("href")
            full_url = urljoin(page.url, href)

            key = (y["year"], month_no)
            if key in seen:
                continue
            seen.add(key)

            months.append({
                "year": y["year"],
                "month": month_name,
                "month_no": month_no,
                "url": full_url
            })

    # Sort by year (desc) and then month number (desc)
    months.sort(
        key=lambda x: (int(x["year"]), x["month_no"]),
        reverse=True
    )

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(months, f, ensure_ascii=False, indent=2)

    print(f"✅ บันทึกเดือนทั้งหมด {len(months)} รายการ -> {output_file}")
