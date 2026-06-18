import streamlit as st
import pandas as pd
import os
import random

st.set_page_config(page_title="n三重盃戰鬥陀螺大賽比賽系統", page_icon="🌀", layout="wide")

DATA_FILE = "beyblade_registrations.csv"
SCORE_FILE = "tournament_scores.csv"
ADMIN_PASSWORD = "admin"  

def load_data():
    if os.path.exists(DATA_FILE): return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["選手名稱", "陀螺1_上蓋", "陀螺1_固鎖", "陀螺1_軸心", "陀螺2_上蓋", "陀螺2_固鎖", "陀螺2_軸心", "陀螺3_上蓋", "陀螺3_固鎖", "陀螺3_軸心", "陀螺4_上蓋", "陀螺4_固鎖", "陀螺4_軸心"])

def save_data(df): df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

df_registrations = load_data()
tab1, tab2 = st.tabs(["📝 選手零件登記表單", "🏆 瑞士輪控制台"])

st.sidebar.header("🔑 管理者驗證專區")
admin_input = st.sidebar.text_input("輸入管理密碼", type="password")
is_admin = (admin_input == ADMIN_PASSWORD)

# ════════════════════════════════════════════════════════════
# 【分頁一：選手登記】
# ════════════════════════════════════════════════════════════
with tab1:
    st.title("🌀 戰鬥陀螺 8人零件登記 (瑞士輪版)")
    st.markdown("### 📝 4分制規則：3勝晉級四強 / 3敗直接淘汰。固鎖與軸心不可重複。禁用：天馬、神杖、鯊魚。")
    
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
        else:
            df_registrations = pd.concat([df_registrations, pd.DataFrame([{"選手名稱": player_name.strip(), "陀螺1_上蓋": b1, "陀螺1_固鎖": r1, "陀螺1_軸心": bit1, "陀螺2_上蓋": b2, "陀螺2_固鎖": r2, "陀螺2_軸心": bit2, "陀螺3_上蓋": b3, "陀螺3_固鎖": r3, "陀螺3_軸心": bit3, "陀螺4_上蓋": b4, "陀螺4_固鎖": r4, "陀螺4_軸心": bit4}])], ignore_index=True)
            save_data(df_registrations)
            st.success(f"🎉 成功登記！"); st.rerun()

    if not df_registrations.empty:
        st.dataframe(df_registrations)

