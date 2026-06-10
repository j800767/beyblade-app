import streamlit as st
import pandas as pd
import os

# 設定網頁標題與寬版風格
st.set_page_config(page_title="戰鬥陀螺大賽系統", page_icon="🌀", layout="wide")

DATA_FILE = "beyblade_registrations.csv"
SCORE_FILE = "tournament_scores.csv"
ADMIN_PASSWORD = "admin"  # 👈 主辦人管理密碼，可自由修改

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
tab1, tab2 = st.tabs(["📝 選手零件登記表單", "🏆 主辦人計分與晉級控制台"])

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
       * 下一場對決換新對手時，才可以重新從 4 顆中挑選 3 顆重新排陣。
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
        submit_btn = st.form_submit_button("🚀 提交登記資料")

    if submit_btn:
        b1_clean = b1.strip().lower()
        b2_clean = b2.strip().lower()
        b3_clean = b3.strip().lower()
        b4_clean = b4.strip().lower()
        
        ban_keywords = ["pegasus", "天馬", "rod", "神杖", "shark", "鯊魚"]
        has_banned_part = any(any(kw in b for kw in ban_keywords) for b in [b1_clean, b2_clean, b3_clean, b4_clean])

        if not player_name.strip():
            st.error("❌ 請輸入選手名稱！")
        elif player_name.strip() in df_registrations["選手名稱"].values:
            st.error(f"❌ 選手 「{player_name}」 已經登記過囉！")
        elif not all([b1, r1, bit1, b2, r2, bit2, b3, r3, bit3, b4, r4, bit4]):
            st.error("❌ 所有陀螺的零件欄位都必須填寫完整！")
        elif has_banned_part:
            st.error("❌ 登記失敗！您的配置中包含本次大賽的【禁用上蓋】（天馬 / 神杖 / 鯊魚），請修改後再送出！")
        else:
            ratchets_list = [r1.strip().lower(), r2.strip().lower(), r3.strip().lower(), r4.strip().lower()]
            bits_list = [bit1.strip().lower(), bit2.strip().lower(), bit3.strip().lower(), bit4.strip().lower()]
            
            has_duplicate_ratchet = len(set(ratchets_list)) < 4
            has_duplicate_bit = len(set(bits_list)) < 4
            
            if has_duplicate_ratchet or has_duplicate_bit:
                st.error("❌ 違反參賽規則：「固鎖」與「軸心」皆絕對不能重複！請重新調整。")
            else:
                new_data = {
                    "選手名稱": player_name.strip(),
                    "陀螺1_上蓋": b1.strip(), "陀螺1_固鎖": r1.strip(), "陀螺1_軸心": bit1.strip(),
                    "陀螺2_上蓋": b2.strip(), "陀螺2_固鎖": r2.strip(), "陀螺2_軸心": bit2.strip(),
                    "陀螺3_上蓋": b3.strip(), "陀螺3_固鎖": r3.strip(), "陀螺3_軸心": bit3.strip(),
                    "陀螺4_上蓋": b4.strip(), "陀螺4_固鎖": r4.strip(), "陀螺4_軸心": bit4.strip(),
                }
                df_registrations = pd.concat([df_registrations, pd.DataFrame([new_data])], ignore_index=True)
                save_data(df_registrations)
                st.success(f"🎉 恭喜 【{player_name}】 成功登記！")
                st.rerun()

    st.write("---")
    st.subheader("📊 目前已登記名單")
    if not df_registrations.empty:
        st.dataframe(df_registrations)
        with st.expander("🛠️ 主辦人資料管理專區"):
            pwd = st.text_input("請輸入管理密碼", type="password", key="del_pwd")
            if pwd == ADMIN_PASSWORD:
                player_to_delete = st.selectbox("請選擇要刪除資料的選手：", ["-- 請選擇 --"] + list(df_registrations["選手名稱"].values))
                if player_to_delete != "-- 請選擇 --" and st.button(f"🗑️ 確定刪除 {player_to_delete}", type="primary"):
                    df_registrations = df_registrations[df_registrations["選手名稱"] != player_to_delete]
                    save_data(df_registrations)
                    st.success(f"已刪除 【{player_to_delete}】")
                    st.rerun()
    else:
        st.info("💡 目前還沒有選手登記喔！")

# ════════════════════════════════════════════════════════════
# 【分頁二：主辦人計分與晉級控制台】
# ════════════════════════════════════════════════════════════
with tab2:
    st.title("🏆 大賽計分與全自動晉級控制台")
    players_list = df_registrations["選手名稱"].tolist() if not df_registrations.empty else []

    if len(players_list) < 6:
        st.warning(f"⚠️ 目前登記人數只有 {len(players_list)} 人。本賽制專為 6 人設計，請等 6 人登記滿後再操作此計分控制台。")
    else:
        players_list = players_list[:6]
        
        if "scores" not in st.session_state:
            if os.path.exists(SCORE_FILE):
                try:
                    st.session_state.scores = pd.read_csv(SCORE_FILE).to_dict(orient="records")[0]
                except:
                    pass
