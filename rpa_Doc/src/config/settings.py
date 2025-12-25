"""
Configuration settings for RPA Document Scraper
รวม constants และ configuration ทั้งหมดไว้ที่นี่
"""
import os

# =============================================================================
# Directory Paths
# =============================================================================
OUTPUT_DIR = "output"

# =============================================================================
# File Paths
# =============================================================================
FILE_PATHS = {
    # Scraper output files
    "years": os.path.join(OUTPUT_DIR, "years.json"),
    "months": os.path.join(OUTPUT_DIR, "months.json"),
    "month_document_urls": os.path.join(OUTPUT_DIR, "month_document_urls.json"),
    "month_document_contents": os.path.join(OUTPUT_DIR, "month_document_contents.json"),
    "month_document_contents_filtered": os.path.join(OUTPUT_DIR, "month_document_contents_filtered.json"),
    
    # RAG files
    "tfidf_embeddings": os.path.join(OUTPUT_DIR, "tfidf_embeddings.pkl"),
}

# =============================================================================
# Scraper Configuration
# =============================================================================
SCRAPER_CONFIG = {
    # Base URL
    "base_url": "https://www.rd.go.th/68047.html",
    
    # Timeouts (milliseconds)
    "page_timeout": 20000,
    "selector_timeout": 10000,
    
    # Sleep times (milliseconds) - for human-like behavior
    "sleep_short": (400, 800),
    "sleep_detail": (800, 1500),
    "error_sleep_sec": 3,
    
    # Limits
    "max_docs_per_month": None,  # None = no limit
}

# =============================================================================
# RAG Configuration
# =============================================================================
RAG_CONFIG = {
    # Ollama model
    "model": "qwen3:4b",
    
    # Retrieval settings
    "top_k": 2,  # จำนวน documents ที่ retrieve
    
    # Timeout
    "ollama_timeout": 180,  # seconds
}

# =============================================================================
# Thai Month Mapping
# =============================================================================
TH_MONTH_MAP = {
    "มกราคม": 1,
    "กุมภาพันธ์": 2,
    "มีนาคม": 3,
    "เมษายน": 4,
    "พฤษภาคม": 5,
    "มิถุนายน": 6,
    "กรกฎาคม": 7,
    "สิงหาคม": 8,
    "กันยายน": 9,
    "ตุลาคม": 10,
    "พฤศจิกายน": 11,
    "ธันวาคม": 12,
}
