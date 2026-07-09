import streamlit as st
import pandas as pd
import numpy as np
import math
import os
import random

# ==========================================
# 1. 基礎設定與檔案路徑
# ==========================================
st.set_page_config(page_title="三重盃 陀螺大賽管理系統", page_icon="💥", layout="wide")

REG_FILE = "players_registration.csv"          # 個人賽檔案
MATCH_FILE = "current_matches.csv"             # 瑞士輪對戰檔案
TEAM_DATA_FILE = "team_players_registration.csv" # 團體賽名單檔案
TEAM_MATCH_FILE = "team_matches.csv"           # 團體賽淘汰賽賽程檔案

ADMIN_PASSWORD = "admin"

# ==========================================
# 2. 資料存取核心函式
# ==========================================
def load_registrations():
    if os.path.exists(REG_FILE):
        df = pd.read_csv(REG_FILE)
        df = df.fillna("")
        if "已對戰選手" in df.columns:
            df["已對戰選手"] = df["已對戰選手"].astype(str)
        return df
    return pd.DataFrame(columns=[
        "選手名稱", 
        "陀螺1_上蓋", "陀螺1_固鎖", "陀螺1_軸心",
        "陀螺2_上蓋", "陀螺2_固鎖", "陀螺2_軸心",
        "陀螺3_上蓋", "陀螺3_固鎖", "陀螺3_軸心",
        "陀螺4_上蓋", "陀螺4_固鎖", "陀螺4_軸心",
        "勝場", "對手件分", "總積分", "已對戰選手", "退賽"
    ])

def save_registrations(df):
    df.to_csv(REG_FILE, index=False, encoding="utf-8-sig")

def load_matches():
    if os.path.exists(MATCH_FILE):
        df = pd.read_csv(MATCH_FILE)
        df = df.fillna("")
        return df
    return None

def save_matches(df):
    if df is not None:
        df.to_csv(MATCH_FILE, index=False, encoding="utf-8-sig")
    elif os.path.exists(MATCH_FILE):
        os.remove(MATCH_FILE)

def load_team_data():
    if os.path.exists(TEAM_DATA_FILE): 
        df = pd.read_csv(TEAM_DATA_FILE)
        df = df.fillna("")
        return df
    columns = [
        "組別", "隊員別", "選手名稱", 
        "陀螺1_上蓋", "陀螺1_固鎖", "陀螺1_軸心", 
        "陀螺2_上蓋", "陀螺2_固鎖", "陀螺2_軸心"
    ]
    default_rows = []
    for team in ["A組", "B組", "C組", "D組"]:
        default_rows.append({"組別": team, "隊員別": "隊員 1", "選手名稱": ""})
        default_rows.append({"組別": team, "隊員別": "隊員 2", "選手名稱": ""})
    df = pd.DataFrame(default_rows, columns=columns)
    df = df.fillna("")
    return df

def save_team_data(df): 
    df.to_csv(TEAM_DATA_FILE, index=False, encoding="utf-8-sig")

def load_team_matches():
    if os.path.exists(TEAM_MATCH_FILE):
        df = pd.read_csv(TEAM_MATCH_FILE)
        df = df.fillna("")
        return df
    return None

def save_team_matches(df):
    if df is not None:
        df.to_csv(TEAM_MATCH_FILE, index=False, encoding="utf-8-sig")
    elif os.path.exists(TEAM_MATCH_FILE):
        os.remove(TEAM_MATCH_FILE)

# 載入初始資料
df_reg = load_registrations()
df_matches = load_matches()
df_teams = load_team_data()
df_team_matches = load_team_matches()

# ==========================================
# 3. 側邊欄：權限與賽制切換
# ==========================================
st.sidebar.header("🔑 管理者驗證專區")
admin_input = st.sidebar.text_input("輸入管理密碼", type="password")
is_admin = (admin_input == ADMIN_PASSWORD)

if is_admin:
    st.sidebar.success("🔓 管理員權限已開啟")
else:
    st.sidebar.info("🔒 目前為訪客唯讀模式")

st.sidebar.write("---")
st.sidebar.header("🏆 賽制系統切換")
main_mode = st.sidebar.radio("選擇要管理的賽制：", ["個人賽 (瑞士輪)", "雙人團體賽 (獨立區)"])

