import streamlit as st
import pandas as pd
import numpy as np
import os
import random

# ==========================================
# 1. 基礎設定與檔案路徑
# ==========================================
st.set_page_config(page_title="三重盃 陀螺大賽管理系統", page_icon="💥", layout="wide")

REG_FILE = "players_registration.csv"          # 個人賽檔案
MATCH_FILE = "current_matches.csv"             # 瑞士輪對戰檔案
FINALS_FILE = "finals_matches.csv"             # 四強單淘汰檔案
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
        if "敗場" not in df.columns:
            df["敗場"] = 0
        return df
    return pd.DataFrame(columns=[
        "選手名稱", 
        "陀螺1_上蓋", "陀螺1_固鎖", "陀螺1_軸心",
        "陀螺2_上蓋", "陀螺2_固鎖", "陀螺2_軸心",
        "陀螺3_上蓋", "陀螺3_固鎖", "陀螺3_軸心",
        "陀螺4_上蓋", "陀螺4_固鎖", "陀螺4_軸心",
        "勝場", "敗場", "對手件分", "總積分", "已對戰選手", "退賽"
    ])

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
        df = pd.read_csv(TEAM_DATA_FILE)
        df = df.fillna("") # 圖一修正：新版 Pandas 避免使用 inplace=True
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
df_finals = load_finals()
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
main_mode = st.sidebar.radio("選擇要管理的賽制：", ["個人賽 (瑞士輪+四強)", "雙人團體賽 (獨立區)"])

RESTRICTED_KEYWORDS = ["空力天馬", "魔導神杖", "鮫鯊狂鱗", "pegasus", "rod", "shark"]

