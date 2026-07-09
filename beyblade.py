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

# 載入初始資料
df_reg = load_registrations()
df_matches = load_matches()
df_finals = load_finals()

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
# 4. 模式一：個人賽 (瑞士輪 3勝晉級四強 ➡️ 單淘汰決出前三名)
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

    # --- Tab 1: 選手登記 ---
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
        st.subheader(f"👥 已登記選手名單 (共 {len(df_reg)} 人)")
        if not df_reg.empty:
            st.dataframe(df_reg[["選手名稱", "陀螺1_上蓋", "陀螺2_上蓋", "陀螺3_上蓋", "陀螺4_上蓋", "勝場", "敗場", "退賽"]], use_container_width=True)

    # --- Tab 2: 瑞士輪控制台 ---
    with tabs[1]:
        st.header("⚔️ 預賽：瑞士輪賽程控制台")
        st.info(f"📊 目前進度：激戰中 `{len(active_players)}` 人 | 👑 已滿3勝晉級四強 `{len(qualifiers)}/4` 人 | ❌ 已滿3敗淘汰 `{len(eliminated)}` 人")
        
        if len(qualifiers) >= 4:
            st.success("🎉 四強名單已集齊！請前往「決賽：四強單淘汰」分頁開打決賽！")
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
            else:
                st.subheader("🔥 當前輪次對戰表")
                for idx, row in df_matches.iterrows():
                    pA, pB, winner = row["選手A"], row["選手B"], row["勝者"]
                    cA, cW = st.columns([3, 1])
                    with cA:
                        sA = f" ({df_reg[df_reg['選手名稱']==pA].iloc[0]['勝場']}勝{df_reg[df_reg['選手名稱']==pA].iloc[0]['敗場']}敗)" if pA in df_reg["選手名稱"].values else ""
                        sB = f" ({df_reg[df_reg['選手名稱']==pB].iloc[0]['勝場']}勝{df_reg[df_reg['選手名稱']==pB].iloc[0]['敗場']}敗)" if pB in df_reg["選手名稱"].values else ""
                        st.write(f"**場次 {idx+1}：** {pA}{sA} 🆚 {pB}{sB} ➡️ 局分結果：`{winner}`")
                    with cW:
                        if is_admin and pB != "BYE (輪空)" and winner == "尚未決定":
                            ans = st.selectbox("回報", ["選擇勝者", pA, pB], key=f"m_{idx}")
                            if ans != "選擇勝者":
                                df_matches.at[idx, "勝者"] = ans
                                save_matches(df_matches)
                                st.rerun()
                if is_admin and all(df_matches["勝者"] != "尚未決定"):
                    if st.button("🏁 確認本輪成績並更新戰績", use_container_width=True):
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
                                # 紀錄對戰歷史防止重複
                                hA = str(df_reg.at[idxW, "已對戰選手"])
                                df_reg.at[idxW, "已對戰選手"] = (hA + ";" + L).strip(";")
                                hB = str(df_reg.at[idxL, "已對戰選手"])
                                df_reg.at[idxL, "已對戰選手"] = (hB + ";" + W).strip(";")
                        save_registrations(df_reg)
                        save_matches(None)
                        st.success("戰績已成功更新！")
                        st.rerun()

    # --- Tab 3: 決賽（四強單淘汰） ---
    with tabs[2]:
        st.header("🏆 決賽：四強單淘汰控制台")
        
        if len(qualifiers) < 4:
            st.warning(f"⏳ 預賽尚未結束，目前僅有 {len(qualifiers)} 人達到 3 勝（滿 4 人即自動開啟四強賽）。")
        else:
            four_players = qualifiers[:4] # 抓取前4個滿3勝的人
            
            if df_finals is None:
                st.success("🤝 四強名單已確認：" + "、".join(four_players))
                if is_admin:
                    if st.button("🔥 抽籤生成四強淘汰賽賽程", type="primary"):
                        random.shuffle(four_players) # 隨機抽籤對戰
                        finals_data = [
                            {"階段": "準決賽A", "選手1": four_players[0], "選手2": four_players[1], "勝者": "尚未決定", "敗者": "尚未決定"},
                            {"階段": "準決賽B", "選手1": four_players[2], "選手2": four_players[3], "勝者": "尚未決定", "敗者": "尚未決定"},
                            {"階段": "季軍賽", "選手1": "準決賽A敗者", "選手2": "準決賽B敗者", "勝者": "尚未決定", "敗者": "尚未決定"},
                            {"階段": "冠軍賽", "選手1": "準決賽A勝者", "選手2": "準決賽B勝者", "勝者": "尚未決定", "敗者": "尚未決定"}
                        ]
                        df_finals = pd.DataFrame(finals_data)
                        save_finals(df_finals)
                        st.rerun()
            else:
                st.subheader("📊 淘汰賽樹狀圖與賽程回報")
                
                # 獨立渲染各場對戰
                semiA = df_finals[df_finals["階段"] == "準決賽A"].iloc[0]
                semiB = df_finals[df_finals["階段"] == "準決賽B"].iloc[0]
                place3 = df_finals[df_finals["階段"] == "季軍賽"].iloc[0]
                final_m = df_finals[df_finals["階段"] == "冠軍賽"].iloc[0]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### ⚔️ 準決賽 (Semi-Finals)")
                    # 準決賽 A
                    st.write(f"**【準決賽 A】** {semiA['選手1']} 🆚 {semiA['選手2']}")
                    st.write(f"➡️ 結果勝者：`{semiA['勝者']}`")
                    if is_admin and semiA["勝者"] == "尚未決定":
                        resA = st.selectbox("回報準決賽 A 勝者", ["選擇", semiA['選手1'], semiA['選手2']], key="semiA_s")
                        if resA != "選擇":
                            lossA = semiA['選手2'] if resA == semiA['選手1'] else semiA['選手1']
                            df_finals.loc[df_finals["階段"] == "準決賽A", ["勝者", "敗者"]] = [resA, lossA]
                            df_finals.loc[df_finals["階段"] == "冠軍賽", "選手1"] = resA
                            df_finals.loc[df_finals["階段"] == "季軍賽", "選手1"] = lossA
                            save_finals(df_finals); st.rerun()
                    
                    st.write("---")
                    # 準決賽 B
                    st.write(f"**【準決賽 B】** {semiB['選手1']} 🆚 {semiB['選手2']}")
                    st.write(f"➡️ 結果勝者：`{semiB['勝者']}`")
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
                    # 季軍賽
                    st.write(f"**🥉【季軍賽】** {place3['選手1']} 🆚 {place3['選手2']}")
                    st.write(f"➡️ **季軍（第三名）：** `{place3['勝者']}`")
                    if is_admin and semiA["勝者"] != "尚未決定" and semiB["勝者"] != "尚未決定" and place3["勝者"] == "尚未決定":
                        res3 = st.selectbox("回報季軍賽勝者", ["選擇", place3['選手1'], place3['選手2']], key="p3_s")
                        if res3 != "選擇":
                            loss3 = place3['選手2'] if res3 == place3['選手1'] else place3['選手1']
                            df_finals.loc[df_finals["階段"] == "季軍賽", ["勝者", "敗者"]] = [res3, loss3]
                            save_finals(df_finals); st.rerun()
                            
                    st.write("---")
                    # 冠軍賽
                    st.write(f"**🥇【冠軍賽】** {final_m['選手1']} 🆚 {final_m['選手2']}")
                    st.write(f"➡️ **冠軍：** `{final_m['勝者']}` | **亞軍：** `{final_m['敗者']}`")
                    if is_admin and semiA["勝者"] != "尚未決定" and semiB["勝者"] != "尚未決定" and final_m["勝者"] == "尚未決定":
                        resF = st.selectbox("回報冠軍賽勝者", ["選擇", final_m['選手1'], final_m['選手2']], key="final_s")
                        if resF != "選擇":
                            lossF = final_m['選手2'] if resF == final_m['選手1'] else final_m['選手1']
                            df_finals.loc[df_finals["階段"] == "冠軍賽", ["勝者", "敗者"]] = [resF, lossF]
                            save_finals(df_finals); st.rerun()
                
                # 最終榮譽榜
                if final_m["勝者"] != "尚未決定" and place3["勝者"] != "尚未決定":
                    st.success("🏆 恭喜本次大賽最終前三名誕生！")
                    st.balloons()
                    st.markdown(f"""
                    ### 🎖️ 三重盃 榮譽殿堂
                    * 🥇 **冠軍**：{final_m['勝者']}
                    * 🥈 **亞軍**：{final_m['敗者']}
                    * 🥉 **季軍**：{place3['勝者']}
                    """)
                    
                if is_admin:
                    if st.button("🔄 重置四強決賽（重抽賽程）", type="secondary"):
                        save_finals(None)
                        st.rerun()

    # --- Tab 4: 即時榜單 ---
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
# 5. 模式二：雙人團體賽 (保留原本架構不干涉)
# ==========================================
elif main_mode == "雙人團體賽 (獨立區)":
    st.title("👥 雙人團體賽管理系統")
    st.write("（此區域保持原本你與管理員設定好的團隊規則、不干涉個人賽）")
    # 原有的團體賽邏輯可以在這邊保持不變...
