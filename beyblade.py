import streamlit as st
import pandas as pd
import os
import random

# ==========================================
# 1. 基礎設定與檔案路徑
# ==========================================
st.set_page_config(page_title="三重盃 陀螺賽事管理系統", page_icon="💥", layout="wide")

REG_FILE = "players_registration.csv"          # 個人賽檔案 (10人)
MATCH_FILE = "current_matches.csv"             # 10人單循環賽程檔案 (45場)
FINALS_FILE = "finals_matches.csv"             # 四強單淘汰檔案
TEAM_DATA_FILE = "team_players_registration.csv" # 團體賽名單檔案 (5組)
TEAM_MATCH_FILE = "team_matches.csv"           # 團體賽淘汰賽賽程檔案

ADMIN_PASSWORD = "admin"  # 管理員預設密碼

# 10 人單循環 45 場固定最佳賽程表 (儘量避免連續上場)
SCHEDULE_45 = [
    (1, 2), (3, 4), (5, 6), (7, 8), (9, 10),
    (1, 3), (2, 5), (4, 7), (6, 9), (8, 10),
    (1, 4), (2, 6), (3, 8), (5, 10), (7, 9),
    (1, 5), (2, 7), (3, 9), (4, 10), (6, 8),
    (1, 6), (2, 8), (3, 10), (4, 9), (5, 7),
    (1, 7), (2, 9), (3, 5), (4, 8), (6, 10),
    (1, 8), (2, 10), (3, 7), (4, 6), (5, 9),
    (1, 9), (2, 4), (3, 6), (5, 8), (7, 10),
    (1, 10), (2, 3), (4, 5), (6, 7), (8, 9)
]

TEAM_NAMES = ["A組", "B組", "C組", "D組", "E組"]

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

def load_matches():
    if os.path.exists(MATCH_FILE):
        return pd.read_csv(MATCH_FILE).fillna("")
    return None

def save_matches(df):
    if df is not None:
        df.to_csv(MATCH_FILE, index=False, encoding="utf-8-sig")
    elif os.path.exists(MATCH_FILE):
        os.remove(MATCH_FILE)

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

# 載入初始資料
df_reg = load_registrations()
df_matches = load_matches()
df_finals = load_finals()
df_teams = load_team_data()
df_team_matches = load_team_matches()

# ==========================================
# 3. 側邊欄：權限與賽制切換
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
main_mode = st.sidebar.radio("選擇要管理的賽制：", ["個人賽 (10人單循環+4強)", "雙人團體賽 (獨立區)"])

