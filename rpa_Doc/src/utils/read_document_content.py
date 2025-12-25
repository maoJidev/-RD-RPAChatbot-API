import json
import os
from urllib.parse import urljoin
from playwright.sync_api import Page, TimeoutError

OUTPUT_DIR = "output"
INPUT_FILE = os.path.join(OUTPUT_DIR, "month_document_urls.json")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "month_document_contents.json")

# ------------------------------------------------------------------
# Utils: อ่าน field จาก table (หน้า detail)
# ------------------------------------------------------------------
def extract_field_from_table(page: Page, label: str) -> str:
    """
    ดึงข้อมูลจาก table row <tr> ที่มี label
    เช่น 'เรื่อง', 'เลขที่หนังสือ', 'ข้อหารือ'
    """
    try:
        row = page.locator(
            f"xpath=//tr[td/strong[contains(normalize-space(), '{label}')]]"
        ).first

        if row.count() == 0:
            return ""

        content = row.locator("td").nth(1).inner_text().strip()
        if content.startswith(":"):
            content = content[1:].strip()

        return content

    except Exception as e:
        print(f"⚠️ ดึงข้อมูล '{label}' ไม่ได้: {e}")
        return ""

# ------------------------------------------------------------------
# อ่านหน้า list แบบ table (1 เรื่อง = 2 tr)
# ------------------------------------------------------------------
def read_documents_from_table_list(page: Page) -> list[dict]:
    """
    อ่านหน้า list ที่เป็น table:
    - เลือกเฉพาะ tr ที่มีคำว่า 'เรื่อง'
    - tr ถัดไป = เลขที่หนังสือ + วันที่
    - ตัด pagination / header / footer ทิ้ง
    """
    results = []

    # จำกัด scope แค่เนื้อหา ป้องกัน header/footer
    container = page.locator("div[id^='c'] table tbody")

    topic_rows = container.locator(
        "xpath=.//tr[td//span[contains(normalize-space(), 'เรื่อง')]]"
    )

    count = topic_rows.count()
    print(f"📌 ตรวจพบหน้า list มี {count} รายการ")

    for i in range(count):
        row = topic_rows.nth(i)

        # ---- เรื่อง + link ----
        link = row.locator("a").first
        title = link.inner_text().strip()
        href = link.get_attribute("href")
        url = urljoin(page.url, href)

        # ---- tr ถัดไป: เลขที่หนังสือ + วันที่ ----
        detail_row = row.locator("xpath=following-sibling::tr[1]")
        detail_text = detail_row.inner_text()

        def extract(label: str) -> str:
            if label in detail_text:
                return (
                    detail_text
                    .split(label, 1)[1]
                    .strip()
                    .split("\n")[0]
                )
            return ""

        book_no = extract("เลขที่หนังสือ")
        date = extract("วันที่")

        results.append({
            "title": title,
            "url": url,
            "เลขที่หนังสือ": book_no,
            "วันที่": date,
        })

    return results

# ------------------------------------------------------------------
# อ่านหน้าเอกสาร 1 URL (auto detect หน้า list / detail)
# ------------------------------------------------------------------
def read_single_document(page: Page, url: str, fallback_title: str):
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
    except TimeoutError:
        print(f"⚠️ โหลดหน้าเว็บ timeout: {url}")
        return {
            "title": fallback_title,
            "url": url,
            "error": "timeout"
        }

    # -------------------------
    # ตรวจว่าเป็นหน้า list หรือไม่
    # -------------------------
    if page.locator("span:has-text('เรื่อง')").count() > 1:
        print("📄 เป็นหน้า list แบบ table")
        return read_documents_from_table_list(page)

    # -------------------------
    # หน้า detail ปกติ
    # -------------------------
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

# ------------------------------------------------------------------
# Main task: อ่านเอกสารทั้งหมดของแต่ละเดือน
# ------------------------------------------------------------------
def run_read_document_content(page: Page):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        months = json.load(f)

    results = []

    # =========================
    # NEW: ตัวนับทั้งหมด
    # =========================
    total_links = 0
    total_documents = 0

    for m in months:
        print(f"\n📅 ปี {m['year']} เดือน {m['month']}")

        documents = []
        month_documents_count = 0  # NEW: นับต่อเดือน

        for item in m.get("links", []):
            total_links += 1
            print(f"   🔗 {item['url']}")

            data = read_single_document(
                page,
                item["url"],
                item.get("title", "")
            )

            # ถ้าเป็น list → แตกหลายเอกสาร
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

    # =========================
    # NEW: สรุปผลรวมทั้งหมด
    # =========================
    print("\n📊 สรุปผลการอ่านเอกสารทั้งหมด")
    print(f"🔗 URL ที่พยายามอ่านทั้งหมด : {total_links}")
    print(f"📄 เอกสารที่อ่านได้จริง    : {total_documents}")
    print(f"💾 บันทึกไฟล์แล้วที่        : {OUTPUT_FILE}")

# ------------------------------------------------------------------
# Debug run (standalone)
# ------------------------------------------------------------------
if __name__ == "__main__":
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        run_read_document_content(page)
        browser.close()
