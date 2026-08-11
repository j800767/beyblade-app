import streamlit as st
import pandas as pd
import os
import random
from functools import cmp_to_key

# ==========================================
# 1. 基礎設定與檔案路徑
# ==========================================
st.set_page_config(page_title="第三屆 三重盃 戰鬥陀螺大賽", page_icon="💥", layout="wide")

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

# 載入個人賽資料
df_reg = load_registrations()
df_swiss = load_swiss_matches()
df_finals = load_finals()

# ==========================================
# 3. 個人賽瑞士輪演算與正確 H2H / SOS 機制
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
    
    # 計算對手強度分 SOS (Buchholz)：所擊敗過的對手的總勝場加總
    sos = {p_id: sum(wins[opp] for opp in defeated_opponents[p_id]) for p_id in range(1, 11)}

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

    ranked_ids = sorted(range(1, 11), key=cmp_to_key(compare_players), reverse=True)
    return wins, losses, sos, h2h, played_pairs, ranked_ids

def generate_next_round_pairs(current_round):
    wins, losses, _, _, played_pairs, ranked_ids = calculate_swiss_standings()
    
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
        i = 0
        p1 = pool[i]
        found = False
        for j in range(1, len(pool)):
            p2 = pool[j]
            if tuple(sorted([p1, p2])) not in played_pairs:
                new_pairs.append((p1, p2))
                pool.pop(j)
                pool.pop(i)
                found = True
                break
        if not found:
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
# 5. 通用 PK 加賽渲染模組（支援 2人, 3人, 4人平手）
# ==========================================
def render_pk_section(rank_target, candidates, player_map):
    st.error(f"⚠️ 觸發 PK 加賽條款！第 {rank_target} 名晉級門檻出現勝場與 SOS 完全同分：{', '.join([f'{p}號 {player_map[p]}' for p in candidates])}")
    st.info("📌 **PK 賽規則**：1 顆陀螺不換零件，進行【一分定勝負（1-Point Sudden Death）】單淘汰賽。")

    num_c = len(candidates)
    
    # 2 人同分 PK
    if num_c == 2:
        if is_admin:
            chosen = st.selectbox(
                f"選擇爭奪第 {rank_target} 名 PK 勝出的選手：",
                candidates,
                format_func=lambda x: f"{x}號 {player_map[x]}",
                key=f"pk_sel_2_{rank_target}"
            )
            if st.button(f"確定第 {rank_target} 名 PK 晉級者", key=f"btn_pk_2_{rank_target}", type="primary"):
                st.session_state[f"selected_rank_{rank_target}"] = chosen
                st.rerun()
        else:
            st.warning("等待管理員進行 PK 加賽裁決...")

    # 3 人同分 PK (方案 A：盲抽 1 人輪空)
    elif num_c == 3:
        st.markdown("""
        **方案 A 賽程流程**：
        1. 現場 3 位選手盲抽：兩位進行第一輪戰鬥，一位抽中輪空（直接進入 PK 決賽）。
        2. 第一輪 PK 勝者與輪空者進行決賽，勝者取得第 4 名晉級資格！
        """)
        if is_admin:
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                p_win1 = st.selectbox(
                    "選擇第一輪 PK 勝出的選手：",
                    candidates,
                    format_func=lambda x: f"{x}號 {player_map[x]}",
                    key=f"pk_sel_3_r1_{rank_target}"
                )
            with col_p2:
                chosen = st.selectbox(
                    f"選擇【PK 決賽】最終勝出（取得第 {rank_target} 名）的選手：",
                    candidates,
                    format_func=lambda x: f"{x}號 {player_map[x]}",
                    key=f"pk_sel_3_fin_{rank_target}"
                )
            if st.button(f"確定第 {rank_target} 名 PK 晉級者", key=f"btn_pk_3_{rank_target}", type="primary"):
                st.session_state[f"selected_rank_{rank_target}"] = chosen
                st.rerun()
        else:
            st.warning("等待管理員進行 PK 加賽裁決...")

    # 4 人同分 PK (4 人單淘汰)
    elif num_c == 4:
        st.markdown("""
        **4 人單淘汰賽流程**：
        1. 現場盲抽分成兩組進行準決賽：(A vs B) 與 (C vs D)。
        2. 兩組勝者進行【PK 決賽】，勝者取得晉級資格！
        """)
        if is_admin:
            col_a, col_b = st.columns(2)
            with col_a:
                win_sf1 = st.selectbox("準決賽 A 勝者：", candidates, format_func=lambda x: f"{x}號 {player_map[x]}", key=f"pk_sel_4_sfa_{rank_target}")
                win_sf2 = st.selectbox("準決賽 B 勝者：", candidates, format_func=lambda x: f"{x}號 {player_map[x]}", key=f"pk_sel_4_sfb_{rank_target}")
            with col_b:
                chosen = st.selectbox(
                    f"選擇【PK 決賽】最終勝出（取得第 {rank_target} 名）的選手：",
                    candidates,
                    format_func=lambda x: f"{x}號 {player_map[x]}",
                    key=f"pk_sel_4_fin_{rank_target}"
                )
            if st.button(f"確定第 {rank_target} 名 PK 晉級者", key=f"btn_pk_4_{rank_target}", type="primary"):
                st.session_state[f"selected_rank_{rank_target}"] = chosen
                st.rerun()
        else:
            st.warning("等待管理員進行 PK 加賽裁決...")