RESTRICTED_KEYWORDS = ["空力天馬", "魔導神杖", "鮫鯊狂鱗", "pegasus", "rod", "shark"]

# ==========================================
# 4. 模式一：個人賽 (瑞士輪系統 - 4選3版本)
# ==========================================
if main_mode == "個人賽 (瑞士輪)":
    st.title("💥 三重盃 戰鬥陀螺個人賽（瑞士輪系統）")
    
    tabs = st.tabs(["📝 選手登記與防呆", "⚔️ 瑞士輪對戰與計分", "📊 當前排名總覽"])
    
    # --- Tab 1: 個人賽登記 ---
    with tabs[0]:
        st.header("選手改造登記（4選3 規則）")
        st.markdown("⚠️ **戰術備戰規則**：每位選手可登記 **4 顆陀螺**，比賽時從中挑選 3 顆上場。")
        st.markdown("⚠️ **禁卡表限制**：登記的 4 顆陀螺中，【魔導神杖 / 鮫鯊狂鱗 / 空力天馬】**最多只能出現 1 顆**！且 4 顆陀螺的所有零件完全不可重複。")
        
        if is_admin:
            with st.form("registration_form", clear_on_submit=True):
                col_name, col_b1, col_b2, col_b3, col_b4 = st.columns([1.2, 2, 2, 2, 2])
                
                with col_name:
                    name = st.text_input("選手名稱*")
                with col_b1:
                    st.markdown("**陀螺 1**")
                    b1 = st.text_input("上蓋(Blade) 1")
                    r1 = st.text_input("固鎖(Ratchet) 1")
                    bit1 = st.text_input("軸心(Bit) 1")
                with col_b2:
                    st.markdown("**陀螺 2**")
                    b2 = st.text_input("上蓋(Blade) 2")
                    r2 = st.text_input("固鎖(Ratchet) 2")
                    bit2 = st.text_input("軸心(Bit) 2")
                with col_b3:
                    st.markdown("**陀螺 3**")
                    b3 = st.text_input("上蓋(Blade) 3")
                    r3 = st.text_input("固鎖(Ratchet) 3")
                    bit3 = st.text_input("軸心(Bit) 3")
                with col_b4:
                    st.markdown("**陀螺 4**")
                    b4 = st.text_input("上蓋(Blade) 4")
                    r4 = st.text_input("固鎖(Ratchet) 4")
                    bit4 = st.text_input("軸心(Bit) 4")
                    
                submit_reg = st.form_submit_button("📥 驗證並新增登記", use_container_width=True)
                
                if submit_reg:
                    if not name.strip():
                        st.error("❌ 登記失敗：選手名稱不能為空！")
                    elif name.strip() in df_reg["選手名稱"].values:
                        st.error(f"❌ 登記失敗：選手【{name}】已經登記過了！")
                    else:
                        blades = [b1, b2, b3, b4]
                        ratchets = [r1, r2, r3, r4]
                        bits = [bit1, bit2, bit3, bit4]
                        
                        if len(set(ratchets)) < 4 or len(set(bits)) < 4:
                            st.error("❌ 登記失敗：個人的 4 顆陀螺中「固鎖(Ratchet)」或「軸心(Bit)」有零件重複，請更換！")
                        else:
                            rest_count = sum(1 for b in blades if any(k in str(b).lower() for k in RESTRICTED_KEYWORDS))
                            if rest_count > 1:
                                st.error(f"❌ 違規！在登記的 4 顆陀螺中偵測到 {rest_count} 顆限制零件（神杖/鮫鯊/天馬），每人最多只能帶 1 顆備戰！")
                            else:
                                new_player = {
                                    "選手名稱": name.strip(),
                                    "陀螺1_上蓋": b1, "陀螺1_固鎖": r1, "陀螺1_軸心": bit1,
                                    "陀螺2_上蓋": b2, "陀螺2_固鎖": r2, "陀螺2_軸心": bit2,
                                    "陀螺3_上蓋": b3, "陀螺3_固鎖": r3, "陀螺3_軸心": bit3,
                                    "陀螺4_上蓋": b4, "陀螺4_固鎖": r4, "陀螺4_軸心": bit4,
                                    "勝場": 0, "對手件分": 0, "總積分": 0, "已對戰選手": "", "退賽": "否"
                                }
                                df_reg = pd.concat([df_reg, pd.DataFrame([new_player])], ignore_index=True)
                                save_registrations(df_reg)
                                st.success(f"🎉 選手【{name}】成功通過 4 選 3 禁卡表驗證，完成登記！")
                                st.rerun()
        else:
            st.warning("請在側邊欄輸入管理密碼以進行選手登記。")
            
        st.write("---")
        st.subheader(f"👥 已登記選手名單 (共 {len(df_reg)} 人)")
        if not df_reg.empty:
            display_cols = ["選手名稱", "陀螺1_上蓋", "陀螺2_上蓋", "陀螺3_上蓋", "陀螺4_上蓋", "退賽"]
            for c in display_cols:
                if c not in df_reg.columns: df_reg[c] = ""
            st.dataframe(df_reg[display_cols], use_container_width=True)
            
            if is_admin:
                st.markdown("#### ⚙️ 選手狀態管理")
                mod_player = st.selectbox("選擇要處理的選手", df_reg["選手名稱"].values)
                c_quit, c_del = st.columns(2)
                with c_quit:
                    if st.button("🚪 設定該選手 退賽/取消退賽", use_container_width=True):
                        idx = df_reg[df_reg["選手名稱"] == mod_player].index[0]
                        current_status = df_reg.at[idx, "退賽"]
                        df_reg.at[idx, "退賽"] = "是" if current_status != "是" else "否"
                        save_registrations(df_reg)
                        st.success(f"變更成功！重新載入中...")
                        st.rerun()
                with c_del:
                    if st.button("🗑️ 完全刪除該選手", use_container_width=True):
                        df_reg = df_reg[df_reg["選手名稱"] != mod_player]
                        save_registrations(df_reg)
                        st.warning("選手已從資料庫移除。")
                        st.rerun()

    # --- Tab 2: 瑞士輪對戰區 ---
    with tabs[1]:
        st.header("⚔️ 瑞士輪賽程與成績回報")
        active_players = df_reg[df_reg["退賽"] != "是"]["選手名稱"].tolist()
        
        if len(active_players) < 2:
            st.info("目前參賽人數不足 2 人，無法生成對戰。")
        else:
            if df_matches is None:
                st.success("🛰️ 目前沒有進行中的輪次。")
                if is_admin:
                    if st.button("🎲 依積分自動生成下一輪對戰 (Swiss Pairing)", type="primary", use_container_width=True):
                        players_sorted = df_reg[df_reg["退賽"] != "是"].sort_values(by=["總積分", "勝場"], ascending=False)["選手名稱"].tolist()
                        paired = set()
                        matches = []
                        
                        for i in range(len(players_sorted)):
                            p1 = players_sorted[i]
                            if p1 in paired: continue
                            
                            p1_hist_str = str(df_reg[df_reg["選手名稱"] == p1]["已對戰選手"].values[0])
                            p1_history = p1_hist_str.replace(";", ",").split(",")
                            p1_history = [p.strip() for p in p1_history if p.strip() and p != "nan"]
                            
                            found_opponent = False
                            for j in range(i + 1, len(players_sorted)):
                                p2 = players_sorted[j]
                                if p2 in paired: continue
                                
                                if p2 not in p1_history:
                                    matches.append({"選手A": p1, "選手B": p2, "勝者": "尚未決定"})
                                    paired.add(p1)
                                    paired.add(p2)
                                    found_opponent = True
                                    break
                            
                            if not found_opponent:
                                for j in range(i + 1, len(players_sorted)):
                                    p2 = players_sorted[j]
                                    if p2 not in paired:
                                        matches.append({"選手A": p1, "選手B": p2, "勝者": "尚未決定"})
                                        paired.add(p1)
                                        paired.add(p2)
                                        found_opponent = True
                                        break
                                        
                        for p in players_sorted:
                            if p not in paired:
                                matches.append({"選手A": p, "選手B": "BYE (輪空)", "勝者": p})
                                paired.add(p)
                                
                        df_matches = pd.DataFrame(matches)
                        save_matches(df_matches)
                        st.rerun()
            else:
                st.subheader("🔥 當前輪次對戰表")
                for idx, row in df_matches.iterrows():
                    pA, pB, winner = row["選手A"], row["選手B"], row["勝者"]
                    with st.container():
                        c_m, c_w = st.columns([3, 1])
                        with c_m:
                            st.write(f"**場次 {idx+1}：** {pA} 🆚 {pB} ➡️ **結果：** `{winner}`")
                        with c_w:
                            if is_admin and pB != "BYE (輪空)" and winner == "尚未決定":
                                win_choice = st.selectbox(f"回報場次 {idx+1}", ["選擇勝者", pA, pB], key=f"match_{idx}")
                                if win_choice != "選擇勝者":
                                    df_matches.at[idx, "勝者"] = win_choice
                                    save_matches(df_matches)
                                    st.rerun()
                        st.write("---")
                        
                if is_admin:
                    all_reported = all(df_matches["勝者"] != "尚未決定")
                    if all_reported:
                        if st.button("🏁 確認本輪所有成績，結算並寫入積分表", type="primary", use_container_width=True):
                            for _, match in df_matches.iterrows():
                                pA, pB, winner = match["選手A"], match["選手B"], match["勝者"]
                                
                                if pB == "BYE (輪空)":
                                    idxA = df_reg[df_reg["選手名稱"] == pA].index[0]
                                    df_reg.at[idxA, "勝場"] += 1
                                    df_reg.at[idxA, "總積分"] += 3
                                else:
                                    idxA = df_reg[df_reg["選手名稱"] == pA].index[0]
                                    idxB = df_reg[df_reg["選手名稱"] == pB].index[0]
                                    
                                    histA = str(df_reg.at[idxA, "已對戰選手"])
                                    histA = "" if histA == "nan" else histA
                                    df_reg.at[idxA, "已對戰選手"] = f"{histA},{pB}" if histA else pB
                                    
                                    histB = str(df_reg.at[idxB, "已對戰選手"])
                                    histB = "" if histB == "nan" else histB
                                    df_reg.at[idxB, "已對戰選手"] = f"{histB},{pA}" if histB else pA
                                    
                                    if winner == pA:
                                        df_reg.at[idxA, "勝場"] += 1
                                        df_reg.at[idxA, "總積分"] += 3
                                    elif winner == pB:
                                        df_reg.at[idxB, "勝場"] += 1
                                        df_reg.at[idxB, "總積分"] += 3
                                        
                            for idx, row in df_reg.iterrows():
                                enemies_str = str(row["已對戰選手"]).replace(";", ",")
                                enemies = enemies_str.split(",")
                                enemy_points = 0
                                for e in enemies:
                                    e_clean = e.strip()
                                    if e_clean and e_clean != "nan" and e_clean in df_reg["選手名稱"].values:
                                        enemy_points += df_reg[df_reg["選手名稱"] == e_clean]["總積分"].values[0]
                                df_reg.at[idx, "對手件分"] = enemy_points
                                
                            save_registrations(df_reg)
                            save_matches(None)
                            st.success("分數結算成功！本輪賽事結束。")
                            st.rerun()
                    else:
                        st.info("💡 線上還有場次尚未回報結果，請管理員評分完畢後即可結算本輪。")
                        
                    if st.button("🚨 強制取消並重置本輪賽程"):
                        save_matches(None)
                        st.warning("本輪賽程已作廢。")
                        st.rerun()

    # --- Tab 3: 排行榜 ---
    with tabs[2]:
        st.header("📊 賽事當前即時排行榜")
        if not df_reg.empty:
            leaderboard = df_reg.sort_values(by=["總積分", "對手件分", "勝場"], ascending=False).reset_index(drop=True)
            leaderboard.index += 1
            st.dataframe(leaderboard[["選手名稱", "勝場", "對手件分", "總積分", "退賽"]], use_container_width=True)
        else:
            st.info("尚無選手資料。")

