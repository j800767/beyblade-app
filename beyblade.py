import streamlit as st
import pandas as pd
import os
import random
from functools import cmp_to_key

# ==========================================
# 1. 基礎設定與檔案路徑
# ==========================================
st.set_page_config(page_title="第三屆 三重盃 戰鬥陀螺大賽", page_icon="💥", layout="wide")

REG_FILE = "players_registration.csv"         # 個人賽選手名單 (11人)
SWISS_MATCH_FILE = "swiss_matches.csv"        # 個人賽瑞士輪賽程檔案
FINALS_FILE = "finals_matches.csv"             # 個人賽四強單淘汰檔案

TEAM_DATA_FILE = "team_players_registration.csv" # 團體賽名單檔案 (5組)
TEAM_MATCH_FILE = "team_matches.csv"           # 團體賽單循環賽程檔案
TEAM_FINALS_FILE = "team_finals_matches.csv"   # 團體賽冠亞軍決賽檔案

ADMIN_PASSWORD = "admin"  # 管理員預設密碼
TEAM_NAMES = ["A組", "B組", "C組", "D組", "E組"]

# 5 組單循環固定對戰組合 (共 10 場)
TEAM_SCHEDULE_10 = [
    ("A組", "B組"), ("C組", "D組"),
    ("A組", "C組"), ("B組", "E組"),
    ("A組", "D組"), ("C組", "E組"),
    ("B組", "D組"), ("A組", "E組"),
    ("B組", "C組"), ("D組", "E組")
]

# ==========================================
# 2. 個人賽資料存取與計算 (11人瑞士輪支援輪空)
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
        df = pd.read_csv(FINALS_FILE).fillna("")
        for col in ["階段", "選手1", "選手2", "勝者", "敗者"]:
            if col in df.columns:
                df[col] = df[col].astype(str)
        return df
    return None

def save_finals(df):
    if df is not None:
        df.to_csv(FINALS_FILE, index=False, encoding="utf-8-sig")
    elif os.path.exists(FINALS_FILE):
        os.remove(FINALS_FILE)

df_reg = load_registrations()
df_swiss = load_swiss_matches()
df_finals = load_finals()

def calculate_swiss_standings():
    wins = {p_id: 0 for p_id in range(1, 12)}
    losses = {p_id: 0 for p_id in range(1, 12)}
    played_pairs = set()
    defeated_opponents = {p_id: [] for p_id in range(1, 12)}
    h2h = {}
    bye_players = set()

    if df_swiss is not None:
        for _, r in df_swiss.iterrows():
            w = int(r["勝者_編號"])
            p1, p2 = int(r["選手A_編號"]), int(r["選手B_編號"])
            
            # 處理輪空 (p2 == 0)
            if p2 == 0:
                if p1 != 0:
                    wins[p1] += 1
                    bye_players.add(p1)
                continue

            if p1 != 0 and p2 != 0:
                played_pairs.add(tuple(sorted([p1, p2])))
            
            if w != 0:
                l = p2 if w == p1 else p1
                wins[w] += 1
                losses[l] += 1
                defeated_opponents[w].append(l)
                h2h[(p1, p2)] = w
                h2h[(p2, p1)] = w
    
    sos = {p_id: sum(wins[opp] for opp in defeated_opponents[p_id]) for p_id in range(1, 12)}

    def compare_players(p1, p2):
        if wins[p1] != wins[p2]:
            return 1 if wins[p1] > wins[p2] else -1
        winner = h2h.get((p1, p2))
        if winner == p1:
            return 1
        elif winner == p2:
            return -1
        if sos[p1] != sos[p2]:
            return 1 if sos[p1] > sos[p2] else -1
        return 0

    ranked_ids = sorted(range(1, 12), key=cmp_to_key(compare_players), reverse=True)
    return wins, losses, sos, h2h, played_pairs, ranked_ids, bye_players

