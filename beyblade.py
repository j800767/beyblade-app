import streamlit as st
import pandas as pd
import os

# 設定網頁標題與風格
st.set_page_config(page_title="戰鬥陀螺大賽登記系統", page_icon="🌀", layout="centered")

DATA_FILE = "beyblade_registrations.csv"
ADMIN_PASSWORD = "admin"  # 👈 主辦人管理密碼（目前設定為 admin，可隨時修改）

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

st.title("🌀 戰鬥陀螺大賽零件登記系統")
st.markdown("### 📝 規則提示：每人需登記 4 顆陀螺")
st.markdown("⚠️ **核心限制：4 顆陀螺的「固鎖」與「軸心」皆絕對不能重複！**")
st.write("---")

# 填寫表單
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
        # 將輸入整理並統一轉小寫，避免因大小寫或空格判定不同
        ratchets_list = [r1.strip().lower(), r2.strip().lower(), r3.strip().lower(), r4.strip().lower()]
        bits_list = [bit1.strip().lower(), bit2.strip().lower(), bit3.strip().lower(), bit4.strip().lower()]
        
        # 檢查重複
        has_duplicate_ratchet = len(set(ratchets_list)) < 4
        has_duplicate_bit = len(set(bits_list)) < 4
        
        if has_duplicate_ratchet and has_duplicate_bit:
            st.error("❌ 違反參賽規則：您的 4 顆陀螺中，**「固鎖」與「軸心」都有重複**！請重新調整。")
        elif has_duplicate_ratchet:
            st.error("❌ 違反參賽規則：您的 4 顆陀螺中，有**重複的固鎖**！請重新調整。")
        elif has_duplicate_bit:
            st.error("❌ 違反參賽規則：您的 4 顆陀螺中，有**重複的軸心**！請重新調整。")
        else:
            # 檢查完全通過，寫入資料
            new_data = {
                "選手名稱": player_name.strip(),
                "陀螺1_上蓋": b1.strip(), "陀螺1_固鎖": r1.strip(), "陀螺1_軸心": bit1.strip(),
                "陀螺2_上蓋": b2.strip(), "陀螺2_固鎖": r2.strip(), "陀螺2_軸心": bit2.strip(),
                "陀螺3_上蓋": b3.strip(), "陀螺3_固鎖": r3.strip(), "陀螺3_軸心": bit3.strip(),
                "陀螺4_上蓋": b4.strip(), "陀螺4_固鎖": r4.strip(), "陀螺4_軸心": bit4.strip(),
            }
            df_registrations = pd.concat([df_registrations, pd.DataFrame([new_data])], ignore_index=True)
            
            try:
                save_data(df_registrations)
                st.success(f"🎉 恭喜 【{player_name}】 成功登記！4 顆陀螺的固鎖與軸心均符合不重複規則。")
                st.rerun()
            except PermissionError:
                st.error("❌ 儲存失敗！主辦人可能正用 Excel 開啟 `beyblade_registrations.csv`，請請主辦人關閉 Excel 後再試一次。")

# 後台管理與名單顯示
st.write("---")
st.subheader("📊 目前已登記名單")

if not df_registrations.empty:
    st.dataframe(df_registrations)
    
    csv_data = df_registrations.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 下載完整登記名單 (CSV 格式)",
        data=csv_data,
        file_name="beyblade_players_list.csv",
        mime="text/csv"
    )
    
    # 🔐 主辦人刪改管理專區
    st.write("---")
    with st.expander("🛠️ 主辦人資料管理專區"):
        pwd = st.text_input("請輸入管理密碼", type="password")
        if pwd == ADMIN_PASSWORD:
            st.success("密碼正確！已開啟管理權限")
            
            # 刪除功能
            player_to_delete = st.selectbox("請選擇要刪除資料的選手：", ["-- 請選擇 --"] + list(df_registrations["選手名稱"].values))
            if player_to_delete != "-- 請選擇 --":
                if st.button(f"🗑️ 確定刪除 {player_to_delete} 的登記資料", type="primary"):
                    df_registrations = df_registrations[df_registrations["選手名稱"] != player_to_delete]
                    try:
                        save_data(df_registrations)
                        st.success(f"已成功刪除選手 【{player_to_delete}】 的資料！")
                        st.rerun()
                    except PermissionError:
                        st.error("❌ 刪除失敗！請先關閉正在開啟該 CSV 的 Excel 視窗。")
        elif pwd:
            st.error("密碼錯誤！")
else:
    st.info("💡 目前還沒有選手登記喔！")