# tasks.py
from robocorp.tasks import task
from robocorp.browser import browser
import json

from src.config.settings import FILE_PATHS
from src.utils.document_filter_by_title import filter_documents_by_keywords
from src.utils.document_summarizer import summarize_documents

from src.scrapers.year_collector import collect_years
from src.scrapers.month_collector import collect_months
from src.scrapers.document_url_collector import run_collect_month_urls
from src.scrapers.document_reader import run_read_document_content
from src.utils.document_filter import run_filter_documents
from src.utils.cleanup import clean_logs

# To run a task use: python -m robocorp.tasks run tasks.py -t <TaskName>

@task
def run_year():
    with browser() as b:
        page = b.new_page()
        print("📌 Stage 1: เก็บปี")
        collect_years(page)

@task
def run_month():
    with browser() as b: 
        page = b.new_page()
        print("📌 Stage 2: เก็บเดือน")
        collect_months(page)

@task
def run_collect_month_urls_task():
    with browser() as b:
        page = b.new_page()
        print("📌 Stage 3: เก็บลิงก์เอกสารจากเดือน")
        run_collect_month_urls(page)

@task
def run_read_document_content_task():
    with browser() as b:
        page = b.new_page()
        print("📌 Stage 4: อ่านเนื้อหาเอกสาร")
        run_read_document_content(page)

@task
def run_filter_documents_task():
    print("📌 Stage 5: กรองข้อมูลที่สมบูรณ์")
    run_filter_documents()

@task
def run_filter_documents_by_title_task():
    """
    Task: กรองเอกสารตาม title keyword
    """
    print("📌 Stage 6: กรองเอกสารตาม title keyword")

    input_file = FILE_PATHS["month_document_contents_filtered"]
    with open(input_file, "r", encoding="utf-8") as f:
        all_documents = json.load(f)

    documents = []
    for month in all_documents:
        for doc in month.get("documents", []):
            documents.append({
                "title": doc.get("เรื่อง", ""),
                "content": doc.get("แนววินิจฉัย", "")
            })

    # กำหนด keyword หลัก ๆ ที่สนใจ
    target_keywords = ["ภาษีมูลค่าเพิ่ม", "อาหารสัตว์"]

    filtered_documents = filter_documents_by_keywords(documents, target_keywords)
    print(f"   🔎 เอกสารหลังกรอง: {len(filtered_documents)} เรื่อง")

    output_file = FILE_PATHS["month_document_urls_filtered"]
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(filtered_documents, f, ensure_ascii=False, indent=2)

    print(f"💾 บันทึกไฟล์ filtered เรียบร้อย: {output_file}")

@task
def run_summarize_filtered_documents_task():
    """
    Task: สรุปเอกสารหลังกรอง title keyword
    """
    print("📌 Stage 7: สรุปเอกสารหลังกรอง")
    input_file = FILE_PATHS["month_document_urls_filtered"]

    with open(input_file, "r", encoding="utf-8") as f:
        documents = json.load(f)

    summaries = summarize_documents(documents)

    output_file = FILE_PATHS["month_document_urls_summary"]
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(summaries, f, ensure_ascii=False, indent=2)

    print(f"💾 บันทึกไฟล์ summary เรียบร้อย: {output_file}")

@task
def run_cleanup():
    """
    Task: ลบไฟล์ขยะ (logs) ในโฟลเดอร์ output
    """
    clean_logs()