def generate_next_round_pairs(current_round):
    """【修正防重複對戰演算法】採用迴溯法 (Backtracking) 進行全域防重複對戰配對"""
    wins, losses, _, _, played_pairs, ranked_ids, bye_players = calculate_swiss_standings()
    
    # 選擇本次輪空的選手 (優先挑選戰績最低且未輪空過的選手)
    bye_candidate = None
    for p_id in reversed(ranked_ids):
        if p_id not in bye_players:
            bye_candidate = p_id
            break

    active_players = [p for p in ranked_ids if p != bye_candidate]

    # 使用 Backtracking (迴溯法) 尋找不重複對戰的最佳配對
    def backtrack_pairings(candidates):
        if not candidates:
            return []
        
        p1 = candidates[0]
        for i in range(1, len(candidates)):
            p2 = candidates[i]
            pair = tuple(sorted([p1, p2]))
            if pair not in played_pairs:
                remaining = candidates[1:i] + candidates[i+1:]
                sub_res = backtrack_pairings(remaining)
                if sub_res is not None:
                    return [(p1, p2)] + sub_res
        return None

    new_pairs = backtrack_pairings(active_players)

    # 備用機制：若極端狀況下無法完全避開重複，則退回預設強行配對
    if new_pairs is None:
        new_pairs = []
        temp_pool = list(active_players)
        while len(temp_pool) >= 2:
            p1 = temp_pool.pop(0)
            p2 = temp_pool.pop(0)
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
    
    # 加入輪空場次
    if bye_candidate is not None:
        match_data.append({
            "輪次": current_round,
            "組別標籤": "輪空區 (BYE)",
            "選手A_編號": bye_candidate,
            "選手B_編號": 0,
            "勝者_編號": bye_candidate
        })

    return match_data

# ==========================================
# 3. 團體賽資料存取與計算 (修正三方/多方平手問題)
# ==========================================
def load_team_players():
    if os.path.exists(TEAM_DATA_FILE):
        return pd.read_csv(TEAM_DATA_FILE).fillna("")
    return pd.DataFrame(columns=["組別", "選手1", "選手2"])

def save_team_players(df):
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

df_team_p = load_team_players()
df_team_m = load_team_matches()
df_team_f = load_team_finals()

def calculate_team_standings():
    t_wins = {t: 0 for t in TEAM_NAMES}
    t_losses = {t: 0 for t in TEAM_NAMES}
    h2h = {}

    if df_team_m is not None:
        for _, r in df_team_m.iterrows():
            t1, t2 = r["隊伍A"], r["隊伍B"]
            w = r["勝隊"]
            if w in TEAM_NAMES:
                t_wins[w] += 1
                l = t2 if w == t1 else t1
                t_losses[l] += 1
                h2h[(t1, t2)] = w
                h2h[(t2, t1)] = w

    ranked_teams = sorted(TEAM_NAMES, key=lambda t: t_wins[t], reverse=True)
    return t_wins, t_losses, h2h, ranked_teams

# ==========================================
# 4. 側邊欄與權限控制
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

# ==========================================
# 5. 通用 PK 加賽渲染模組 (個人賽)
# ==========================================
def render_pk_section(rank_target, candidates, player_map):
    st.error(f"⚠️ 觸發 PK 加賽條款！第 {rank_target} 名門檻出現完全同分：{', '.join([f'{p}號 {player_map[p]}' for p in candidates])}")
    st.info("📌 **PK 賽規則**：1 顆陀螺不換零件，進行【一分定勝負】單淘汰賽。")

    num_c = len(candidates)
    if num_c == 2:
        if is_admin:
            chosen = st.selectbox(f"選擇爭奪第 {rank_target} 名 PK 勝出的選手：", candidates, format_func=lambda x: f"{x}號 {player_map[x]}", key=f"pk_sel_2_{rank_target}")
            if st.button(f"確定第 {rank_target} 名 PK 晉級者", key=f"btn_pk_2_{rank_target}", type="primary"):
                st.session_state[f"selected_rank_{rank_target}"] = chosen
                st.rerun()
        else:
            st.warning("等待管理員進行 PK 加賽裁決...")

    elif num_c == 3:
        st.markdown("1. 盲抽 1 人輪空。<br>2. 另外兩人打 1 場加賽，勝者與輪空者打 PK 決賽！", unsafe_allow_html=True)
        if is_admin:
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                p_win1 = st.selectbox("第一輪 PK 勝者：", candidates, format_func=lambda x: f"{x}號 {player_map[x]}", key=f"pk_sel_3_r1_{rank_target}")
            with col_p2:
                chosen = st.selectbox(f"【PK 決賽】最終勝者：", candidates, format_func=lambda x: f"{x}號 {player_map[x]}", key=f"pk_sel_3_fin_{rank_target}")
            if st.button(f"確定第 {rank_target} 名 PK 晉級者", key=f"btn_pk_3_{rank_target}", type="primary"):
                st.session_state[f"selected_rank_{rank_target}"] = chosen
                st.rerun()
        else:
            st.warning("等待管理員進行 PK 加賽裁決...")

