import random
import pandas as pd
import streamlit as st

st.set_page_config(page_title="三重盃 陀螺大賽賽務系統", layout="wide")

st.title("🏆 三重盃 陀螺大賽賽務系統")

# ==========================================
# 1. 初始化 Session State
# ==========================================
# 個人賽資料庫
if "swiss_matches" not in st.session_state:
    st.session_state.swiss_matches = {}

if "players" not in st.session_state:
    st.session_state.players = {i: f"選手 {i}" for i in range(1, 11)}

# 團體賽資料庫
if "team_matches" not in st.session_state:
    st.session_state.team_matches = {}

if "teams" not in st.session_state:
    st.session_state.teams = {
        "A": "隊伍 A",
        "B": "隊伍 B",
        "C": "隊伍 C",
        "D": "隊伍 D",
        "E": "隊伍 E"
    }

# ==========================================
# 2. 個人賽：瑞士輪計算與智慧配對邏輯
# ==========================================
def calculate_swiss_standings():
    wins = {i: 0 for i in range(1, 11)}
    losses = {i: 0 for i in range(1, 11)}
    defeated_opponents = {i: [] for i in range(1, 11)}
    played_pairs = set()

    for r, matches in st.session_state.swiss_matches.items():
        for p1, p2, winner in matches:
            if winner is not None and winner != "未比賽":
                pair = (min(p1, p2), max(p1, p2))
                played_pairs.add(pair)
                if winner == p1:
                    wins[p1] += 1
                    losses[p2] += 1
                    defeated_opponents[p1].append(p2)
                elif winner == p2:
                    wins[p2] += 1
                    losses[p1] += 1
                    defeated_opponents[p2].append(p1)

    # 計算 SOS (對手強度分：擊敗過的對手總勝場)
    sos = {p: sum(wins[opp] for opp in defeated_opponents[p]) for p in range(1, 11)}

    # 排序：1.總勝場 2.SOS強度 3.選手ID
    ranked_ids = sorted(
        range(1, 11),
        key=lambda x: (wins[x], sos[x], -x),
        reverse=True
    )
    
    return wins, losses, sos, played_pairs, ranked_ids, defeated_opponents

def generate_swiss_round_pairings(target_round):
    wins, losses, _, played_pairs, ranked_ids, _ = calculate_swiss_standings()
    
    # 第 1 輪：隨機對戰
    if target_round == 1:
        shuffled = list(range(1, 11))
        random.shuffle(shuffled)
        return [(shuffled[i], shuffled[i+1], "0-0") for i in range(0, 10, 2)]

    # 第 2~4 輪：戰績相近配對 (含避開重複對戰與極端備案)
    unpaired = ranked_ids.copy()
    pairings = []

    while unpaired:
        p1 = unpaired.pop(0)
        best_p2 = None
        
        for p2 in unpaired:
            pair_key = (min(p1, p2), max(p1, p2))
            if pair_key not in played_pairs:
                best_p2 = p2
                break
        
        # 容錯機制：若極端狀況下全打過，強制配對第一個未配對選手
        if best_p2 is None:
            best_p2 = unpaired[0]
            
        unpaired.remove(best_p2)
        group_label = f"{wins[p1]}-{losses[p1]}"
        pairings.append((p1, best_p2, group_label))
        
    return pairings

# ==========================================
# 3. 雙人團體賽：單循環計算與生成
# ==========================================
def generate_team_round_robin():
    teams_list = ["A", "B", "C", "D", "E"]
    matches = []
    for i in range(len(teams_list)):
        for j in range(i + 1, len(teams_list)):
            matches.append((teams_list[i], teams_list[j]))
    return matches

def calculate_team_standings():
    team_wins = {t: 0 for t in st.session_state.teams}
    team_losses = {t: 0 for t in st.session_state.teams}
    h2h = {}

    for (t1, t2), winner in st.session_state.team_matches.items():
        if winner in [t1, t2]:
            h2h[(t1, t2)] = winner
            h2h[(t2, t1)] = winner
            if winner == t1:
                team_wins[t1] += 1
                team_losses[t2] += 1
            else:
                team_wins[t2] += 1
                team_losses[t1] += 1

    # 排序：1.勝場多優先
    ranked_teams = sorted(
        st.session_state.teams.keys(),
        key=lambda t: (team_wins[t], -ord(t)),
        reverse=True
    )
    return team_wins, team_losses, ranked_teams

# ==========================================
# 4. 主介面：分頁切換
# ==========================================
tab1, tab2 = st.tabs(["🤺 個人賽 (4輪瑞士輪 + 4強決賽)", "🤝 雙人團體賽 (5隊單循環)"])

