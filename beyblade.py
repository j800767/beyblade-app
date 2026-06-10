import streamlit as st
import pandas as pd
import os

# 設定網頁標題與風格
st.set_page_config(page_title="戰鬥陀螺大賽登記系統", page_icon="🌀", layout="centered")

DATA_FILE = "beyblade_registrations.csv"
ADMIN_PASSWORD = "admin"  # 👈 主辦人管理密碼

# 讀取現有資料
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

# 儲存資料
def save_data(df):
    df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

# 載入目前的登記名單
df_registrations = load_data()

# ════════════════════════════════════════════════════════════
# 📸 圖片區：如果 GitHub 有對應檔案就會自動顯示，沒有的話會先顯示提示
# ════════════════════════════════════════════════════════════

# 1. 大賽頂部主視覺海報
if os.path.exists("tournament_banner.png"):
    st.image("tournament_banner.png", use_container_width=True)
elif os.path.exists("tournament_banner.jpg"):
    st.image("tournament_banner.jpg", use_container_width=True)

st.title("🌀 戰鬥陀螺大賽零件登記系統")
st.markdown("### 📝 規則提示：每人需登記 4 顆陀螺")
st.markdown("⚠️ **核心限制：4 顆陀螺的「固鎖」與「軸心」皆絕對不能重複！**")
st.write("---")

# 填寫表單
with st.form("registration_form", clear_on_submit=False):
    player_name = st.text_input("👤 選手名稱 / 綽號", placeholder="請輸入您的名字")
    
    st.write("---")
    st.write("#### 💡 填寫指引：請對照下方零件部位進行登記")
    
    # 2. 零件拆解對照說明圖
    if os.path.exists("parts_guide.png"):
        st.image("parts_guide.png", caption="▲ Beyblade X 零件部位對照圖", use_container_width=True)
    elif os.path.exists("parts_guide.jpg"):
        st.image("parts_guide.jpg", caption="▲ Beyblade X 零件部位對照圖", use_container_width=True)
    else:
        st.info("💡 (提示：如果你把名為 `parts_guide.png` 的說明圖上傳到 GitHub，這裡就會自動顯示圖片喔！)")

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
        b4 = st.text_input("第四顆 上蓋", key="b4", placeholder="例：Wizard Rod")
        r4 = st.text_input("第四顆 固鎖 ⚠️", key="r4", placeholder="例：5-70")
        bit4 = st.text_input("第四顆 軸心 ⚠️", key="bit4", placeholder="例：Hexa")

    st.write("---")
    submit_btn = st.form_submit_button("🚀 提交登記資料")

# 表單提交邏輯與規則檢查
if submit_btn:
    if not player_name.strip():
        st.error("❌ 請輸入選手名稱！")
    elif player_name.strip() in df_registrations["選手名稱"].values:
        st.error(f"❌ 選手 「{player_name}」 已經登記過囉！若要修改請聯絡主辦人。")
    elif not all([b1, r1, bit1, b2, r2, bit2, b3, r3, bit3, b4, r4, bit4]):
        st.error("❌ 所有陀螺的零件欄位都必須填寫完整！")
    else:
        ratchets_list = [r1.strip().lower(), r2.strip().lower(), r3.strip().lower(), r4.strip().lower()]
        bits_list = [bit1.strip().lower(), bit2.strip().lower(), bit3.strip().lower(), bit4.strip().lower()]
        
        has_duplicate_ratchet = len(set(ratchets_list)) < 4
        has_duplicate_bit = len(set(bits_list)) < 4
        
        if has_duplicate_ratchet and has_duplicate_bit:
            st.error("❌ 違反參賽規則：您的 4 顆陀螺中，**「固鎖」與「軸心」都有