# ==========================================
# 6. 主介面：個人賽
# ==========================================
st.title("💥 9/12 第三屆 三重盃戰鬥陀螺大賽 - 個人賽")
st.caption("【個人賽】預賽搶 4 分制 | 限定 10 人 4 輪瑞士輪 | 冠軍獎品：UX-15 鮫鯊狂鱗")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 選手報名與抽籤", 
    "⚔️ 預賽：瑞士輪控制台", 
    "🗓️ 預賽賽程對戰表", 
    "🏆 決賽：四強單淘汰", 
    "📊 即時積分榜"
])

player_map = dict(zip(df_reg["編號"], df_reg["選手名稱"])) if not df_reg.empty else {}

# --- Tab 1: 報名 ---
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
            if st.button("🎲 滿 10 人！盲抽 1~10 號編號並生成第 1 輪對戰", type="primary", use_container_width=True):
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

# --- Tab 2: 控制台 ---
with tab2:
    st.header("⚔️ 預賽：4輪瑞士輪控制台 (常規賽採 4 分制)")
    if df_swiss is None or (df_reg["編號"] == 0).all():
        st.warning("⏳ 請先在「選手報名與抽籤」分頁集滿 10 人並完成盲抽！")
    else:
        current_max_round = int(df_swiss["輪次"].max())
        r_matches = df_swiss[df_swiss["輪次"] == current_max_round]
        completed_r_count = sum(1 for w in r_matches["勝者_編號"] if w != 0)
        
        col_header, col_undo = st.columns([3, 1.2])
        with col_header:
            st.info(f"### 📍 當前進行：第 {current_max_round} / 4 輪 (該輪進度：{completed_r_count} / 5 場)")
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
            p2_str = f"{p2_id}號 {player_map.get(p2_id, '')}"

            st.write(f"#### 🥊 【{row['組別標籤']}】 **🔴 {p1_str}** 🆚 **🔵 {p2_str}**")
            
            if is_admin:
                c1, c2, c3 = st.columns([2, 2, 3])
                with c1:
                    if st.button(f"🏆 {p1_str} 獲勝 (先滿4分)", key=f"r{current_max_round}_{m_idx}_p1", use_container_width=True, type="primary" if w_id == p1_id else "secondary"):
                        df_swiss.at[m_idx, "勝者_編號"] = p1_id
                        save_swiss_matches(df_swiss)
                        st.rerun()
                with c2:
                    if st.button(f"🏆 {p2_str} 獲勝 (先滿4分)", key=f"r{current_max_round}_{m_idx}_p2", use_container_width=True, type="primary" if w_id == p2_id else "secondary"):
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

# --- Tab 3: 對戰表 ---
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