# ------------------------------------------
# TAB 1: 個人賽
# ------------------------------------------
with tab1:
    st.header("🤺 個人賽：10人 4輪瑞士輪賽制")
    
    # 選手名稱設定區
    with st.expander("⚙️ 選手名單管理"):
        cols = st.columns(5)
        for i in range(1, 11):
            with cols[(i-1) % 5]:
                st.session_state.players[i] = st.text_input(f"選手 {i} 姓名", value=st.session_state.players[i], key=f"p_name_{i}")

    # 分頁管理預賽與決賽
    p_tab1, p_tab2 = st.tabs(["📊 預賽戰績榜與對戰輸入", "🏆 4強決賽賽程"])

    with p_tab1:
        wins, losses, sos, _, ranked_ids, _ = calculate_swiss_standings()

        st.subheader("📈 目前瑞士輪積分榜")
        standings_data = []
        for rank, p_id in enumerate(ranked_ids, 1):
            standings_data.append({
                "名次": rank,
                "選手編號": f"#{p_id}",
                "選手姓名": st.session_state.players[p_id],
                "勝場 (Wins)": wins[p_id],
                "敗場 (Losses)": losses[p_id],
                "SOS (對手強度分)": sos[p_id]
            })
        st.dataframe(pd.DataFrame(standings_data), use_container_width=True)

        st.markdown("---")
        st.subheader("⚔️ 各輪次對戰結果登記")
        
        r_tabs = st.tabs([f"第 {r} 輪" for r in range(1, 5)])
        
        for r_idx, r_tab in enumerate(r_tabs, 1):
            with r_tab:
                if r_idx not in st.session_state.swiss_matches:
                    st.session_state.swiss_matches[r_idx] = [
                        (p1, p2, None) for p1, p2, _ in generate_swiss_round_pairings(r_idx)
                    ]
                
                updated_matches = []
                for m_idx, (p1, p2, winner) in enumerate(st.session_state.swiss_matches[r_idx]):
                    name1 = st.session_state.players[p1]
                    name2 = st.session_state.players[p2]
                    
                    options = ["未比賽", name1, name2]
                    default_idx = 0
                    if winner == p1: default_idx = 1
                    elif winner == p2: default_idx = 2
                    
                    selected_winner_name = st.selectbox(
                        f"Match {m_idx+1}: {name1} VS {name2}",
                        options,
                        index=default_idx,
                        key=f"swiss_r{r_idx}_m{m_idx}"
                    )
                    
                    if selected_winner_name == name1: win_id = p1
                    elif selected_winner_name == name2: win_id = p2
                    else: win_id = None
                    
                    updated_matches.append((p1, p2, win_id))
                
                st.session_state.swiss_matches[r_idx] = updated_matches

    with p_tab2:
        st.subheader("🏆 4強單淘汰決賽")
        
        # 抓取預賽前 4 名
        top4 = ranked_ids[:4]
        p1_id, p2_id, p3_id, p4_id = top4[0], top4[1], top4[2], top4[3]
        
        p1_name, p2_name = st.session_state.players[p1_id], st.session_state.players[p2_id]
        p3_name, p4_name = st.session_state.players[p3_id], st.session_state.players[p4_id]

        df_finals = pd.DataFrame([
            {"階段": "準決賽A", "對戰": f"預賽第1 [{p1_name}] vs 預賽第4 [{p4_name}]", "勝者": "", "敗者": ""},
            {"階段": "準決賽B", "對戰": f"預賽第2 [{p2_name}] vs 預賽第3 [{p3_name}]", "勝者": "", "敗者": ""},
            {"階段": "季軍賽", "對戰": "準決賽A敗者 vs 準決賽B敗者", "勝者": "", "敗者": ""},
            {"階段": "冠軍賽", "對戰": "準決賽A勝者 vs 準決賽B勝者", "勝者": "", "敗者": ""}
        ])

        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 準決賽對戰結果")
            resA = st.selectbox("準決賽 A 勝者", [p1_name, p4_name], key="sf_a_res")
            lossA = p4_name if resA == p1_name else p1_name

            resB = st.selectbox("準決賽 B 勝者", [p2_name, p3_name], key="sf_b_res")
            lossB = p3_name if resB == p2_name else p2_name

        with col2:
            st.markdown("#### 決賽與季軍賽對戰結果")
            res3 = st.selectbox("季軍賽 勝者 (季軍)", [lossA, lossB], key="f_3rd_res")
            loss3 = lossB if res3 == lossA else lossA

            resF = st.selectbox("冠軍賽 勝者 (冠軍)", [resA, resB], key="f_1st_res")
            lossF = resB if resF == resA else resA

        # 安全賦值寫入 (以 .at 避開 TypeError)
        idx_a = df_finals[df_finals["階段"] == "準決賽A"].index
        if not idx_a.empty:
            df_finals.at[idx_a[0], "勝者"] = str(resA)
            df_finals.at[idx_a[0], "敗者"] = str(lossA)

        idx_b = df_finals[df_finals["階段"] == "準決賽B"].index
        if not idx_b.empty:
            df_finals.at[idx_b[0], "勝者"] = str(resB)
            df_finals.at[idx_b[0], "敗者"] = str(lossB)

        idx_3 = df_finals[df_finals["階段"] == "季軍賽"].index
        if not idx_3.empty:
            df_finals.at[idx_3[0], "勝者"] = str(res3)
            df_finals.at[idx_3[0], "敗者"] = str(loss3)

        idx_f = df_finals[df_finals["階段"] == "冠軍賽"].index
        if not idx_f.empty:
            df_finals.at[idx_f[0], "勝者"] = str(resF)
            df_finals.at[idx_f[0], "敗者"] = str(lossF)

        st.markdown("### 📋 決賽樹狀圖與最終名次")
        st.table(df_finals)


