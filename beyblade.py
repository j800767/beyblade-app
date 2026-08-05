import streamlit as st
import pandas as pd
import os
import random

# ==========================================
# 1. 基礎設定與檔案路徑
# ==========================================
st.set_page_config(page_title="三重盃 陀螺賽事管理系統", page_icon="💥", layout="wide")

REG_FILE = "players_registration.csv"          # 個人賽選手名單 (10人)
SWISS_MATCH_FILE = "swiss_matches.csv"         # 個人賽瑞士輪賽程檔案
FINALS_FILE = "finals_matches.csv"             # 個人賽四強單淘汰檔案

TEAM_DATA_FILE = "team_players_registration.csv" # 團體賽名單檔案 (5組)
TEAM_MATCH_FILE = "team_matches.csv"           # 團體賽單循環賽程檔案
TEAM_FINALS_FILE = "team_finals_matches.csv"   # 團體賽冠亞軍決賽檔案

ADMIN_PASSWORD = "admin"  # 管理員預設密碼
TEAM_NAMES = ["A組", "B組", "C組", "D組", "E組"]

TEAM_SCHEDULE_10 = [
    ("A組", "B組"), ("C組", "D組"),
    ("A組", "C組"), ("B組", "E組"),
    ("A組", "D組"), ("C組", "E組"),
    ("B組", "D組"), ("A組", "E組"),
    ("B組", "C組"), ("D組", "E組")
]

# ==========================================
# 2. 資料存取核心函式
# ==========================================
def load_registrations():
    if os.path.exists(REG_FILE):
        df = pd.read_csv(REG_FILE).fillna("")
        if "編號" not in df.columns:
            df["編號"] = 0
        return df
    return pd.DataFrame(columns=["編號", "選手名稱"])

def save_registrations(df):
    df.to_csv(REG_FILE, index=False, encoding="utf-8-sig")

def load_swiss_matches():
    if os.path.exists(SWISS_MATCH_FILE):
        return pd.read_csv(SWISS_MATCH_FILE).fillna("")
    return None

def save_swiss_matches(df):
    if df is not None:
        df.to_csv(SWISS_MATCH_FILE, index=False, encoding="utf-8-sig")
    elif os.path.exists(SWISS_MATCH_FILE):
        os.remove(SWISS_MATCH_FILE)

def load_finals():
    if os.path.exists(FINALS_FILE):
        return pd.read_csv(FINALS_FILE).fillna("")
    return None

def save_finals(df):
    if df is not None:
        df.to_csv(FINALS_FILE, index=False, encoding="utf-8-sig")
    elif os.path.exists(FINALS_FILE):
        os.remove(FINALS_FILE)

def load_team_data():
    if os.path.exists(TEAM_DATA_FILE): 
        return pd.read_csv(TEAM_DATA_FILE).fillna("")
    columns = ["組別", "隊員別", "選手名稱"]
    default_rows = []
    for team in TEAM_NAMES:
        default_rows.append({"組別": team, "隊員別": "隊員 1", "選手名稱": ""})
        default_rows.append({"組別": team, "隊員別": "隊員 2", "選手名稱": ""})
    return pd.DataFrame(default_rows, columns=columns).fillna("")

def save_team_data(df): 
    df.to_csv(TEAM_DATA_FILE, index=False, encoding="utf-8-sig")

def load_team_matches():
    if os.path.exists(TEAM_MATCH_FILE):
        return pd.read_csv(TEAM_MATCH_FILE).fillna("")
    return None

def save_team_matches(df):
    if df is not None:
        df.to_csv(TEAM_MATCH_FILE, index=False, encoding="utf-8-sig")
    elif os.path.exists(TEAM_MATCH_FILE):
        os.remove(TEAM_MATCH_FILE)

def load_team_finals():
    if os.path.exists(TEAM_FINALS_FILE):
        return pd.read_csv(TEAM_FINALS_FILE).fillna("")
    return None

