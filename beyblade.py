import streamlit as st
import pandas as pd
import os

# --- 頁面基本設定 ---
st.set_page_config(page_title="三重盃個人賽對戰管理系統", layout="wide")

SWISS_FILE = "swiss_matches.csv"
FINALS_FILE = "finals_matches.csv"

# 10 位選手預設名單
PLAYER_DICT = {
    1: "Q", 2: "S", 3: "C", 4: "E", 5: "W",
    6: "D", 7: "X", 8: "A", 9: "F", 10: "Z"
}

# --- 資料讀取與儲存函式 ---
def load_swiss_matches():
    if os.path.exists(SWISS_FILE):
        try:
            return pd.read_csv(SWISS_FILE)
        except Exception:
            return None
    return None

def save_swiss_matches(df):
    df.to_csv(SWISS_FILE, index=False)

def load_finals_matches():
    if os.path.exists(FINALS_FILE):
        try:
            return pd.read_csv(FINALS_FILE)
        except Exception:
            return None
    return None

def save_finals_matches(df):
    df.to_csv(FINALS_FILE, index=False)

# --- 讀取當前資料 ---
df_swiss = load_swiss_matches()
df_finals = load_finals_matches()

# --- 核心邏輯：計算瑞士輪戰績、SOS 與排名 ---
def calculate_swiss_standings():
    wins = {pid: 0 for pid in PLAYER_DICT.keys()}
    losses = {pid: 0 for pid in PLAYER_DICT.keys()}
    h2h = {pid: {} for pid in PLAYER_DICT.keys()}
    
    # 1. 統計總勝敗數與對戰紀錄
    if df_swiss is not None and not df_swiss.empty:
        for _, row in df_swiss.iterrows():
            w = row["勝者_編號"]
            l = row["敗者_編號"]
            if w != 0 and l != 0:
                wins[w] += 1
                losses[l] += 1
                h2h[w][l] = 1
                h2h[l][w] = -1

    # 2. 計算 SOS（對手強度分）：僅採計前 4 輪，避免第 5 輪加賽影響 SOS
    sos = {pid: 0 for pid in PLAYER_DICT.keys()}
    if df_swiss is not None and not df_swiss.empty:
        for pid in PLAYER_DICT.keys():
            r1_to_4 = df_swiss[(df_swiss["輪次"] <= 4) & ((df_swiss["選手1_編號"] == pid) | (df_swiss["選手2_編號"] == pid))]
            opponents = []
            for _, row in r1_to_4.iterrows():
                if row["勝者_編號"] != 0:
                    opp = row["選手2_編號"] if row["選手1_編號"] == pid else row["選手1_編號"]
                    opponents.append(opp)
            sos[pid] = sum(wins[opp] for opp in set(opponents))

    # 3. 排序邏輯：1. 勝場數 -> 2. SOS
    def sort_key(pid):
        return (wins[pid], sos[pid])

    ranked_ids = sorted(PLAYER_DICT.keys(), key=sort_key, reverse=True)

    # 4. 判斷同分待加賽與晉級狀態
    status = {}
    for i, pid in enumerate(ranked_ids):
        has_tie = False
        if i > 0:
            prev_id = ranked_ids[i-1]
            if wins[pid] == wins[prev_id] and sos[pid] == sos[prev_id]:
                has_tie = True
        if i < len(ranked_ids) - 1:
            next_id = ranked_ids[i+1]
            if wins[pid] == wins[next_id] and sos[pid] == sos[next_id]:
                has_tie = True

        if has_tie:
            status[pid] = "⚠️ 同分待加賽"
        elif i < 4:
            status[pid] = "🟢 晉級4強決賽"
        else:
            status[pid] = "🔴 預賽淘汰"

    return wins, losses, sos, h2h, status, ranked_ids