# ==========================================
# 6. 主頁面：個人賽與團體賽切換
# ==========================================
main_tab1, main_tab2 = st.tabs(["👤 個人賽 (11人 5輪瑞士輪)", "👥 團體賽 (5組 單循環)"])

player_map = dict(zip(df_reg["編號"], df_reg["選手名稱"])) if not df_reg.empty else {}
player_map[0] = "無 (輪空)"

# ==========================================
# 👥 團體賽主區塊
# ==========================================
with main_tab2:
    st.title("👥 9/12 第三屆 三重盃戰鬥陀螺大賽 - 團體賽")
    st.caption("【團體賽】5 組單循環賽 | 依勝場與對戰勝負排名 | 前 2 名晉級冠亞軍決賽 | 冠軍獎品: CX-18 腕龍鞭打*2")

    t_tab1, t_tab2, t_tab3, t_tab4 = st.tabs([
        "📝 隊伍與選手登記", 
        "⚔️ 循環賽對戰控制台", 
        "🏆 冠亞軍決賽", 
        "📊 團體賽積分榜"
    ])

    with t_tab1:
        st.header("📝 團體賽隊伍與選手登記")
        if df_team_p.empty:
            df_team_p = pd.DataFrame({"組別": TEAM_NAMES, "選手1": [""]*5, "選手2": [""]*5})

        if is_admin:
            with st.form("team_p_form"):
                st.info("請為 A~E 組各登記 2 位選手名稱：")
                updated_rows = []
                for t in TEAM_NAMES:
                    curr_p1 = df_team_p.loc[df_team_p["組別"] == t, "選手1"].values[0] if t in df_team_p["組別"].values else ""
                    curr_p2 = df_team_p.loc[df_team_p["組別"] == t, "選手2"].values[0] if t in df_team_p["組別"].values else ""
                    c1, c2, c3 = st.columns([1, 2, 2])
                    with c1:
                        st.markdown(f"### **{t}**")
                    with c2:
                        p1_val = st.text_input(f"{t} - 選手 1", value=curr_p1, key=f"tp1_{t}")
                    with c3:
                        p2_val = st.text_input(f"{t} - 選手 2", value=curr_p2, key=f"tp2_{t}")
                    updated_rows.append({"組別": t, "選手1": p1_val.strip(), "選手2": p2_val.strip()})
                
                if st.form_submit_button("💾 儲存團體賽名單", type="primary"):
                    df_team_p = pd.DataFrame(updated_rows)
                    save_team_players(df_team_p)
                    st.success("🎉 團體賽隊伍名單儲存成功！")
                    st.rerun()

            st.write("---")
            if st.button("🚀 初始化團體賽 10 場單循環對戰表", type="secondary", use_container_width=True):
                t_matches = []
                for idx, (t1, t2) in enumerate(TEAM_SCHEDULE_10, 1):
                    t_matches.append({
                        "場次": idx,
                        "隊伍A": t1,
                        "隊伍B": t2,
                        "勝隊": "未完賽"
                    })
                save_team_matches(pd.DataFrame(t_matches))
                save_team_finals(None)
                st.success("🎉 團體賽 10 場單循環賽程生成完畢！")
                st.rerun()
        else:
            st.dataframe(df_team_p, use_container_width=True, hide_index=True)

    with t_tab2:
        st.header("⚔️ 團體賽單循環對戰控制台")
        if df_team_m is None or df_team_m.empty:
            st.warning("⏳ 請先在「隊伍與選手登記」分頁點擊【初始化團體賽 10 場單循環對戰表】！")
        else:
            for m_idx, r in df_team_m.iterrows():
                m_num = int(r["場次"])
                t1, t2 = r["隊伍A"], r["隊伍B"]
                w_team = r["勝隊"]

                p1_str = f"({df_team_p.loc[df_team_p['組別']==t1, '選手1'].values[0]} & {df_team_p.loc[df_team_p['組別']==t1, '選手2'].values[0]})" if not df_team_p.empty else ""
                p2_str = f"({df_team_p.loc[df_team_p['組別']==t2, '選手1'].values[0]} & {df_team_p.loc[df_team_p['組別']==t2, '選手2'].values[0]})" if not df_team_p.empty else ""

                st.write(f"#### 🥊 場次 {m_num}：**🔴 {t1}** {p1_str} 🆚 **🔵 {t2}** {p2_str}")
                
                if is_admin:
                    c1, c2, c3 = st.columns([3, 3, 2])
                    with c1:
                        if st.button(f"🏆 {t1} 獲勝", key=f"tm_btn_a_{m_idx}", use_container_width=True, type="primary" if w_team == t1 else "secondary"):
                            df_team_m.at[m_idx, "勝隊"] = t1
                            save_team_matches(df_team_m)
                            st.toast(f"場次 {m_num}：{t1} 勝出！")
                            st.rerun()
                    with c2:
                        if st.button(f"🏆 {t2} 獲勝", key=f"tm_btn_b_{m_idx}", use_container_width=True, type="primary" if w_team == t2 else "secondary"):
                            df_team_m.at[m_idx, "勝隊"] = t2
                            save_team_matches(df_team_m)
                            st.toast(f"場次 {m_num}：{t2} 勝出！")
                            st.rerun()
                    with c3:
                        st.caption(f"目前勝隊：`{w_team}`")
                else:
                    st.write(f"比賽結果：`{w_team}`")
                st.write("---")

    with t_tab3:
        st.header("🏆 團體賽 冠亞軍決賽")
        completed_tm = sum(1 for w in df_team_m["勝隊"] if w in TEAM_NAMES) if df_team_m is not None else 0
        
        if df_team_m is None or completed_tm < 10:
            st.warning(f"⏳ 團體賽預賽尚未結束（已完成 {completed_tm}/10 場）")
        else:
            t_wins, t_losses, h2h, ranked_teams = calculate_team_standings()
            
            top3 = ranked_teams[:3]
            is_3way_tie = (t_wins[top3[0]] == t_wins[top3[1]] == t_wins[top3[2]])
            
            if is_3way_tie and ("selected_team_rank_1" not in st.session_state or "selected_team_rank_2" not in st.session_state):
                st.error(f"⚠️ 觸發三方互咬加賽！前 3 名出現完全同分：【{top3[0]}】、【{top3[1]}】與【{top3[2]}】（勝場同為 {t_wins[top3[0]]} 勝，且對戰互有勝負）！")
                st.info("📌 **三方 PK 賽建議**：1 隊盲抽輪空，另外 2 隊先打 1 場 PK，勝者與輪空隊爭奪第 1、2 名晉級冠亞軍決賽。")
                
                if is_admin:
                    col1, col2 = st.columns(2)
                    with col1:
                        chosen_t1 = st.selectbox("請指定 PK 最終【第 1 名】隊伍：", top3, key="pk_team_sel_1")
                    with col2:
                        remaining_teams = [t for t in top3 if t != chosen_t1]
                        chosen_t2 = st.selectbox("請指定 PK 最終【第 2 名】隊伍：", remaining_teams, key="pk_team_sel_2")
                        
                    if st.button("確定冠亞軍決賽晉級隊伍 (第1、2名)", type="primary"):
                        st.session_state["selected_team_rank_1"] = chosen_t1
                        st.session_state["selected_team_rank_2"] = chosen_t2
                        st.rerun()
                else:
                    st.warning("等待管理員進行三方 PK 加賽裁決...")

            elif t_wins[ranked_teams[1]] == t_wins[ranked_teams[2]] and "selected_team_rank_2" not in st.session_state:
                st.error(f"⚠️ 團體賽第 2 名出現平手狀況：【{ranked_teams[1]}】 與 【{ranked_teams[2]}】（勝場同為 {t_wins[ranked_teams[1]]} 勝）！")
                if is_admin:
                    chosen_t2 = st.selectbox("請由管理員指定/PK裁決晉級冠亞軍賽的隊伍：", [ranked_teams[1], ranked_teams[2]], key="pk_team_sel_2_only")
                    if st.button("確定團體賽第 2 名晉級者", type="primary"):
                        st.session_state["selected_team_rank_2"] = chosen_t2
                        st.rerun()
                else:
                    st.warning("等待管理員進行裁決...")

            else:
                final_t1 = st.session_state.get("selected_team_rank_1", ranked_teams[0])
                final_t2 = st.session_state.get("selected_team_rank_2", ranked_teams[1])

                if df_team_f is None:
                    df_team_f = pd.DataFrame([{"隊伍1": final_t1, "隊伍2": final_t2, "冠軍": ""}])
                    save_team_finals(df_team_f)

                tf_r = df_team_f.iloc[0]
                t1_f, t2_f = tf_r["隊伍1"], tf_r["隊伍2"]
                champ = tf_r["冠軍"]

                st.subheader(f"👑 冠亞軍決賽：**🔴 {t1_f}** 🆚 **🔵 {t2_f}**")
                
                if is_admin:
                    c1, c2 = st.columns([3, 3])
                    with c1:
                        if st.button(f"🎉 判定【{t1_f}】為總冠軍", key="tf_btn_1", type="primary" if champ == t1_f else "secondary", use_container_width=True):
                            df_team_f.at[0, "冠軍"] = t1_f
                            save_team_finals(df_team_f)
                            st.rerun()
                    with c2:
                        if st.button(f"🎉 判定【{t2_f}】為總冠軍", key="tf_btn_2", type="primary" if champ == t2_f else "secondary", use_container_width=True):
                            df_team_f.at[0, "冠軍"] = t2_f
                            save_team_finals(df_team_f)
                            st.rerun()
                else:
                    st.write(f"總冠軍：`{champ if champ else '比賽中'}`")

                if champ and champ != "未決定":
                    st.balloons()
                    runner_t = t2_f if champ == t1_f else t1_f
                    st.success(f"""
                    ### 🎉 團體賽最終結果：
                    * 🥇 **總冠軍**：{champ}
                    * 🥈 **亞軍**：{runner_t}
                    """)

    with t_tab4:
        st.header("📊 團體賽即時積分榜")
        if df_team_m is not None:
            t_wins, t_losses, _, ranked_teams = calculate_team_standings()
            t_table = []
            for rank, t in enumerate(ranked_teams, 1):
                p1 = df_team_p.loc[df_team_p["組別"]==t, "選手1"].values[0] if not df_team_p.empty else ""
                p2 = df_team_p.loc[df_team_p["組別"]==t, "選手2"].values[0] if not df_team_p.empty else ""
                t_table.append({
                    "排名": f"第 {rank} 名",
                    "隊伍名稱": t,
                    "選手名單": f"{p1} & {p2}",
                    "勝場": t_wins[t],
                    "敗場": t_losses[t]
                })
            st.table(t_table)

