import streamlit as st
import pandas as pd
import os
import random

st.set_page_config(page_title="三重盃 戰鬥陀螺 瑞士輪系統", page_icon="🌀", layout="wide")

DATA_FILE = "beyblade_registrations.csv"
SCORE_FILE = "tournament_scores.csv"
ADMIN_PASSWORD = "admin"  

def load_data():
    if os.path.exists(DATA_FILE): 
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["選手名稱", "陀螺1_上蓋", "陀螺1_固鎖", "陀螺1_軸心", "陀螺2_上蓋", "陀螺2_固鎖", "陀螺2_軸心", "陀螺3_上蓋", "陀螺3_固鎖", "陀螺3_軸心", "陀螺4_上蓋", "陀螺4_固鎖", "陀螺4_軸心"])

def save_data(df): 
    df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

# 📝 核心防呆檢查函式
def check_inputs(name, b1, r1, bit1, b2, r2, bit2, b3, r3, bit3, b4, r4, bit4, is_edit=False, original_name=""):
    if not name.strip(): return False, "❌ 選手名稱不能留空！"
    
    if is_edit:
        if name.strip() != original_name and name.strip() in df_registrations["選手名稱"].values:
            return False, f"❌ 選手名稱【{name.strip()}】已經有人登記過了！"
    else:
        if name.strip() in df_registrations["選手名稱"].values:
            return False, f"❌ 選手名稱【{name.strip()}】已經有人登記過了！"
            
    banned_keywords = ["天馬", "神杖", "鯊魚", "pegasus", "rod", "shark"]
    blades = [str(b1), str(b2), str(b3), str(b4)]
    for idx, b in enumerate(blades, 1):
        for banned in banned_keywords:
            if banned in b.lower(): return False, f"❌ 登記失敗！第 {idx} 顆陀螺的上蓋【{b}】屬於禁用零件（天馬/神杖/鯊魚）！"
            
    ratchets = [r for r in [str(r1).strip(), str(r2).strip(), str(r3).strip(), str(r4).strip()] if r]
    if len(ratchets) != len(set(ratchets)): return False, "❌ 登記失敗！4 顆陀螺的「固鎖 (Ratchet)」存在重複零件，請重新配置！"
    
    bits = [b for b in [str(bit1).strip(), str(bit2).strip(), str(bit3).strip(), str(bit4).strip()] if b]
    if len(bits) != len(set(bits)): return False, "❌ 登記失敗！4 顆陀螺的「軸心 (Bit)」存在重複零件，請重新配置！"
    
    return True, ""

df_registrations = load_data()
tab1, tab2 = st.tabs(["📝 選手零件登記與名單管理", "🏆 瑞士輪控制台"])

st.sidebar.header("🔑 管理者驗證專區")
admin_input = st.sidebar.text_input("輸入管理密碼", type="password")
is_admin = (admin_input == ADMIN_PASSWORD)

if is_admin: st.sidebar.success("🔓 管理員權限已全開。")
else: st.sidebar.info("🔒 目前為訪客唯讀模式。")

# ════════════════════════════════════════════════════════════
# 【分頁一：選手登記與名單管理】
# ════════════════════════════════════════════════════════════
with tab1:
    st.title("🌀 戰鬥陀螺零件登記與後台管理")
    st.markdown("### 📝 4分制規則：3勝晉級四強 / 3敗直接淘汰。固鎖與軸心不可重複。禁用：天馬、神杖、鯊魚。")
    
    st.subheader("➕ 新增選手登記")
    with st.form("reg_form"):
        player_name = st.text_input("👤 選手名稱 / 綽號")
        c1, c2 = st.columns(2)
        with c1:
            b1, r1, bit1 = st.text_input("1_上蓋"), st.text_
