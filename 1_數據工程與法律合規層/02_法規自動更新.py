#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
專案名稱：營造業職災風險自動化評估系統
模組名稱：1_數據工程與法律合規層 / 02_法規自動更新.py
功能描述：法規庫智慧型雙軌結構化轉換器。自動掃描法規庫資料夾，
          若已有轉好的 JSON 則直接載入；若只有 PDF 則自動深度結構化解析，
          最終整合成單一系統核心法規庫大字典。
"""

import os
import re
import json
import sys
import pdfplumber
from datetime import datetime

# 確保支援繁體中文路徑與輸出
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

def parse_single_law_pdf(pdf_path):
    """
    深度法規 PDF 解析器：
    將勞動部/職安署官方 PDF 法規文本，精準切分為「章節」與「條文內容」
    """
    檔名不含副檔名 = os.path.splitext(os.path.basename(pdf_path))[0]
    
    law_entry = {
        "法規名稱": 檔名不含副檔名,  # 預設先拿檔名當作法規名稱，防止排版破損
        "修正日期": "未知",
        "解析時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "章節列表": []
    }
    
    # 智慧型正規表達式編編譯
    chapter_regex = re.compile(r"^第\s*[一二三四五六七八九十百]+[章編總]\s+(.*)$")
    article_regex = re.compile(r"^第\s*(\d+(?:-\d+)?)\s*條\s*(.*)$")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                return None
                
            # --- 1. 智慧型標頭與修正日期提取 ---
            first_page_text = pdf.pages[0].extract_text() or ""
            
            # 多重比對模式
            name_match = re.search(r"(?:法規名稱：|名稱：)\s*(.*)", first_page_text)
            date_match = re.search(r"(?:修正日期：|發布日期：)\s*民國\s*(\d+\s*年\s*\d+\s*月\s*\d+\s*日)", first_page_text)
            
            if name_match:
                安全名稱 = name_match.group(1).strip()
                if 安全名稱:
                    law_entry["法規名稱"] = 安全名稱
                    
            if date_match:
                law_entry["修正日期"] = date_match.group(1).strip()
                
            print(f"   ⚙️ 偵測到 PDF，啟動核心解析：【{law_entry['法規名稱']}】")
            
            current_chapter = None
            current_article = None
            
            # --- 2. 逐頁行掃描結構化 ---
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                    
                for line in text.split('\n'):
                    line = line.strip()
                    
                    # 髒資料橫向防禦：跳過頁碼、政府網址與空白行
                    if not line or "全國法規資料庫" in line or "law.moj.gov.tw" in line:
                        continue
                        
                    # A. 條文「章」切分
                    c_match = chapter_regex.match(line)
                    if c_match:
                        current_chapter = {"章名": line, "條文列表": []}
                        law_entry["章節列表"].append(current_chapter)
                        current_article = None
                        continue
                        
                    # B. 條文「條號與內文」切分
                    a_match = article_regex.match(line)
                    if a_match:
                        條號 = f"第 {a_match.group(1).strip()} 條"
                        條文當行本文 = a_match.group(2).strip()
                        
                        current_article = {"條號": 條號, "內容": 條文當行本文}
                        
                        # 降級防禦：若法規一開頭沒有「章」，自動塞入虛擬主章
                        if current_chapter is None:
                            current_chapter = {"章名": "本文通則", "條文列表": []}
                            law_entry["章節列表"].append(current_chapter)
                            
                        current_chapter["條文列表"].append(current_article)
                        continue
                        
                    # C. 跨行條文內容縱向累積
                    if current_article is not None:
                        if current_article["內容"]:
                            current_article["內容"] += " " + line
                        else:
                            current_article["內容"] = line
                            
        return law_entry
    except Exception as e:
        print(f"   ❌ 深度解析 PDF 失敗：{檔名不含副檔名}，錯誤原因: {e}")
        return None

def main():
    # =========================================================================
    # 1. 智慧型路徑與法規雙軌掃描
    # =========================================================================
    基礎路徑 = "D:/營造業職災風險自動化評估系統/1_數據工程與法律合規層"
    folder_path = os.path.join(基礎路徑, "法規庫")
    output_json = os.path.join(基礎路徑, "系統結構化法規資料庫_整合版.json")
    
    print("==================================================")
    print("🚀 正在啟動 [智慧雙軌整合型] 法規自動更新系統...")
    print("==================================================")
    
    if not os.path.exists(folder_path):
        print(f"❌ 找不到法規庫資料夾，請確認路徑是否為：{folder_path}")
        return
        
    所有檔案 = os.listdir(folder_path)
    # 分流處理：找出所有 PDF 檔案
    pdf_檔案清單 = [f for f in 所有檔案 if f.lower().endswith('.pdf')]
    
    if not pdf_檔案清單:  # 👈 這裡已修正為繁體【清單】
        print(f"⚠️ 警告：在 {folder_path} 內沒有發現任何法規 PDF 檔案！")
        return
        
    總法規庫清單 = []
    
    # =========================================================================
    # 2. 核心雙軌制動態更新排查
    # =========================================================================
    for file in pdf_檔案清單:  # 👈 這裡已修正為繁體【清單】
        檔名主體 = os.path.splitext(file)[0]
        對應json檔名 = f"{檔名主體}.json"
        
        pdf_完整路徑 = os.path.join(folder_path, file)
        json_完整路路径 = os.path.join(folder_path, 對應json檔名)
        
        # 軌道一：若本機已經存在對應的單一 JSON 結構，直接載入提升效能
        if os.path.exists(json_完整路路径):
            try:
                with open(json_完整路路径, 'r', encoding='utf-8') as j_f:
                    單一法規數據 = json.load(j_f)
                print(f"   ⚡ [快取快充] 成功直接讀取現成 JSON 結構：【{檔名主體}】")
                
                # 確保結構格式正確載入
                if isinstance(單一法規數據, dict):
                    總法規庫清單.append(單一法規數據)
                elif isinstance(單一法規數據, list) and len(單一法規數據) > 0:
                    總法規庫清單.append(單一法規數據[0])
                continue
            except Exception:
                print(f"   [提示] 發現現成 JSON 但讀取有雜訊，將自動切換回 PDF 重新解析...")
                
        # 軌道二：若無現成 JSON，則啟動 pdfplumber 深度核心結構化重組
        結構化數據 = parse_single_law_pdf(pdf_完整路徑)
        if 結構化數據:
            總法規庫清單.append(結構化數據)
            # 自動在本機法規庫中備份一份單一 JSON，下次執行直接走軌道一快充
            try:
                with open(json_完整路路径, 'w', encoding='utf-8') as b_f:
                    json.dump(結構化數據, b_f, ensure_ascii=False, indent=4)
            except Exception:
                pass

    # =========================================================================
    # 3. 結構化匯出全系統總法規庫大字典
    # =========================================================================
    if 總法規庫清單:
        with open(output_json, 'w', encoding='utf-8') as main_f:
            json.dump(總法規庫清單, main_f, ensure_ascii=False, indent=4)
            
        print("\n==================================================")
        print(f"🎉 [成功] 智慧法規庫全模組自動整合轉換完成！")
        print(f"📊 總計控管營造業核心法規數：{len(總法規庫清單)} 份")
        print(f"📂 系統總資料庫輸出路徑：{output_json}")
        print("==================================================")
    else:
        print("⚠️ 未成功整合任何法規資料，請檢查法規庫資料夾。")

if __name__ == "__main__":
    main()
