import os
import json
import time
import sys
import re
from process_ods_to_db import run_ods_sync
from refresh_bank import get_node_descriptions, load_existing_extra_bank, generate_questions, EXTRA_DATA_PATH, CHECKPOINT_PATH
import refresh_bank

def main():
    print("\n" + "="*50)
    print("[AI Exam Tool] All-in-One Sync")
    print("="*50)


    # 第一階段：同步學生 ODS 數據
    print("\n[Step 1] Syncing Student ODS Data...")
    student_records, ods_nodes = run_ods_sync()
    
    if not student_records:
        print("[Error] Failed to read ODS data.")
        return

    print(f"[OK] Successfully processed {len(student_records)} students.")
    print(f"[Info] Detected {len(ods_nodes)} unique nodes in ODS: {', '.join(sorted(ods_nodes)[:10])}...")
    
    # 第二階段：稽核本地題庫完整性
    print("\n[Step 2] Checking Local Bank Coverage...")
    
    # 載入全部知識點定義
    all_descriptions = get_node_descriptions()
    # 載入現有題庫 (擴充)
    existing_extra = load_existing_extra_bank()
    
    # 讀取原始 data.js 中的 QUESTION_BANK (主題庫)
    def load_master_bank():
        try:
            with open("data.js", "r", encoding="utf-8") as f:
                content = f.read()
            # 找到 const QUESTION_BANK = { ... };
            match = re.search(r"const QUESTION_BANK = (\{.*?\});", content, re.DOTALL)
            if match:
                return json.loads(match.group(1))
        except: pass
        return {}
    
    master_bank = load_master_bank()
    
    def is_placeholder(qs):
        if not qs: return True
        real_qs = []
        seen_questions = set()
        for q in qs:
            q_text = q.get('q', "").strip()
            options = q.get('options', [])
            exp = q.get('exp', "")
            
            # 檢查是否為重複題目
            if q_text in seen_questions:
                continue
            seen_questions.add(q_text)
            
            # 檢查長度是否太短 (過於基礎)
            if len(q_text) < 10:
                continue
                
            has_fake1 = any("錯誤值" in opt or "正確結果" in opt for opt in options)
            has_fake2 = "基礎題型" in exp
            has_fake3 = any("此為正確的觀念描述" in opt or "該觀念的錯誤誤解" in opt or "完全不相干的描述" in opt for opt in options)
            
            if not has_fake1 and not has_fake2 and not has_fake3:
                real_qs.append(q)
        
        # 如果有效題目太少 (少於 2 題)，也視為需要補題
        return len(real_qs) < 2

    # 找出 ODS 有提到，但「兩邊題庫」都沒題目的節點
    missing_nodes = []
    for node in ods_nodes:
        # 檢查 master bank
        has_master = node in master_bank and not is_placeholder(master_bank[node].get('beginner', []))
        # 檢查 extra bank
        has_extra = node in existing_extra and not is_placeholder(existing_extra[node].get('beginner', []))
        
        if not has_master and not has_extra:
            missing_nodes.append(node)
    
    if not missing_nodes:
        print("[OK] All nodes covered by local bank.")
        print("[Finish] Task completed successfully!")
        return

    print(f"[Warning] {len(missing_nodes)} nodes are missing in local bank!")
    print(f"[Nodes] {', '.join(missing_nodes)}")
    
    confirm = input("\nGenerate questions for missing nodes via AI? (y/n): ").strip().lower()
    if confirm != 'y':
        print("\n[Skip] Skipping AI generation. You can manually fill these gaps in extra_data.js.")
        return

    # 第三階段：執行補題 (此時才檢查 API Key)
    global GROQ_API_KEY
    if not GROQ_API_KEY:
        print("\n[Auth] GROQ_API_KEY not found in environment.")
        key = input("Please enter your GROQ_API_KEY to proceed (or press Enter to cancel): ").strip()
        if not key:
            print("[Cancel] AI generation cancelled by user.")
            return
        GROQ_API_KEY = key
        refresh_bank.GROQ_API_KEY = key

    print("\n[Step 3] Launching AI Engine...")
    
    new_bank = existing_extra.copy()
    success_count = 0
    
    for i, code in enumerate(missing_nodes):
        desc = all_descriptions.get(code, "No Description")
        print(f"[Processing] [{i+1}/{len(missing_nodes)}] Generating {code}...")
        
        qs = generate_questions(code, desc)
        if qs:
            new_bank[code] = {
                "beginner": qs[:2],
                "intermediate": qs[2:4],
                "advanced": qs[4:]
            }
            success_count += 1
            # 存檔 (預防萬一)
            with open(EXTRA_DATA_PATH, "w", encoding="utf-8") as f:
                update_time = time.ctime()
                f.write(f"// 自動補全題庫 - 最後更新: {update_time}\n")
                f.write(f"const EXTRA_DATA_UPDATE_TIME = '{update_time}';\n")
                f.write("const EXTRA_QUESTION_BANK = ")
                json.dump(new_bank, f, ensure_ascii=False, indent=2)
                f.write(";\n")
            time.sleep(2) # 避開速率限制
        else:
            print(f"[Error] Failed to generate {code}.")

    print(f"\n[Finish] Completed! Generated {success_count} nodes.")
    print(f"[OK] Records saved to {EXTRA_DATA_PATH}")
    print("\n[Done] Students can now see complete question sets! ✅")

if __name__ == "__main__":
    main()