# ==========================================
# 5. 模式二：雙人團體賽 (獨立管理專區 + 淘汰賽賽程表)
# ==========================================
elif main_mode == "雙人團體賽 (獨立區)":
    st.title("🤝 三重盃 雙人團體賽獨立登記與淘汰賽系統")
    
    team_tabs = st.tabs(["📝 4組選手名單配置", "🏆 團體淘汰賽賽程表"])
    
    # --- 團體賽分頁 1：名單配置 ---
    with team_tabs[0]:
        st.markdown("### 📝 賽制規則：共 4 個組，每組固定 2 人，每人登記 2 顆陀螺。")
        st.markdown("⚠️ **整組禁卡限制**：該組兩位隊員（**共 4 顆陀螺**）中，【魔導神杖 / 鮫鯊狂鱗 / 空力天馬】**總共只能出現 1 顆**！且個人配置的固鎖與軸心不可重複。")
        
        def validate_team_setup(team_name, p1_data, p2_data):
            if not p1_data["name"].strip() or not p2_data["name"].strip():
                return False, f"❌ {team_name} 驗證失敗：兩位隊員的「選手名稱」皆不能留空！"
                
            p1_ratchets = [r for r in [p1_data["r1"], p1_data["r2"]] if r.strip()]
            p1_bits = [b for b in [p1_data["bit1"], p1_data["bit2"]] if b.strip()]
            if len(p1_ratchets) != len(set(p1_ratchets)): return False, f"❌ {team_name} 驗證失敗：{p1_data['name']} 的「固鎖(Ratchet)」重複零件！"
            if len(p1_bits) != len(set(p1_bits)): return False, f"❌ {team_name} 驗證失敗：{p1_data['name']} 的「軸心(Bit)」重複零件！"
            
            p2_ratchets = [r for r in [p2_data["r1"], p2_data["r2"]] if r.strip()]
            p2_bits = [b for b in [p2_data["bit1"], p2_data["bit2"]] if b.strip()]
            if len(p2_ratchets) != len(set(p2_ratchets)): return False, f"❌ {team_name} 驗證失敗：{p2_data['name']} 的「固鎖(Ratchet)」重複零件！"
            if len(p2_bits) != len(set(p2_bits)): return False, f"❌ {team_name} 驗證失敗：{p2_data['name']} 的「軸心(Bit)」重複零件！"

            all_blades = [
                str(p1_data["b1"]).lower(), str(p1_data["b2"]).lower(),
                str(p2_data["b1"]).lower(), str(p2_data["b2"]).lower()
            ]
            
            restricted_count = 0
            detected_details = []
            for b in all_blades:
                for keyword in RESTRICTED_KEYWORDS:
                    if keyword in b:
                        restricted_count += 1
                        detected_details.append(b)
                        break
                        
            if restricted_count > 1:
                return False, f"❌ {team_name} 禁卡表違規！該組 4 顆陀螺中偵測到 {restricted_count} 顆限制零件 {detected_details}（全組最多只能裝配 1 顆【魔導神杖/鮫鯊狂鱗/空力天馬】）！"
                
            return True, ""

        st.write("---")
        form_cols = st.columns(2)
        ui_inputs = {}

        for idx, team in enumerate(["A組", "B組", "C組", "D組"]):
            with form_cols[idx % 2]:
                st.subheader(f"🛡️ 團體賽 - {team} 配置面板")
                
                row_p1 = df_teams[(df_teams["組別"] == team) & (df_teams["隊員別"] == "隊員 1")].iloc[0]
                row_p2 = df_teams[(df_teams["組別"] == team) & (df_teams["隊員別"] == "隊員 2")].iloc[0]
                
                st.markdown(f"**👤 隊員 1 配置**")
                p1_name = st.text_input(f"選手名稱 (隊員1)", value=str(row_p1["選手名稱"]), key=f"{team}_p1_name", disabled=not is_admin)
                c1, c2 = st.columns(2)
                with c1:
                    p1_b1 = st.text_input("陀螺1_上蓋", value=str(row_p1["陀螺1_上蓋"]), key=f"{team}_p1_b1", disabled=not is_admin)
                    p1_r1 = st.text_input("陀螺1_固鎖", value=str(row_p1["陀螺1_固鎖"]), key=f"{team}_p1_r1", disabled=not is_admin)
                    p1_bit1 = st.text_input("陀螺1_軸心", value=str(row_p1["陀螺1_軸心"]), key=f"{team}_p1_bit1", disabled=not is_admin)
                with c2:
                    p1_b2 = st.text_input("陀螺2_上蓋", value=str(row_p1["陀螺2_上蓋"]), key=f"{team}_p1_b2", disabled=not is_admin)
                    p1_r2 = st.text_input("陀螺2_固鎖", value=str(row_p1["陀螺2_固鎖"]), key=f"{team}_p1_r2", disabled=not is_admin)
                    p1_bit2 = st.text_input("陀螺2_軸心", value=str(row_p1["陀螺2_軸心"]), key=f"{team}_p1_bit2", disabled=not is_admin)
                    
                st.markdown(f"**👤 隊員 2 配置**")
                p2_name = st.text_input(f"選手名稱 (隊員2)", value=str(row_p2["選手名稱"]), key=f"{team}_p2_name", disabled=not is_admin)
                c3, c4 = st.columns(2)
                with c3:
                    p2_b1 = st.text_input("陀螺1_上蓋", value=str(row_p2["陀螺1_上蓋"]), key=f"{team}_p2_b1", disabled=not is_admin)
                    p2_r1 = st.text_input("陀螺1_固鎖", value=str(row_p2["陀螺1_固鎖"]), key=f"{team}_p2_r1", disabled=not is_admin)
                    p2_bit1 = st.text_input("陀螺1_軸心", value=str(row_p2["陀螺1_軸心"]), key=f"{team}_p2_bit1", disabled=not is_admin)
                with c4:
                    p2_b2 = st.text_input("陀螺2_上蓋", value=str(row_p2["陀螺2_上蓋"]), key=f"{team}_p2_b2", disabled=not is_admin)
                    p2_r2 = st.text_input("陀螺2_固鎖", value=str(row_p2["陀螺2_固鎖"]), key=f"{team}_p2_r2", disabled=not is_admin)
                    p2_bit2 = st.text_input("陀螺2_軸心", value=str(row_p2["陀螺2_軸心"]), key=f"{team}_p2_bit2", disabled=not is_admin)
                    
                ui_inputs[team] = {
                    "p1": {"name": p1_name, "b1": p1_b1, "r1": p1_r1, "bit1": p1_bit1, "b2": p1_b2, "r2": p1_r2, "bit2": p1_bit2},
                    "p2": {"name": p2_name, "b1": p2_b1, "r1": p2_r1, "bit1": p2_bit1, "b2": p2_b2, "r2": p2_r2, "bit2": p2_bit2}
                }
                st.write("---")

        if is_admin:
            if st.button("💾 驗證禁卡表並儲存 4 組團體賽名單", type="primary", use_container_width=True):
                passed_all = True
                for team in ["A組", "B組", "C組", "D組"]:
                    p1_in = ui_inputs[team]["p1"]
                    p2_in = ui_inputs[team]["p2"]
                    if not p1_in["name"].strip() and not p2_in["name"].strip():
                        continue
                    success, err_msg = validate_team_setup(team, p1_in, p2_in)
                    if not success:
                        st.error(err_msg)
                        passed_all = False
                
                if passed_all:
                    new_rows = []
                    for team in ["A組", "B組", "C組", "D組"]:
                        p1 = ui_inputs[team]["p1"]
                        p2 = ui_inputs[team]["p2"]
                        new_rows.append({
                            "組別": team, "隊員別": "隊員 1", "選手名稱": p1["name"].strip(),
                            "陀螺1_上蓋": p1["b1"], "陀螺1_固鎖": p1["r1"], "陀螺1_軸心": p1["bit1"],
                            "陀螺2_上蓋": p1["b2"], "陀螺2_固鎖": p1["r2"], "陀螺2_軸心": p1["bit2"]
                        })
                        new_rows.append({
                            "組別": team, "隊員別": "隊員 2", "選手名稱": p2["name"].strip(),
                            "陀螺1_上蓋": p2["b1"], "陀螺1_固鎖": p2["r1"], "陀螺1_軸心": p2["bit1"],
                            "陀螺2_上蓋": p2["b2"], "陀螺2_固鎖": p2["r2"], "陀螺2_軸心": p2["bit2"]
                        })
                    df_to_save = pd.DataFrame(new_rows)
                    save_team_data(df_to_save)
                    st.success("🎉 團體賽名單儲存成功！")
                    st.rerun()

        st.write("---")
        st.subheader("📊 當前已儲存的團體賽選手名單總覽")
        st.dataframe(df_teams, use_container_width=True)

        # ====== 💥 新增：團體賽名單管理控制台 (刪除與重置功能) ======
        if is_admin:
            st.write("---")
            st.subheader("⚙️ 團體賽名單管理控制台")
            st.markdown("💡 選手若不小心打錯零件或名字，可在下方單獨清除該組資料重新填寫。")
            
            del_col1, del_col2 = st.columns([2, 1])
            with del_col1:
                target_team = st.selectbox("選擇要刪除並清空的組別", ["A組", "B組", "C組", "D組"])
            with del_col2:
                st.markdown("<br>", unsafe_allow_html=True) # 稍微對齊按鈕
                if st.button(f"🗑️ 清空 {target_team} 資料", use_container_width=True):
                    # 將選定組別的文字全部刷白空字串
                    df_teams.loc[df_teams["組別"] == target_team, [
                        "選手名稱", "陀螺1_上蓋", "陀螺1_固鎖", "陀螺1_軸心", 
                        "陀螺2_上蓋", "陀螺2_固鎖", "陀2_軸心"
                    ]] = ""
                    # 舊欄位名稱防呆，確保所有衍生欄位一致
                    for col in df_teams.columns:
                        if col != "組別" and col != "隊員別":
                            df_teams.loc[df_teams["組別"] == target_team, col] = ""
                            
                    save_team_data(df_teams)
                    st.warning(f"已成功清除【{target_team}】的所有選手及陀螺登記資料。")
                    st.rerun()
            
            if st.button("🚨 一鍵重置並【清空所有 4 組】名單資料", type="secondary", use_container_width=True):
                # 完全重設為全新的空表格
                columns = [
                    "組別", "隊員別", "選手名稱", 
                    "陀螺1_上蓋", "陀螺1_固鎖", "陀螺1_軸心", 
                    "陀螺2_上蓋", "陀螺2_固鎖", "陀螺2_軸心"
                ]
                default_rows = []
                for team in ["A組", "B組", "C組", "D組"]:
                    default_rows.append({"組別": team, "隊員別": "隊員 1", "選手名稱": ""})
                    default_rows.append({"組別": team, "隊員別": "隊員 2", "選手名稱": ""})
                df_reset = pd.DataFrame(default_rows, columns=columns)
                df_reset = df_reset.fillna("")
                save_team_data(df_reset)
                st.error("💥 團體賽所有組別名單已完全清空重置！")
                st.rerun()

    # --- 團體賽分頁 2：單敗淘汰賽賽程區 ---
    with team_tabs[1]:
        st.header("🏆 4強團體單敗淘汰賽程")
        
        def get_team_members_str(team_code):
            if not team_code or team_code == "TBD": return "(等待晉級中)"
            members = df_teams[df_teams["組別"] == team_code]["選手名稱"].tolist()
            members_clean = [m for m in members if m.strip()]
            return f"({ ' ＆ '.join(members_clean) })" if members_clean else "(未登記選手)"

        if df_team_matches is None:
            st.info("💡 目前尚無淘汰賽賽程。點擊下方按鈕將 A, B, C, D 四組隨機分配至準決賽。")
            if is_admin:
                if st.button("🎲 隨機抽籤生成 4強淘汰賽程表", type="primary", use_container_width=True):
                    teams_list = ["A組", "B組", "C組", "D組"]
                    random.shuffle(teams_list)
                    
                    bracket_data = [
                        {"場次編號": "SF1", "階段": "準決賽 1", "組別A": teams_list[0], "組別B": teams_list[1], "勝者": "尚未決定"},
                        {"場次編號": "SF2", "階段": "準決賽 2", "組別A": teams_list[2], "組別B": teams_list[3], "勝者": "尚未決定"},
                        {"場次編號": "F1",  "階段": "總決賽",    "組別A": "TBD",       "組別B": "TBD",       "勝者": "尚未決定"}
                    ]
                    df_team_matches = pd.DataFrame(bracket_data)
                    save_team_matches(df_team_matches)
                    st.success("🎯 淘汰賽程樹狀表已成功生成！")
                    st.rerun()
        else:
            sf1 = df_team_matches[df_team_matches["場次編號"] == "SF1"].iloc[0]
            sf2 = df_team_matches[df_team_matches["場次編號"] == "SF2"].iloc[0]
            f1 = df_team_matches[df_team_matches["場次編號"] == "F1"].iloc[0]
            
            st.markdown("### 📊 賽程樹狀總覽")
            b_col1, b_col2, b_col3 = st.columns(3)
            
            with b_col1:
                st.info(f"🧱 **{sf1['階段']}**\n\n【{sf1['組別A']}】 vs 【{sf1['組別B']}】\n\n ➡️ 勝者：`{sf1['勝者']}`")
                st.info(f"🧱 **{sf2['階段']}**\n\n【{sf2['組別A']}】 vs 【{sf2['組別B']}】\n\n ➡️ 勝者：`{sf2['勝者']}`")
                
            with b_col2:
                st.markdown("<br><br><br><br>", unsafe_allow_html=True)
                st.warning(f"👑 **{f1['階段']}**\n\n【{f1['組別A']}】 vs 【{f1['組別B']}】\n\n ➡️ 總冠軍：`{f1['勝者']}`")
                
            with b_col3:
                st.markdown("<br><br><br><br>", unsafe_allow_html=True)
                if f1['勝者'] != "尚未決定":
                    st.balloons()
                    st.success(f"🎉 恭喜本屆三重盃團體賽總冠軍：\n\n### 🏆 {f1['勝者']} {get_team_members_str(f1['勝者'])} 🏆")
            
            st.write("---")
            st.markdown("### 🥊 賽事評分與晉級控制台")
            
            with st.container():
                c_info, c_score = st.columns([3, 1])
                with c_info:
                    st.markdown(f"#### 📅 準決賽 1 (Match 1)")
                    st.write(f"**{sf1['組別A']}** {get_team_members_str(sf1['組別A'])}  🆚  **{sf1['組別B']}** {get_team_members_str(sf1['組別B'])}")
                    st.write(f"當前狀態：`勝者 - {sf1['勝者']}`")
                with c_score:
                    if is_admin and sf1['勝者'] == "尚未決定":
                        sf1_win = st.selectbox("回報準決賽 1 勝者", ["選擇勝組", sf1['組別A'], sf1['組別B']], key="sel_sf1")
                        if sf1_win != "選擇勝組":
                            df_team_matches.loc[df_team_matches["場次編號"] == "SF1", "勝者"] = sf1_win
                            df_team_matches.loc[df_team_matches["場次編號"] == "F1", "組別A"] = sf1_win
                            save_team_matches(df_team_matches)
                            st.rerun()
            st.write("---")
            
            with st.container():
                c_info, c_score = st.columns([3, 1])
                with c_info:
                    st.markdown(f"#### 📅 準決賽 2 (Match 2)")
                    st.write(f"**{sf2['組別A']}** {get_team_members_str(sf2['組別A'])}  🆚  **{sf2['組別B']}** {get_team_members_str(sf2['組別B'])}")
                    st.write(f"當前狀態：`勝者 - {sf2['勝者']}`")
                with c_score:
                    if is_admin and sf2['勝者'] == "尚未決定":
                        sf2_win = st.selectbox("回報準決賽 2 勝者", ["選擇勝組", sf2['組別A'], sf2['組別B']], key="sel_sf2")
                        if sf2_win != "選擇勝組":
                            df_team_matches.loc[df_team_matches["場次編號"] == "SF2", "勝者"] = sf2_win
                            df_team_matches.loc[df_team_matches["場次編號"] == "F1", "組別B"] = sf2_win
                            save_team_matches(df_team_matches)
                            st.rerun()
            st.write("---")
            
            with st.container():
                c_info, c_score = st.columns([3, 1])
                with c_info:
                    st.markdown(f"#### 🏆 冠軍總決賽 (Grand Final)")
                    st.write(f"**{f1['組別A']}** {get_team_members_str(f1['組別A'])}  🆚  **{f1['組別B']}** {get_team_members_str(f1['組別B'])}")
                    st.write(f"當前狀態：`總冠軍 - {f1['勝者']}`")
                with c_score:
                    if is_admin and f1['組別A'] != "TBD" and f1['組別B'] != "TBD" and f1['勝者'] == "尚未決定":
                        f1_win = st.selectbox("回報總冠軍", ["選擇總冠軍", f1['組別A'], f1['組別B']], key="sel_f1")
                        if f1_win != "選擇總冠軍":
                            df_team_matches.loc[df_team_matches["場次編號"] == "F1", "勝者"] = f1_win
                            save_team_matches(df_team_matches)
                            st.rerun()
                            
            if is_admin:
                st.write("<br>", unsafe_allow_html=True)
                if st.button("🚨 重置並清空此淘汰賽程表 (重新抽籤)", type="secondary", use_container_width=True):
                    save_team_matches(None)
                    st.warning("舊對戰已被清除。")
                    st.rerun()