# ==========================================
# 👤 個人賽主區塊 (11人 5輪瑞士輪 + 指定第1輪輪空)
# ==========================================
with main_tab1:
    st.title("💥 9/12 第三屆 三重盃戰鬥陀螺大賽 - 個人賽")
    st.caption("【個人賽】預賽採 4 分制 | 限定 11 人 5 輪瑞士輪 (含每人最多1次輪空) | 冠軍獎品：UX-15 鮫鯊狂鱗")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 選手報名與抽籤", 
        "⚔️ 預賽：瑞士輪控制台", 
        "🗓️ 預賽賽程對戰表", 
        "🏆 決賽：四強單淘汰", 
        "📊 即時積分榜"
    ])

    # --- Tab 1: 報名與指定輪空抽籤 ---
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
                    elif len(df_reg) >= 11:
                        st.error("❌ 個人賽限定 11 人，已滿額！")
                    else:
                        new_p = {"編號": 0, "選手名稱": name.strip()}
                        df_reg = pd.concat([df_reg, pd.DataFrame([new_p])], ignore_index=True)
                        save_registrations(df_reg)
                        st.success(f"🎉 選手【{name}】報名成功！")
                        st.rerun()

        st.subheader(f"👥 已報名選手名單 (共 {len(df_reg)} / 11 人)")
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
            if len(df_reg) == 11 and (df_reg["編號"] == 0).all():
                st.write("---")
                st.subheader("🎲 抽籤與第 1 輪對戰生成")
                
                bye_candidate_name = st.selectbox(
                    "📌 請選擇第 1 輪指定【輪空 (BYE)】的選手（可指定小孩優先輪空）：",
                    options=df_reg["選手名稱"].tolist(),
                    key="manual_bye_select"
                )
                
                if st.button("🎲 確定指定並產生 1~11 號編號與第 1 輪對戰", type="primary", use_container_width=True):
                    bye_row = df_reg[df_reg["選手名稱"] == bye_candidate_name]
                    other_rows = df_reg[df_reg["選手名稱"] != bye_candidate_name]
                    
                    shuffled_others = other_rows.sample(frac=1).reset_index(drop=True)
                    reordered_df = pd.concat([shuffled_others, bye_row], ignore_index=True)
                    reordered_df["編號"] = list(range(1, 12))
                    df_reg = reordered_df
                    save_registrations(df_reg)
                    
                    p_ids = list(range(1, 11))
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
                    
                    # 11 號 (指定輪空者) 直接自動記 1 勝
                    round1_matches.append({
                        "輪次": 1,
                        "組別標籤": "輪空區 (BYE)",
                        "選手A_編號": 11,
                        "選手B_編號": 0,
                        "勝者_編號": 11
                    })
                    
                    save_swiss_matches(pd.DataFrame(round1_matches))
                    st.success(f"🎉 抽籤完成！已指定【{bye_candidate_name}】於第 1 輪輪空並自動獲得 1 勝！")
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

    # --- Tab 2: 控制台 ---
    with tab2:
        st.header("⚔️ 預賽：5輪瑞士輪控制台 (常規賽採 4 分制)")
        if df_swiss is None or (df_reg["編號"] == 0).all():
            st.warning("⏳ 請先在「選手報名與抽籤」分頁集滿 11 人並完成盲抽！")
        else:
            current_max_round = int(df_swiss["輪次"].max())
            r_matches = df_swiss[df_swiss["輪次"] == current_max_round]
            completed_r_count = sum(1 for w in r_matches["勝者_編號"] if w != 0)
            
            col_header, col_undo = st.columns([3, 1.2])
            with col_header:
                st.info(f"### 📍 當前進行：第 {current_max_round} / 5 輪 (該輪進度：{completed_r_count} / 6 場)")
            with col_undo:
                if is_admin and current_max_round > 1:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button(f"🔙 回復至第 {current_max_round - 1} 輪", type="secondary", use_container_width=True):
                        df_swiss = df_swiss[df_swiss["輪次"] < current_max_round]
                        save_swiss_matches(df_swiss)
                        save_finals(None)
                        st.toast(f"已成功退回第 {current_max_round - 1} 輪！")
                        st.rerun()

            for m_idx, row in r_matches.iterrows():
                p1_id, p2_id, w_id = int(row["選手A_編號"]), int(row["選手B_編號"]), int(row["勝者_編號"])
                p1_str = f"{p1_id}號 {player_map.get(p1_id, '')}"
                p2_str = f"{p2_id}號 {player_map.get(p2_id, '')}" if p2_id != 0 else "輪空 (BYE)"

                if p2_id == 0:
                    st.write(f"#### ☕ 【{row['組別標籤']}】 **🔴 {p1_str}** 輪空（自動獲得 1 勝）")
                else:
                    st.write(f"#### 🥊 【{row['組別標籤']}】 **🔴 {p1_str}** 🆚 **🔵 {p2_str}**")
                
                if is_admin:
                    if p2_id != 0:
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
                        st.success("✅ 已自動記為 1 勝")
                else:
                    if p2_id != 0:
                        st.write(f"結果：`{player_map.get(w_id, '比賽中')}`")
                    else:
                        st.write("結果：`輪空勝`")
                st.write("---")

            if is_admin and completed_r_count == 6:
                if current_max_round < 5:
                    if st.button(f"🚀 生成第 {current_max_round + 1} 輪對戰", type="primary", use_container_width=True):
                        next_m = generate_next_round_pairs(current_max_round + 1)
                        df_swiss = pd.concat([df_swiss, pd.DataFrame(next_m)], ignore_index=True)
                        save_swiss_matches(df_swiss)
                        st.rerun()

    # --- Tab 3: 對戰表 ---
    with tab3:
        st.header("🗓️ 預賽 5 輪對戰表")
        if df_swiss is not None:
            for r in range(1, int(df_swiss["輪次"].max()) + 1):
                st.subheader(f"🌀 第 {r} 輪")
                r_df = df_swiss[df_swiss["輪次"] == r]
                disp = []
                for _, row in r_df.iterrows():
                    p1_id, p2_id, w_id = int(row["選手A_編號"]), int(row["選手B_編號"]), int(row["勝者_編號"])
                    p2_name = f"{p2_id}號 {player_map.get(p2_id, '')}" if p2_id != 0 else "無 (輪空)"
                    disp.append({
                        "組別": row["組別標籤"],
                        "選手 A": f"{p1_id}號 {player_map.get(p1_id, '')}",
                        "選手 B": p2_name,
                        "獲勝者": player_map.get(w_id, "⏳ 待定") if w_id != 0 else "⏳ 待定"
                    })
                st.dataframe(pd.DataFrame(disp), use_container_width=True, hide_index=True)

    # --- Tab 4: 決賽 (四強單淘汰) ---
    with tab4:
        st.header("🏆 個人賽 四強單淘汰決賽")
        total_swiss_matches = len(df_swiss) if df_swiss is not None else 0
        completed_swiss_matches = sum(1 for w in df_swiss["勝者_編號"] if w != 0) if df_swiss is not None else 0

        if df_swiss is None or total_swiss_matches < 30 or completed_swiss_matches < 30:
            st.warning(f"⏳ 瑞士輪預賽尚未結束（進度：{completed_swiss_matches} / 30 場）")
        else:
            wins, losses, sos, h2h, played_pairs, ranked_ids, bye_players = calculate_swiss_standings()

            # 檢查第 4 名門檻平手
            top4_ids = ranked_ids[:4]
            cut_win = wins[ranked_ids[3]]
            candidates_for_cut = [p for p in ranked_ids if wins[p] == cut_win]

            need_pk_for_4th = len(candidates_for_cut) > 1 and not set(candidates_for_cut).issubset(set(top4_ids))

            if need_pk_for_4th and f"selected_rank_4" not in st.session_state:
                render_pk_section(4, candidates_for_cut, player_map)
            else:
                if f"selected_rank_4" in st.session_state:
                    chosen_4 = st.session_state[f"selected_rank_4"]
                    top4_ids = [p for p in ranked_ids if p != chosen_4 and p in ranked_ids[:3]] + [chosen_4]

                if df_finals is None:
                    init_finals = [
                        {"階段": "準決賽 1", "選手1": str(top4_ids[0]), "選手2": str(top4_ids[3]), "勝者": "", "敗者": ""},
                        {"階段": "準決賽 2", "選手1": str(top4_ids[1]), "選手2": str(top4_ids[2]), "勝者": "", "敗者": ""},
                        {"階段": "季軍賽", "選手1": "", "選手2": "", "勝者": "", "敗者": ""},
                        {"階段": "冠亞軍賽", "選手1": "", "選手2": "", "勝者": "", "敗者": ""}
                    ]
                    df_finals = pd.DataFrame(init_finals)
                    save_finals(df_finals)

                st.subheader("🥊 四強對戰控制台")
                for idx, r in df_finals.iterrows():
                    stage = r["階段"]
                    p1 = int(r["選手1"]) if r["選手1"] and r["選手1"] != "nan" else 0
                    p2 = int(r["選手2"]) if r["選手2"] and r["選手2"] != "nan" else 0
                    w = int(r["勝者"]) if r["勝者"] and r["勝者"] != "nan" else 0

                    p1_str = f"{p1}號 {player_map.get(p1, '')}" if p1 != 0 else "待定"
                    p2_str = f"{p2}號 {player_map.get(p2, '')}" if p2 != 0 else "待定"

                    st.write(f"#### ⚔️ {stage}：**🔴 {p1_str}** 🆚 **🔵 {p2_str}**")

                    if is_admin and p1 != 0 and p2 != 0:
                        c1, c2, c3 = st.columns([2, 2, 3])
                        with c1:
                            if st.button(f"🏆 {p1_str} 獲勝", key=f"fin_btn_{idx}_1", use_container_width=True, type="primary" if w == p1 else "secondary"):
                                df_finals.at[idx, "勝者"] = str(p1)
                                df_finals.at[idx, "敗者"] = str(p2)

                                # 自動推進準決賽結果至決賽/季軍賽
                                if stage == "準決賽 1":
                                    df_finals.at[2, "選手1"] = str(p2) # 敗者進季軍賽
                                    df_finals.at[3, "選手1"] = str(p1) # 勝者進冠軍賽
                                elif stage == "準決賽 2":
                                    df_finals.at[2, "選手2"] = str(p2)
                                    df_finals.at[3, "選手2"] = str(p1)

                                save_finals(df_finals)
                                st.rerun()
                        with c2:
                            if st.button(f"🏆 {p2_str} 獲勝", key=f"fin_btn_{idx}_2", use_container_width=True, type="primary" if w == p2 else "secondary"):
                                df_finals.at[idx, "勝者"] = str(p2)
                                df_finals.at[idx, "敗者"] = str(p1)

                                if stage == "準決賽 1":
                                    df_finals.at[2, "選手1"] = str(p1)
                                    df_finals.at[3, "選手1"] = str(p2)
                                elif stage == "準決賽 2":
                                    df_finals.at[2, "選手2"] = str(p1)
                                    df_finals.at[3, "選手2"] = str(p2)

                                save_finals(df_finals)
                                st.rerun()
                        with c3:
                            st.caption(f"勝者：`{player_map.get(w, '未決定')}`")
                    else:
                        st.write(f"勝者：`{player_map.get(w, '比賽中')}`")
                    st.write("---")

                # 展示頒獎台結果
                final_champ = df_finals.loc[df_finals["階段"] == "冠亞軍賽", "勝者"].values[0]
                final_runner = df_finals.loc[df_finals["階段"] == "冠亞軍賽", "敗者"].values[0]
                final_third = df_finals.loc[df_finals["階段"] == "季軍賽", "勝者"].values[0]

                if final_champ and final_champ != "nan":
                    st.balloons()
                    st.success(f"""
                    ### 🎉 個人賽最終頒獎台：
                    * 🥇 **總冠軍**：{final_champ}號 {player_map.get(int(final_champ), '')}
                    * 🥈 **亞軍**：{final_runner}號 {player_map.get(int(final_runner), '')}
                    * 🥉 **季軍**：{final_third}號 {player_map.get(int(final_third), '')}
                    """)

    # --- Tab 5: 即時積分榜 ---
    with tab5:
        st.header("📊 個人賽瑞士輪即時積分榜")
        if df_swiss is not None:
            wins, losses, sos, h2h, played_pairs, ranked_ids, bye_players = calculate_swiss_standings()
            standings_data = []
            for rank, p_id in enumerate(ranked_ids, 1):
                standings_data.append({
                    "排名": f"第 {rank} 名",
                    "編號": f"{p_id} 號",
                    "選手名稱": player_map.get(p_id, ""),
                    "勝場 (Wins)": wins[p_id],
                    "敗場 (Losses)": losses[p_id],
                    "對手總勝場 (SOS)": sos[p_id],
                    "是否曾輪空": "是" if p_id in bye_players else "否"
                })
            st.table(standings_data)
        else:
            st.info("尚未開始比賽，無積分榜數據。")
