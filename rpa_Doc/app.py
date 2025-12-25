# app.py
import streamlit as st
from src.rag.core import ask_question

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

if st.button("ถาม AI"):
    if not question.strip():
        st.warning("กรุณาพิมพ์คำถาม")
    else:
        with st.spinner("AI กำลังประมวลผล..."):
            try:
                answer, refs = ask_question(question)

                st.subheader("📌 คำตอบ")
                st.write(answer)

                st.subheader("📚 เอกสารอ้างอิง")
                for r in refs:
                    st.write(f"- {r}")

            except Exception as e:
                st.error(str(e))
