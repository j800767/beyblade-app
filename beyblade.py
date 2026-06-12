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
# 【分頁一：選手登記系統】—— ⚠️ 補回安全版刪除功能
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
        
        # 🗑️ 重新補回：主辦人專用選手資料管理區（受左側密碼鎖控制）
        st.write("---")
        if is_admin:
            with st.expander("🛠️ 主辦人資料管理專區（已解鎖）", expanded=True):
                player_to_delete = st.selectbox("請選擇要刪除資料的選手：", ["-- 請選擇 --"] + list(df_registrations["選手名稱"].values))
                if player_to_delete != "-- 請選擇 --" and st.button(f"🗑️ 確定從大賽刪除 {player_to_delete}", type="primary"):
                    df_registrations = df_registrations[df_registrations["選手名稱"] != player_to_delete]
                    save_data(df_registrations)
                    st.success(f"已成功將 【{player_to_delete}】 移出登記名單！")
                    st.rerun()
        else:
            st.caption("💡 提示：若輸入錯誤欲刪除或修改登記資料，請洽現場大賽主辦人解鎖權限。")
    else:
        st.info("💡 目前還沒有選手登記喔！")

# ════════════════════════════════════════════════════════════
# 【分頁二：主辦人計分與晉級控制台】
# ════════════════════════════════════════════════════════════
with tab2:
    st.title("🏆 大賽計分與全自動晉級控制台")
    
    # 建立基礎名單
    raw_players = df_registrations["選手名稱"].tolist() if not df_registrations.empty else []
    players_list = raw_players.copy()
    while len(players_list) < 6:
        players_list.append(f"待定選手_{len(players_list)+1}")
    players_list = players_list[:6]
    
    if "scores" not in st.session_state:
        if os.path.exists(SCORE_FILE):
            try: st.session_state.scores = pd.read_csv(SCORE_FILE).to_dict(orient="records")[0]
            except: pass
        if "scores" not in st.session_state:
            st.session_state.scores = {
                "A1": players_list[0], "A2": players_list[1], "A3": players_list[2],
                "B1": players_list[3], "B2": players_list[4], "B3": players_list[5],
                "m1_s1": 0, "m1_s2": 0, "m2_s1": 0, "m2_s2": 0,
                "m3_s1": 0, "m3_s2": 0, "m4_s1": 0, "m4_s2": 0,
                "m5_s1": 0, "m5_s2": 0, "m6_s1": 0, "m6_s2": 0,
                "r1_s1": 0, "r1_s2": 0, "r2_s1": 0, "r2_s2": 0,
                "sf1_s1": 0, "sf1_s2": 0, "sf2_s1": 0, "sf2_s2": 0,
                "f_s1": 0, "f_s2": 0, "bm_s1": 0, "bm_s2": 0,
            }

    s = st.session_state.scores
    def save_scores():
        pd.DataFrame([s]).to_csv(SCORE_FILE, index=False)

    # 🔑 管理者在側邊欄可以使用的加強型控制功能
    if is_admin:
        # 🎲 自動抽籤功能
        st.sidebar.write("---")
        st.sidebar.subheader("🎲 現場分組抽籤系統")
        if st.sidebar.button("💥 開始現場隨機抽籤！", type="primary"):
            pool = raw_players.copy()
            while len(pool) < 6: pool.append(f"待定選手_{len(pool)+1}")
            pool = pool[:6]
            random.shuffle(pool)
            s["A1"], s["A2"], s["A3"] = pool[0], pool[1], pool[2]
            s["B1"], s["B2"], s["B3"] = pool[3], pool[4], pool[5]
            save_scores()
            st.sidebar.success("🎉 抽籤完成！名單已更新！")
            st.rerun()

        # ✍️ 手動調整選單
        st.sidebar.write("---")
        st.sidebar.subheader("✍️ 手動微調選單")
        for key in ["A1", "A2", "A3", "B1", "B2", "B3"]:
            if s[key] not in players_list: s[key] = players_list[0]
        s["A1"] = st.sidebar.selectbox("A組 1號", players_list, index=players_list.index(s["A1"]))
        s["A2"] = st.sidebar.selectbox("A組 2號", players_list, index=players_list.index(s["A2"]))
        s["A3"] = st.sidebar.selectbox("A組 3號", players_list, index=players_list.index(s["A3"]))
        s["B1"] = st.sidebar.selectbox("B組 1號", players_list, index=players_list.index(s["B1"]))
        s["B2"] = st.sidebar.selectbox("B組 2號", players_list, index=players_list.index(s["B2"]))
        s["B3"] = st.sidebar.selectbox("B組 3號", players_list, index=players_list.index(s["B3"]))
        
        if st.sidebar.button("💾 儲存目前所有比分狀態"):
            save_scores()
            st.sidebar.success("比分存檔成功！")
        if st.sidebar.button("🔄 重設大賽（比分與選手全部歸零）"):
            if os.path.exists(SCORE_FILE): os.remove(SCORE_FILE)
            if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
            if "scores" in st.session_state: del st.session_state.scores
            st.rerun()

    # 計算與顯示戰果
    def get_rank(p1, p2, p3, m1_1, m1_2, m2_1, m2_2, m3_1, m3_2):
        stats = {p1: {"wins": 0, "diff": 0}, p2: {"wins": 0, "diff": 0}, p3: {"wins": 0, "diff": 0}}
        if m1_1 > m1_2: stats[p1]["wins"]+=1
        elif m1_2 > m1_1: stats[p2]["wins"]+=1
        stats[p1]["diff"] += (m1_1 - m1_2); stats[p2]["diff"] += (m1_2 - m1_1)
        if m2_1 > m2_2: stats[p2]["wins"]+=1
        elif m2_2 > m2_1: stats[p3]["wins"]+=1
        stats[p2]["diff"] += (m2_1 - m2_2); stats[p3]["diff"] += (m2_2 - m2_1)
        if m3_1 > m3_2: stats[p1]["wins"]+=1
        elif m3_2 > m3_1: stats[p3]["wins"]+=1
        stats[p1]["diff"] += (m3_1 - m3_2); stats[p3]["diff"] += (m3_2 - m3_1)
        sorted_p = sorted(stats.items(), key=lambda x: (x[1]["wins"], x[1]["diff"]), reverse=True)
        return [sorted_p[0][0], sorted_p[1][0], sorted_p[2][0]]

    rank_A = get_rank(s["A1"], s["A2"], s["A3"], s["m1_s1"], s["m1_s2"], s["m3_s1"], s["m3_s2"], s["m5_s1"], s["m5_s2"])
    rank_B = get_rank(s["B1"], s["B2"], s["B3"], s["m2_s1"], s["m2_s2"], s["m4_s1"], s["m4_s2"], s["m6_s1"], s["m6_s2"])

    # 📍 第一階段：小組循環賽
    st.header("📍 第一階段：小組循環賽 (常規賽 6 場)")
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("🌀 A 組 (循環賽)")
        st.write(f"**【場次 1】** {s['A1']} vs {s['A2']}")
        s["m1_s1"] = st.number_input(f"{s['A1']} 分數", min_value=0, max_value=5, value=int(s["m1_s1"]), key="m1_s1_input", disabled=not is_admin)
        s["m1_s2"] = st.number_input(f"{s['A2']} 分數", min_value=0, max_value=5, value=int(s["m1_s2"]), key="m1_s2_input", disabled=not is_admin)
        
        st.write(f"**【場次 3】** {s['A2']} vs {s['A3']}")
        s["m3_s1"] = st.number_input(f"{s['A2']} 分數 ", min_value=0, max_value=5, value=int(s["m3_s1"]), key="m3_s1_input", disabled=not is_admin)
        s["m3_s2"] = st.number_input(f"{s['A3']} 分數 ", min_value=0, max_value=5, value=int(s["m3_s2"]), key="m3_s2_input", disabled=not is_admin)
        
        st.write(f"**【場次 5】** {s['A1']} vs {s['A3']}")
        s["m5_s1"] = st.number_input(f"{s['A1']} 分數  ", min_value=0, max_value=5, value=int(s["m5_s1"]), key="m5_s1_input", disabled=not is_admin)
        s["m5_s2"] = st.number_input(f"{s['A3']} 分數  ", min_value=0, max_value=5, value=int(s["m5_s2"]), key="m5_s2_input", disabled=not is_admin)

    with col_b:
        st.subheader("🌀 B 組 (循環賽)")
        st.write(f"**【場次 2】** {s['B1']} vs {s['B2']}")
        s["m2_s1"] = st.number_input(f"{s['B1']} 分數", min_value=0, max_value=5, value=int(s["m2_s1"]), key="m2_s1_input", disabled=not is_admin)
        s["m2_s2"] = st.number_input(f"{s['B2']} 分數", min_value=0, max_value=5, value=int(s["m2_s2"]), key="m2_s2_input", disabled=not is_admin)
        
        st.write(f"**【場次 4】** {s['B2']} vs {s['B3']}")
        s["m4_s1"] = st.number_input(f"{s['B2']} 分數 ", min_value=0, max_value=5, value=int(s["m4_s1"]), key="m4_s1_input", disabled=not is_admin)
        s["m4_s2"] = st.number_input(f"{s['B3']} 分數 ", min_value=0, max_value=5, value=int(s["m4_s2"]), key="m4_s2_input", disabled=not is_admin)
        
        st.write(f"**【場次 6】** {s['B1']} vs {s['B3']}")
        s["m6_s1"] = st.number_input(f"{s['B1']} 分數   ", min_value=0, max_value=5, value=int(s["m6_s1"]), key="m6_s1_input", disabled=not is_admin)
        s["m6_s2"] = st.number_input(f"{s['B3']} 分數   ", min_value=0, max_value=5, value=int(s["m6_s2"]), key="m6_s2_input", disabled=not is_admin)

    st.write("---")
    st.subheader("📊 目前小組排名預覽")
    st.info(f"**🥇 A組第一 (直升四強):** {rank_A[0]} | 🥈 第二: {rank_A[1]} | 🥉 第三: {rank_A[2]}")
    st.info(f"**🥇 B組第一 (直升四強):** {rank_B[0]} | 🥈 第二: {rank_B[1]} | 🥉 第三: {rank_B[2]}")

    # 📍 第二階段：敗部復活挑戰賽
    st.write("---")
    st.header("🔥 第二階段：敗部復活挑戰賽")
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.subheader("⚔️ 敗部戰 1")
        st.write(f"**A組第二** `{rank_A[1]}` vs **B組第三** `{rank_B[2]}`")
        s["r1_s1"] = st.number_input(f"{rank_A[1]} 敗部分1", min_value=0, max_value=5, value=int(s["r1_s1"]), key="r1_s1_input", disabled=not is_admin)
        s["r1_s2"] = st.number_input(f"{rank_B[2]} 敗部分2", min_value=0, max_value=5, value=int(s["r1_s2"]), key="r1_s2_input", disabled=not is_admin)
        r1_winner = rank_A[1] if s["r1_s1"] > s["r1_s2"] else rank_B[2]
    with col_r2:
        st.subheader("⚔️ 敗部戰 2")
        st.write(f"**B組第二** `{rank_B[1]}` vs **A組第三** `{rank_A[2]}`")
        s["r2_s1"] = st.number_input(f"{rank_B[1]} 敗部分3", min_value=0, max_value=5, value=int(s["r2_s1"]), key="r2_s1_input", disabled=not is_admin)
        s["r2_s2"] = st.number_input(f"{rank_A[2]} 敗部分4", min_value=0, max_value=5, value=int(s["r2_s2"]), key="r2_s2_input", disabled=not is_admin)
        r2_winner = rank_B[1] if s["r2_s1"] > s["r2_s2"] else rank_A[2]

    # 📍 第三階段：四強賽
    st.write("---")
    st.header("👑 第三階段：真正核心四強賽")
    col_sf1, col_sf2 = st.columns(2)
    with col_sf1:
        st.subheader("🏆 四強賽 A")
        st.write(f"**A組第一** `{rank_A[0]}` vs **敗部戰 2 勝者** `{r2_winner}`")
        s["sf1_s1"] = st.number_input(f"{rank_A[0]} 四強分1", min_value=0, max_value=5, value=int(s["sf1_s1"]), key="sf1_s1_input", disabled=not is_admin)
        s["sf1_s2"] = st.number_input(f"{r2_winner} 四強分2", min_value=0, max_value=5, value=int(s["sf1_s2"]), key="sf1_s2_input", disabled=not is_admin)
        sf1_winner = rank_A[0] if s["sf1_s1"] > s["sf1_s2"] else r2_winner
        sf1_loser = r2_winner if s["sf1_s1"] > s["sf1_s2"] else rank_A[0]
    with col_sf2:
        st.subheader("🏆 四強賽 B")
        st.write(f"**B組第一** `{rank_B[0]}` vs **敗部戰 1 勝者** `{r1_winner}`")
        s["sf2_s1"] = st.number_input(f"{rank_B[0]} 四強分3", min_value=0, max_value=5, value=int(s["sf2_s1"]), key="sf2_s1_input", disabled=not is_admin)
        s["sf2_s2"] = st.number_input(f"{r1_winner} 四強分4", min_value=0, max_value=5, value=int(s["sf2_s2"]), key="sf2_s2_input", disabled=not is_admin)
        sf2_winner = rank_B[0] if s["sf2_s1"] > s["sf2_s2"] else r1_winner
        sf2_loser = r1_winner if s["sf2_s1"] > s["sf2_s2"] else rank_B[0]

    # 📍 第四階段：決賽圈
    st.write("---")
    st.header("✨ 第四階段：榮譽決賽圈")
    col_bm, col_f = st.columns(2)
    with col_bm:
        st.subheader("🥉 季軍賽 (銅牌戰)")
        st.write(f"`{sf1_loser}` vs `{sf2_loser}`")
        s["bm_s1"] = st.number_input(f"{sf1_loser} 決賽分1", min_value=0, max_value=5, value=int(s["bm_s1"]), key="bm_s1_input", disabled=not is_admin)
        s["bm_s2"] = st.number_input(f"{sf2_loser} 決賽分2", min_value=0, max_value=5, value=int(s["bm_s2"]), key="bm_s2_input", disabled=not is_admin)
    with col_f:
        st.subheader("🥇 🚀 總冠軍賽 (金牌戰)")
        st.write(f"👑 `{sf1_winner}` vs 👑 `{sf2_winner}`")
        s["f_s1"] = st.number_input(f"{sf1_winner} 決賽分3", min_value=0, max_value=5, value=int(s["f_s1"]), key="f_s1_input", disabled=not is_admin)
        s["f_s2"] = st.number_input(f"{sf2_winner} 決賽分4", min_value=0, max_value=5, value=int(s["f_s2"]), key="f_s2_input", disabled=not is_admin)

    # 儲存每一步的比分狀態
    if is_admin:
        save_scores()

    # 頒獎台
    if s["f_s1"] > 0 or s["f_s2"] > 0:
        st.write("---")
        st.balloons()
        st.header("🎉 👑 第一屆 戰鬥陀螺 BX 大賽 最終榮譽榜 👑 🎉")
        champion = sf1_winner if s["f_s1"] > s["f_s2"] else sf2_winner
        second_place = sf2_winner if s["f_s1"] > s["f_s2"] else sf1_winner
        third_place = sf1_loser if s["bm_s1"] > s["bm_s2"] else sf2_loser
        
        c1, c2, c3 = st.columns(3)
        c1.metric("🥇 總冠軍 (金牌)", champion)
        c2.metric("🥈 亞軍 (銀牌)", second_place)
        c3.metric("🥉 季軍 (銅牌)", third_place)
