# rag_core.py
import json
import os
import pickle
import subprocess

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---------------- CONFIG ----------------
DOC_FILE = "output/month_document_contents_filtered.json"
EMBED_FILE = "output/tfidf_embeddings.pkl"
TOP_K = 2
OLLAMA_MODEL = "qwen3:4b"   # model name for Ollama
# ----------------------------------------

# ---------------- LOAD DATA ----------------
def load_documents():
    if not os.path.exists(DOC_FILE):
        raise FileNotFoundError(f"ไม่พบไฟล์ {DOC_FILE}")

    with open(DOC_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    chunks = []
    for month in data:
        for doc in month.get("documents", []):
            law_text = doc.get("ข้อกฎหมาย", "")

            # heuristic แยกประเภทภาษี
            income_type = "ไม่ระบุ"
            if "มาตรา 40" in law_text:
                income_type = "เงินได้บุคคลธรรมดา"
            elif "มาตรา 65" in law_text:
                income_type = "ภาษีเงินได้นิติบุคคล"

            text = (
                f"[ประเภทภาษี]: {income_type}\n"
                f"เลขที่หนังสือ: {doc.get('เลขที่หนังสือ','')}\n"
                f"เรื่อง: {doc.get('เรื่อง','')}\n"
                f"ข้อกฎหมาย: {law_text}\n"
                f"ข้อหารือ: {doc.get('ข้อหารือ','')}\n"
                f"แนววินิจฉัย: {doc.get('แนววินิจฉัย','')}"
            )
            chunks.append(text)

    return chunks

# ---------------- EMBEDDINGS ----------------
def load_or_create_embeddings(chunks):
    if os.path.exists(EMBED_FILE):
        with open(EMBED_FILE, "rb") as f:
            vectorizer, X = pickle.load(f)
    else:
        vectorizer = TfidfVectorizer()
        X = vectorizer.fit_transform(chunks)

        os.makedirs(os.path.dirname(EMBED_FILE), exist_ok=True)
        with open(EMBED_FILE, "wb") as f:
            pickle.dump((vectorizer, X), f)

    return vectorizer, X

# ---------------- QUESTION ANALYSIS ----------------
def analyze_question(question: str):
    """วิเคราะห์คำถามเพื่อกำหนดประเภทภาษี (heuristic)"""
    q = question.lower()
    if any(word in q for word in ["youtube", "ออนไลน์", "แพลตฟอร์ม", "เงินเดือน", "โบนัส", "เงินได้", "บุคคลธรรมดา"]):
        return "เงินได้บุคคลธรรมดา"
    if any(word in q for word in ["บริษัท", "ห้างหุ้นส่วน", "นิติบุคคล"]):
        return "ภาษีเงินได้นิติบุคคล"
    return "ไม่ระบุ"

# ---------------- SEARCH ----------------
def search_chunks(question, vectorizer, X, chunks, k=TOP_K):
    q_vec = vectorizer.transform([question])
    scores = cosine_similarity(q_vec, X)[0]
    top_ids = scores.argsort()[::-1][:k]
    results = []
    for i in top_ids:
        results.append({"text": chunks[i], "score": scores[i]})
    return results

# ---------------- OLLAMA ----------------
def ask_ollama(prompt):
    result = subprocess.run(
        ["ollama", "run", OLLAMA_MODEL],
        input=prompt,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=180
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    return result.stdout.strip()

# ---------------- MAIN API ----------------
def ask_question(question):
    chunks = load_documents()
    inferred_type = analyze_question(question)
    if inferred_type != "ไม่ระบุ":
        filtered = [c for c in chunks if f"[ประเภทภาษี]: {inferred_type}" in c]
        if filtered:
            chunks = filtered
    vectorizer, X = load_or_create_embeddings(chunks)
    search_results = search_chunks(question, vectorizer, X, chunks)
    if not search_results:
        return "ไม่พบเอกสารที่เกี่ยวข้องกับคำถามนี้", []
    context_text = ""
    refs = []
    for i, res in enumerate(search_results):
        for line in res["text"].split("\n"):
            if "เลขที่หนังสือ:" in line:
                refs.append(line.replace("เลขที่หนังสือ:", "").strip())
        context_text += f"--- เอกสารที่ {i+1} ---\n{res['text']}\n\n"
    prompt = (
        "คุณคือผู้ช่วยด้านกฎหมายและเอกสารราชการ\n"
        "ตอบคำถามโดยอ้างอิงจากข้อมูลอ้างอิงด้านล่างเท่านั้น\n"
        "หากข้อมูลไม่เกี่ยวข้องกับคำถาม ให้ตอบว่า 'ไม่พบเอกสารที่เกี่ยวข้องกับคำถามนี้'\n"
        "ห้ามคาดเดา ห้ามอธิบายนอกข้อมูล\n"
        "สรุปคำตอบไม่เกิน 5–7 บรรทัด\n"
        "ต้องระบุเลขที่หนังสือที่ใช้อ้างอิง\n\n"
        "========== ข้อมูลอ้างอิง ==========\n"
        + context_text +
        "========== คำถาม ==========\n"
        + question +
        "\n\n========== คำตอบ ==========\n"
    )
    answer = ask_ollama(prompt)
    return answer, refs
