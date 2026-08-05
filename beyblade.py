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

# 5 隊單循環 10 場固定對戰組合
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

# 載入初始資料
df_reg = load_registrations()
df_swiss = load_swiss_matches()
df_finals = load_finals()
df_teams = load_team_data()
df_team_matches = load_team_matches()
df_team_finals = load_team_finals()

# ==========================================
# 3. 瑞士輪演算演算法 (Swiss-System)
# ==========================================
def calculate_swiss_standings():
    """計算目前的勝敗、對戰紀錄與 SOS 強度分"""
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
    
    # 計算 SOS (Buchholz): 你擊敗過的對手的總勝場和
    sos = {p_id: sum(wins[opp] for opp in defeated_opponents[p_id]) for p_id in range(1, 11)}

    def sort_key(p_id):
        w_cnt = wins[p_id]
        s_score = sos[p_id]
        # H2H 比分計算
        h2h_score = sum(
            1 for other in range(1, 11)
            if other != p_id and wins[other] == w_cnt and h2h.get((p_id, other)) == p_id
        )
        return (w_cnt, h2h_score, s_score)

    ranked_ids = sorted(range(1, 11), key=sort_key, reverse=True)
    return wins, losses, sos, h2h, played_pairs, ranked_ids, sort_key

def generate_next_round_pairs(current_round):
    """根據當前戰績與不重複原則，生成下一輪瑞士輪對戰"""
    wins, losses, _, _, played_pairs, ranked_ids, _ = calculate_swiss_standings()
    
    # 按當前勝場數進行分組
    groups = {}
    for p_id in ranked_ids:
        w = wins[p_id]
        groups.setdefault(w, []).append(p_id)

    unpaired = []
    new_pairs = []

    # 排序勝場組 (由高到低配對)
    for w in sorted(groups.keys(), reverse=True):
        group_players = unpaired + groups[w]
        unpaired = []
        
        while len(group_players) >= 2:
            p1 = group_players.pop(0)
            found_opponent = False
            for idx, p2 in enumerate(group_players):
                if tuple(sorted([p1, p2])) not in played_pairs:
                    new_pairs.append((p1, p2))
                    group_players.pop(idx)
                    found_opponent = True
                    break
            
            # 若組內無法完全配對，將餘下選手向下跨組 (Downpairing)
            if not found_opponent:
                unpaired.append(p1)

    # 處理剩餘跨組選手
    while len(unpaired) >= 2:
        p1 = unpaired.pop(0)
        p2 = unpaired.pop(0)
        new_pairs.append((p1, p2))

    # 轉換為寫入格式
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

if not st.session_state["is_admin"]:
    admin_input = st.sidebar.text_input("輸入管理密碼", type="password", key="pwd_input")
    if st.sidebar.button("🔑 登入系統", use_container_width=True):
        if admin_input.strip() == ADMIN_PASSWORD:
            st.session_state["is_admin"] = True
            st.sidebar.success("🔓 驗證成功！")
            st.rerun()
        else:
            st.sidebar.error("❌ 密碼錯誤！")
else:
    st.sidebar.success("🔓 管理員權限已開啟")
    if st.sidebar.button("🔒 登出管理員", use_container_width=True):
        st.session_state["is_admin"] = False
        st.rerun()

is_admin = st.session_state["is_admin"]

st.sidebar.write("---")
st.sidebar.header("🏆 賽制系統切換")
main_mode = st.sidebar.radio("選擇要管理的賽制：", ["個人賽 (10人 4輪瑞士輪+4強)", "雙人團體賽 (5隊單循環+決賽)"])

