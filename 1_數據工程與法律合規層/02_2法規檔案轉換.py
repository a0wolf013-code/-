import pdfplumber
import re
import json
import os

def process_law_from_desktop():
    # 1. 自動定位桌面上的「法規暫存」資料夾
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    folder_path = os.path.join(desktop_path, "法規暫存")
    
    # 定義輸入 PDF 與預期產出的 JSON 檔名
    pdf_filename = "職業安全衛生教育訓練規則.pdf"
    json_filename = "職業安全衛生教育訓練規則.json"
    
    input_path = os.path.join(folder_path, pdf_filename)
    output_path = os.path.join(folder_path, json_filename)

    # 檢查資料夾與檔案是否存在
    if not os.path.exists(folder_path):
        print(f"錯誤：在桌面找不到「法規暫存」資料夾。路徑應為：{folder_path}")
        return
    if not os.path.exists(input_path):
        print(f"錯誤：在資料夾內找不到 {pdf_filename}，請確認檔案已放入。")
        return

    # 2. 初始化法規資料結構 (對應來源 114 年最新修正版本)
    law_data = {
        "法規名稱": "職業安全衛生教育訓練規則",
        "修正日期": "114-9-4",
        "章節列表": []
    }

    current_chapter = None
    current_article = None
    
    # 正則表達式：匹配章節與條號
    chapter_regex = re.compile(r'^第\s*[一二三四五六七八九十]+\s*章\s+(.*)')
    article_regex = re.compile(r'^第\s*(\d+)\s*條')

    print(f"正在處理：{input_path}...")
    
    with pdfplumber.open(input_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text: continue
                
            for line in text.split('\n'):
                line = line.strip()
                if "全國法規資料庫" in line: continue # 過濾頁首雜訊
                
                # 辨識「章」(例如：第一章 總則)
                chapter_match = chapter_regex.match(line)
                if chapter_match:
                    current_chapter = {"章名": line, "條文列表": []}
                    law_data["章節列表"].append(current_chapter)
                    continue

                # 辨識「條」(例如：第 6 條)
                article_match = article_regex.match(line)
                if article_match:
                    article_no = f"第 {article_match.group(1)} 條"
                    current_article = {"條號": article_no, "內容": ""}
                    if current_chapter:
                        current_chapter["條文列表"].append(current_article)
                    continue

                # 累積條文內容
                if current_article:
                    current_article["內容"] += line

    # 3. 將結構化結果存回桌面的「法規暫存」資料夾
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(law_data, f, ensure_ascii=False, indent=4)
    
    print(f"成功！JSON 檔案已產出並存放在桌面資料夾：{output_path}")

if __name__ == "__main__":
    process_law_from_desktop()