import re

def extract_keywords_from_title(title: str):
    """
    แยกคำสำคัญจากหัวข้อเอกสาร
    """
    keywords = []

    # ตัวอย่างกฎง่าย ๆ สำหรับเอกสารภาษี
    if "ภาษีมูลค่าเพิ่ม" in title:
        keywords.append("ภาษีมูลค่าเพิ่ม")
    if "ภาษีเงินได้" in title:
        keywords.append("ภาษีเงินได้")
    if "เช่าซื้อ" in title:
        keywords.append("เช่าซื้อ")
    if "นำเข้า" in title or "อาหารสัตว์" in title:
        keywords.append("นำเข้า")
        keywords.append("อาหารสัตว์")

    # เพิ่ม filter อื่น ๆ ตามต้องการ
    return keywords


def filter_documents_by_keywords(documents, target_keywords):
    """
    เลือกเอกสารที่ title หรือ content มี keyword ตรงกับ target_keywords
    """
    filtered_docs = []

    for doc in documents:
        title = doc.get("title", "")
        content = doc.get("content", "")

        # สร้าง keyword จาก title
        title_keywords = extract_keywords_from_title(title)

        # รวม content กับ title keyword เป็นชุดเดียว
        text_to_check = " ".join([title, content])

        # check if any keyword match
        if any(k in text_to_check for k in target_keywords + title_keywords):
            filtered_docs.append(doc)

    return filtered_docs