# ════════════════════════════════════════════════════════════
# 【分頁二：LOL 瑞士輪核心控制台】
# ════════════════════════════════════════════════════════════
with tab2:
    st.title("🏆 LOL世界賽制：3勝晉級四強 / 3敗淘汰控制台")
    
    raw_players = df_registrations["選手名稱"].tolist()
    while len(raw_players) < 8: raw_players.append(f"選手_{len(raw_players)+1}")
    players_list = raw_players[:8]

    # 初始化大賽狀態
    if "lol_swiss" not in st.session_state:
        if os.path.exists(SCORE_FILE):
            try: st.session_state.lol_swiss = pd.read_csv(SCORE_FILE).to_dict(orient="records")[0]
            except: pass
        if "lol_swiss" not in st.session_state:
            st.session_state.lol_swiss = {
                "stage": "swiss", # swiss 或是 playoffs
                "round": 1,
                "matches_num": 4, # 當前輪次有幾場比賽
                # 預留最多4場對戰的名單與比分儲存格
                "m1_p1": players_list[0], "m1_p2": players_list[1], "m1_s1": 0, "m1_s2": 0,
                "m2_p1": players_list[2], "m2_p2": players_list[3], "m2_s1": 0, "m2_s2": 0,
                "m3_p1": players_list[4], "m3_p2": players_list[5], "m3_s1": 0, "m3_s2": 0,
                "m4_p1": players_list[6], "m4_p2": players_list[7], "m4_s1": 0, "m4_s2": 0,
                "history": "", # 格式: "pa,pb,sa,sb;..."
                # 季後賽四強比分
                "sf1_s1": 0, "sf1_s2": 0, "sf2_s1": 0, "sf2_s2": 0, "f_s1": 0, "f_s2": 0, "bm_s1": 0, "bm_s2": 0,
                "qualified": "", # 已晉級名單 "," 隔開
                "eliminated": "" # 已淘汰名單 "," 隔開
            }

    lw = st.session_state.lol_swiss
    def save_lw(): pd.DataFrame([lw]).to_csv(SCORE_FILE, index=False)

    if is_admin:
        st.sidebar.subheader("🎲 大賽初始化")
        if st.sidebar.button("💥 生成第一輪隨機對戰組合", type="primary"):
            random.shuffle(players_list)
            lw["stage"] = "swiss"
            lw["round"] = 1
            lw["matches_num"] = 4
            lw["m1_p1"], lw["m1_p2"] = players_list[0], players_list[1]
            lw["m2_p1"], lw["m2_p2"] = players_list[2], players_list[3]
            lw["m3_p1"], lw["m3_p2"] = players_list[4], players_list[5]
            lw["m4_p1"], lw["m4_p2"] = players_list[6], players_list[7]
            lw["m1_s1"] = lw["m1_s2"] = lw["m2_s1"] = lw["m2_s2"] = 0
            lw["m3_s1"] = lw["m3_s2"] = lw["m4_s1"] = lw["m4_s2"] = 0
            lw["history"] = ""
            lw["qualified"] = ""
            lw["eliminated"] = ""
            save_lw(); st.rerun()
        if st.sidebar.button("🔄 全大賽完全歸零重置"):
            if os.path.exists(SCORE_FILE): os.remove(SCORE_FILE)
            if "lol_swiss" in st.session_state: del st.session_state.lol_swiss
            st.rerun()

    # 計算每個人目前的勝敗場
    def get_current_records():
        records = {p: {"w": 0, "l": 0, "diff": 0} for p in players_list}
        if lw["history"]:
            for m in lw["history"].split(";"):
                if not m: continue
                pa, pb, sa, sb = m.split(",")
                sa, sb = int(sa), int(sb)
                if sa > sb:
                    records[pa]["w"] += 1; records[pb]["l"] += 1
                else:
                    records[pb]["w"] += 1; records[pa]["l"] += 1
                records[pa]["diff"] += (sa - sb); records[pb]["diff"] += (sb - sa)
        return records

    records = get_current_records()

    # 顯示瑞士輪戰況
    if lw["stage"] == "swiss":
        st.header(f"📍 LOL瑞士輪預賽：第 【{lw['round']}】 輪 (4分制)")
        
        # 顯示目前每場對決輸入
        cols = st.columns(2)
        for i in range(int(lw["matches_num"])):
            idx = i + 1
            p1_key, p2_key = f"m{idx}_p1", f"m{idx}_p2"
            s1_key, s2_key = f"m{idx}_s1", f"m{idx}_s2"
            
            with cols[i % 2]:
                st.subheader(f"⚔️ 對決 {idx} ({records[lw[p1_key]]['w']}-{records[lw[p1_key]]['l']}戰績組)")
                st.write(f"**{lw[p1_key]}** vs **{lw[p2_key]}**")
                lw[s1_key] = st.number_input(f"{lw[p1_key]} 分數", min_value=0, max_value=4, value=int(lw[s1_key]), key=f"lw_s1_{idx}", disabled=not is_admin)
                lw[s2_key] = st.number_input(f"{lw[p2_key]} 分數", min_value=0, max_value=4, value=int(lw[s2_key]), key=f"lw_s2_{idx}", disabled=not is_admin)

        if is_admin:
            save_lw()
            if st.button("💾 確定本輪打完！由系統自動動態配對下一輪", type="primary"):
                # 1. 把當前輪次塞進歷史
                new_hist = []
                for i in range(int(lw["matches_num"])):
                    idx = i + 1
                    new_hist.append(f"{lw[f'm{idx}_p1']},{lw[f'm{idx}_p2']},{lw[f'm{idx}_s1']},{lw[f'm{idx}_s2']}")
                lw["history"] = (lw["history"] + ";" + ";".join(new_hist)) if lw["history"] else ";".join(new_hist)
                
                # 2. 重新計算最新勝敗
                current_rec = get_current_records()
                
                # 3. 檢查是否有新晉級或新淘汰
                q_list = [p for p, r in current_rec.items() if r["w"] == 3]
                e_list = [p for p, r in current_rec.items() if r["l"] == 3]
                lw["qualified"] = ",".join(q_list)
                lw["eliminated"] = ",".join(e_list)
                
                # 4. 如果晉級人數滿4個，瑞士輪結束，進四強
                if len(q_list) >= 4:
                    lw["stage"] = "playoffs"
                else:
                    # 否則，繼續幫還沒晉級也還沒淘汰的人進行下一輪配對
                    lw["round"] += 1
                    active_players = [p for p in players_list if p not in q_list and p not in e_list]
                    
                    # 依照勝場數分類群組
                    groups = {}
                    for p in active_players:
                        w_count = current_rec[p]["w"]
                        groups.setdefault(w_count, []).append(p)
                    
                    # 將同勝場的湊對
                    next_matches = []
                    for w_count, group_players in sorted(groups.items(), reverse=True):
                        random.shuffle(group_players)
                        # 如果該組是奇數，跟隔壁組借人（LOL瑞士輪標準溢出處理）
                        while len(group_players) >= 2:
                            next_matches.append((group_players.pop(), group_players.pop()))
                    
                    # 如果因為奇數跨組剩下最後一對
                    flat_remain = []
                    for w_count, group_players in groups.items():
                        flat_remain.extend(group_players)
                    while len(flat_remain) >= 2:
                        next_matches.append((flat_remain.pop(), flat_remain.pop()))
                    
                    # 把配對寫入下一輪
                    lw["matches_num"] = len(next_matches)
                    for i, (pa, pb) in enumerate(next_matches):
                        idx = i + 1
                        lw[f"m{idx}_p1"], lw[f"m{idx}_p2"] = pa, pb
                        lw[f"m{idx}_s1"], lw[f"m{idx}_s2"] = 0, 0
                        
                save_lw(); st.rerun()

    # ════════════════════════════════════════════════════════════
    # 📊 顯示即時大會看板（左邊：名單狀態 / 右邊：目前詳細數據）
    # ════════════════════════════════════════════════════════════
    st.write("---")
    c_board1, c_board2 = st.columns([1, 2])
    with c_board1:
        st.subheader("📢 核心戰績狀態公告")
        q_names = lw["qualified"].split(",") if lw["qualified"] else []
        e_names = lw["eliminated"].split(",") if lw["eliminated"] else []
        
        st.success(f"👑 **已成功晉級四強 ({len(q_names)}/4):**\n" + "\n".join([f"* {name} (3勝)" for name in q_names if name]))
        st.error(f"💀 **已不幸遭到淘汰 ({len(e_names)}/4):**\n" + "\n".join([f"* {name} (3敗)" for name in e_names if name]))
    
    with c_board2:
        st.subheader("📊 每位選手即時詳細戰績表")
        df_show = pd.DataFrame.from_dict(records, orient="index").reset_index().rename(columns={"index": "選手名稱", "w": "勝場", "l": "敗場", "diff": "淨勝分差"})
        st.dataframe(df_show.sort_values(by=["勝場", "淨勝分差"], ascending=False).reset_index(drop=True))

    # ════════════════════════════════════════════════════════════
    # 👑 核心四強單敗淘汰賽 (當晉級滿4人時自動炸裂解鎖)
    # ════════════════════════════════════════════════════════════
    if lw["stage"] == "playoffs" or len(lw["qualified"].split(",")) >= 4:
        st.write("---")
        st.header("🔥 終極決賽圈：核心四強單敗淘汰賽 (4分制)")
        
        top_4 = [p for p in lw["qualified"].split(",") if p]
        # 防呆確保滿四人
        while len(top_4) < 4: top_4.append(f"決賽選手_{len(top_4)+1}")
        
        rank1, rank2, rank3, rank4 = top_4[0], top_4[1], top_4[2], top_4[3]
        
        col_sf1, col_sf2 = st.columns(2)
        with col_sf1:
            st.subheader("🏆 四強準決賽 A")
            st.write(f"**強者 A** `{rank1}` vs **強者 D** `{rank4}`")
            lw["sf1_s1"] = st.number_input(f"{rank1} 得分", min_value=0, max_value=4, value=int(lw["sf1_s1"]), key="lol_sf1_1", disabled=not is_admin)
            lw["sf1_s2"] = st.number_input(f"{rank4} 得分", min_value=0, max_value=4, value=int(lw["sf1_s2"]), key="lol_sf1_2", disabled=not is_admin)
            sf1_winner = rank1 if lw["sf1_s1"] > lw["sf1_s2"] else rank4
            sf1_loser = rank4 if lw["sf1_s1"] > lw["sf1_s2"] else rank1
        with col_sf2:
            st.subheader("🏆 四強準決賽 B")
            st.write(f"**強者 B** `{rank2}` vs **強者 C** `{rank3}`")
            lw["sf2_s1"] = st.number_input(f"{rank2} 得分 ", min_value=0, max_value=4, value=int(lw["sf2_s1"]), key="lol_sf2_1", disabled=not is_admin)
            lw["sf2_s2"] = st.number_input(f"{rank3} 得分 ", min_value=0, max_value=4, value=int(lw["sf2_s2"]), key="lol_sf2_2", disabled=not is_admin)
            sf2_winner = rank2 if lw["sf2_s1"] > lw["sf2_s2"] else rank3
            sf2_loser = rank3 if lw["sf2_s1"] > lw["sf2_s2"] else rank2

        st.write("---")
        st.header("✨ 最終榮譽戰")
        col_bm, col_f = st.columns(2)
        with col_bm:
            st.subheader("🥉 季軍賽 (銅牌戰)")
            st.write(f"`{sf1_loser}` vs `{sf2_loser}`")
            lw["bm_s1"] = st.number_input(f"{sf1_loser} 決賽得分1", min_value=0, max_value=4, value=int(lw["bm_s1"]), key="lol_bm_1", disabled=not is_admin)
            lw["bm_s2"] = st.number_input(f"{sf2_loser} 決賽得分2", min_value=0, max_value=4, value=int(lw["bm_s2"]), key="lol_bm_2", disabled=not is_admin)
        with col_f:
            st.subheader("🥇 🚀 總冠軍賽 (金牌戰)")
            st.write(f"👑 `{sf1_winner}` vs 👑 `{sf2_winner}`")
            lw["f_s1"] = st.number_input(f"{sf1_winner} 決賽得分3", min_value=0, max_value=4, value=int(lw["f_s1"]), key="lol_f_1", disabled=not is_admin)
            lw["f_s2"] = st.number_input(f"{sf2_winner} 決賽得分4", min_value=0, max_value=4, value=int(lw["f_s2"]), key="lol_f_2", disabled=not is_admin)

        if is_admin: save_lw()

        if lw["f_s1"] > 0 or lw["f_s2"] > 0:
            st.write("---")
            st.balloons()
            st.header("🎉 👑 第一屆 三重盃 戰鬥陀螺 最終榮譽榜 👑 🎉")
            champion = sf1_winner if lw["f_s1"] > lw["f_s2"] else sf2_winner
            second_place = sf2_winner if lw["f_s1"] > lw["f_s2"] else sf1_winner
            third_place = sf1_loser if lw["bm_s1"] > lw["bm_s2"] else sf2_loser
            
            c1, c2, c3 = st.columns(3)
            c1.metric("🥇 總冠軍 (金牌)", champion)
            c2.metric("🥈 亞軍 (銀牌)", second_place)
            c3.metric("🥉 季軍 (銅牌)", third_place)
