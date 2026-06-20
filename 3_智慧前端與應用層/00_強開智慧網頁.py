# -*- coding: utf-8 -*-
"""
專案名稱：營造業職災風險自動化評估系統
功能描述：終極網頁伺服器開拓器。一鍵免終端機指令，直接透過 Python 背景無效阻斷技術
          強行叫醒 Streamlit 豪華產品化大廳環境，開啟 Chrome 前端智慧預警儀表板。
"""
import os
import sys
import subprocess
import time
import webbrowser

def main():
    第三層路徑 = "D:/營造業職災風險自動化評估系統/3_智慧前端與應用層"
    網頁程式路徑 = os.path.join(第三層路徑, "15_主網頁介面程式.py")
    python_exe = "E:/python/python.exe"
    
    print("==================================================")
    print("🚀 正在啟動 [豪華網頁伺服器開拓核心] ...")
    print("==================================================")
    print(f"⏳ 系統正在背景為您強推開機 Streamlit 產品化大廳，請稍候...")
    
    # 強制將工作資料夾切換至第三層，防止相對路徑迷路
    os.chdir(第三層路徑)
    
    try:
        # 🎯 產品化終極破局：利用獨立主控台強推 15 號豪華版開機，直接掛在標準 8501 埠！
        cmd = [python_exe, "-m", "streamlit", "run", "15_主網頁介面程式.py", "--server.port", "8501", "--server.headless", "true"]
        
        # 在 Windows 後台強制開拓全新進程，徹底隔離 Spyder 記憶體衝突
        subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
        
        # 讓伺服器在背景飛 4 秒鐘（完成 NLP 大腦模型讀取）
        print("⏳ 正在引導 AI 語意大腦與 8D 罰則資料鏈組裝，倒數 3 秒...")
        time.sleep(4)
        
        print("\n==================================================")
        print("🎉 [大獲全勝] 豪華多專案智慧巡檢網頁已在背景完全通電開機！")
        print("🌐 系統正引導 Chrome 瀏覽器為您開啟大廳門戶...")
        print("==================================================")
        
        # 強制開啟 Chrome 直連標準黃金大廳
        webbrowser.open("http://localhost:8501")
        
    except Exception as e:
        print(f"❌ 網頁啟動失敗，原因: {e}")

if __name__ == "__main__":
    main()
