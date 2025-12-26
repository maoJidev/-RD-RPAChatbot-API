# app.py
import streamlit as st
from src.rag.pipeline import run_pipeline

st.set_page_config(
    page_title="RAG Legal Chatbot",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 ระบบค้นหาเอกสารราชการ")
st.caption("ค้นจากหนังสือตอบข้อหารือ (RAG + Ollama)")

question = st.text_area(
    "พิมพ์คำถาม",
    placeholder="เช่น เงินปันผลที่ได้รับจากการตีราคาทรัพย์สินเพิ่ม ต้องเสียภาษีหรือไม่",
    height=180
)

use_summary = st.checkbox("ใช้สรุปเอกสาร (Summary)", value=False)

if st.button("ถาม AI"):
    if not question.strip():
        st.warning("กรุณาพิมพ์คำถาม")
    else:
        with st.spinner("AI กำลังประมวลผล..."):
            try:
                answer = run_pipeline(question, keywords=None, use_summary=use_summary)

                st.subheader("📌 คำตอบ")
                st.write(answer)

                # โหลดเอกสาร Top-K จาก pipeline log
                import json, os
                log_file = "output/pipeline_feedback.json"
                if os.path.exists(log_file):
                    with open(log_file, "r", encoding="utf-8") as f:
                        logs = json.load(f)
                    last_entry = logs[-1]  # ใช้ entry ล่าสุด
                    refs = last_entry.get("refs", [])
                else:
                    refs = []

                if refs:
                    st.subheader("📚 เอกสารอ้างอิง")
                    for r in refs:
                        st.write(f"- {r}")

            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {str(e)}")