# ------------------------------------------
# TAB 2: 雙人團體賽
# ------------------------------------------
with tab2:
    st.header("🤝 雙人團體賽：5隊單循環賽制")

    # 隊伍名稱設定區
    with st.expander("⚙️ 隊伍名稱管理"):
        t_cols = st.columns(5)
        for idx, team_code in enumerate(["A", "B", "C", "D", "E"]):
            with t_cols[idx]:
                st.session_state.teams[team_code] = st.text_input(
                    f"隊伍 {team_code}",
                    value=st.session_state.teams[team_code],
                    key=f"t_name_{team_code}"
                )

    team_tab1, team_tab2 = st.tabs(["📊 預賽單循環對戰與戰績", "👑 團體總冠軍賽"])

    with team_tab1:
        st.subheader("⚔️ 單循環對戰登記 (共 10 場)")
        all_team_matches = generate_team_round_robin()
        
        col_left, col_right = st.columns(2)
        
        for idx, (t1, t2) in enumerate(all_team_matches):
            t1_name = st.session_state.teams[t1]
            t2_name = st.session_state.teams[t2]
            
            target_col = col_left if idx < 5 else col_right
            
            with target_col:
                curr_winner = st.session_state.team_matches.get((t1, t2), "未比賽")
                
                opts = ["未比賽", t1_name, t2_name]
                def_i = 0
                if curr_winner == t1: def_i = 1
                elif curr_winner == t2: def_i = 2
                
                sel = st.selectbox(
                    f"場次 {idx+1}: {t1_name} VS {t2_name}",
                    opts,
                    index=def_i,
                    key=f"tm_{t1}_{t2}"
                )
                
                if sel == t1_name: st.session_state.team_matches[(t1, t2)] = t1
                elif sel == t2_name: st.session_state.team_matches[(t1, t2)] = t2
                else: st.session_state.team_matches[(t1, t2)] = "未比賽"

        st.markdown("---")
        st.subheader("📈 團體賽預賽戰績榜")
        t_wins, t_losses, ranked_teams = calculate_team_standings()
        
        t_standings_data = []
        for rank, t_code in enumerate(ranked_teams, 1):
            t_standings_data.append({
                "名次": rank,
                "隊伍代號": t_code,
                "隊伍名稱": st.session_state.teams[t_code],
                "勝場": t_wins[t_code],
                "敗場": t_losses[t_code]
            })
        st.dataframe(pd.DataFrame(t_standings_data), use_container_width=True)

    with team_tab2:
        st.subheader("👑 團體冠亞軍總決賽")
        t_wins, t_losses, ranked_teams = calculate_team_standings()
        
        top1_code, top2_code = ranked_teams[0], ranked_teams[1]
        top1_name = st.session_state.teams[top1_code]
        top2_name = st.session_state.teams[top2_code]

        df_team_final = pd.DataFrame([
            {"階段": "團體總冠軍賽", "對戰": f"預賽第1 [{top1_name}] vs 預賽第2 [{top2_name}]", "總冠軍": "", "總亞軍": ""}
        ])

        team_champ = st.selectbox("🏆 請選擇團體總冠軍", [top1_name, top2_name], key="team_champ_sel")
        team_runner = top2_name if team_champ == top1_name else top1_name

        idx_tf = df_team_final[df_team_final["階段"] == "團體總冠軍賽"].index
        if not idx_tf.empty:
            df_team_final.at[idx_tf[0], "總冠軍"] = str(team_champ)
            df_team_final.at[idx_tf[0], "總亞軍"] = str(team_runner)

        st.table(df_team_final)
