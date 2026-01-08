# src/config/settings.py
import os

OUTPUT_DIR = "output"

FILE_PATHS = {
    "years": os.path.join(OUTPUT_DIR, "years.json"),
    "months": os.path.join(OUTPUT_DIR, "months.json"),
    "month_document_urls": os.path.join(OUTPUT_DIR, "month_document_urls.json"),
    "month_document_contents": os.path.join(OUTPUT_DIR, "month_document_contents.json"),
    "month_document_contents_filtered": os.path.join(OUTPUT_DIR, "month_document_contents_filtered.json"),
    
    # สำหรับ stage 6 & 7
    "month_document_urls_filtered": os.path.join(OUTPUT_DIR, "month_document_urls_filtered.json"),
    "month_document_urls_summary": os.path.join(OUTPUT_DIR, "month_document_urls_summary.json"),

    # RAG files
    "tfidf_embeddings": os.path.join(OUTPUT_DIR, "tfidf_embeddings.pkl"),
}

SCRAPER_CONFIG = {
    "base_url": "https://www.rd.go.th/68047.html",
    "year_selector": "div[id^='c'] ul li a",
    "month_selector": "div[id^='c'] ul li a",
    "page_timeout": 60000,
    "selector_timeout": 15000,
    "sleep_short": (400, 800),
    "sleep_detail": (800, 1500),
    "error_sleep_sec": 3,
    "max_docs_per_month": None,
}

# Ollama Configuration (using IP Server Computer)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

RAG_CONFIG = {
    "model": "qwen2.5:7b",
    "top_k": 2,
    "min_similarity": 0.05,
    "strict_mode": True,
    "strict_threshold": 0.05,
    "rewrite_question": False,
    "enable_fallback": False,
    "debug": True
}

TH_MONTH_MAP = {
    "มกราคม": 1, "กุมภาพันธ์": 2, "มีนาคม": 3, "เมษายน": 4,
    "พฤษภาคม": 5, "มิถุนายน": 6, "กรกฎาคม": 7, "สิงหาคม": 8,
    "กันยายน": 9, "ตุลาคม": 10, "พฤศจิกายน": 11, "ธันวาคม": 12,
}
