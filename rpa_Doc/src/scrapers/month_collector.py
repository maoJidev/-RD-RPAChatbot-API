import json
import os
from urllib.parse import urljoin
from playwright.sync_api import Page
from src.config.settings import FILE_PATHS, TH_MONTH_MAP

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

    # โหลด JSON ปี
    with open(year_file, "r", encoding="utf-8") as f:
        years = json.load(f)

    months = []
    seen = set()

    for y in years:
        print(f"➡️ กำลังเข้า URL ปี: {y['year']} -> {y['url']}")
        page.goto(y["url"])
        page.wait_for_load_state("networkidle")

        # ดึง link ทั้งหมด
        all_links = page.locator("a").all()
        
        # filter link ที่ title เป็นชื่อเดือน
        month_links = [a for a in all_links if a.get_attribute("title") in TH_MONTH_MAP.keys()]
        print(f"🔹 เจอ {len(month_links)} link เดือน")

        for a in month_links:
            month_name = a.inner_text().strip()
            month_no = TH_MONTH_MAP.get(month_name)
            if not month_no:
                print(f"❌ ชื่อเดือนไม่ตรงกับ map: {month_name}")
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

    # Sort by year (desc) และ month_no (desc)
    months.sort(key=lambda x: (int(x["year"]), x["month_no"]), reverse=True)

    # บันทึก JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(months, f, ensure_ascii=False, indent=2)

    print(f"✅ บันทึกเดือนทั้งหมด {len(months)} รายการ -> {output_file}")
