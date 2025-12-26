# src/utils/document_summarizer.py
def summarize_documents(documents):
    """
    สรุปเนื้อหา filtered documents
    สมมติ structure: [{"title":..., "content":...}]
    คืนค่า list ของ dict: [{"title":..., "summary":...}]
    """
    summaries = []
    for doc in documents:
        content = doc.get("content", "").strip()
        title = doc.get("title", "")
        
        if not content:
            summary = "ไม่มีเนื้อหาให้สรุป"
        else:
            # สรุปง่าย ๆ: ประโยคแรกหรือ 200 ตัวอักษรแรก
            summary = content.split(".")[0][:200] + ("..." if len(content) > 200 else "")
        
        summaries.append({
            "title": title,
            "summary": summary
        })
    return summaries