# ==========================================
# 5. 模式一：個人賽 (10人 4輪瑞士輪 + 4強)
# ==========================================
if main_mode == "個人賽 (10人 4輪瑞士輪+4強)":
    st.title("💥 三重盃 個人賽（10人 4輪瑞士輪 ➡️ 4強單淘汰賽）")
    
    tabs = st.tabs(["📝 選手報名與抽籤", "⚔️ 預賽：瑞士輪控制台", "🗓️ 預賽賽程對戰表", "🏆 決賽：四強單淘汰", "📊 即時積分榜"])
    
    # --- Tab 1: 選手名單管理 ---
    with tabs[0]:
        st.header("參賽選手報名紀錄")
        if is_admin:
            with st.form("registration_form", clear_on_submit=True):
                col_name, col_btn = st.columns([3, 1])
                with col_name:
                    name = st.text_input("輸入選手名稱*")
                with col_btn:
                    st.markdown("<br>", unsafe_allow_html=True)
                    submit_reg = st.form_submit_button("📥 新增選手", use_container_width=True)
                    
                if submit_reg:
                    if not name.strip(): 
                        st.error("❌ 報名失敗：名稱不能為空！")
                    elif name.strip() in df_reg["選手名稱"].values: 
                        st.error(f"❌ 選手【{name}】已在報名名單中！")
                    elif len(df_reg) >= 10: 
                        st.error("❌ 報名失敗：個人賽限定 10 人，已滿額！")
                    else:
                        new_player = {"編號": 0, "選手名稱": name.strip()}
                        df_reg = pd.concat([df_reg, pd.DataFrame([new_player])], ignore_index=True)
                        save_registrations(df_reg)
                        st.success(f"🎉 選手【{name}】成功完成報名！")
                        st.rerun()
        
        st.write("---")
        st.subheader(f"👥 已報名選手名單 (共 {len(df_reg)} / 10 人)")
        if not df_reg.empty:
            st.dataframe(df_reg[["編號", "選手名稱"]], use_container_width=True)

        if is_admin:
            if len(df_reg) == 10 and (df_reg["編號"] == 0).all():
                st.write("---")
                if st.button("🎲 滿 10 人！盲抽生成 1~10 號編號並生成第 1 輪對戰", type="primary", use_container_width=True):
                    nums = list(range(1, 11))
                    random.shuffle(nums)
                    df_reg["編號"] = nums
                    save_registrations(df_reg)
                    
                    # 第 1 輪隨機配對 (0-0 組別)
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
                    st.success("🎉 10 人抽籤成功！第 1 輪瑞士輪對戰已自動生成！")
                    st.rerun()

            st.write("---")
            st.subheader("⚙️ 名單管理控制台")
            del_col1, del_col2 = st.columns([2, 1])
            with del_col1:
                target_player = st.selectbox("選擇要刪除的選手", df_reg["選手名稱"].tolist()) if not df_reg.empty else None
            with del_col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if target_player and st.button(f"🗑️ 刪除選手 {target_player}", use_container_width=True):
                    df_reg = df_reg[df_reg["選手名稱"] != target_player]
                    save_registrations(df_reg)
                    save_swiss_matches(None)
                    save_finals(None)
                    st.warning(f"已刪除選手【{target_player}】。")
                    st.rerun()
            
            if st.button("🚨 一鍵清空所有【個人賽名單與成績】", type="secondary", use_container_width=True):
                if os.path.exists(REG_FILE): os.remove(REG_FILE)
                save_swiss_matches(None)
                save_finals(None)
                st.error("💥 個人賽所有名單與戰績已完全清空！")
                st.rerun()

    player_map = dict(zip(df_reg["編號"], df_reg["選手名稱"])) if not df_reg.empty else {}

    # --- Tab 2: 預賽瑞士輪控制台 ---
    with tabs[1]:
        st.header("⚔️ 預賽：4輪瑞士輪控制台")
        
        if df_swiss is None or (df_reg["編號"] == 0).all():
            st.warning("⏳ 需先在「選手報名」分頁集滿 10 人並進行【盲抽編號】後，才能開始瑞士輪比賽！")
        else:
            current_max_round = int(df_swiss["輪次"].max())
            r_matches = df_swiss[df_swiss["輪次"] == current_max_round]
            completed_r_count = sum(1 for w in r_matches["勝者_編號"] if w != 0)
            
            st.info(f"### 📍 當前進行：第 {current_max_round} / 4 輪瑞士輪 (該輪完成進度：{completed_r_count} / 5 場)")

            # 控制台單場輸入
            for m_idx, row in r_matches.iterrows():
                p1_id, p2_id, w_id = int(row["選手A_編號"]), int(row["選手B_編號"]), int(row["勝者_編號"])
                p1_str = f"{p1_id}號 {player_map.get(p1_id, '')}"
                p2_str = f"{p2_id}號 {player_map.get(p2_id, '')}"
                label = row["組別標籤"]

                st.write(f"#### 🥊 【{label}】 **🔴 {p1_str}**  🆚  **🔵 {p2_str}**")
                
                if is_admin:
                    c1, c2, c3 = st.columns([2, 2, 3])
                    with c1:
                        if st.button(f"🏆 {p1_str} 獲勝", key=f"r{current_max_round}_m{m_idx}_p1", use_container_width=True, type="primary" if w_id == p1_id else "secondary"):
                            df_swiss.at[m_idx, "勝者_編號"] = p1_id
                            save_swiss_matches(df_swiss)
                            st.rerun()
                    with c2:
                        if st.button(f"🏆 {p2_str} 獲勝", key=f"r{current_max_round}_m{m_idx}_p2", use_container_width=True, type="primary" if w_id == p2_id else "secondary"):
                            df_swiss.at[m_idx, "勝者_編號"] = p2_id
                            save_swiss_matches(df_swiss)
                            st.rerun()
                    with c3:
                        st.caption(f"目前登記結果：`{player_map.get(w_id, '未完成')}`")
                else:
                    st.write(f"比賽結果：`{player_map.get(w_id, '進行中')}`")
                st.write("---")

            # 產生下一輪按鈕
            if is_admin and completed_r_count == 5:
                if current_max_round < 4:
                    if st.button(f"🚀 生成第 {current_max_round + 1} 輪瑞士輪對戰賽程", type="primary", use_container_width=True):
                        next_matches = generate_next_round_pairs(current_max_round + 1)
                        df_next = pd.DataFrame(next_matches)
                        df_swiss = pd.concat([df_swiss, df_next], ignore_index=True)
                        save_swiss_matches(df_swiss)
                        st.success(f"🎉 第 {current_max_round + 1} 輪賽程配對完成！")
                        st.rerun()
                else:
                    st.success("🎉 預賽 4 輪瑞士輪已完全結束！請前往【🏆 決賽：四強單淘汰】分頁開啟決賽！")

    # --- Tab 3: 預賽賽程總覽 ---
    with tabs[2]:
        st.header("🗓️ 預賽 4 輪賽程對戰表總覽")
        if df_swiss is None or (df_reg["編號"] == 0).all():
            st.info("尚無賽程數據。")
        else:
            for r in range(1, int(df_swiss["輪次"].max()) + 1):
                st.subheader(f"🌀 第 {r} 輪對戰")
                r_df = df_swiss[df_swiss["輪次"] == r]
                display_list = []
                for _, row in r_df.iterrows():
                    p1_id, p2_id, w_id = int(row["選手A_編號"]), int(row["選手B_編號"]), int(row["勝者_編號"])
                    p1_str = f"{p1_id}號 {player_map.get(p1_id, '')}"
                    p2_str = f"{p2_id}號 {player_map.get(p2_id, '')}"
                    w_str = f"🏆 {player_map.get(w_id, '')}" if w_id != 0 else "⏳ 未比賽"

                    display_list.append({
                        "戰績組別": row["組別標籤"],
                        "選手 A (紅)": p1_str,
                        "選手 B (藍)": p2_str,
                        "獲勝者": w_str
                    })
                st.dataframe(pd.DataFrame(display_list), use_container_width=True, hide_index=True)

    # --- Tab 4: 四強決賽 ---
    with tabs[3]:
        st.header("🏆 決賽：四強單淘汰控制台")
        total_played = sum(1 for w in df_swiss["勝者_編號"] if w != 0) if df_swiss is not None else 0
        
        if df_swiss is None or total_played < 20:
            st.warning(f"⏳ 預賽瑞士輪尚未結束（目前完成 {total_played}/20 場），完賽後將自動開放四強決賽！")
        else:
            wins, losses, sos, h2h, _, ranked_ids, _ = calculate_swiss_standings()
            rank1_id, rank2_id, rank3_id, rank4_id = ranked_ids[:4]
            
            p1_str = f"第1名: {rank1_id}號 {player_map[rank1_id]}"
            p2_str = f"第2名: {rank2_id}號 {player_map[rank2_id]}"
            p3_str = f"第3名: {rank3_id}號 {player_map[rank3_id]}"
            p4_str = f"第4名: {rank4_id}號 {player_map[rank4_id]}"

            if df_finals is None:
                st.success("🎉 預賽已完成！前 4 強名單已自動鎖定：\n" + f"\n* {p1_str}\n* {p2_str}\n* {p3_str}\n* {p4_str}")
                if is_admin and st.button("🔥 生成 4 強決賽賽程對戰表", type="primary", use_container_width=True):
                    finals_data = [
                        {"階段": "準決賽A", "選手1": player_map[rank1_id], "選手2": player_map[rank4_id], "勝者": "尚未決定", "敗者": "尚未決定"},
                        {"階段": "準決賽B", "選手1": player_map[rank2_id], "選手2": player_map[rank3_id], "勝者": "尚未決定", "敗者": "尚未決定"},
                        {"階段": "季軍賽", "選手1": "準決賽A敗者", "選手2": "準決賽B敗者", "勝者": "尚未決定", "敗者": "尚未決定"},
                        {"階段": "冠軍賽", "選手1": "準決賽A勝者", "選手2": "準決賽B勝者", "勝者": "尚未決定", "敗者": "尚未決定"}
                    ]
                    df_finals = pd.DataFrame(finals_data)
                    save_finals(df_finals)
                    st.rerun()
            else:
                semiA = df_finals[df_finals["階段"] == "準決賽A"].iloc[0]
                semiB = df_finals[df_finals["階段"] == "準決賽B"].iloc[0]
                place3 = df_finals[df_finals["階段"] == "季軍賽"].iloc[0]
                final_m = df_finals[df_finals["階段"] == "冠軍賽"].iloc[0]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("### ⚔️ 準決賽 (Semi-Finals)")
                    st.write(f"**【準決賽 A】** {semiA['選手1']} 🆚 {semiA['選手2']} ➡️ 勝者：`{semiA['勝者']}`")
                    if is_admin and semiA["勝者"] == "尚未決定":
                        resA = st.selectbox("回報準決賽 A 勝者", ["選擇", semiA['選手1'], semiA['選手2']], key="semiA_s")
                        if resA != "選擇":
                            lossA = semiA['選手2'] if resA == semiA['選手1'] else semiA['選手1']
                            idx_a = df_finals[df_finals["階段"] == "準決賽A"].index[0]
                            df_finals.at[idx_a, "勝者"] = resA
                            df_finals.at[idx_a, "敗者"] = lossA
                            
                            idx_f = df_finals[df_finals["階段"] == "冠軍賽"].index[0]
                            df_finals.at[idx_f, "選手1"] = resA
                            
                            idx_3 = df_finals[df_finals["階段"] == "季軍賽"].index[0]
                            df_finals.at[idx_3, "選手1"] = lossA
                            
                            save_finals(df_finals)
                            st.rerun()

                    st.write("---")
                    st.write(f"**【準決賽 B】** {semiB['選手1']} 🆚 {semiB['選手2']} ➡️ 勝者：`{semiB['勝者']}`")
                    if is_admin and semiB["勝者"] == "尚未決定":
                        resB = st.selectbox("回報準決賽 B 勝者", ["選擇", semiB['選手1'], semiB['選手2']], key="semiB_s")
                        if resB != "選擇":
                            lossB = semiB['選手2'] if resB == semiB['選手1'] else semiB['選手1']
                            idx_b = df_finals[df_finals["階段"] == "準決賽B"].index[0]
                            df_finals.at[idx_b, "勝者"] = resB
                            df_finals.at[idx_b, "敗者"] = lossB
                            
                            idx_f = df_finals[df_finals["階段"] == "冠軍賽"].index[0]
                            df_finals.at[idx_f, "選手2"] = resB
                            
                            idx_3 = df_finals[df_finals["階段"] == "季軍賽"].index[0]
                            df_finals.at[idx_3, "選手2"] = lossB
                            
                            save_finals(df_finals)
                            st.rerun()

                with col2:
                    st.markdown("### 🥇 榮譽決賽 (Finals)")
                    p3_p1, p3_p2 = place3['選手1'], place3['選手2']
                    st.write(f"**🥉【季軍賽】** {p3_p1} 🆚 {p3_p2} ➡️ 季軍：`{place3['勝者']}`")
                    if is_admin and p3_p1 != "準決賽A敗者" and p3_p2 != "準決賽B敗者" and place3["勝者"] == "尚未決定":
                        res3 = st.selectbox("回報季軍賽勝者", ["選擇", p3_p1, p3_p2], key="p3_s")
                        if res3 != "選擇":
                            loss3 = p3_p2 if res3 == p3_p1 else p3_p1
                            idx_3 = df_finals[df_finals["階段"] == "季軍賽"].index[0]
                            df_finals.at[idx_3, "勝者"] = res3
                            df_finals.at[idx_3, "敗者"] = loss3
                            
                            save_finals(df_finals)
                            st.rerun()

                    st.write("---")
                    f_p1, f_p2 = final_m['選手1'], final_m['選手2']
                    st.write(f"**🥇【冠軍賽】** {f_p1} 🆚 {f_p2} ➡️ 冠軍：`{final_m['勝者']}`")
                    if is_admin and f_p1 != "準決賽A勝者" and f_p2 != "準決賽B勝者" and final_m["勝者"] == "尚未決定":
                        resF = st.selectbox("回報冠軍賽勝者", ["選擇", f_p1, f_p2], key="final_s")
                        if resF != "選擇":
                            lossF = f_p2 if resF == f_p1 else f_p1
                            idx_f = df_finals[df_finals["階段"] == "冠軍賽"].index[0]
                            df_finals.at[idx_f, "勝者"] = resF
                            df_finals.at[idx_f, "敗者"] = lossF
                            
                            save_finals(df_finals)
                            st.rerun()
                
                if final_m["勝者"] != "尚未決定" and place3["勝者"] != "尚未決定":
                    st.balloons()
                    st.markdown(f"### 🎖️ 三重盃 個人賽榮譽殿堂\n* 🥇 **冠軍**：{final_m['勝者']}\n* 🥈 **亞軍**：{final_m['敗者']}\n* 🥉 **季軍**：{place3['勝者']}")

    # --- Tab 5: 排行榜 ---
    with tabs[4]:
        st.header("📊 預賽即時戰績積分榜")
        st.caption("💡 破平順序（Tie-breakers）：1. 總勝場數 (Wins) ➡️ 2. 直接對戰勝負 (H2H) ➡️ 3. 對手強度分 (SOS)")
        
        if df_reg.empty or (df_reg["編號"] == 0).all():
            st.info("尚無排名數據（需先完成盲抽編號與比賽）。")
        else:
            wins, losses, sos, h2h, _, ranked_ids, sort_key = calculate_swiss_standings()
            
            tie_break_needed = set()
            for i in range(len(ranked_ids) - 1):
                id1, id2 = ranked_ids[i], ranked_ids[i+1]
                if sort_key(id1) == sort_key(id2) and wins[id1] > 0:
                    tie_break_needed.add(id1); tie_break_needed.add(id2)

            table_data = []
            for rank, p_id in enumerate(ranked_ids, 1):
                w_cnt, l_cnt, s_score = wins[p_id], losses[p_id], sos[p_id]
                
                if p_id in tie_break_needed and rank in [4, 5]: status_str = "⚔️ 平手需加賽爭決賽門票"
                elif p_id in tie_break_needed: status_str = "⚠️ 同分待加賽"
                elif rank <= 4: status_str = "🟢 晉級 4 強決賽"
                else: status_str = "🔴 預賽淘汰"

                table_data.append({
                    "預賽排名": f"第 {rank} 名",
                    "編號": f"{p_id} 號",
                    "選手名稱": player_map.get(p_id, "未定"),
                    "勝場": f"{w_cnt} 勝",
                    "敗場": f"{l_cnt} 敗",
                    "對手強度 (SOS)": f"{s_score} 分",
                    "晉級狀態": status_str
                })
            st.table(table_data)