# --- 生成下一輪對戰配對邏輯 ---
def generate_next_round_pairs(round_num):
    wins, losses, sos, h2h, status, ranked_ids = calculate_swiss_standings()

    # 👉 第 5 輪以上：只針對「⚠️ 同分待加賽」的選手進行加賽配對
    if round_num >= 5:
        tie_players = [pid for pid in ranked_ids if status[pid] == "⚠️ 同分待加賽"]
        next_matches = []
        for i in range(0, len(tie_players) - 1, 2):
            p1 = tie_players[i]
            p2 = tie_players[i + 1]
            next_matches.append({
                "輪次": round_num,
                "桌號": (i // 2) + 1,
                "選手1_編號": p1,
                "選手1名稱": PLAYER_DICT[p1],
                "選手2_編號": p2,
                "選手2名稱": PLAYER_DICT[p2],
                "勝者_編號": 0,
                "敗者_編號": 0
            })
        return next_matches

    # 👉 第 1~4 輪：標準瑞士輪配對 (避免重複對戰)
    history_pairs = set()
    if df_swiss is not None and not df_swiss.empty:
        for _, row in df_swiss.iterrows():
            history_pairs.add(tuple(sorted([row["選手1_編號"], row["選手2_編號"]])))

    unpaired = ranked_ids.copy()
    next_matches = []
    table_num = 1

    while len(unpaired) >= 2:
        p1 = unpaired.pop(0)
        found_opp = None
        for p2 in unpaired:
            if tuple(sorted([p1, p2])) not in history_pairs:
                found_opp = p2
                break
        
        if found_opp is None:
            found_opp = unpaired[0]

        unpaired.remove(found_opp)
        next_matches.append({
            "輪次": round_num,
            "桌號": table_num,
            "選手1_編號": p1,
            "選手1名稱": PLAYER_DICT[p1],
            "選手2_編號": found_opp,
            "選手2名稱": PLAYER_DICT[found_opp],
            "勝者_編號": 0,
            "敗者_編號": 0
        })
        table_num += 1

    return next_matches

# --- 介面呈現 ---
st.title("💥 三重盃個人賽（10人 4輪瑞士輪 ➡️ 4強單淘汰賽）")

# 管理員模式切換
is_admin = st.sidebar.checkbox("🔑 開啟管理員控制權限", value=True)

tabs = st.tabs(["📝 選手報名與抽籤", "⚔️ 預賽：瑞士輪控制台", "📅 預賽賽程對戰表", "🏆 決賽：四強單淘汰", "📊 即時積分榜"])

# --- Tab 1: 報名與抽籤 ---
with tabs[0]:
    st.header("📝 選手抽籤與初始化")
    if is_admin:
        if st.button("🎲 初始化/重置 4 輪瑞士輪賽程", type="primary"):
            r1 = [
                {"輪次": 1, "桌號": 1, "選手1_編號": 1, "選手1名稱": "Q", "選手2_編號": 2, "選手2名稱": "S", "勝者_編號": 0, "敗者_編號": 0},
                {"輪次": 1, "桌號": 2, "選手1_編號": 3, "選手1名稱": "C", "選手2_編號": 4, "選手2名稱": "E", "勝者_編號": 0, "敗者_編號": 0},
                {"輪次": 1, "桌號": 3, "選手1_編號": 5, "選手1名稱": "W", "選手2_編號": 6, "選手2名稱": "D", "勝者_編號": 0, "敗者_編號": 0},
                {"輪次": 1, "桌號": 4, "選手1_編號": 7, "選手1名稱": "X", "選手2_編號": 8, "選手2名稱": "A", "勝者_編號": 0, "敗者_編號": 0},
                {"輪次": 1, "桌號": 5, "選手1_編號": 9, "選手1名稱": "F", "選手2_編號": 10, "選手2名稱": "Z", "勝者_編號": 0, "敗者_編號": 0},
            ]
            df_swiss = pd.DataFrame(r1)
            save_swiss_matches(df_swiss)
            if os.path.exists(FINALS_FILE):
                os.remove(FINALS_FILE)
            st.success("✅ 賽程已成功初始化為第 1 輪！請切換至「預賽：瑞士輪控制台」登記比賽結果。")
            st.rerun()

# --- Tab 2: 瑞士輪控制台 ---
with tabs[1]:
    st.header("⚔️ 預賽賽果登記控制台")
    if df_swiss is None or df_swiss.empty:
        st.info("💡 目前無賽程資料，請至第一個分頁「📝 選手報名與抽籤」點擊初始化按鈕。")
    else:
        max_r = int(df_swiss["輪次"].max())
        selected_r = st.selectbox("請選擇要登記的輪次：", range(1, max_r + 1), index=max_r - 1)
        
        r_matches = df_swiss[df_swiss["輪次"] == selected_r]
        for idx, row in r_matches.iterrows():
            st.subheader(f"第 {selected_r} 輪 - 第 {row['桌號']} 桌")
            col1, col2, col3 = st.columns([3, 3, 2])
            
            p1_code = row["選手1_編號"]
            p2_code = row["選手2_編號"]
            w_code = row["勝者_編號"]

            with col1:
                st.write(f"🔵 **{p1_code}號 {row['選手1名稱']}**")
                if is_admin and st.button(f"🏆 {row['選手1名稱']} 獲勝", key=f"w1_{idx}"):
                    df_swiss.at[idx, "勝者_編號"] = p1_code
                    df_swiss.at[idx, "敗者_編號"] = p2_code
                    save_swiss_matches(df_swiss)
                    st.rerun()

            with col2:
                st.write(f"🔴 **{p2_code}號 {row['選手2名稱']}**")
                if is_admin and st.button(f"🏆 {row['選手2名稱']} 獲勝", key=f"w2_{idx}"):
                    df_swiss.at[idx, "勝者_編號"] = p2_code
                    df_swiss.at[idx, "敗者_編號"] = p1_code
                    save_swiss_matches(df_swiss)
                    st.rerun()

            with col3:
                if w_code != 0:
                    st.success(f"勝者：{PLAYER_DICT[w_code]}")
                else:
                    st.info("尚未比賽")
            st.write("---")

        current_r_finished = (r_matches["勝者_編號"] != 0).all()
        if is_admin and current_r_finished and selected_r == max_r:
            _, _, _, _, status, _ = calculate_swiss_standings()
            has_tie = any(s == "⚠️ 同分待加賽" for s in status.values())

            if max_r < 4:
                btn_text = f"🚀 生成第 {max_r + 1} 輪瑞士輪對戰賽程"
            else:
                btn_text = f"⚔️ 生成第 {max_r + 1} 輪【特定選手同分加賽】"

            if max_r < 4 or (max_r >= 4 and has_tie):
                if st.button(btn_text, type="primary", use_container_width=True):
                    next_matches = generate_next_round_pairs(max_r + 1)
                    df_next = pd.DataFrame(next_matches)
                    df_swiss = pd.concat([df_swiss, df_next], ignore_index=True)
                    save_swiss_matches(df_swiss)
                    st.success(f"🎉 第 {max_r + 1} 輪對戰已生成！")
                    st.rerun()

# --- Tab 3: 對戰總表 ---
with tabs[2]:
    st.header("📅 預賽完整賽程表")
    if df_swiss is not None and not df_swiss.empty:
        st.dataframe(df_swiss, use_container_width=True)
    else:
        st.info("💡 尚未建立預賽資料。")

# --- Tab 4: 四強決賽 ---
with tabs[3]:
    st.header("🏆 決賽：四強單淘汰控制台")
    if df_swiss is None or df_swiss.empty:
        st.info("💡 請先初始化預賽並完成 4 輪賽事。")
    else:
        wins, losses, sos, h2h, status, ranked_ids = calculate_swiss_standings()
        top4 = ranked_ids[:4]
        
        st.subheader("🎉 預賽晉級 4 強選手：")
        for r, pid in enumerate(top4, 1):
            st.write(f"第 {r} 名：**{pid}號 {PLAYER_DICT[pid]}** ({wins[pid]}勝 {losses[pid]}敗)")
        
        st.write("---")
        
        if df_finals is None or df_finals.empty:
            if is_admin:
                if st.button("🔥 生成 4 強決賽賽程對戰表", type="primary", use_container_width=True):
                    finals_data = [
                        {"階段": "準決賽A", "選手1": PLAYER_DICT[top4[0]], "選手2": PLAYER_DICT[top4[3]], "勝者": "尚未決定"},
                        {"階段": "準決賽B", "選手1": PLAYER_DICT[top4[1]], "選手2": PLAYER_DICT[top4[2]], "勝者": "尚未決定"},
                        {"階段": "季軍賽", "選手1": "準決賽A敗者", "選手2": "準決賽B敗者", "勝者": "尚未決定"},
                        {"階段": "冠軍賽", "選手1": "準決賽A勝者", "選手2": "準決賽B勝者", "勝者": "尚未決定"}
                    ]
                    df_finals = pd.DataFrame(finals_data)
                    save_finals_matches(df_finals)
                    st.rerun()
        else:
            st.subheader("⚔️ 四強決賽對戰表")
            st.dataframe(df_finals, use_container_width=True)

# --- Tab 5: 即時積分榜 ---
with tabs[4]:
    st.header("📊 預賽即時戰績積分榜")
    st.caption("💡 破平順序 (Tie-breakers) : 1. 總勝場數 (Wins) ➡️ 2. 對手強度分 (SOS)")
    
    wins, losses, sos, h2h, status, ranked_ids = calculate_swiss_standings()
    
    data = []
    for rank, pid in enumerate(ranked_ids, 1):
        data.append({
            "預賽排名": f"第 {rank} 名",
            "編號": f"{pid} 號",
            "選手名稱": PLAYER_DICT[pid],
            "勝場": f"{wins[pid]} 勝",
            "敗場": f"{losses[pid]} 敗",
            "對手強度 (SOS)": f"{sos[pid]} 分",
            "晉級狀態": status[pid]
        })
    
    st.table(pd.DataFrame(data))