def save_team_finals(df):
    if df is not None:
        df.to_csv(TEAM_FINALS_FILE, index=False, encoding="utf-8-sig")
    elif os.path.exists(TEAM_FINALS_FILE):
        os.remove(TEAM_FINALS_FILE)

# 載入資料
df_reg = load_registrations()
df_swiss = load_swiss_matches()
df_finals = load_finals()
df_teams = load_team_data()
df_team_matches = load_team_matches()
df_team_finals = load_team_finals()

# ==========================================
# 3. 瑞士輪演算與三階破平機制 (Tie-breakers)
# ==========================================
def calculate_swiss_standings():
    wins = {p_id: 0 for p_id in range(1, 11)}
    losses = {p_id: 0 for p_id in range(1, 11)}
    played_pairs = set()
    defeated_opponents = {p_id: [] for p_id in range(1, 11)}
    h2h = {}

    if df_swiss is not None:
        for _, r in df_swiss.iterrows():
            w = int(r["勝者_編號"])
            p1, p2 = int(r["選手A_編號"]), int(r["選手B_編號"])
            if p1 != 0 and p2 != 0:
                played_pairs.add(tuple(sorted([p1, p2])))
            if w != 0:
                l = p2 if w == p1 else p1
                wins[w] += 1
                losses[l] += 1
                defeated_opponents[w].append(l)
                h2h[(p1, p2)] = w
                h2h[(p2, p1)] = w
    
    # 第三順位：對手強度分 (SOS / Buchholz) = 你擊敗過的對手之總勝場和
    sos = {p_id: sum(wins[opp] for opp in defeated_opponents[p_id]) for p_id in range(1, 11)}

    def sort_key(p_id):
        w_cnt = wins[p_id]      # 第一順位：總勝場數
        s_score = sos[p_id]     # 第三順位：對手強度分 (SOS)
        
        # 第二順位：直接對戰成績 (Head-to-Head)
        h2h_score = sum(
            1 for other in range(1, 11)
            if other != p_id and wins[other] == w_cnt and h2h.get((p_id, other)) == p_id
        )
        return (w_cnt, h2h_score, s_score)

    ranked_ids = sorted(range(1, 11), key=sort_key, reverse=True)
    return wins, losses, sos, h2h, played_pairs, ranked_ids, sort_key

def generate_next_round_pairs(current_round):
    wins, losses, _, _, played_pairs, ranked_ids, _ = calculate_swiss_standings()
    
    groups = {}
    for p_id in ranked_ids:
        w = wins[p_id]
        groups.setdefault(w, []).append(p_id)

    sorted_wins = sorted(groups.keys(), reverse=True)
    new_pairs = []
    pool = []

    for w in sorted_wins:
        pool.extend(groups[w])
        i = 0
        while i < len(pool):
            p1 = pool[i]
            found = False
            for j in range(i + 1, len(pool)):
                p2 = pool[j]
                if tuple(sorted([p1, p2])) not in played_pairs:
                    new_pairs.append((p1, p2))
                    pool.pop(j)
                    pool.pop(i)
                    found = True
                    break
            if not found:
                i += 1

    while len(pool) >= 2:
        p1 = pool.pop(0)
        p2 = pool.pop(0)
        new_pairs.append((p1, p2))

    match_data = []
    for p1, p2 in new_pairs:
        p1_record = f"{wins[p1]}-{losses[p1]}"
        p2_record = f"{wins[p2]}-{losses[p2]}"
        group_label = f"戰績 {p1_record} 區" if p1_record == p2_record else f"跨組區 ({p1_record} vs {p2_record})"
        match_data.append({
            "輪次": current_round,
            "組別標籤": group_label,
            "選手A_編號": p1,
            "選手B_編號": p2,
            "勝者_編號": 0
        })
    return match_data

# ==========================================
# 4. 側邊欄：權限與賽制切換
# ==========================================
if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False

st.sidebar.header("🔑 管理者驗證專區")
is_admin_check = st.sidebar.checkbox("開啟管理員控制權限", value=st.session_state["is_admin"])

