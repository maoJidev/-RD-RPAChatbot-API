import sys
from src.rag.core import ask_question

def main():
    print("🎉 ChatBot พร้อมใช้งาน! พิมพ์ 'exit' เพื่อออก")
    while True:
        question = input("\nถามเอกสารราชการ: ").strip()
        if question.lower() == "exit":
            break
        if not question:
            continue

        print("🤖 กำลังคิดคำตอบ...")
        try:
            answer, refs = ask_question(question)
            print("\n🤖 คำตอบจาก AI:")
            print("-" * 30)
            print(answer)
            print("-" * 30)
            if refs:
                print("📚 เอกสารอ้างอิง:")
                for r in refs:
                    print(f"- {r}")
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาด: {str(e)}")

if __name__ == "__main__":
    main()