# ==========================================
# 4. 模式一：個人賽 (10人單循環 + 4強淘汰賽)
# ==========================================
if main_mode == "個人賽 (10人單循環+4強)":
    st.title("💥 三重盃 個人賽（10人單循環預賽 ➡️ 4強淘汰賽）")
    
    tabs = st.tabs(["📝 選手報名與抽籤", "⚔️ 預賽：單循環控制台", "🗓️ 預賽賽程總覽", "🏆 決賽：四強單淘汰", "📊 即時積分榜"])
    
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
                if st.button("🎲 滿 10 人！盲抽生成 1~10 號編號並初始化賽程", type="primary", use_container_width=True):
                    nums = list(range(1, 11))
                    random.shuffle(nums)
                    df_reg["編號"] = nums
                    save_registrations(df_reg)
                    
                    matches_init = []
                    for idx, (p1_id, p2_id) in enumerate(SCHEDULE_45, 1):
                        matches_init.append({
                            "場次": idx,
                            "選手A_編號": p1_id,
                            "選手B_編號": p2_id,
                            "勝者_編號": 0
                        })
                    save_matches(pd.DataFrame(matches_init))
                    st.success("🎉 10 人抽籤成功！預賽 45 場賽程已自動生成！")
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
                    save_matches(None)
                    save_finals(None)
                    st.warning(f"已刪除選手【{target_player}】。")
                    st.rerun()
            
            if st.button("🚨 一鍵清空所有【個人賽名單與成績】", type="secondary", use_container_width=True):
                if os.path.exists(REG_FILE): os.remove(REG_FILE)
                save_matches(None)
                save_finals(None)
                st.error("💥 個人賽所有名單與戰績已完全清空！")
                st.rerun()

    player_map = dict(zip(df_reg["編號"], df_reg["選手名稱"])) if not df_reg.empty else {}

    # --- Tab 2: 10人單循環賽程控制台 ---
    with tabs[1]:
        st.header("⚔️ 預賽：10人單循環對戰控制台")
        
        if df_matches is None or (df_reg["編號"] == 0).all():
            st.warning("⏳ 需先在「選手報名」分頁集滿 10 人並進行【盲抽編號】後，才能開始單循環賽！")
        else:
            completed_count = sum(1 for w in df_matches["勝者_編號"] if w != 0)
            st.progress(completed_count / 45, text=f"預賽進度：{completed_count} / 45 場")
            
            selected_match_idx = st.number_input("選擇對戰場次：", min_value=1, max_value=45, value=min(completed_count + 1, 45), step=1)
            match_row = df_matches[df_matches["場次"] == selected_match_idx].iloc[0]
            
            p1_id = int(match_row["選手A_編號"])
            p2_id = int(match_row["選手B_編號"])
            p1_name = player_map.get(p1_id, f"{p1_id}號")
            p2_name = player_map.get(p2_id, f"{p2_id}號")
            current_winner_id = int(match_row["勝者_編號"])

            st.info(f"### 🥊 第 {selected_match_idx} 場對戰\n\n## **🔴 {p1_id}號 {p1_name}**  🆚  **🔵 {p2_id}號 {p2_name}**")
            
            st.write("---")
            if is_admin:
                st.write("**登記勝者：**")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button(f"🏆 {p1_id}號 {p1_name} 獲勝", use_container_width=True, type="primary" if current_winner_id == p1_id else "secondary"):
                        row_idx = df_matches[df_matches["場次"] == selected_match_idx].index[0]
                        df_matches.at[row_idx, "勝者_編號"] = p1_id
                        save_matches(df_matches)
                        st.rerun()
                with c2:
                    if st.button(f"🏆 {p2_id}號 {p2_name} 獲勝", use_container_width=True, type="primary" if current_winner_id == p2_id else "secondary"):
                        row_idx = df_matches[df_matches["場次"] == selected_match_idx].index[0]
                        df_matches.at[row_idx, "勝者_編號"] = p2_id
                        save_matches(df_matches)
                        st.rerun()
            else:
                w_str = player_map.get(current_winner_id, "尚未決定") if current_winner_id != 0 else "尚未比賽"
                st.write(f"**當前比賽結果**：`{w_str}`")

    # --- Tab 3: 預賽賽程總覽 ---
    with tabs[2]:
        st.header("🗓️ 預賽賽程總覽")
        if df_matches is None or (df_reg["編號"] == 0).all():
            st.info("尚無賽程數據（需先完成選手盲抽編號）。")
        else:
            view_mode = st.radio("選擇檢視方式：", ["交叉對戰矩陣表", "完整 45 場對戰清單"], horizontal=True)
            
            if view_mode == "交叉對戰矩陣表":
                st.caption("💡 矩陣表說明：單循環對戰圖。顯示勝者名稱，`VS` 代表未比賽，`---` 代表同選手。")
                
                match_results = {}
                for _, row in df_matches.iterrows():
                    p1, p2, w = int(row["選手A_編號"]), int(row["選手B_編號"]), int(row["勝者_編號"])
                    match_results[(p1, p2)] = w
                    match_results[(p2, p1)] = w

                grid_data = []
                for row_id in range(1, 11):
                    row_dict = {"選手": f"{row_id}號 {player_map.get(row_id, '')}"}
                    for col_id in range(1, 11):
                        col_label = f"{col_id}號"
                        if row_id == col_id:
                            row_dict[col_label] = "---"
                        else:
                            w_id = match_results.get((row_id, col_id), 0)
                            if w_id == 0:
                                row_dict[col_label] = "VS"
                            else:
                                row_dict[col_label] = f"🏆 {player_map.get(w_id, f'{w_id}號')}"
                    grid_data.append(row_dict)

                df_grid = pd.DataFrame(grid_data)
                st.dataframe(df_grid, use_container_width=True, hide_index=True)

            else:
                st.caption("💡 清單模式：按比賽順序列出 45 場賽程。")
                schedule_list = []
                for _, row in df_matches.iterrows():
                    m_idx = int(row["場次"])
                    p1_id, p2_id, w_id = int(row["選手A_編號"]), int(row["選手B_編號"]), int(row["勝者_編號"])
                    
                    p1_str = f"{p1_id}號 {player_map.get(p1_id, '')}"
                    p2_str = f"{p2_id}號 {player_map.get(p2_id, '')}"
                    
                    if w_id == 0:
                        status = "⏳ 待比賽"
                        w_str = "未進行"
                    else:
                        status = "✅ 已完成"
                        w_str = f"🏆 {p1_str}" if w_id == p1_id else f"🏆 {p2_str}"

                    schedule_list.append({
                        "場次": f"第 {m_idx} 場",
                        "選手 A (紅)": p1_str,
                        "選手 B (藍)": p2_str,
                        "比賽狀態": status,
                        "獲勝者": w_str
                    })
                st.dataframe(pd.DataFrame(schedule_list), use_container_width=True, hide_index=True)

    # 進階戰績計算函式
    def calculate_standings():
        wins_dict = {p_id: 0 for p_id in range(1, 11)}
        losses_dict = {p_id: 0 for p_id in range(1, 11)}
        defeated_opponents = {p_id: [] for p_id in range(1, 11)}
        h2h = {}

        if df_matches is not None:
            for _, r in df_matches.iterrows():
                w = int(r["勝者_編號"])
                p1, p2 = int(r["選手A_編號"]), int(r["選手B_編號"])
                if w != 0:
                    l = p2 if w == p1 else p1
                    wins_dict[w] += 1
                    losses_dict[l] += 1
                    defeated_opponents[w].append(l)
                    h2h[(p1, p2)] = w
                    h2h[(p2, p1)] = w
        
        sos_dict = {p_id: sum(wins_dict[opp] for opp in defeated_opponents[p_id]) for p_id in range(1, 11)}

        def sort_key(p_id):
            wins = wins_dict[p_id]
            sos = sos_dict[p_id]
            h2h_score = sum(
                1 for other_id in range(1, 11)
                if other_id != p_id and wins_dict[other_id] == wins and h2h.get((p_id, other_id)) == p_id
            )
            return (wins, h2h_score, sos)

        ranked_ids = sorted(range(1, 11), key=sort_key, reverse=True)
        return wins_dict, losses_dict, sos_dict, h2h, ranked_ids, sort_key

    # --- Tab 4: 四強決賽 ---
    with tabs[3]:
        st.header("🏆 決賽：四強單淘汰控制台")
        completed_count = sum(1 for w in df_matches["勝者_編號"] if w != 0) if df_matches is not None else 0
        
        if completed_count < 45:
            st.warning(f"⏳ 預賽尚未結束（目前完成 {completed_count}/45 場），預賽打完後將自動開啟四強決賽！")
        else:
            wins_dict, losses_dict, sos_dict, h2h, ranked_ids, _ = calculate_standings()
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
                            
                            # 修復：改用 .at 安全賦值
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
                            
                            # 修復：改用 .at 安全賦值
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
                            
                            # 修復：改用 .at 安全賦值
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
                            
                            # 修復：改用 .at 安全賦值
                            idx_f = df_finals[df_finals["階段"] == "冠軍賽"].index[0]
                            df_finals.at[idx_f, "勝者"] = resF
                            df_finals.at[idx_f, "敗者"] = lossF
                            
                            save_finals(df_finals)
                            st.rerun()
                
                if final_m["勝者"] != "尚未決定" and place3["勝者"] != "尚未決定":
                    st.balloons()
                    st.markdown(f"### 🎖️ 三重盃 榮譽殿堂\n* 🥇 **冠軍**：{final_m['勝者']}\n* 🥈 **亞軍**：{final_m['敗者']}\n* 🥉 **季軍**：{place3['勝者']}")

    # --- Tab 5: 排行榜 ---
    with tabs[4]:
        st.header("📊 預賽即時戰績積分榜")
        st.caption("💡 排名優先順序：1. 總勝場 ➡️ 2. 對戰勝負 (Head-to-Head) ➡️ 3. 戰績強度 (擊敗對手的總勝場數)")
        
        if df_reg.empty or (df_reg["編號"] == 0).all():
            st.info("尚無排名數據（需先完成盲抽編號與比賽）。")
        else:
            wins_dict, losses_dict, sos_dict, h2h, ranked_ids, sort_key = calculate_standings()
            
            tie_break_needed = set()
            for i in range(len(ranked_ids) - 1):
                id1, id2 = ranked_ids[i], ranked_ids[i+1]
                if sort_key(id1) == sort_key(id2) and wins_dict[id1] > 0:
                    tie_break_needed.add(id1); tie_break_needed.add(id2)

            table_data = []
            for rank, p_id in enumerate(ranked_ids, 1):
                wins, losses, sos = wins_dict[p_id], losses_dict[p_id], sos_dict[p_id]
                
                if p_id in tie_break_needed and rank in [4, 5]: status_str = "⚔️ 需加賽爭奪 4 強"
                elif p_id in tie_break_needed: status_str = "⚠️ 同分待加賽"
                elif rank <= 4: status_str = "🟢 晉級 4 強"
                else: status_str = "🔴 預賽淘汰"

                table_data.append({
                    "預賽排名": f"第 {rank} 名",
                    "編號": f"{p_id} 號",
                    "選手名稱": player_map.get(p_id, "未定"),
                    "勝場": f"{wins} 勝",
                    "敗場": f"{losses} 敗",
                    "戰績強度": f"{sos} 分",
                    "晉級狀態": status_str
                })
            st.table(table_data)