# ==========================================
# 6. 模式二：雙人團體賽 (5隊單循環 + 決賽)
# ==========================================
elif main_mode == "雙人團體賽 (5隊單循環+決賽)":
    st.title("🤝 三重盃 雙人團體賽（5隊單循環預賽 ➡️ 冠亞軍決賽）")
    
    team_tabs = st.tabs(["📝 5組選手名單管理", "⚔️ 預賽：單循環控制台", "🗓️ 預賽賽程總覽", "🏆 冠亞軍總決賽", "📊 團體積分榜"])
    
    # --- 團體賽 Tab 1: 名單管理 ---
    with team_tabs[0]:
        st.markdown("### 📝 賽制說明：共 5 個組別（A~E），每組 2 位隊員。")
        st.write("---")
        
        ui_inputs = {}
        form_cols = st.columns(2)
        for idx, team in enumerate(TEAM_NAMES):
            with form_cols[idx % 2]:
                st.subheader(f"🛡️ 團體賽 - {team} 名單")
                row_p1 = df_teams[(df_teams["組別"] == team) & (df_teams["隊員別"] == "隊員 1")].iloc[0]
                row_p2 = df_teams[(df_teams["組別"] == team) & (df_teams["隊員別"] == "隊員 2")].iloc[0]
                
                p1_name = st.text_input(f"隊員 1 姓名", value=str(row_p1["選手名稱"]), key=f"{team}_p1_name", disabled=not is_admin)
                p2_name = st.text_input(f"隊員 2 姓名", value=str(row_p2["選手名稱"]), key=f"{team}_p2_name", disabled=not is_admin)
                
                ui_inputs[team] = {"p1": p1_name, "p2": p2_name}
                st.write("---")

        if is_admin:
            if st.button("💾 儲存 5 組團體賽選手名單", type="primary", use_container_width=True):
                new_rows = []
                for team in TEAM_NAMES:
                    new_rows.append({"組別": team, "隊員別": "隊員 1", "選手名稱": ui_inputs[team]["p1"].strip()})
                    new_rows.append({"組別": team, "隊員別": "隊員 2", "選手名稱": ui_inputs[team]["p2"].strip()})
                df_teams = pd.DataFrame(new_rows)
                save_team_data(df_teams)
                
                # 初始化 10 場隊伍單循環賽程
                if df_team_matches is None:
                    t_matches = []
                    for idx, (t1, t2) in enumerate(TEAM_SCHEDULE_10, 1):
                        t_matches.append({
                            "場次": idx,
                            "隊伍A": t1,
                            "隊伍B": t2,
                            "勝隊": "尚未決定"
                        })
                    save_team_matches(pd.DataFrame(t_matches))
                st.success("🎉 團體賽名單與預賽 10 場單循環賽程已儲存！")
                st.rerun()

        st.write("---")
        st.subheader("📊 當前團體賽選手名單總覽")
        st.dataframe(df_teams, use_container_width=True)

        if is_admin:
            st.write("---")
            if st.button("🚨 一鍵清空所有團體賽名單與戰績", type="secondary", use_container_width=True):
                default_rows = []
                for team in TEAM_NAMES:
                    default_rows.append({"組別": team, "隊員別": "隊員 1", "選手名稱": ""})
                    default_rows.append({"組別": team, "隊員別": "隊員 2", "選手名稱": ""})
                save_team_data(pd.DataFrame(default_rows))
                save_team_matches(None)
                save_team_finals(None)
                st.error("💥 團體賽所有名單與戰績已完全清空！")
                st.rerun()

    def get_team_members_str(team_code):
        if not team_code or team_code in ["TBD", "尚未決定"]: return ""
        members = df_teams[df_teams["組別"] == team_code]["選手名稱"].tolist()
        members_clean = [m for m in members if str(m).strip()]
        return f"({ ' ＆ '.join(members_clean) })" if members_clean else ""

    # 團體戰績計算
    def calculate_team_standings():
        t_wins = {t: 0 for t in TEAM_NAMES}
        t_losses = {t: 0 for t in TEAM_NAMES}
        t_h2h = {}

        if df_team_matches is not None:
            for _, r in df_team_matches.iterrows():
                w = str(r["勝隊"])
                t1, t2 = str(r["隊伍A"]), str(r["隊伍B"])
                if w != "尚未決定":
                    l = t2 if w == t1 else t1
                    t_wins[w] += 1
                    t_losses[l] += 1
                    t_h2h[(t1, t2)] = w
                    t_h2h[(t2, t1)] = w

        def team_sort_key(t):
            w_cnt = t_wins[t]
            h2h_score = sum(
                1 for other in TEAM_NAMES
                if other != t and t_wins[other] == w_cnt and t_h2h.get((t, other)) == t
            )
            return (w_cnt, h2h_score)

        ranked_teams = sorted(TEAM_NAMES, key=team_sort_key, reverse=True)
        return t_wins, t_losses, t_h2h, ranked_teams, team_sort_key

    # --- 團體賽 Tab 2: 控制台 ---
    with team_tabs[1]:
        st.header("⚔️ 團體預賽：5隊單循環控制台")
        if df_team_matches is None:
            st.warning("⏳ 請先至「5組選手名單管理」儲存選手名單以生成 10 場對戰賽程！")
        else:
            completed_t_count = sum(1 for w in df_team_matches["勝隊"] if w != "尚未決定")
            st.progress(completed_t_count / 10, text=f"團體預賽進度：{completed_t_count} / 10 場")

            selected_t_match = st.number_input("選擇對戰場次：", min_value=1, max_value=10, value=min(completed_t_count + 1, 10), step=1)
            t_match_row = df_team_matches[df_team_matches["場次"] == selected_t_match].iloc[0]
            
            t1 = str(t_match_row["隊伍A"])
            t2 = str(t_match_row["隊伍B"])
            curr_winner = str(t_match_row["勝隊"])

            st.info(f"### 🥊 第 {selected_t_match} 場團體賽\n\n## **🔴 {t1} {get_team_members_str(t1)}**  🆚  **🔵 {t2} {get_team_members_str(t2)}**")
            
            st.write("---")
            if is_admin:
                st.write("**登記勝隊：**")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button(f"🏆 {t1} 獲勝", use_container_width=True, type="primary" if curr_winner == t1 else "secondary"):
                        row_idx = df_team_matches[df_team_matches["場次"] == selected_t_match].index[0]
                        df_team_matches.at[row_idx, "勝隊"] = t1
                        save_team_matches(df_team_matches)
                        st.rerun()
                with c2:
                    if st.button(f"🏆 {t2} 獲勝", use_container_width=True, type="primary" if curr_winner == t2 else "secondary"):
                        row_idx = df_team_matches[df_team_matches["場次"] == selected_t_match].index[0]
                        df_team_matches.at[row_idx, "勝隊"] = t2
                        save_team_matches(df_team_matches)
                        st.rerun()
            else:
                st.write(f"**當前比賽結果**：`{curr_winner}`")

    # --- 團體賽 Tab 3: 賽程對戰表 ---
    with team_tabs[2]:
        st.header("🗓️ 團體賽 10 場對戰表總覽")
        if df_team_matches is None:
            st.info("尚無賽程資料。")
        else:
            t_list = []
            for _, r in df_team_matches.iterrows():
                m_idx = int(r["場次"])
                t1, t2, w = str(r["隊伍A"]), str(r["隊伍B"]), str(r["勝隊"])
                status = "✅ 已完成" if w != "尚未決定" else "⏳ 待比賽"
                w_str = f"🏆 {w} {get_team_members_str(w)}" if w != "尚未決定" else "未進行"

                t_list.append({
                    "場次": f"第 {m_idx} 場",
                    "隊伍 A": f"{t1} {get_team_members_str(t1)}",
                    "隊伍 B": f"{t2} {get_team_members_str(t2)}",
                    "狀態": status,
                    "獲勝隊伍": w_str
                })
            st.dataframe(pd.DataFrame(t_list), use_container_width=True, hide_index=True)

    # --- 團體賽 Tab 4: 冠亞軍決賽 ---
    with team_tabs[3]:
        st.header("🏆 團體賽：冠亞軍總決賽")
        completed_t_count = sum(1 for w in df_team_matches["勝隊"] if w != "尚未決定") if df_team_matches is not None else 0

        if df_team_matches is None or completed_t_count < 10:
            st.warning(f"⏳ 團體預賽尚未結束（目前完成 {completed_t_count}/10 場），預賽完成後自動開啟冠亞軍決賽！")
        else:
            _, _, _, ranked_teams, _ = calculate_team_standings()
            t_rank1, t_rank2 = ranked_teams[0], ranked_teams[1]

            if df_team_finals is None:
                st.success(f"🎉 團體預賽已結束！晉級總決賽隊伍：\n* 🥇 **預賽第 1 名**：{t_rank1} {get_team_members_str(t_rank1)}\n* 🥈 **預賽第 2 名**：{t_rank2} {get_team_members_str(t_rank2)}")
                if is_admin and st.button("🔥 生成【團體冠亞軍總決賽】對戰", type="primary", use_container_width=True):
                    f_data = [{"隊伍1": t_rank1, "隊伍2": t_rank2, "冠軍": "尚未決定", "亞軍": "尚未決定"}]
                    df_team_finals = pd.DataFrame(f_data)
                    save_team_finals(df_team_finals)
                    st.rerun()
            else:
                tf_row = df_team_finals.iloc[0]
                t_p1, t_p2 = tf_row["隊伍1"], tf_row["隊伍2"]
                winner = tf_row["冠軍"]

                st.markdown(f"### 👑 【三重盃 團體總冠軍賽】\n\n## **🔴 {t_p1} {get_team_members_str(t_p1)}**  🆚  **🔵 {t_p2} {get_team_members_str(t_p2)}**")
                st.write("---")

                if is_admin and winner == "尚未決定":
                    res_tf = st.selectbox("回報團體總冠軍", ["選擇勝隊", t_p1, t_p2])
                    if res_tf != "選擇勝隊":
                        runner_up = t_p2 if res_tf == t_p1 else t_p1
                        df_team_finals.at[0, "冠軍"] = res_tf
                        df_team_finals.at[0, "亞軍"] = runner_up
                        save_team_finals(df_team_finals)
                        st.rerun()
                else:
                    st.write(f"**決賽結果**：`{winner}`")

                if winner != "尚未決定":
                    st.balloons()
                    st.markdown(f"### 🎖️ 三重盃 團體賽殿堂\n* 🏆 **總冠軍**：{winner} {get_team_members_str(winner)}\n* 🥈 **總亞軍**：{tf_row['亞軍']} {get_team_members_str(tf_row['亞軍'])}")

    # --- 團體賽 Tab 5: 積分榜 ---
    with team_tabs[4]:
        st.header("📊 團體預賽即時戰績積分榜")
        st.caption("💡 破平順序：1. 勝場數 ➡️ 2. 直接對戰成績 (H2H) ➡️ 3. 一局定勝負加賽")
        
        if df_team_matches is None:
            st.info("尚無數據。")
        else:
            t_wins, t_losses, _, ranked_teams, team_sort_key = calculate_team_standings()
            
            tie_needed = set()
            for i in range(len(ranked_teams) - 1):
                t1, t2 = ranked_teams[i], ranked_teams[i+1]
                if team_sort_key(t1) == team_sort_key(t2) and t_wins[t1] > 0:
                    tie_needed.add(t1); tie_needed.add(t2)

            t_table = []
            for rank, t in enumerate(ranked_teams, 1):
                w_cnt, l_cnt = t_wins[t], t_losses[t]
                
                if t in tie_needed and rank in [2, 3]: status_str = "⚔️ 平手需進行 1 局加賽搶決賽門票"
                elif rank <= 2: status_str = "🟢 晉級冠亞軍總決賽"
                else: status_str = "🔴 預賽淘汰"

                t_table.append({
                    "預賽排名": f"第 {rank} 名",
                    "隊伍名稱": t,
                    "選手陣容": get_team_members_str(t),
                    "勝場": f"{w_cnt} 勝",
                    "敗場": f"{l_cnt} 敗",
                    "晉級狀態": status_str
                })
            st.table(t_table)
