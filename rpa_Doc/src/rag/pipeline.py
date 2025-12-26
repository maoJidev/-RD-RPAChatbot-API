# src/rag/pipeline.py
import json
import os
import pickle
import requests
import time
from typing import List, Dict, Any
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from src.config.settings import FILE_PATHS, RAG_CONFIG

# =========================
# Configuration & Constants
# =========================
# เลือกใช้ไฟล์ที่มี structure ชัดเจนกว่า (month_document_contents_filtered) จะแม่นยำกว่า urls_filtered
DOC_FILE = FILE_PATHS.get("month_document_contents_filtered", FILE_PATHS["month_document_urls_filtered"])
EMBED_FILE = FILE_PATHS["tfidf_embeddings"]
LOG_FILE = "output/pipeline_feedback.json"

TOP_K = RAG_CONFIG.get("top_k", 3)
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = RAG_CONFIG["model"]
DEBUG = True

# =========================
# 1. Document Loading & Preparation
# =========================
def load_documents() -> List[Dict]:
    """โหลดเอกสารและแปลงเป็น Chunks สำหรับ Search"""
    if not os.path.exists(DOC_FILE):
        raise FileNotFoundError(f"ไม่พบไฟล์เอกสาร: {DOC_FILE}")

    with open(DOC_FILE, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    chunks = []
    # รองรับ structure แบบ nested (contents_filtered) ที่คุณส่งตัวอย่างมา
    if isinstance(raw_data, list) and "month" in raw_data[0]:
        for month_data in raw_data:
            for doc in month_data.get("documents", []):
                # สร้าง text สำหรับ search โดยรวม title + ข้อหารือ + แนววินิจฉัย
                search_text = f"{doc.get('title', '')} {doc.get('ข้อหารือ', '')} {doc.get('แนววินิจฉัย', '')}"
                chunks.append({
                    "search_text": search_text,
                    "title": doc.get("title", ""),
                    "content": f"ข้อหารือ: {doc.get('ข้อหารือ', '')}\nแนววินิจฉัย: {doc.get('แนววินิจฉัย', '')}",
                    "full_obj": doc
                })
    
    # รองรับ structure แบบ flat (urls_filtered) เผื่อกรณีใช้ไฟล์เดิม
    else:
        for doc in raw_data:
            chunks.append({
                "search_text": f"{doc.get('title', '')} {doc.get('content', '')}",
                "title": doc.get("title", ""),
                "content": doc.get("content", ""),
                "full_obj": doc
            })
            
    if DEBUG: print(f"[INIT] Loaded {len(chunks)} documents.")
    return chunks

# =========================
# 2. Search Engine (TF-IDF)
# =========================
def get_retriever(chunks: List[Dict]):
    """Load or Create TF-IDF Embeddings"""
    corpus = [c["search_text"] for c in chunks]
    
    if os.path.exists(EMBED_FILE):
        with open(EMBED_FILE, "rb") as f:
            vectorizer, matrix = pickle.load(f)
        # Check consistency
        if matrix.shape[0] == len(chunks):
            return vectorizer, matrix
    
    # Re-create if not exists or count mismatch
    if DEBUG: print("[INDEX] Creating new TF-IDF index...")
    vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
    matrix = vectorizer.fit_transform(corpus)
    
    os.makedirs(os.path.dirname(EMBED_FILE), exist_ok=True)
    with open(EMBED_FILE, "wb") as f:
        pickle.dump((vectorizer, matrix), f)
        
    return vectorizer, matrix

def retrieve(question: str, chunks: List[Dict], top_k=TOP_K):
    vectorizer, matrix = get_retriever(chunks)
    q_vec = vectorizer.transform([question])
    scores = cosine_similarity(q_vec, matrix).flatten()
    
    # Get Top-K indices
    top_indices = scores.argsort()[::-1][:top_k]
    
    results = []
    for idx in top_indices:
        if scores[idx] < 0.05: # Threshold ตัดทิ้งถ้าไม่เหมือนเลย
            continue
        results.append({
            "score": float(scores[idx]),
            "doc": chunks[idx]
        })
    return results

# =========================
# 3. LLM Interface (Ollama)
# =========================
def ask_ollama(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.3} # อุณหภูมิต่ำเพื่อให้ตอบตาม fact
    }
    
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "")
    except Exception as e:
        print(f"[ERROR] Ollama call failed: {e}")
        return ""