if is_admin_check != st.session_state["is_admin"]:
    st.session_state["is_admin"] = is_admin_check

if st.session_state["is_admin"]:
    admin_input = st.sidebar.text_input("輸入管理密碼", type="password", key="pwd_input")
    if admin_input == ADMIN_PASSWORD:
        st.sidebar.success("🔓 管理員已授權")
    else:
        st.sidebar.info("💡 預設密碼為: admin")

is_admin = st.session_state["is_admin"]

st.sidebar.write("---")
st.sidebar.header("🏆 賽制系統切換")
main_mode = st.sidebar.radio(
    "選擇要管理的賽制：",
    ["個人賽 (10人 4輪瑞士輪+4強)", "雙人團體賽 (5隊單循環+決賽)"]
)

# ==========================================
# 5. 模式一：個人賽
# ==========================================
if main_mode == "個人賽 (10人 4輪瑞士輪+4強)":
    st.title("💥 三重盃個人賽（10人 4輪瑞士輪 ➡️ 4強單淘汰賽）")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 選手報名與抽籤", 
        "⚔️ 預賽：瑞士輪控制台", 
        "🗓️ 預賽賽程對戰表", 
        "🏆 決賽：四強單淘汰", 
        "📊 即時積分榜"
    ])
    
    # --- Tab 1: 選手名單管理 ---
    with tab1:
        st.header("📝 選手報名與抽籤初始化")
        
        if is_admin:
            with st.form("reg_form", clear_on_submit=True):
                col_name, col_btn = st.columns([3, 1])
                with col_name:
                    name = st.text_input("輸入選手名稱*")
                with col_btn:
                    st.markdown("<br>", unsafe_allow_html=True)
                    submit_reg = st.form_submit_button("📥 新增選手", use_container_width=True)
                    
                if submit_reg:
                    if not name.strip():
                        st.error("❌ 名稱不能為空！")
                    elif name.strip() in df_reg["選手名稱"].values:
                        st.error(f"❌ 選手【{name}】已在名單中！")
                    elif len(df_reg) >= 10:
                        st.error("❌ 個人賽限定 10 人，已滿額！")
                    else:
                        new_p = {"編號": 0, "選手名稱": name.strip()}
                        df_reg = pd.concat([df_reg, pd.DataFrame([new_p])], ignore_index=True)
                        save_registrations(df_reg)
                        st.success(f"🎉 選手【{name}】報名成功！")
                        st.rerun()

        st.subheader(f"👥 已報名選手名單 (共 {len(df_reg)} / 10 人)")

        if not df_reg.empty:
            if is_admin:
                for idx, row in df_reg.iterrows():
                    col_info, col_del = st.columns([4, 1])
                    with col_info:
                        p_num = f"{int(row['編號'])} 號" if row["編號"] != 0 else "尚未抽籤"
                        st.write(f"• **{row['選手名稱']}** （編號：{p_num}）")
                    with col_del:
                        if st.button("🗑️ 刪除", key=f"del_player_{idx}"):
                            df_reg = df_reg.drop(idx).reset_index(drop=True)
                            save_registrations(df_reg)
                            st.toast(f"已刪除選手：{row['選手名稱']}")
                            st.rerun()
            else:
                st.dataframe(df_reg[["編號", "選手名稱"]], use_container_width=True)
        else:
            st.info("目前尚未有選手報名。")

        if is_admin:
            if len(df_reg) == 10 and (df_reg["編號"] == 0).all():
                st.write("---")
                if st.button("🎲 滿 10 人！盲抽生成 1~10 號編號並生成第 1 輪對戰", type="primary", use_container_width=True):
                    nums = list(range(1, 11))
                    random.shuffle(nums)
                    df_reg["編號"] = nums
                    save_registrations(df_reg)
                    
                    p_ids = nums.copy()
                    random.shuffle(p_ids)
                    round1_matches = []
                    for i in range(0, 10, 2):
                        round1_matches.append({
                            "輪次": 1,
                            "組別標籤": "戰績 0-0 區",
                            "選手A_編號": p_ids[i],
                            "選手B_編號": p_ids[i+1],
                            "勝者_編號": 0
                        })
                    save_swiss_matches(pd.DataFrame(round1_matches))
                    st.success("🎉 抽籤成功！第 1 輪瑞士輪對戰已生成！")
                    st.rerun()

            st.write("---")
            col_reset1, col_reset2 = st.columns(2)
            with col_reset1:
                if st.button("🗑️ 一鍵清空所有報名名單", use_container_width=True):
                    df_reg = pd.DataFrame(columns=["編號", "選手名稱"])
                    save_registrations(df_reg)
                    st.toast("已清空名單")
                    st.rerun()
            with col_reset2:
                if st.button("🚨 初始化/重置所有對戰與抽籤", type="secondary", use_container_width=True):
                    save_swiss_matches(None)
                    save_finals(None)
                    df_reg["編號"] = 0
                    save_registrations(df_reg)
                    st.warning("已重置抽籤與比賽數據。")
                    st.rerun()

    player_map = dict(zip(df_reg["編號"], df_reg["選手名稱"])) if not df_reg.empty else {}

    # --- Tab 2: 預賽控制台 ---
    with tab2:
        st.header("⚔️ 預賽：4輪瑞士輪控制台")
        if df_swiss is None or (df_reg["編號"] == 0).all():
            st.warning("⏳ 請先在「選手報名與抽籤」分頁集滿 10 人並完成盲抽！")
        else:
            current_max_round = int(df_swiss["輪次"].max())
            r_matches = df_swiss[df_swiss["輪次"] == current_max_round]
            completed_r_count = sum(1 for w in r_matches["勝者_編號"] if w != 0)
            
            st.info(f"### 📍 當前進行：第 {current_max_round} / 4 輪 (該輪進度：{completed_r_count} / 5 場)")

            for m_idx, row in r_matches.iterrows():
                p1_id, p2_id, w_id = int(row["選手A_編號"]), int(row["選手B_編號"]), int(row["勝者_編號"])
                p1_str = f"{p1_id}號 {player_map.get(p1_id, '')}"
                p2_str = f"{p2_id}號 {player_map.get(p2_id, '')}"

                st.write(f"#### 🥊 【{row['組別標籤']}】 **🔴 {p1_str}** 🆚 **🔵 {p2_str}**")
                
                if is_admin:
                    c1, c2, c3 = st.columns([2, 2, 3])
                    with c1:
                        if st.button(f"🏆 {p1_str} 獲勝", key=f"r{current_max_round}_{m_idx}_p1", use_container_width=True, type="primary" if w_id == p1_id else "secondary"):
                            df_swiss.at[m_idx, "勝者_編號"] = p1_id
                            save_swiss_matches(df_swiss)
                            st.rerun()
                    with c2:
                        if st.button(f"🏆 {p2_str} 獲勝", key=f"r{current_max_round}_{m_idx}_p2", use_container_width=True, type="primary" if w_id == p2_id else "secondary"):
                            df_swiss.at[m_idx, "勝者_編號"] = p2_id
                            save_swiss_matches(df_swiss)
                            st.rerun()
                    with c3:
                        st.caption(f"勝者：`{player_map.get(w_id, '未登記')}`")
                else:
                    st.write(f"結果：`{player_map.get(w_id, '比賽中')}`")
                st.write("---")

            if is_admin and completed_r_count == 5:
                if current_max_round < 4:
                    if st.button(f"🚀 生成第 {current_max_round + 1} 輪對戰", type="primary", use_container_width=True):
                        next_m = generate_next_round_pairs(current_max_round + 1)
                        df_swiss = pd.concat([df_swiss, pd.DataFrame(next_m)], ignore_index=True)
                        save_swiss_matches(df_swiss)
                        st.rerun()

    # --- Tab 3: 對戰表總覽 ---
    with tab3:
        st.header("🗓️ 預賽 4 輪對戰表")
        if df_swiss is not None:
            for r in range(1, int(df_swiss["輪次"].max()) + 1):
                st.subheader(f"🌀 第 {r} 輪")
                r_df = df_swiss[df_swiss["輪次"] == r]
                disp = []
                for _, row in r_df.iterrows():
                    p1_id, p2_id, w_id = int(row["選手A_編號"]), int(row["選手B_編號"]), int(row["勝者_編號"])
                    disp.append({
                        "組別": row["組別標籤"],
                        "選手 A": f"{p1_id}號 {player_map.get(p1_id, '')}",
                        "選手 B": f"{p2_id}號 {player_map.get(p2_id, '')}",
                        "獲勝者": player_map.get(w_id, "⏳ 待定") if w_id != 0 else "⏳ 待定"
                    })
                st.dataframe(pd.DataFrame(disp), use_container_width=True, hide_index=True)

    # --- Tab 4: 決賽 ---
    with tab4:
        st.header("🏆 四強單淘汰決賽")
        total_p = sum(1 for w in df_swiss["勝者_編號"] if w != 0) if df_swiss is not None else 0
        if df_swiss is None or total_p < 20:
            st.warning(f"⏳ 預賽尚未完成（已完成 {total_p}/20 場）")
        else:
            wins, losses, sos, h2h, _, ranked_ids, sort_key = calculate_swiss_standings()
            
            # 檢查第 4 名是否有完全平手的情況
            rank4_id = ranked_ids[3]
            tied_candidates = [p for p in ranked_ids if sort_key(p) == sort_key(rank4_id)]
            
            if len(tied_candidates) > 1 and "selected_4th" not in st.session_state:
                st.error(f"⚠️ 偵測到第 4 名存在三階指標完全平手爭議！同分選手：{', '.join([f'{p}號 {player_map[p]}' for p in tied_candidates])}")
                st.info("請現場進行加賽或抽籤，並由管理員指定最終晉級第 4 名的選手：")
                
                if is_admin:
                    chosen_4th = st.selectbox(
                        "選擇晉級四強的第 4 名選手：", 
                        tied_candidates, 
                        format_func=lambda x: f"{x}號 {player_map[x]}"
                    )
                    if st.button("確定第 4 名晉級者", type="primary"):
                        st.session_state["selected_4th"] = chosen_4th
                        st.rerun()
                else:
                    st.warning("等待管理員裁決平手同分者...")
            
            else:
                final_4 = ranked_ids[:3]
                if "selected_4th" in st.session_state:
                    fourth_p = st.session_state["selected_4th"]
                    if fourth_p in final_4:
                        final_4.remove(fourth_p)
                    final_4.append(fourth_p)
                else:
                    final_4.append(ranked_ids[3])

                r1, r2, r3, r4 = final_4[0], final_4[1], final_4[2], final_4[3]

                if df_finals is None:
                    st.success(f"前 4 強名單：1️⃣{player_map[r1]}、2️⃣{player_map[r2]}、3️⃣{player_map[r3]}、4️⃣{player_map[r4]}")
                    if is_admin and st.button("🔥 生成 4 強決賽對戰表", type="primary"):
                        finals_data = [
                            {"階段": "準決賽A", "選手1": player_map[r1], "選手2": player_map[r4], "勝者": "尚未決定", "敗者": "尚未決定"},
                            {"階段": "準決賽B", "選手1": player_map[r2], "選手2": player_map[r3], "勝者": "尚未決定", "敗者": "尚未決定"},
                            {"階段": "季軍賽", "選手1": "準決賽A敗者", "選手2": "準決賽B敗者", "勝者": "尚未決定", "敗者": "尚未決定"},
                            {"階段": "冠軍賽", "選手1": "準決賽A勝者", "選手2": "準決賽B勝者", "勝者": "尚未決定", "敗者": "尚未決定"}
                        ]
                        df_finals = pd.DataFrame(finals_data)
                        save_finals(df_finals)
                        st.rerun()
                else:
                    st.dataframe(df_finals, use_container_width=True)

    # --- Tab 5: 積分榜 ---
    with tab5:
        st.header("📊 即時積分榜")
        if df_swiss is not None:
            wins, losses, sos, h2h, _, ranked_ids, _ = calculate_swiss_standings()
            table_data = []
            for rank, p_id in enumerate(ranked_ids, 1):
                table_data.append({
                    "排名": f"第 {rank} 名",
                    "編號": f"{p_id} 號",
                    "選手名稱": player_map.get(p_id, ""),
                    "勝場": wins[p_id],
                    "敗場": losses[p_id],
                    "SOS 強度": sos[p_id]
                })
            st.table(table_data)

