import streamlit as st
import pandas as pd
import os
import random

st.set_page_config(page_title="戰鬥陀螺大賽系統", page_icon="🌀", layout="wide")

DATA_FILE = "beyblade_registrations.csv"
SCORE_FILE = "tournament_scores.csv"
ADMIN_PASSWORD = "admin"  

# 💾 資料載入與儲存
def load_data():
    if os.path.exists(DATA_FILE): return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["選手名稱", "陀螺1_上蓋", "陀螺1_固鎖", "陀螺1_軸心", "陀螺2_上蓋", "陀螺2_固鎖", "陀螺2_軸心", "陀螺3_上蓋", "陀螺3_固鎖", "陀螺3_軸心", "陀螺4_上蓋", "陀螺4_固鎖", "陀螺4_軸心"])

def save_data(df): df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

df_registrations = load_data()

tab1, tab2 = st.tabs(["📝 選手零件登記表單", "🏆 瑞士輪大賽控制台"])

st.sidebar.header("🔑 管理者驗證專區")
admin_input = st.sidebar.text_input("輸入管理密碼", type="password")
is_admin = (admin_input == ADMIN_PASSWORD)

if is_admin: st.sidebar.success("🔓 管理員權限已全開。")
else: st.sidebar.info("🔒 目前為訪客唯讀模式。")

# ════════════════════════════════════════════════════════════
# 【分頁一：選手登記】
# ════════════════════════════════════════════════════════════
with tab1:
    st.title("🌀 戰鬥陀螺 8人瑞士輪零件登記")
    st.markdown("### 📝 4分制大賽規則：每人 4 顆陀螺，固鎖與軸心不可重複。禁用：天馬、神杖、鯊魚。")
    
    with st.form("reg_form"):
        player_name = st.text_input("👤 選手名稱 / 綽號")
        c1, c2 = st.columns(2)
        with c1:
            b1, r1, bit1 = st.text_input("1_上蓋"), st.text_input("1_固鎖"), st.text_input("1_軸心")
            b3, r3, bit3 = st.text_input("3_上蓋"), st.text_input("3_固鎖"), st.text_input("3_軸心")
        with c2:
            b2, r2, bit2 = st.text_input("2_上蓋"), st.text_input("2_固鎖"), st.text_input("2_軸心")
            b4, r4, bit4 = st.text_input("4_上蓋"), st.text_input("4_固鎖"), st.text_input("4_軸心")
        submit_btn = st.form_submit_button("🚀 提交登記")

    if submit_btn:
        if not player_name.strip() or player_name.strip() in df_registrations["選手名稱"].values:
            st.error("❌ 名字留空或重複登記！")
        elif not all([b1, r1, bit1, b2, r2, bit2, b3, r3, bit3, b4, r4, bit4]):
            st.error("❌ 請填滿所有零件欄位！")
        else:
            df_registrations = pd.concat([df_registrations, pd.DataFrame([{"選手名稱": player_name.strip(), "陀螺1_上蓋": b1, "陀螺1_固鎖": r1, "陀螺1_軸心": bit1, "陀螺2_上蓋": b2, "陀螺2_固鎖": r2, "陀螺2_軸心": bit2, "陀螺3_上蓋": b3, "陀螺3_固鎖": r3, "陀螺3_軸心": bit3, "陀螺4_上蓋": b4, "陀螺4_固鎖": r4, "陀螺4_軸心": bit4}])], ignore_index=True)
            save_data(df_registrations)
            st.success(f"🎉 成功登記！"); st.rerun()

    if not df_registrations.empty:
        st.dataframe(df_registrations)
        if is_admin and st.button("🗑️ 清空所有報名資料"):
            if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
            st.rerun()