# ==========================================
# 5. 模式二：雙人團體賽 (10人 5組 A~E)
# ==========================================
elif main_mode == "雙人團體賽 (獨立區)":
    st.title("🤝 三重盃 雙人團體賽獨立報名與淘汰賽系統")
    
    team_tabs = st.tabs(["📝 5組選手名單管理", "🏆 團體淘汰賽賽程表"])
    
    # --- 團體賽分頁 1：名單管理 ---
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
                st.success("🎉 團體賽名單儲存成功！")
                st.rerun()

        st.write("---")
        st.subheader("📊 當前團體賽選手名單總覽")
        st.dataframe(df_teams, use_container_width=True)

        if is_admin:
            st.write("---")
            if st.button("🚨 一鍵清空所有團體賽名單", type="secondary", use_container_width=True):
                default_rows = []
                for team in TEAM_NAMES:
                    default_rows.append({"組別": team, "隊員別": "隊員 1", "選手名稱": ""})
                    default_rows.append({"組別": team, "隊員別": "隊員 2", "選手名稱": ""})
                df_reset = pd.DataFrame(default_rows)
                save_team_data(df_reset)
                st.error("💥 團體賽所有名單已完全清空！")
                st.rerun()

    # --- 團體賽分頁 2：淘汰賽區 ---
    with team_tabs[1]:
        st.header("🏆 5隊團體單敗淘汰賽程")
        def get_team_members_str(team_code):
            if not team_code or team_code in ["TBD", "輪空晉級"]: return f"({team_code})"
            members = df_teams[df_teams["組別"] == team_code]["選手名稱"].tolist()
            members_clean = [m for m in members if str(m).strip()]
            return f"({ ' ＆ '.join(members_clean) })" if members_clean else "(未登記選手)"

        if df_team_matches is None:
            st.info("💡 點擊下方按鈕將 A, B, C, D, E 五組進行隨機抽籤：1 組種子輪空直升準決賽，其餘 4 組對決爭取晉級。")
            if is_admin and st.button("🎲 隨機抽籤生成 5隊淘汰賽程表", type="primary", use_container_width=True):
                teams_list = TEAM_NAMES.copy()
                random.shuffle(teams_list)
                
                bracket_data = [
                    {"場次編號": "QF1", "階段": "預賽", "組別A": teams_list[1], "組別B": teams_list[2], "勝者": "尚未決定"},
                    {"場次編號": "QF2", "階段": "預賽", "組別A": teams_list[3], "組別B": teams_list[4], "勝者": "尚未決定"},
                    {"場次編號": "SF1", "階段": "準決賽 1", "組別A": teams_list[0], "組別B": "QF1勝者", "勝者": "尚未決定"},
                    {"場次編號": "SF2", "階段": "準決賽 2", "組別A": "QF2勝者", "組別B": "輪空晉級", "勝者": "尚未決定"},
                    {"場次編號": "F1",  "階段": "總決賽", "組別A": "TBD", "組別B": "TBD", "勝者": "尚未決定"}
                ]
                df_team_matches = pd.DataFrame(bracket_data)
                save_team_matches(df_team_matches)
                st.rerun()
        else:
            qf1 = df_team_matches[df_team_matches["場次編號"] == "QF1"].iloc[0]
            qf2 = df_team_matches[df_team_matches["場次編號"] == "QF2"].iloc[0]
            sf1 = df_team_matches[df_team_matches["場次編號"] == "SF1"].iloc[0]
            f1 = df_team_matches[df_team_matches["場次編號"] == "F1"].iloc[0]
            
            st.markdown("### 📊 賽程樹狀總覽")
            b_col1, b_col2, b_col3 = st.columns(3)
            with b_col1:
                st.info(f"🧱 **預賽 Match 1 (QF1)**\n\n【{qf1['組別A']}】 vs 【{qf1['組別B']}】\n\n ➡️ 勝者：`{qf1['勝者']}`")
                st.info(f"🧱 **預賽 Match 2 (QF2)**\n\n【{qf2['組別A']}】 vs 【{qf2['組別B']}】\n\n ➡️ 勝者：`{qf2['勝者']}`")
            with b_col2:
                st.info(f"⚔️ **準決賽 1**\n\n【{sf1['組別A']} (種子)】 vs 【{sf1['組別B']}】\n\n ➡️ 勝者：`{sf1['勝者']}`")
                st.info(f"⚔️ **準決賽 2**\n\n【{qf2['勝者']}】 (直升總決賽)")
            with b_col3:
                st.warning(f"👑 **{f1['階段']}**\n\n【{f1['組別A']}】 vs 【{f1['組別B']}】\n\n ➡️ 總冠軍：`{f1['勝者']}`")
                if f1['勝者'] != "尚未決定":
                    st.balloons()
                    st.success(f"🎉 恭喜本屆三重盃團體賽總冠軍：\n\n### 🏆 {f1['勝者']} {get_team_members_str(f1['勝者'])} 🏆")
            
            st.write("---")
            st.markdown("### 🥊 賽事勝負回報")
            
            # QF1
            c_info, c_score = st.columns([3, 1])
            with c_info:
                st.write(f"**預賽 QF1**：**{qf1['組別A']}** {get_team_members_str(qf1['組別A'])} 🆚 **{qf1['組別B']}** {get_team_members_str(qf1['組別B'])}")
            with c_score:
                if is_admin and qf1['勝者'] == "尚未決定":
                    qf1_win = st.selectbox("回報 QF1 勝者", ["選擇勝組", qf1['組別A'], qf1['組別B']], key="sel_qf1")
                    if qf1_win != "選擇勝組":
                        # 修復：改用 .at 安全賦值
                        idx_qf1 = df_team_matches[df_team_matches["場次編號"] == "QF1"].index[0]
                        df_team_matches.at[idx_qf1, "勝者"] = qf1_win
                        
                        idx_sf1 = df_team_matches[df_team_matches["場次編號"] == "SF1"].index[0]
                        df_team_matches.at[idx_sf1, "組別B"] = qf1_win
                        
                        save_team_matches(df_team_matches)
                        st.rerun()

            st.write("---")
            # QF2
            c_info, c_score = st.columns([3, 1])
            with c_info:
                st.write(f"**預賽 QF2**：**{qf2['組別A']}** {get_team_members_str(qf2['組別A'])} 🆚 **{qf2['組別B']}** {get_team_members_str(qf2['組別B'])}")
            with c_score:
                if is_admin and qf2['勝者'] == "尚未決定":
                    qf2_win = st.selectbox("回報 QF2 勝者", ["選擇勝組", qf2['組別A'], qf2['組別B']], key="sel_qf2")
                    if qf2_win != "選擇勝組":
                        # 修復：改用 .at 安全賦值
                        idx_qf2 = df_team_matches[df_team_matches["場次編號"] == "QF2"].index[0]
                        df_team_matches.at[idx_qf2, "勝者"] = qf2_win
                        
                        idx_f1 = df_team_matches[df_team_matches["場次編號"] == "F1"].index[0]
                        df_team_matches.at[idx_f1, "組別B"] = qf2_win
                        
                        save_team_matches(df_team_matches)
                        st.rerun()

            st.write("---")
            # SF1
            c_info, c_score = st.columns([3, 1])
            with c_info:
                st.write(f"**準決賽 SF1**：**{sf1['組別A']} (種子隊)** {get_team_members_str(sf1['組別A'])} 🆚 **{sf1['組別B']}** {get_team_members_str(sf1['組別B'])}")
            with c_score:
                if is_admin and sf1['組別B'] != "QF1勝者" and sf1['勝者'] == "尚未決定":
                    sf1_win = st.selectbox("回報 SF1 勝者", ["選擇勝組", sf1['組別A'], sf1['組別B']], key="sel_sf1")
                    if sf1_win != "選擇勝組":
                        # 修復：改用 .at 安全賦值
                        idx_sf1 = df_team_matches[df_team_matches["場次編號"] == "SF1"].index[0]
                        df_team_matches.at[idx_sf1, "勝者"] = sf1_win
                        
                        idx_f1 = df_team_matches[df_team_matches["場次編號"] == "F1"].index[0]
                        df_team_matches.at[idx_f1, "組別A"] = sf1_win
                        
                        save_team_matches(df_team_matches)
                        st.rerun()

            st.write("---")
            # F1
            c_info, c_score = st.columns([3, 1])
            with c_info:
                st.write(f"**總決賽 Grand Final**：**{f1['組別A']}** {get_team_members_str(f1['組別A'])} 🆚 **{f1['組別B']}** {get_team_members_str(f1['組別B'])}")
            with c_score:
                if is_admin and f1['組別A'] != "TBD" and f1['組別B'] != "TBD" and f1['勝者'] == "尚未決定":
                    f1_win = st.selectbox("回報總冠軍", ["選擇總冠軍", f1['組別A'], f1['組別B']], key="sel_f1")
                    if f1_win != "選擇總冠軍":
                        # 修復：改用 .at 安全賦值
                        idx_f1 = df_team_matches[df_team_matches["場次編號"] == "F1"].index[0]
                        df_team_matches.at[idx_f1, "勝者"] = f1_win
                        
                        save_team_matches(df_team_matches)
                        st.rerun()
                            
            if is_admin:
                st.write("<br>", unsafe_allow_html=True)
                if st.button("🚨 重置淘汰賽程表 (重新抽籤)", type="secondary", use_container_width=True):
                    save_team_matches(None)
                    st.rerun()