# ==========================================
# 4. 模式一：個人賽 (瑞士輪 3勝晉級四強)
# ==========================================
if main_mode == "個人賽 (瑞士輪+四強)":
    st.title("💥 三重盃 個人賽（3勝晉級四強 ➡️ 單淘汰賽）")
    
    tabs = st.tabs(["📝 選手登記與名單", "⚔️ 預賽：瑞士輪控制台", "🏆 決賽：四強單淘汰", "📊 即時排行榜"])
    
    # 算一下目前各階段人數
    qualifiers = df_reg[(df_reg["勝場"] >= 3) & (df_reg["退賽"] != "是")]["選手名稱"].tolist()
    eliminated = df_reg[(df_reg["敗場"] >= 3) & (df_reg["退賽"] != "是")]["選手名稱"].tolist()
    active_players = df_reg[
        (df_reg["退賽"] != "是") & (df_reg["勝場"] < 3) & (df_reg["敗場"] < 3)
    ]["選手名稱"].tolist()

    # --- Tab 1: 選手登記與管理 ---
    with tabs[0]:
        st.header("選手改造登記（4選3 備戰規則）")
        if is_admin:
            with st.form("registration_form", clear_on_submit=True):
                col_name, col_b1, col_b2, col_b3, col_b4 = st.columns([1.2, 2, 2, 2, 2])
                with col_name: name = st.text_input("選手名稱*")
                with col_b1:
                    st.markdown("**陀螺 1**")
                    b1, r1, bit1 = st.text_input("上蓋 1"), st.text_input("固鎖 1"), st.text_input("軸心 1")
                with col_b2:
                    st.markdown("**陀螺 2**")
                    b2, r2, bit2 = st.text_input("上蓋 2"), st.text_input("固鎖 2"), st.text_input("軸心 2")
                with col_b3:
                    st.markdown("**陀螺 3**")
                    b3, r3, bit3 = st.text_input("上蓋 3"), st.text_input("固鎖 3"), st.text_input("軸心 3")
                with col_b4:
                    st.markdown("**陀螺 4**")
                    b4, r4, bit4 = st.text_input("上蓋 4"), st.text_input("固鎖 4"), st.text_input("軸心 4")
                    
                submit_reg = st.form_submit_button("📥 驗證並新增登記", use_container_width=True)
                if submit_reg:
                    if not name.strip(): st.error("❌ 登記失敗：名稱不能為空！")
                    elif name.strip() in df_reg["選手名稱"].values: st.error(f"❌ 選手【{name}】已登記！")
                    else:
                        ratchets, bits = [r1, r2, r3, r4], [bit1, bit2, bit3, bit4]
                        if len(set(ratchets)) < 4 or len(set(bits)) < 4:
                            st.error("❌ 登記失敗：個人的 4 顆陀螺中「固鎖」或「軸心」有零件重複！")
                        else:
                            rest_count = sum(1 for b in [b1, b2, b3, b4] if any(k in str(b).lower() for k in RESTRICTED_KEYWORDS))
                            if rest_count > 1:
                                st.error(f"❌ 違規！4 顆內偵測到 {rest_count} 顆限制零件（神杖/鮫鯊/天馬），限帶 1 顆！")
                            else:
                                new_player = {
                                    "選手名稱": name.strip(),
                                    "陀螺1_上蓋": b1, "陀螺1_固鎖": r1, "陀螺1_軸心": bit1,
                                    "陀螺2_上蓋": b2, "陀螺2_固鎖": r2, "陀螺2_軸心": bit2,
                                    "陀螺3_上蓋": b3, "陀螺3_固鎖": r3, "陀螺3_軸心": bit3,
                                    "陀螺4_上蓋": b4, "陀螺4_固鎖": r4, "陀螺4_軸心": bit4,
                                    "勝場": 0, "敗場": 0, "對手件分": 0, "總積分": 0, "已對戰選手": "", "退賽": "否"
                                }
                                df_reg = pd.concat([df_reg, pd.DataFrame([new_player])], ignore_index=True)
                                save_registrations(df_reg)
                                st.success(f"🎉 選手【{name}】成功通過驗證，完成登記！")
                                st.rerun()
        
        st.write("---")
        st.subheader(f"👥 已登記選手名單與配置總覽 (共 {len(df_reg)} 人)")
        if not df_reg.empty:
            # 圖三修正：強制將欄位轉為字串處理，避免數字或 NaN 觸發 AttributeError
            df_display = df_reg.copy()
            
            for i in range(1, 5):
                df_display[f"陀螺{i}_上蓋"] = df_display[f"陀螺{i}_上蓋"].astype(str).str.strip()
                df_display[f"陀螺{i}_固鎖"] = df_display[f"陀螺{i}_固鎖"].astype(str).str.strip()
                df_display[f"陀螺{i}_軸心"] = df_display[f"陀螺{i}_軸心"].astype(str).str.strip()
                
                df_display[f"💥 陀螺 {i} 配置"] = df_display.apply(
                    lambda row: f"{row[f'陀螺{i}_上蓋']} ({row[f'陀螺{i}_固鎖']} / {row[f'陀螺{i}_軸心']})"
                    if row[f'陀螺{i}_上蓋'] and row[f'陀螺{i}_上蓋'] != "nan" else "未配置", axis=1
                )
            
            show_cols = ["選手名稱", "💥 陀螺 1 配置", "💥 陀螺 2 配置", "💥 陀螺 3 配置", "💥 陀螺 4 配置", "勝場", "敗場", "退賽"]
            st.dataframe(df_display[show_cols], use_container_width=True)

        # ====== ⚙️ 個人賽名單管理控制台 ======
        if is_admin and not df_reg.empty:
            st.write("---")
            st.subheader("⚙️ 個人賽名單管理控制台")
            del_col1, del_col2 = st.columns([2, 1])
            with del_col1:
                target_player = st.selectbox("選擇要刪除的個人賽選手", df_reg["選手名稱"].tolist())
            with del_col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button(f"🗑️ 刪除選手 {target_player}", use_container_width=True):
                    df_reg = df_reg[df_reg["選手名稱"] != target_player]
                    save_registrations(df_reg)
                    st.warning(f"已刪除選手【{target_player}】。")
                    st.rerun()
            
            if st.button("🚨 一鍵清空所有【個人賽登記名單與成績】", type="secondary", use_container_width=True):
                if os.path.exists(REG_FILE): os.remove(REG_FILE)
                save_matches(None)
                save_finals(None)
                st.error("💥 個人賽所有登記資料、對戰賽程與四強數據已完全清空！")
                st.rerun()

    # --- Tab 2: 瑞士輪控制台 ---
    with tabs[1]:
        st.header("⚔️ 預賽：瑞士輪賽程控制台")
        st.info(f"📊 目前進度：激戰中 `{len(active_players)}` 人 | 👑 已滿3勝晉級四強 `{len(qualifiers)}/4` 人 | ❌ 已滿3敗淘汰 `{len(eliminated)}` 人")
        
        if len(qualifiers) >= 4:
            st.success("🎉 四強名單已集齊！請前往「決賽：四強單淘汰」分頁開打決賽！")
            if is_admin:
                st.write("---")
                st.subheader("⚙️ 預賽賽程管理")
                if st.button("🚨 徹底重置所有人戰績與對戰紀錄（重新打預賽）", type="secondary", use_container_width=True):
                    df_reg["勝場"] = 0
                    df_reg["敗場"] = 0
                    df_reg["已對戰選手"] = ""
                    save_registrations(df_reg)
                    save_matches(None)
                    save_finals(None)
                    st.error("💥 所有人勝敗戰績已歸零，對戰歷史已清空！")
                    st.rerun()
        else:
            if df_matches is None:
                if is_admin and len(active_players) >= 2:
                    if st.button("🎲 生成瑞士輪下一輪對戰 (戰績同分優先)", type="primary", use_container_width=True):
                        players_sorted = df_reg[df_reg["選手名稱"].isin(active_players)].sort_values(by=["勝場", "敗場"], ascending=[False, True])["選手名稱"].tolist()
                        paired, matches = set(), []
                        
                        for i in range(len(players_sorted)):
                            p1 = players_sorted[i]
                            if p1 in paired: continue
                            hist = str(df_reg[df_reg["選手名稱"] == p1]["已對戰選手"].values[0]).replace(";", ",").split(",")
                            hist = [p.strip() for p in hist if p.strip() and p != "nan"]
                            
                            found = False
                            for j in range(i + 1, len(players_sorted)):
                                p2 = players_sorted[j]
                                if p2 not in paired and p2 not in hist:
                                    matches.append({"選手A": p1, "選手B": p2, "勝者": "尚未決定"})
                                    paired.add(p1); paired.add(p2)
                                    found = True; break
                            if not found:
                                for j in range(i + 1, len(players_sorted)):
                                    p2 = players_sorted[j]
                                    if p2 not in paired:
                                        matches.append({"選手A": p1, "選手B": p2, "勝者": "尚未決定"})
                                        paired.add(p1); paired.add(p2)
                                        found = True; break
                        for p in players_sorted:
                            if p not in paired:
                                matches.append({"選手A": p, "選手B": "BYE (輪空)", "勝者": p})
                                paired.add(p)
                        df_matches = pd.DataFrame(matches)
                        save_matches(df_matches)
                        st.rerun()
                
                if is_admin and not df_reg.empty:
                    st.write("---")
                    st.subheader("⚙️ 預賽戰績管理")
                    if st.button("🚨 徹底重置所有人戰績與對戰紀錄（戰績歸零）", type="secondary", use_container_width=True):
                        df_reg["勝場"] = 0
                        df_reg["敗場"] = 0
                        df_reg["已對戰選手"] = ""
                        save_registrations(df_reg)
                        save_matches(None)
                        save_finals(None)
                        st.error("💥 所有人勝敗戰績已歸零，對戰歷史已清空！")
                        st.rerun()
            else:
                st.subheader("🔥 當前輪次對戰表")
                for idx, row in df_matches.iterrows():
                    pA, pB, winner = row["選手A"], row["選手B"], row["勝者"]
                    cA, cW = st.columns([3, 1])
                    with cA:
                        sA = f" ({df_reg[df_reg['選手名稱']==pA].iloc[0]['勝場']}勝{df_reg[df_reg['選手名稱']==pA].iloc[0]['敗場']}敗)" if pA in df_reg["選手名稱"].values else ""
                        sB = f" ({df_reg[df_reg['選手名稱']==pB].iloc[0]['勝場']}勝{df_reg[df_reg['選手名稱']==pB].iloc[0]['敗場']}敗)" if pB in df_reg["選手名稱"].values else ""
                        st.write(f"**場次 {idx+1}：** {pA}{sA} 🆚 {pB}{sB} ➡️ 結果：`{winner}`")
                    with cW:
                        if is_admin and pB != "BYE (輪空)" and winner == "尚未決定":
                            ans = st.selectbox("回報", ["選擇勝者", pA, pB], key=f"m_{idx}")
                            if ans != "選擇勝者":
                                df_matches.at[idx, "勝者"] = ans
                                save_matches(df_matches)
                                st.rerun()
                
                if is_admin:
                    st.write("---")
                    col_action1, col_action2 = st.columns(2)
                    with col_action1:
                        if all(df_matches["勝者"] != "尚未決定"):
                            if st.button("🏁 確認本輪成績並更新戰績", use_container_width=True, type="primary"):
                                for _, r in df_matches.iterrows():
                                    pA, pB, W = r["選手A"], r["選手B"], r["勝者"]
                                    if pB == "BYE (輪空)":
                                        idxA = df_reg[df_reg["選手名稱"] == pA].index[0]
                                        df_reg.at[idxA, "勝場"] += 1
                                    else:
                                        L = pB if W == pA else pA
                                        idxW = df_reg[df_reg["選手名稱"] == W].index[0]
                                        idxL = df_reg[df_reg["選手名稱"] == L].index[0]
                                        df_reg.at[idxW, "勝場"] += 1
                                        df_reg.at[idxL, "敗場"] += 1
                                        hA = str(df_reg.at[idxW, "已對戰選手"])
                                        df_reg.at[idxW, "已對戰選手"] = (hA + ";" + L).strip(";")
                                        hB = str(df_reg.at[idxL, "已對戰選手"])
                                        df_reg.at[idxL, "已對戰選手"] = (hB + ";" + W).strip(";")
                                save_registrations(df_reg)
                                save_matches(None)
                                st.success("戰績已成功更新！")
                                st.rerun()
                    with col_action2:
                        if st.button("❌ 撤銷本輪賽程（重新抽籤）", use_container_width=True, type="secondary"):
                            save_matches(None)
                            st.warning("本輪賽程已撒銷清空。")
                            st.rerun()

    # --- Tab 3: 四強決賽 ---
    with tabs[2]:
        st.header("🏆 決賽：四強單淘汰控制台")
        if len(qualifiers) < 4:
            st.warning(f"⏳ 預賽尚未結束，目前僅有 {len(qualifiers)} 人達到 3 勝（滿 4 人即自動開啟四強賽）。")
        else:
            four_players = qualifiers[:4]
            if df_finals is None:
                st.success("🤝 四強名單已確認：" + "、".join(four_players))
                if is_admin and st.button("🔥 抽籤生成四強淘汰賽賽程", type="primary"):
                    random.shuffle(four_players)
                    finals_data = [
                        {"階段": "準決賽A", "選手1": four_players[0], "選手2": four_players[1], "勝者": "尚未決定", "敗者": "尚未決定"},
                        {"階段": "準決賽B", "選手1": four_players[2], "選手2": four_players[3], "勝者": "尚未決定", "敗者": "尚未決定"},
                        {"階段": "季軍賽", "選手1": "準決賽A敗者", "選手2": "準決賽B敗者", "勝者": "尚未決定", "敗者": "尚未決定"},
                        {"階段": "冠軍賽", "選手1": "準決賽A勝者", "選手2": "準決賽B勝者", "勝者": "尚未決定", "敗者": "尚未決定"}
                    ]
                    df_finals = pd.DataFrame(finals_data)
                    save_finals(df_finals); st.rerun()
            else:
                # 圖二修正：安全地用階段名稱來撈取對應資料行
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
                            df_finals.loc[df_finals["階段"] == "準決賽A", ["勝者", "敗者"]] = [resA, lossA]
                            df_finals.loc[df_finals["階段"] == "冠軍賽", "選手1"] = resA
                            df_finals.loc[df_finals["階段"] == "季軍賽", "選手1"] = lossA
                            save_finals(df_finals); st.rerun()
                    st.write("---")
                    st.write(f"**【準決賽 B】** {semiB['選手1']} 🆚 {semiB['選手2']} ➡️ 勝者：`{semiB['勝者']}`")
                    if is_admin and semiB["勝者"] == "尚未決定":
                        resB = st.selectbox("回報準決賽 B 勝者", ["選擇", semiB['選手1'], semiB['選手2']], key="semiB_s")
                        if resB != "選擇":
                            lossB = semiB['選手2'] if resB == semiB['選手1'] else semiB['選手1']
                            df_finals.loc[df_finals["階段"] == "準決賽B", ["勝者", "敗者"]] = [resB, lossB]
                            df_finals.loc[df_finals["階段"] == "冠軍賽", "選手2"] = resB
                            df_finals.loc[df_finals["階段"] == "季軍賽", "選手2"] = lossB
                            save_finals(df_finals); st.rerun()

                with col2:
                    st.markdown("### 🥇 獎牌總決賽 (Finals)")
                    p3_p1 = place3['選手1']
                    p3_p2 = place3['選手2']
                    st.write(f"**🥉【季軍賽】** {p3_p1} 🆚 {p3_p2} ➡️ 季軍：`{place3['勝者']}`")
                    
                    # 必須雙方都有明確名字（非預設字串）才可以下拉選擇
                    if is_admin and p3_p1 != "準決賽A敗者" and p3_p2 != "準決賽B敗者" and place3["勝者"] == "尚未決定":
                        res3 = st.selectbox("回報季軍賽勝者", ["選擇", p3_p1, p3_p2], key="p3_s")
                        if res3 != "選擇":
                            loss3 = p3_p2 if res3 == p3_p1 else p3_p1
                            df_finals.loc[df_finals["階段"] == "季軍賽", ["勝者", "敗者"]] = [res3, loss3]
                            save_finals(df_finals); st.rerun()
                    st.write("---")
                    
                    f_p1 = final_m['選手1']
                    f_p2 = final_m['選手2']
                    st.write(f"**🥇【冠軍賽】** {f_p1} 🆚 {f_p2} ➡️ 冠軍：`{final_m['勝者']}`")
                    if is_admin and f_p1 != "準決賽A勝者" and f_p2 != "準決賽B勝者" and final_m["勝者"] == "尚未決定":
                        resF = st.selectbox("回報冠軍賽勝者", ["選擇", f_p1, f_p2], key="final_s")
                        if resF != "選擇":
                            lossF = f_p2 if resF == f_p1 else f_p1
                            df_finals.loc[df_finals["階段"] == "冠軍賽", ["勝者", "敗者"]] = [resF, lossF]
                            save_finals(df_finals); st.rerun()
                
                if final_m["勝者"] != "尚未決定" and place3["勝者"] != "尚未決定":
                    st.success("🏆 恭喜本次大賽最終前三名誕生！")
                    st.balloons()
                    st.markdown(f"### 🎖️ 三重盃 榮譽殿堂\n* 🥇 **冠軍**：{final_m['勝者']}\n* 🥈 **亞軍**：{final_m['敗者']}\n* 🥉 **季軍**：{place3['勝者']}")
                
                if is_admin:
                    st.write("---")
                    if st.button("🔄 重置四強決賽（重新抽籤與排定）", type="secondary", use_container_width=True):
                        save_finals(None); st.rerun()

    # --- Tab 4: 排行榜 ---
    with tabs[3]:
        st.header("📊 預賽即時晉級與淘汰榜單")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("### 👑 順利晉級四強區")
            for p in qualifiers: st.success(f"🔥 {p} (3勝)")
        with c2:
            st.markdown("### ⚔️ 激戰區 (存活中)")
            for p in active_players:
                r = df_reg[df_reg["選手名稱"] == p].iloc[0]
                st.info(f"⚡ {p} ({r['勝場']}勝 {r['敗場']}敗)")
        with c3:
            st.markdown("### ❌ 累積3敗淘汰區")
            for p in eliminated: st.error(f"💀 {p} (3敗)")

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
            if len(p1_ratchets) != len(set(p1_ratchets)): return False, f"❌ {team_name} 驗證失敗：{p1_data['name']} 的固鎖零件重複！"
            if len(p1_bits) != len(set(p1_bits)): return False, f"❌ {team_name} 驗證失敗：{p1_data['name']} 的軸心零件重複！"
            
            p2_ratchets = [r for r in [p2_data["r1"], p2_data["r2"]] if r.strip()]
            p2_bits = [b for b in [p2_data["bit1"], p2_data["bit2"]] if b.strip()]
            if len(p2_ratchets) != len(set(p2_ratchets)): return False, f"❌ {team_name} 驗證失敗：{p2_data['name']} 的固鎖零件重複！"
            if len(p2_bits) != len(set(p2_bits)): return False, f"❌ {team_name} 驗證失敗：{p2_data['name']} 的軸心零件重複！"

            all_blades = [str(p1_data["b1"]).lower(), str(p1_data["b2"]).lower(), str(p2_data["b1"]).lower(), str(p2_data["b2"]).lower()]
            restricted_count = 0
            for b in all_blades:
                if any(keyword in b for keyword in RESTRICTED_KEYWORDS): restricted_count += 1
            if restricted_count > 1:
                return False, f"❌ {team_name} 禁卡表違規！偵測到 {restricted_count} 顆限制零件（整組限 1 顆）！"
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
                    p1_in, p2_in = ui_inputs[team]["p1"], ui_inputs[team]["p2"]
                    if not p1_in["name"].strip() and not p2_in["name"].strip(): continue
                    success, err_msg = validate_team_setup(team, p1_in, p2_in)
                    if not success: st.error(err_msg); passed_all = False
                
                if passed_all:
                    new_rows = []
                    for team in ["A組", "B組", "C組", "D組"]:
                        p1, p2 = ui_inputs[team]["p1"], ui_inputs[team]["p2"]
                        new_rows.append({"組別": team, "隊員別": "隊員 1", "選手名稱": p1["name"].strip(), "陀螺1_上蓋": p1["b1"], "陀螺1_固鎖": p1["r1"], "陀螺1_軸心": p1["bit1"], "陀螺2_上蓋": p1["b2"], "陀螺2_固鎖": p1["r2"], "陀螺2_軸心": p1["bit2"]})
                        new_rows.append({"組別": team, "隊員別": "隊員 2", "選手名稱": p2["name"].strip(), "陀螺1_上蓋": p2["b1"], "陀螺1_固鎖": p2["r1"], "陀螺1_軸心": p2["bit1"], "陀螺2_上蓋": p2["b2"], "陀螺2_固鎖": p2["r2"], "陀螺2_軸心": p2["bit2"]})
                    df_teams = pd.DataFrame(new_rows)
                    save_team_data(df_teams); st.success("🎉 團體賽名單儲存成功！"); st.rerun()

        st.write("---")
        st.subheader("📊 當前已儲存的團體賽選手名單總覽")
        st.dataframe(df_teams, use_container_width=True)

        # ====== ⚙️ 團體賽名單管理控制台 ======
        if is_admin:
            st.write("---")
            st.subheader("⚙️ 團體賽名單管理控制台")
            del_col1, del_col2 = st.columns([2, 1])
            with del_col1:
                target_team = st.selectbox("選擇要刪除並清空的組別", ["A組", "B組", "C組", "D組"])
            with del_col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button(f"🗑️ 清空 {target_team} 資料", use_container_width=True):
                    for col in df_teams.columns:
                        if col != "組別" and col != "隊員別": df_teams.loc[df_teams["組別"] == target_team, col] = ""
                    save_team_data(df_teams); st.warning(f"已清除【{target_team}】登記資料。"); st.rerun()
            
            if st.button("🚨 一鍵重置並【清空所有 4 組】名單資料", type="secondary", use_container_width=True):
                columns = ["組別", "隊員別", "選手名稱", "陀螺1_上蓋", "陀螺1_固鎖", "陀螺1_軸心", "陀螺2_上蓋", "陀螺2_固鎖", "陀螺2_軸心"]
                default_rows = []
                for team in ["A組", "B組", "C組", "D組"]:
                    default_rows.append({"組別": team, "隊員別": "隊員 1", "選手名稱": ""})
                    default_rows.append({"組別": team, "隊員別": "隊員 2", "選手名稱": ""})
                df_reset = pd.DataFrame(default_rows, columns=columns)
                save_team_data(df_reset); st.error("💥 團體賽所有組別名單已完全清空重置！"); st.rerun()

    # --- 團體賽分頁 2：單敗淘汰賽賽程區 ---
    with team_tabs[1]:
        st.header("🏆 4強團體單敗淘汰賽程")
        def get_team_members_str(team_code):
            if not team_code or team_code == "TBD": return "(等待晉級中)"
            members = df_teams[df_teams["組別"] == team_code]["選手名稱"].tolist()
            members_clean = [m for m in members if str(m).strip()]
            return f"({ ' ＆ '.join(members_clean) })" if members_clean else "(未登記選手)"

        if df_team_matches is None:
            st.info("💡 目前尚無淘汰賽賽程。點擊下方按鈕將 A, B, C, D 四組隨機分配至準決賽。")
            if is_admin and st.button("🎲 隨機抽籤生成 4強淘汰賽程表", type="primary", use_container_width=True):
                teams_list = ["A組", "B組", "C組", "D組"]
                random.shuffle(teams_list)
                bracket_data = [
                    {"場次編號": "SF1", "階段": "準決賽 1", "組別A": teams_list[0], "組別B": teams_list[1], "勝者": "尚未決定"},
                    {"場次編號": "SF2", "階段": "準決賽 2", "組別A": teams_list[2], "組別B": teams_list[3], "勝者": "尚未決定"},
                    {"場次編號": "F1",  "階段": "總決賽",    "組別A": "TBD",       "組別B": "TBD",       "勝者": "尚未決定"}
                ]
                df_team_matches = pd.DataFrame(bracket_data)
                save_team_matches(df_team_matches); st.rerun()
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
                with c_score:
                    if is_admin and sf1['勝者'] == "尚未決定":
                        sf1_win = st.selectbox("回報準決賽 1 勝者", ["選擇勝組", sf1['組別A'], sf1['組別B']], key="sel_sf1")
                        if sf1_win != "選擇勝組":
                            df_team_matches.loc[df_team_matches["場次編號"] == "SF1", "勝者"] = sf1_win
                            df_team_matches.loc[df_team_matches["場次編號"] == "F1", "組別A"] = sf1_win
                            save_team_matches(df_team_matches); st.rerun()
            st.write("---")
            with st.container():
                c_info, c_score = st.columns([3, 1])
                with c_info:
                    st.markdown(f"#### 📅 準決賽 2 (Match 2)")
                    st.write(f"**{sf2['組別A']}** {get_team_members_str(sf2['組別A'])}  🆚  **{sf2['組別B']}** {get_team_members_str(sf2['組別B'])}")
                with c_score:
                    if is_admin and sf2['勝者'] == "尚未決定":
                        sf2_win = st.selectbox("回報準決賽 2 勝者", ["選擇勝組", sf2['組別A'], sf2['組別B']], key="sel_sf2")
                        if sf2_win != "選擇勝組":
                            df_team_matches.loc[df_team_matches["場次編號"] == "SF2", "勝者"] = sf2_win
                            df_team_matches.loc[df_team_matches["場cat編號"] == "F1", "組別B"] = sf2_win
                            save_team_matches(df_team_matches); st.rerun()
            st.write("---")
            with st.container():
                c_info, c_score = st.columns([3, 1])
                with c_info:
                    st.markdown(f"#### 🏆 冠軍總決賽 (Grand Final)")
                    st.write(f"**{f1['組別A']}** {get_team_members_str(f1['組別A'])}  🆚  **{f1['組別B']}** {get_team_members_str(f1['組別B'])}")
                with c_score:
                    if is_admin and f1['組別A'] != "TBD" and f1['組別B'] != "TBD" and f1['勝者'] == "尚未決定":
                        f1_win = st.selectbox("回報總冠軍", ["選擇總冠軍", f1['組別A'], f1['組別B']], key="sel_f1")
                        if f1_win != "選擇總冠軍":
                            df_team_matches.loc[df_team_matches["場次編號"] == "F1", "勝者"] = f1_win
                            save_team_matches(df_team_matches); st.rerun()
                            
            if is_admin:
                st.write("<br>", unsafe_allow_html=True)
                if st.button("🚨 重置並清空此淘汰賽程表 (重新抽籤)", type="secondary", use_container_width=True):
                    save_team_matches(None); st.rerun()