# ════════════════════════════════════════════════════════════
# 【分頁二：瑞士輪與淘汰賽核心引擎】
# ════════════════════════════════════════════════════════════
with tab2:
    st.title("🏆 瑞士輪 3 輪預賽 ＋ 4強單敗決賽控制台")
    
    raw_players = df_registrations["選手名稱"].tolist()
    while len(raw_players) < 8: raw_players.append(f"選手_{len(raw_players)+1}")
    players_list = raw_players[:8]

    # 初始化大賽狀態
    if "swiss" not in st.session_state:
        if os.path.exists(SCORE_FILE):
            try: st.session_state.swiss = pd.read_csv(SCORE_FILE).to_dict(orient="records")[0]
            except: pass
        if "swiss" not in st.session_state:
            st.session_state.swiss = {
                "current_round": 1,
                "p1_1": players_list[0], "p1_2": players_list[1], "p1_s1": 0, "p1_s2": 0,
                "p2_1": players_list[2], "p2_2": players_list[3], "p2_s1": 0, "p2_s2": 0,
                "p3_1": players_list[4], "p3_2": players_list[5], "p3_s1": 0, "p3_s2": 0,
                "p4_1": players_list[6], "p4_2": players_list[7], "p4_s1": 0, "p4_s2": 0,
                "history": "", # 記錄前幾輪結果以計算積分
                "sf1_s1": 0, "sf1_s2": 0, "sf2_s1": 0, "sf2_s2": 0, "f_s1": 0, "f_s2": 0, "bm_s1": 0, "bm_s2": 0
            }

    sw = st.session_state.swiss
    def save_swiss(): pd.DataFrame([sw]).to_csv(SCORE_FILE, index=False)

    # 管理功能
    if is_admin:
        st.sidebar.subheader("🎲 大賽初始化 / 抽籤")
        if st.sidebar.button("💥 生成第一輪隨機對戰組合", type="primary"):
            random.shuffle(players_list)
            sw["current_round"] = 1
            sw["p1_1"], sw["p1_2"] = players_list[0], players_list[1]
            sw["p2_1"], sw["p2_2"] = players_list[2], players_list[3]
            sw["p3_1"], sw["p3_2"] = players_list[4], players_list[5]
            sw["p4_1"], sw["p4_2"] = players_list[6], players_list[7]
            sw["p1_s1"], sw["p1_s2"], sw["p2_s1"], sw["p2_s2"] = 0, 0, 0, 0
            sw["p3_s1"], sw["p3_s2"], sw["p4_s1"], sw["p4_s2"] = 0, 0, 0, 0
            sw["history"] = ""
            save_swiss(); st.rerun()
        if st.sidebar.button("🔄 全大賽完全歸零重置"):
            if os.path.exists(SCORE_FILE): os.remove(SCORE_FILE)
            if "swiss" in st.session_state: del st.session_state.swiss
            st.rerun()

    # 解析歷史與當前數據計算即時積分榜
    def calc_standings():
        stats = {p: {"wins": 0, "diff": 0} for p in players_list}
        # 讀取歷史
        if sw["history"]:
            for match in sw["history"].split(";"):
                if not match: continue
                pa, pb, sa, sb = match.split(",")
                sa, sb = int(sa), int(sb)
                if sa > sb: stats[pa]["wins"] += 1
                elif sb > sa: stats[pb]["wins"] += 1
                stats[pa]["diff"] += (sa - sb); stats[pb]["diff"] += (sb - sa)
        # 如果是當前正在打的輪次且已經打完，也計入排行預覽
        if sw["current_round"] <= 3:
            cur_matches = [(sw["p1_1"], sw["p1_2"], sw["p1_s1"], sw["p1_s2"]), (sw["p2_1"], sw["p2_2"], sw["p2_s1"], sw["p2_s2"]), (sw["p3_1"], sw["p3_2"], sw["p3_s1"], sw["p3_s2"]), (sw["p4_1"], sw["p4_2"], sw["p4_s1"], sw["p4_s2"])]
            for pa, pb, sa, sb in cur_matches:
                if sa > 0 or sb > 0:
                    if sa > sb: stats[pa]["wins"] += 1
                    elif sb > sa: stats[pb]["wins"] += 1
                    stats[pa]["diff"] += (sa - sb); stats[pb]["diff"] += (sb - sa)
        df_rank = pd.DataFrame.from_dict(stats, orient="index").reset_index().rename(columns={"index": "選手名稱", "wins": "總勝場", "diff": "總得分差"})
        return df_rank.sort_values(by=["總勝場", "總得分差"], ascending=False).reset_index(drop=True)

    df_current_rank = calc_standings()

    # 顯示瑞士輪進度
    if sw["current_round"] <= 3:
        st.header(f"📍 瑞士輪預賽：第 【{sw['current_round']} / 3】 輪 (4分制)")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader(f"⚔️ 對決 1")
            st.write(f"**{sw['p1_1']}** vs **{sw['p1_2']}**")
            sw["p1_s1"] = st.number_input(f"{sw['p1_1']} 分數", min_value=0, max_value=4, value=int(sw["p1_s1"]), key="p1_s1_in", disabled=not is_admin)
            sw["p1_s2"] = st.number_input(f"{sw['p1_2']} 分數", min_value=0, max_value=4, value=int(sw["p1_s2"]), key="p1_s2_in", disabled=not is_admin)
            
            st.subheader(f"⚔️ 對決 2")
            st.write(f"**{sw['p2_1']}** vs **{sw['p2_2']}**")
            sw["p2_s1"] = st.number_input(f"{sw['p2_1']} 分數", min_value=0, max_value=4, value=int(sw["p2_s1"]), key="p2_s1_in", disabled=not is_admin)
            sw["p2_s2"] = st.number_input(f"{sw['p2_2']} 分數", min_value=0, max_value=4, value=int(sw["p2_s2"]), key="p2_s2_in", disabled=not is_admin)
        with c2:
            st.subheader(f"⚔️ 對決 3")
            st.write(f"**{sw['p3_1']}** vs **{sw['p3_2']}**")
            sw["p3_s1"] = st.number_input(f"{sw['p3_1']} 分數", min_value=0, max_value=4, value=int(sw["p3_s1"]), key="p3_s1_in", disabled=not is_admin)
            sw["p3_s2"] = st.number_input(f"{sw['p3_2']} 分數", min_value=0, max_value=4, value=int(sw["p3_s2"]), key="p3_s2_in", disabled=not is_admin)
            
            st.subheader(f"⚔️ 對決 4")
            st.write(f"**{sw['p4_1']}** vs **{sw['p4_2']}**")
            sw["p4_s1"] = st.number_input(f"{sw['p4_1']} 分數", min_value=0, max_value=4, value=int(sw["p4_s1"]), key="p4_s1_in", disabled=not is_admin)
            sw["p4_s2"] = st.number_input(f"{sw['p4_2']} 分數", min_value=0, max_value=4, value=int(sw["p4_s2"]), key="p4_s2_in", disabled=not is_admin)

        if is_admin:
            save_swiss()
            if st.button("💾 確定本輪打完！生成下一輪/結算組合", type="primary"):
                round_str = f"{sw['p1_1']},{sw['p1_2']},{sw['p1_s1']},{sw['p1_s2']};{sw['p2_1']},{sw['p2_2']},{sw['p2_s1']},{sw['p2_s2']};{sw['p3_1']},{sw['p3_2']},{sw['p3_s1']},{sw['p3_s2']};{sw['p4_1']},{sw['p4_2']},{sw['p4_s1']},{sw['p4_s2']}"
                sw["history"] = (sw["history"] + ";" + round_str) if sw["history"] else round_str
                
                if sw["current_round"] < 3:
                    sw["current_round"] += 1
                    next_pool = calc_standings()["選手名稱"].tolist()
                    sw["p1_1"], sw["p1_2"] = next_pool[0], next_pool[1]
                    sw["p2_1"], sw["p2_2"] = next_pool[2], next_pool[3]
                    sw["p3_1"], sw["p3_2"] = next_pool[4], next_pool[5]
                    sw["p4_1"], sw["p4_2"] = next_pool[6], next_pool[7]
                    sw["p1_s1"], sw["p1_s2"], sw["p2_s1"], sw["p2_s2"] = 0, 0, 0, 0
                    sw["p3_s1"], sw["p3_s2"], sw["p4_s1"], sw["p4_s2"] = 0, 0, 0, 0
                else:
                    sw["current_round"] = 4 
                save_swiss(); st.rerun()
    else:
        st.write("---")

    st.subheader("📊 瑞士輪即時總排行榜 (前四名晉級決賽)")
    st.dataframe(df_current_rank)

    # ════════════════════════════════════════════════════════════
    # 👑 四強單敗淘汰賽圈 (第 4 輪起自動解鎖)
    # ════════════════════════════════════════════════════════════
    if sw["current_round"] >= 4:
        st.write("---")
        st.header("🔥 決賽圈：核心四強交叉單敗淘汰賽 (4分制)")
        
        top_4 = df_current_rank["選手名稱"].tolist()[:4]
        rank1, rank2, rank3, rank4 = top_4[0], top_4[1], top_4[2], top_4[3]
        
        col_sf1, col_sf2 = st.columns(2)
        with col_sf1:
            st.subheader("🏆 四強準決賽 A")
            st.write(f"**預賽第 1 名** `{rank1}` vs **預賽第 4 名** `{rank4}`")
            sw["sf1_s1"] = st.number_input(f"{rank1} 分", min_value=0, max_value=4, value=int(sw["sf1_s1"]), key="sf1_s1_idx", disabled=not is_admin)
            sw["sf1_s2"] = st.number_input(f"{rank4} 分", min_value=0, max_value=4, value=int(sw["sf1_s2"]), key="sf1_s2_idx", disabled=not is_admin)
            sf1_winner = rank1 if sw["sf1_s1"] > sw["sf1_s2"] else rank4
            sf1_loser = rank4 if sw["sf1_s1"] > sw["sf1_s2"] else rank1
        with col_sf2:
            st.subheader("🏆 四強準決賽 B")
            st.write(f"**預賽第 2 名** `{rank2}` vs **預賽第 3 名** `{rank3}`")
            sw["sf2_s1"] = st.number_input(f"{rank2} 分 ", min_value=0, max_value=4, value=int(sw["sf2_s1"]), key="sf2_s1_idx", disabled=not is_admin)
            sw["sf2_s2"] = st.number_input(f"{rank3} 分 ", min_value=0, max_value=4, value=int(sw["sf2_s2"]), key="sf2_s2_idx", disabled=not is_admin)
            sf2_winner = rank2 if sw["sf2_s1"] > sw["sf2_s2"] else rank3
            sf2_loser = rank3 if sw["sf2_s1"] > sw["sf2_s2"] else rank2

        st.write("---")
        st.header("✨ 最終榮譽殿堂戰")
        col_bm, col_f = st.columns(2)
        with col_bm:
            st.subheader("🥉 季軍賽 (銅牌爭奪戰)")
            st.write(f"`{sf1_loser}` vs `{sf2_loser}`")
            sw["bm_s1"] = st.number_input(f"{sf1_loser} 決賽分1", min_value=0, max_value=4, value=int(sw["bm_s1"]), key="bm_s1_idx", disabled=not is_admin)
            sw["bm_s2"] = st.number_input(f"{sf2_loser} 決賽分2", min_value=0, max_value=4, value=int(sw["bm_s2"]), key="bm_s2_idx", disabled=not is_admin)
        with col_f:
            st.subheader("🥇 🚀 總冠軍賽 (金牌終極戰)")
            st.write(f"👑 `{sf1_winner}` vs 👑 `{sf2_winner}`")
            sw["f_s1"] = st.number_input(f"{sf1_winner} 決賽分3", min_value=0, max_value=4, value=int(sw["f_s1"]), key="f_s1_idx", disabled=not is_admin)
            sw["f_s2"] = st.number_input(f"{sf2_winner} 決賽分4", min_value=0, max_value=4, value=int(sw["f_s2"]), key="f_s2_idx", disabled=not is_admin)

        if is_admin: save_swiss()

        if sw["f_s1"] > 0 or sw["f_s2"] > 0:
            st.write("---")
            st.balloons()
            st.header("🎉 👑 第一屆 戰鬥陀螺 BX 瑞士輪大賽 最終榮譽榜 👑 🎉")
            champion = sf1_winner if sw["f_s1"] > sw["f_s2"] else sf2_winner
            second_place = sf2_winner if sw["f_s1"] > sw["f_s2"] else sf1_winner
            third_place = sf1_loser if sw["bm_s1"] > sw["bm_s2"] else sf2_loser
            
            c1, c2, c3 = st.columns(3)
            c1.metric("🥇 總冠軍 (金牌)", champion)
            c2.metric("🥈 亞軍 (銀牌)", second_place)
            c3.metric("🥉 季軍 (銅牌)", third_place)
