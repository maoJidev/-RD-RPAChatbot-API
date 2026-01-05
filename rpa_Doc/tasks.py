import os
import json
import traceback
from robocorp.tasks import task
from robocorp.browser import browser

from src.config.settings import FILE_PATHS
from src.utils.document_filter_by_title import filter_documents_by_keywords
from src.utils.document_summarizer import summarize_documents

from src.scrapers.year_collector import collect_years
from src.scrapers.month_collector import collect_months
from src.scrapers.document_url_collector import run_collect_month_urls
from src.scrapers.document_reader import run_read_document_content
from src.utils.document_filter import run_filter_documents
from src.utils.cleanup import clean_logs


def _check_file_exists(file_path: str, stage_name: str):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"[{stage_name}] Failed: Output file not found at {file_path}")
    print(f"[VERIFY] {stage_name} output exists: {file_path}")


@task
def run_year():
    with browser() as b:
        page = b.new_page()
        print("[INFO] Stage 1: Collect years")
        collect_years(page)


@task
def run_month():
    with browser() as b:
        page = b.new_page()
        print("[INFO] Stage 2: Collect months")
        collect_months(page)


@task
def run_collect_month_urls_task():
    with browser() as b:
        page = b.new_page()
        print("[INFO] Stage 3: Collect document URLs")
        run_collect_month_urls(page)


@task
def run_read_document_content_task():
    with browser() as b:
        page = b.new_page()
        print("[INFO] Stage 4: Read document contents")
        run_read_document_content(page)


@task
def run_filter_documents_task():
    print("[INFO] Stage 5: Filter valid documents")
    run_filter_documents()


@task
def run_cleanup():
    print("[INFO] Stage 8: Cleanup logs")
    clean_logs()
    print("[OK] Cleanup completed")


@task
def run_all():
    """Run all scraper stages sequentially with high stability (Stage 1-5)"""
    print("[INFO] Starting Full Pipeline Execution...")
    
    try:
        with browser() as b:
            # ใช้หน้ากากอนามัย... เอ้ย page เดียวกันตลอดการรัน
            page = b.new_page()
            
            # Stage 1: Years
            print("\n>>> Stage 1: Year Collector")
            collect_years(page)
            _check_file_exists(FILE_PATHS["years"], "Stage 1")

            # Stage 2: Months
            print("\n>>> Stage 2: Month Collector")
            collect_months(page)
            _check_file_exists(FILE_PATHS["months"], "Stage 2")

            # Stage 3: URLs
            print("\n>>> Stage 3: URL Collector")
            run_collect_month_urls(page)
            _check_file_exists(FILE_PATHS["month_document_urls"], "Stage 3")

            # Stage 4: Content (The long one)
            print("\n>>> Stage 4: Content Reader")
            run_read_document_content(page)
            _check_file_exists(FILE_PATHS["month_document_contents"], "Stage 4")

        # Stage 5: Filter (No browser needed)
        print("\n>>> Stage 5: Data Filter")
        run_filter_documents()
        _check_file_exists(FILE_PATHS["month_document_contents_filtered"], "Stage 5")

        print("\n" + "="*40)
        print("[OK] FULL PIPELINE COMPLETED SUCCESSFULLY!")
        print("="*40)

    except Exception as e:
        print("\n" + "!"*40)
        print(f"[CRITICAL ERROR] Pipeline failed at some stage!")
        print(f"Error Details: {str(e)}")
        print("!"*40)
        traceback.print_exc()
        raise e
