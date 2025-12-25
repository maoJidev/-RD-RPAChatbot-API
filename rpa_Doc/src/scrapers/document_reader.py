import json
import os
from urllib.parse import urljoin
from playwright.sync_api import Page, TimeoutError
from src.config.settings import FILE_PATHS, SCRAPER_CONFIG

INPUT_FILE = FILE_PATHS["month_document_urls"]
OUTPUT_FILE = FILE_PATHS["month_document_contents"]

def extract_field_from_table(page: Page, label: str) -> str:
    """ดึงข้อมูลจาก table row <tr> ที่มี label"""
    try:
        row = page.locator(f"xpath=//tr[td/strong[contains(normalize-space(), '{label}')]]").first
        if row.count() == 0:
            return ""
        content = row.locator("td").nth(1).inner_text().strip()
        if content.startswith(":"):
            content = content[1:].strip()
        return content
    except Exception as e:
        print(f"⚠️ ดึงข้อมูล '{label}' ไม่ได้: {e}")
        return ""

def read_documents_from_table_list(page: Page) -> list[dict]:
    """อ่านหน้า list ที่เป็น table"""
    results = []
    container = page.locator("div[id^='c'] table tbody")
    topic_rows = container.locator("xpath=.//tr[td//span[contains(normalize-space(), 'เรื่อง')]]")
    count = topic_rows.count()
    print(f"📌 ตรวจพบหน้า list มี {count} รายการ")

    for i in range(count):
        row = topic_rows.nth(i)
        link = row.locator("a").first
        title = link.inner_text().strip()
        href = link.get_attribute("href")
        url = urljoin(page.url, href)

        detail_row = row.locator("xpath=following-sibling::tr[1]")
        detail_text = detail_row.inner_text()

        def extract(label: str) -> str:
            if label in detail_text:
                return detail_text.split(label, 1)[1].strip().split("\n")[0]
            return ""

        results.append({
            "title": title,
            "url": url,
            "เลขที่หนังสือ": extract("เลขที่หนังสือ"),
            "วันที่": extract("วันที่"),
        })
    return results

def read_single_document(page: Page, url: str, fallback_title: str):
    """อ่านหน้าเอกสาร 1 URL (auto detect หน้า list / detail)"""
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=SCRAPER_CONFIG["page_timeout"] * 1.5)
    except TimeoutError:
        print(f"⚠️ โหลดหน้าเว็บ timeout: {url}")
        return {"title": fallback_title, "url": url, "error": "timeout"}

    if page.locator("span:has-text('เรื่อง')").count() > 1:
        print("📄 เป็นหน้า list แบบ table")
        return read_documents_from_table_list(page)

    return {
        "title": fallback_title,
        "url": url,
        "เลขที่หนังสือ": extract_field_from_table(page, "เลขที่หนังสือ"),
        "วันที่": extract_field_from_table(page, "วันที่"),
        "เรื่อง": extract_field_from_table(page, "เรื่อง"),
        "ข้อกฎหมาย": extract_field_from_table(page, "ข้อกฎหมาย"),
        "ข้อหารือ": extract_field_from_table(page, "ข้อหารือ"),
        "แนววินิจฉัย": extract_field_from_table(page, "แนววินิจฉัย"),
    }

def run_read_document_content(page: Page):
    """Main task: อ่านเอกสารทั้งหมดของแต่ละเดือน"""
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        months = json.load(f)

    results = []
    total_links = 0
    total_documents = 0

    for m in months:
        print(f"\n📅 ปี {m['year']} เดือน {m['month']}")
        documents = []
        month_documents_count = 0

        for item in m.get("links", []):
            total_links += 1
            print(f"   🔗 {item['url']}")
            data = read_single_document(page, item["url"], item.get("title", ""))

            if isinstance(data, list):
                documents.extend(data)
                month_documents_count += len(data)
                total_documents += len(data)
            else:
                documents.append(data)
                month_documents_count += 1
                total_documents += 1

        print(f"   ✅ เดือนนี้อ่านได้ {month_documents_count} เอกสาร")
        results.append({
            "year": m["year"],
            "month": m["month"],
            "month_no": m.get("month_no", ""),
            "documents": documents
        })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n📊 สรุปผลการอ่านเอกสารทั้งหมด")
    print(f"🔗 URL ที่พยายามอ่านทั้งหมด : {total_links}")
    print(f"📄 เอกสารที่อ่านได้จริง    : {total_documents}")
    print(f"💾 บันทึกไฟล์แล้วที่        : {OUTPUT_FILE}")

if __name__ == "__main__":
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        run_read_document_content(page)
        browser.close()
