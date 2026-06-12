import streamlit as st
import pandas as pd
import os
import random

# 設定網頁標題與寬版風格
st.set_page_config(page_title="戰鬥陀螺大賽系統", page_icon="🌀", layout="wide")

DATA_FILE = "beyblade_registrations.csv"
SCORE_FILE = "tournament_scores.csv"

# 🔑 這裡可以修改你的管理者密碼，預設為 admin
ADMIN_PASSWORD = "admin"  

# ════════════════════════════════════════════════════════════
# 💾 資料核心處理函式
# ════════════════════════════════════════════════════════════
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=[
            "選手名稱", 
            "陀螺1_上蓋", "陀螺1_固鎖", "陀螺1_軸心",
            "陀螺2_上蓋", "陀螺2_固鎖", "陀螺2_軸心",
            "陀螺3_上蓋", "陀螺3_固鎖", "陀螺3_軸心",
            "陀螺4_上蓋", "陀螺4_固鎖", "陀螺4_軸心"
        ])

def save_data(df):
    df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

# 載入資料
df_registrations = load_data()

# ════════════════════════════════════════════════════════════
# 👑 頂部大分頁切換
# ════════════════════════════════════════════════════════════
tab1, tab2 = st.tabs(["📝 選手零件登記表單", "🏆 大賽即時榜與控制台"])

# ════════════════════════════════════════════════════════════
# 🔒 側邊欄密碼驗證區（影響全網頁的權限）
# ════════════════════════════════════════════════════════════
st.sidebar.header("🔑 管理者驗證專區")
admin_input = st.sidebar.text_input("輸入管理密碼以鎖定/解鎖控制項", type="password", help="請輸入主辦人密碼以開啟計分、刪除與抽籤權限")
is_admin = (admin_input == ADMIN_PASSWORD)

if is_admin:
    st.sidebar.success("🔓 驗證成功！管理員操作權限已全開。")
else:
    st.sidebar.info("🔒 目前為【訪客唯讀模式】。若您是主辦人，請輸入密碼以進行計分、刪除資料或抽籤。")

# ════════════════════════════════════════════════════════════
# 【分頁一：選手登記系統】
# ════════════════════════════════════════════════════════════
with tab1:
    st.title("🌀 戰鬥陀螺大賽零件登記系統")
    
    st.markdown("""
    ### 📝 大賽核心規則與限制
    1. **每人需登記 4 顆陀螺**，且 4 顆的**「固鎖」與「軸心」皆絕對不能重複**！
    2. **🚫 大賽禁用零件（禁卡表）：**
       * **上蓋禁用：`天馬 (Pegasus)`、`神杖 (Rod)`、`鯊魚 (Shark)`**
    3. **⚔️ 4 選 3 戰鬥守則：**
       * 每場對決開始前，從登記的 4 顆中**秘密挑選 3 顆**排定出賽順序。
       * **【重點】同一場比賽選定後，中途絕對不可更換陀螺或調整順序！**
    """)
    st.write("---")

    with st.form("registration_form", clear_on_submit=False):
        player_name = st.text_input("👤 選手名稱 / 綽號", placeholder="請輸入您的名字")
        
        st.write("#### ⚙️ 填寫 4 顆陀螺的零件配置")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("【第一顆】")
            b1 = st.text_input("第一顆 上蓋", key="b1", placeholder="例：Cobalt Drake")
            r1 = st.text_input("第一顆 固鎖 ⚠️", key="r1", placeholder="例：4-60")
            bit1 = st.text_input("第一顆 軸心 ⚠️", key="bit1", placeholder="例：Flat")
            
            st.subheader("【第三顆】")
            b3 = st.text_input("第三顆 上蓋", key="b3", placeholder="例：Hells Chain")
            r3 = st.text_input("第三顆 固鎖 ⚠️", key="r3", placeholder="例：5-60")
            bit3 = st.text_input("第三顆 軸心 ⚠️", key="bit3", placeholder="例：High Taper")

        with col2:
            st.subheader("【第二顆】")
            b2 = st.text_input("第二顆 上蓋", key="b2", placeholder="例：Phoenix Wing")
            r2 = st.text_input("第二顆 固鎖 ⚠️", key="r2", placeholder="例：9-60")
            bit2 = st.text_input("第二顆 軸心 ⚠️", key="bit2", placeholder="例：Orb")
            
            st.subheader("【第四顆】")
            b4 = st.text_input("第四顆 上蓋", key="b4", placeholder="例：Cobalt Dragoon")
            r4 = st.text_input("第四顆 固鎖 ⚠️", key="r4", placeholder="例：5-70")
            bit4 = st.text_input("第四顆 軸心 ⚠️", key="bit4", placeholder="例：Hexa")

        st.write("---")
        submit_btn = st.form_submit_button