# --- Tab 4: 決賽與全排名同分 PK 處理 ---
with tab4:
    st.header("🏆 四強單淘汰決賽")
    total_p = sum(1 for w in df_swiss["勝者_編號"] if w != 0) if df_swiss is not None else 0
    if df_swiss is None or total_p < 20:
        st.warning(f"⏳ 預賽尚未完成（已完成 {total_p}/20 場）")
    else:
        wins, losses, sos, h2h, _, ranked_ids = calculate_swiss_standings()

        # 自動檢查前 4 強名額門檻（第 4 名與後面是否有完全平手的情況）
        rank4_p = ranked_ids[3]
        
        # 找出與第 4 名「勝場相同 + SOS相同」的所有候選人
        candidates_4th = [p for p in ranked_ids if wins[p] == wins[rank4_p] and sos[p] == sos[rank4_p]]
        
        # 如果有多人爭奪第 4 名晉級門檻，且尚未紀錄手動 PK 結果
        if len(candidates_4th) > 1 and f"selected_rank_4" not in st.session_state:
            render_pk_section(4, candidates_4th, player_map)
        
        else:
            final_4 = []
            for r_idx in range(4):
                stored_key = f"selected_rank_{r_idx + 1}"
                if stored_key in st.session_state:
                    final_4.append(st.session_state[stored_key])
                else:
                    final_4.append(ranked_ids[r_idx])

            r1, r2, r3, r4 = final_4[0], final_4[1], final_4[2], final_4[3]

            if df_finals is None:
                finals_data = [
                    {"階段": "準決賽A", "選手1": str(player_map[r1]), "選手2": str(player_map[r4]), "勝者": "", "敗者": ""},
                    {"階段": "準決賽B", "選手1": str(player_map[r2]), "選手2": str(player_map[r3]), "勝者": "", "敗者": ""},
                    {"階段": "季軍賽", "選手1": "待定", "選手2": "待定", "勝者": "", "敗者": ""},
                    {"階段": "冠軍賽", "選手1": "待定", "選手2": "待定", "勝者": "", "敗者": ""}
                ]
                df_finals = pd.DataFrame(finals_data)
                save_finals(df_finals)

            for col in ["階段", "選手1", "選手2", "勝者", "敗者"]:
                df_finals[col] = df_finals[col].astype(str)

            sf_a_w = df_finals.loc[df_finals["階段"] == "準決賽A", "勝者"].values[0] if not df_finals.loc[df_finals["階段"] == "準決賽A", "勝者"].empty else ""
            sf_a_l = df_finals.loc[df_finals["階段"] == "準決賽A", "敗者"].values[0] if not df_finals.loc[df_finals["階段"] == "準決賽A", "敗者"].empty else ""
            sf_b_w = df_finals.loc[df_finals["階段"] == "準決賽B", "勝者"].values[0] if not df_finals.loc[df_finals["階段"] == "準決賽B", "勝者"].empty else ""
            sf_b_l = df_finals.loc[df_finals["階段"] == "準決賽B", "敗者"].values[0] if not df_finals.loc[df_finals["階段"] == "準決賽B", "敗者"].empty else ""

            updated_flag = False
            if sf_a_l and sf_b_l and sf_a_l != "" and sf_b_l != "":
                df_finals.loc[df_finals["階段"] == "季軍賽", "選手1"] = str(sf_a_l)
                df_finals.loc[df_finals["階段"] == "季軍賽", "選手2"] = str(sf_b_l)
                updated_flag = True
            if sf_a_w and sf_b_w and sf_a_w != "" and sf_b_w != "":
                df_finals.loc[df_finals["階段"] == "冠軍賽", "選手1"] = str(sf_a_w)
                df_finals.loc[df_finals["階段"] == "冠軍賽", "選手2"] = str(sf_b_w)
                updated_flag = True
            if updated_flag:
                save_finals(df_finals)

            st.subheader("🥊 1. 準決賽 (Semi-Finals)")
            col_sfa, col_sfb = st.columns(2)

            with col_sfa:
                st.markdown("##### ⚔️ 準決賽 A (第 1 名 vs 第 4 名)")
                p1_a, p2_a = str(player_map[r1]), str(player_map[r4])
                st.write(f"🔴 **{p1_a}**  VS  🔵 **{p2_a}**")
                if is_admin:
                    opts_a = ["請選擇勝者...", p1_a, p2_a]
                    curr_a = sf_a_w if sf_a_w in opts_a else "請選擇勝者..."
                    sel_a = st.selectbox("選擇準決賽 A 勝者：", opts_a, index=opts_a.index(curr_a), key="sf_a_sel")
                    if sel_a != "請選擇勝者..." and sel_a != sf_a_w:
                        loser_a = p2_a if sel_a == p1_a else p1_a
                        df_finals.loc[df_finals["階段"] == "準決賽A", "勝者"] = str(sel_a)
                        df_finals.loc[df_finals["階段"] == "準決賽A", "敗者"] = str(loser_a)
                        save_finals(df_finals)
                        st.rerun()
                else:
                    st.write(f"勝者：`{sf_a_w if sf_a_w else '未決定'}`")

            with col_sfb:
                st.markdown("##### ⚔️ 準決賽 B (第 2 名 vs 第 3 名)")
                p1_b, p2_b = str(player_map[r2]), str(player_map[r3])
                st.write(f"🔴 **{p1_b}**  VS  🔵 **{p2_b}**")
                if is_admin:
                    opts_b = ["請選擇勝者...", p1_b, p2_b]
                    curr_b = sf_b_w if sf_b_w in opts_b else "請選擇勝者..."
                    sel_b = st.selectbox("選擇準決賽 B 勝者：", opts_b, index=opts_b.index(curr_b), key="sf_b_sel")
                    if sel_b != "請選擇勝者..." and sel_b != sf_b_w:
                        loser_b = p2_b if sel_b == p1_b else p1_b
                        df_finals.loc[df_finals["階段"] == "準決賽B", "勝者"] = str(sel_b)
                        df_finals.loc[df_finals["階段"] == "準決賽B", "敗者"] = str(loser_b)
                        save_finals(df_finals)
                        st.rerun()
                else:
                    st.write(f"勝者：`{sf_b_w if sf_b_w else '未決定'}`")

            st.write("---")

            st.subheader("🥇 2. 總決賽 (Finals)")
            col_3rd, col_1st = st.columns(2)

            p3_1 = str(df_finals.loc[df_finals["階段"] == "季軍賽", "選手1"].values[0])
            p3_2 = str(df_finals.loc[df_finals["階段"] == "季軍賽", "選手2"].values[0])
            p3_w = str(df_finals.loc[df_finals["階段"] == "季軍賽", "勝者"].values[0])

            p1_1 = str(df_finals.loc[df_finals["階段"] == "冠軍賽", "選手1"].values[0])
            p1_2 = str(df_finals.loc[df_finals["階段"] == "冠軍賽", "選手2"].values[0])
            p1_w = str(df_finals.loc[df_finals["階段"] == "冠軍賽", "勝者"].values[0])

            with col_3rd:
                st.markdown("##### 🥉 季軍賽 (3rd Place Match)")
                if p3_1 != "待定" and p3_2 != "待定":
                    st.write(f"🔴 **{p3_1}**  VS  🔵 **{p3_2}**")
                    if is_admin:
                        opts_3 = ["請選擇勝者...", p3_1, p3_2]
                        curr_3 = p3_w if p3_w in opts_3 else "請選擇勝者..."
                        sel_3 = st.selectbox("選擇季軍賽勝者（第 3 名）：", opts_3, index=opts_3.index(curr_3), key="p3_sel")
                        if sel_3 != "請選擇勝者..." and sel_3 != p3_w:
                            loser_3 = p3_2 if sel_3 == p3_1 else p3_1
                            df_finals.loc[df_finals["階段"] == "季軍賽", "勝者"] = str(sel_3)
                            df_finals.loc[df_finals["階段"] == "季軍賽", "敗者"] = str(loser_3)
                            save_finals(df_finals)
                            st.rerun()
                    else:
                        st.write(f"勝者：`{p3_w if p3_w else '未決定'}`")
                else:
                    st.info("⏳ 等待準決賽兩場結果出爐...")

            with col_1st:
                st.markdown("##### 👑 冠軍賽 (Championship Match)")
                if p1_1 != "待定" and p1_2 != "待定":
                    st.write(f"🔴 **{p1_1}**  VS  🔵 **{p1_2}**")
                    if is_admin:
                        opts_1 = ["請選擇勝者...", p1_1, p1_2]
                        curr_1 = p1_w if p1_w in opts_1 else "請選擇勝者..."
                        sel_1 = st.selectbox("選擇冠軍賽勝者（第 1 名）：", opts_1, index=opts_1.index(curr_1), key="p1_sel")
                        if sel_1 != "請選擇勝者..." and sel_1 != p1_w:
                            loser_1 = p1_2 if sel_1 == p1_1 else p1_1
                            df_finals.loc[df_finals["階段"] == "冠軍賽", "勝者"] = str(sel_1)
                            df_finals.loc[df_finals["階段"] == "冠軍賽", "敗者"] = str(loser_1)
                            save_finals(df_finals)
                            st.rerun()
                    else:
                        st.write(f"勝者：`{p1_w if p1_w else '未決定'}`")
                else:
                    st.info("⏳ 等待準決賽兩場結果出爐...")

            if p1_w and p3_w and p1_w != "" and p3_w != "":
                st.write("---")
                st.balloons()
                st.subheader("🎉 個人賽最終前 4 強榮譽榜")
                
                champion = df_finals.loc[df_finals["階段"] == "冠軍賽", "勝者"].values[0]
                runner_up = df_finals.loc[df_finals["階段"] == "冠軍賽", "敗者"].values[0]
                third_place = df_finals.loc[df_finals["階段"] == "季軍賽", "勝者"].values[0]
                fourth_place = df_finals.loc[df_finals["階段"] == "季軍賽", "敗者"].values[0]

                st.success(f"""
                * 🥇 **冠軍**：{champion} （獲得獎品：UX-15 鮫鯊狂鱗）
                * 🥈 **亞軍**：{runner_up}
                * 🥉 **季軍**：{third_place}
                * 🏅 **殿軍**：{fourth_place}
                """)

# --- Tab 5: 積分榜 ---
with tab5:
    st.header("📊 即時積分榜")
    if df_swiss is not None:
        wins, losses, sos, h2h, _, ranked_ids = calculate_swiss_standings()
        table_data = []
        for rank, p_id in enumerate(ranked_ids, 1):
            table_data.append({
                "排名": f"第 {rank} 名",
                "編號": f"{p_id} 號",
                "選手名稱": player_map.get(p_id, ""),
                "勝場": wins[p_id],
                "敗場": losses[p_id],
                "SOS 對手強度分": sos[p_id]
            })
        st.table(table_data)