def clean_answer(text: str) -> str:
    """ทำความสะอาดคำตอบ แต่ไม่ลบทิ้งมั่วซั่ว"""
    if not text: return ""
    
    # ลบ Tag การคิดของโมเดลบางตัว (เช่น DeepSeek-R1)
    text = text.replace("<think>", "").replace("</think>", "")
    
    # ถ้ามีคำว่า Analysis: หรือ Reasoning: ให้ตัดส่วนหน้าทิ้ง เอาแต่เนื้อหา
    markers = ["คำตอบสรุป:", "Answer:", "สรุป:"]
    for m in markers:
        if m in text:
            text = text.split(m)[-1]
            
    return text.strip()

# =========================
# 4. Main Pipeline
# =========================
def run_pipeline(question: str, keywords=None, use_summary=False) -> str:
    start_time = datetime.now()
    chunks = load_documents()
    
    # 4.1 Analyze Domain (Simple Keyword Check)
    domain = "ทั่วไป"
    if any(x in question for x in ["vat", "ภาษีมูลค่าเพิ่ม"]): domain = "ภาษีมูลค่าเพิ่ม"
    elif any(x in question for x in ["เงินเดือน", "บุคคลธรรมดา"]): domain = "เงินได้บุคคลธรรมดา"
    
    # 4.2 Retrieve
    hits = retrieve(question, chunks, top_k=TOP_K)
    
    # Prepare Context
    context_text = ""
    refs = []
    top_k_docs_log = []
    
    if not hits:
        return "ไม่พบข้อมูลในฐานข้อมูลที่ตรงกับคำถามครับ"

    for hit in hits:
        doc = hit["doc"]
        score = hit["score"]
        title = doc["title"]
        content = doc["content"]
        
        refs.append(title)
        top_k_docs_log.append(f"[Score: {score:.2f}] {title}")
        
        context_text += f"\n---\nหัวข้อ: {title}\n{content}\n"

    # 4.3 Generate Prompt
    prompt = (
        f"<|im_start|>system\n"
        f"คุณคือผู้เชี่ยวชาญด้านกฎหมายภาษีอากรของกรมสรรพากร ตอบคำถามโดยใช้ข้อมูลจาก 'เอกสารอ้างอิง' ที่ให้มาเท่านั้น\n"
        f"กฎเหล็ก:\n"
        f"1. ถ้าในเอกสารบอกว่า 'ได้รับยกเว้น' ให้ตอบว่ายกเว้น พร้อมบอกเงื่อนไข\n"
        f"2. ถ้าข้อมูลไม่พอ ให้ตอบตรงๆ ว่าไม่พบข้อมูลอ้างอิงที่ชัดเจน\n"
        f"3. ตอบเป็นภาษาไทยที่สุภาพ กระชับ และเป็นทางการ<|im_end|>\n"
        f"1user\n"
        f"เอกสารอ้างอิง:\n{context_text}\n\n"
        f"คำถาม: {question}"
        f"2assistant\n"
        f"คำตอบสรุป:"
    )
    
    # 4.4 Call AI
    if DEBUG: print(f"[LLM] Sending prompt... (Context len: {len(context_text)})")
    raw_answer = ask_ollama(prompt)
    final_answer = clean_answer(raw_answer)
    
    if not final_answer:
        final_answer = "ขออภัย ระบบขัดข้องในการประมวลผลคำตอบ (LLM Return Empty)"

    # 4.5 Logging (บันทึกลงไฟล์ JSON เพื่อให้ App.py อ่าน)
    log_entry = {
        "timestamp": start_time.isoformat(),
        "question": question,
        "domain": domain,
        "top_k_docs": top_k_docs_log,
        "refs": list(set(refs)), # unique refs
        "answer": final_answer
    }
    
    save_log(log_entry)
    
    return final_answer

def save_log(entry: Dict):
    """Append log to JSON file"""
    logs = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except:
            logs = []
            
    logs.append(entry)
    # Keep last 50 logs only
    logs = logs[-50:]
    
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    # Test
    q = "นำเข้าอาหารสัตว์ต้องเสีย vat ไหม"
    print(run_pipeline(q))