# ==========================================
# 6. 模式二：雙人團體賽
# ==========================================
elif main_mode == "雙人團體賽 (5隊單循環+決賽)":
    st.title("🤝 三重盃雙人團體賽（5隊單循環 ➡️ 冠亞軍決賽）")
    
    ttab1, ttab2, ttab3, ttab4, ttab5 = st.tabs([
        "📝 5組選手名單管理", 
        "⚔️ 預賽：單循環控制台", 
        "🗓️ 預賽賽程總覽", 
        "🏆 冠亞軍總決賽", 
        "📊 團體積分榜"
    ])
    
    with ttab1:
        st.header("📝 團體名單管理")
        ui_inputs = {}
        cols = st.columns(2)
        for idx, team in enumerate(TEAM_NAMES):
            with cols[idx % 2]:
                st.subheader(f"🛡️ {team} 名單")
                row_p1 = df_teams[(df_teams["組別"] == team) & (df_teams["隊員別"] == "隊員 1")].iloc[0]
                row_p2 = df_teams[(df_teams["組別"] == team) & (df_teams["隊員別"] == "隊員 2")].iloc[0]
                
                p1 = st.text_input(f"隊員 1 姓名", value=str(row_p1["選手名稱"]), key=f"{team}_p1", disabled=not is_admin)
                p2 = st.text_input(f"隊員 2 姓名", value=str(row_p2["選手名稱"]), key=f"{team}_p2", disabled=not is_admin)
                ui_inputs[team] = {"p1": p1, "p2": p2}
                st.write("---")

        if is_admin and st.button("💾 儲存團體名單並初始化預賽 10 場賽程", type="primary", use_container_width=True):
            new_rows = []
            for team in TEAM_NAMES:
                new_rows.append({"組別": team, "隊員別": "隊員 1", "選手名稱": ui_inputs[team]["p1"].strip()})
                new_rows.append({"組別": team, "隊員別": "隊員 2", "選手名稱": ui_inputs[team]["p2"].strip()})
            df_teams = pd.DataFrame(new_rows)
            save_team_data(df_teams)
            
            if df_team_matches is None:
                t_matches = []
                for idx, (t1, t2) in enumerate(TEAM_SCHEDULE_10, 1):
                    t_matches.append({"場次": idx, "隊伍A": t1, "隊伍B": t2, "勝隊": "尚未決定"})
                save_team_matches(pd.DataFrame(t_matches))
            st.success("團體名單與 10 場預賽賽程儲存完成！")
            st.rerun()

        st.dataframe(df_teams, use_container_width=True)

    with ttab2:
        st.header("⚔️ 團體預賽控制台")
        if df_team_matches is not None:
            st.dataframe(df_team_matches, use_container_width=True)
            
    with ttab3:
        st.header("🗓️ 團體賽 10 場對戰總覽")
        if df_team_matches is not None:
            st.table(df_team_matches)

    with ttab4:
        st.header("🏆 團體冠亞軍總決賽")
        st.info("預賽 10 場完成後開放。")

    with ttab5:
        st.header("📊 團體積分榜")
        st.info("戰績統計將於預賽開始後顯示。")
