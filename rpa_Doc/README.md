# กองกฎหมาย - RPA RD Scraper & ChatBot (Refactored)

โปรเจกต์นี้เป็นเครื่องมือสำหรับรวบรวมข้อมูลเอกสารข้อหารือภาษีอากรจากเว็บไซต์กรมสรรพากร (RD) และระบบ ChatBot สำหรับสอบถามข้อมูลจากเอกสารที่รวบรวมได้ โดยใช้เทคโนโลยี RPA (Robocorp/Playwright) และ AI (Ollama/RAG)

---

## 🛠 HOW TO SET UP (การติดตั้ง)

1. **RCC (Robocorp Command Chain)**: จัดการ Environment และรัน Robot Tasks
2. **Ollama**: สำหรับรัน AI ChatBot (แนะนำโมเดล `qwen2:7b` หรือ `llama3.2`)
3. **Python 3.10+**: จัดการผ่าน `conda.yaml` หรือ `requirements.txt`

---

## 🚀 HOW TO RUN (วิธีการรัน)

### 1. การรัน Scraper (เพื่อดึงข้อมูล) - รันผ่าน `tasks.py`

| Stage | คำสั่งรัน (RCC) | คำอธิบาย |
| :--- | :--- | :--- |
| **Stage 1** | `rcc run -t run_year` | เก็บรายการปี พ.ศ. ของข้อหารือ |
| **Stage 2** | `rcc run -t run_month` | เก็บรายการเดือนในแต่ละปี |
| **Stage 3** | `rcc run -t run_collect_month_urls_task` | เก็บลิงก์ของเอกสารทั้งหมด |
| **Stage 4** | `rcc run -t run_read_document_content_task` | เข้าไปอ่านเนื้อหาในแต่ละลิงก์ |
| **Stage 5** | `rcc run -t run_filter_documents_task` | กรองและรวมข้อมูลที่สมบูรณ์ |

### 2. การรัน ChatBot

สามารถเลือกใช้ได้ 2 รูปแบบ:

- **CLI Mode**: `python -m src.rag.cli`
- **Web UI Mode**: `streamlit run app.py`

---

## 📂 โครงสร้างโปรเจกต์ (Project Structure)

```text
rpa_Doc/
├── src/
│   ├── config/
│   │   └── settings.py          # รวมตั้งค่าและ constants ทั้งหมด
│   ├── scrapers/
│   │   ├── year_collector.py     # Stage 1
│   │   ├── month_collector.py    # Stage 2
│   │   ├── document_url_collector.py # Stage 3
│   │   └── document_reader.py    # Stage 4
│   ├── utils/
│   │   ├── document_filter.py    # Stage 5
│   │   └── helpers.py            # Shared utility functions
│   └── rag/
│       ├── core.py               # Core logic สำหรับ RAG
│       └── cli.py                # Interface แบบ Terminal
├── app.py                         # Interface แบบ Web (Streamlit)
├── tasks.py                       # Robocorp Task Entry Points
├── output/                        # ข้อมูลที่ดึงมาได้ (JSON/Pickle)
└── README.md
```

---

## ⚙️ การตั้งค่า (Configuration)

หากต้องการเปลี่ยน URL, ชื่อโมเดล AI หรือ Path ไฟล์ ให้แก้ไขที่:
`src/config/settings.py`

---

## ✅ ผลลัพธ์

เมื่อรันสำเร็จ ข้อมูลจะถูกเก็บไว้ในโฟลเดอร์ `output/` โดยไฟล์หลักที่ ChatBot ใช้งานคือ `month_document_contents_filtered.json`
