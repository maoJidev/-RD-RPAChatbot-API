# src/api/services/rag_service.py
import requests
from typing import List, Dict
from datetime import datetime
from src.config.settings import RAG_CONFIG, OLLAMA_BASE_URL
from src.repository.document_repository import DocumentRepository
from src.repository.log_repository import LogRepository
from sklearn.metrics.pairwise import cosine_similarity

class RAGService:
    def __init__(self):
        self.doc_repo = DocumentRepository()
        self.log_repo = LogRepository()
        self.ollama_url = f"{OLLAMA_BASE_URL}/api/generate"
        self.model = RAG_CONFIG["model"]
        self.top_k = RAG_CONFIG.get("top_k", 2)
        self.debug = True

    def ask_question(self, question: str) -> str:
        start_time = datetime.now()
        chunks = self.doc_repo.load_documents()
        
        # 1. Domain Detection
        domain = "ทั่วไป"
        if any(x in question.lower() for x in ["vat", "ภาษีมูลค่าเพิ่ม"]): domain = "ภาษีมูลค่าเพิ่ม"
        elif any(x in question for x in ["เงินเดือน", "บุคคลธรรมดา"]): domain = "เงินได้บุคคลธรรมดา"

        # 2. Retrieval
        vectorizer, matrix = self.doc_repo.get_retriever(chunks)
        q_vec = vectorizer.transform([question])
        scores = cosine_similarity(q_vec, matrix).flatten()
        
        top_indices = scores.argsort()[::-1][:self.top_k]
        hits = []
        for idx in top_indices:
            if scores[idx] >= 0.05:
                hits.append({"score": float(scores[idx]), "doc": chunks[idx]})

        if not hits:
            return "ไม่พบข้อมูลในฐานข้อมูลที่ตรงกับคำถามครับ"

        # 3. Context Preparation
        context_text = ""
        refs = []
        top_k_docs_log = []
        for hit in hits:
            doc = hit["doc"]
            full_obj = doc.get("full_obj", {})
            
            # ดึงเลขหนังสือ (ถ้ามีใน full_obj) หรือใช้ Title
            doc_no = full_obj.get("เลขที่หนังสือ", full_obj.get("no", ""))
            ref_name = f"{doc['title']}"
            if doc_no:
                ref_name = f"{doc_no}: {doc['title']}"
            
            refs.append(ref_name)
            top_k_docs_log.append(f"[Score: {hit['score']:.2f}] {ref_name}")
            context_text += f"\n---\nหัวข้อ: {ref_name}\n{doc['content']}\n"

        # 4. Generate Prompt & Call AI
        prompt = self._build_prompt(context_text, question)
        raw_answer = self._call_ollama(prompt)
        final_answer = self._clean_answer(raw_answer)

        # Determine status
        status = "error" if final_answer.startswith("Error:") else "success"

        # 5. Save Log
        self.log_repo.save_log({
            "timestamp": start_time.isoformat(),
            "question": question,
            "domain": domain,
            "top_k_docs": top_k_docs_log,
            "refs": list(set(refs)),
            "answer": final_answer,
            "status": status
        })

        return final_answer

    def _build_prompt(self, context: str, question: str) -> str:
        return (
            f"<|im_start|>system\n"
            f"คุณคือผู้เชี่ยวชาญด้านกฎหมายภาษีอากรของกรมสรรพากร หน้าที่ของคุณคือการตอบคำถามโดยใช้ข้อมูลจาก 'เอกสารอ้างอิง' ที่ได้รับเท่านั้น\n"
            f"ข้อปฏิบัติอย่างเคร่งครัด:\n"
            f"1. ตอบคำถามโดยอิงจากเนื้อหาใน 'เอกสารอ้างอิง' เท่านั้น ห้ามใช้ความรู้ภายนอกหรือความคิดเห็นส่วนตัว\n"
            f"2. หากข้อมูลในเอกสารอ้างอิงไม่เพียงพอที่จะตอบคำถาม หรือไม่เกี่ยวข้อง ให้ตอบว่า 'ไม่พบข้อมูลในเอกสารอ้างอิงที่ระบุ' เท่านั้น ห้ามพยายามตอบหรือคาดเดา\n"
            f"3. ห้ามอ้างถึงกฎหมายหรือมาตราที่ไม่มีอยู่ในเอกสารอ้างอิง\n"
            f"4. ใช้ภาษาไทยที่เป็นทางการ สุภาพ และกระชับ\n"
            f"<|im_end|>\n"
            f"<|im_start|>user\n"
            f"เอกสารอ้างอิง:\n{context}\n\n"
            f"คำถาม: {question}<|im_end|>\n"
            f"<|im_start|>assistant\n"
            f"จากเอกสารอ้างอิง: " # Pre-fill start of response to encourage citation logic
        )

    def _call_ollama(self, prompt: str) -> str:
        try:
            payload = {
                "model": self.model, 
                "prompt": prompt, 
                "stream": False, 
                "options": {
                    "temperature": 0.3,
                    "num_ctx": 4096
                }
            }
            response = requests.post(self.ollama_url, json=payload, timeout=300)
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            return f"Error: {e}"

    def _clean_answer(self, text: str) -> str:
        if not text: return ""
        text = text.replace("<think>", "").replace("</think>", "")
        for m in ["คำตอบสรุป:", "Answer:", "สรุป:"]:
            if m in text: text = text.split(m)[-1]
        return text.strip()
