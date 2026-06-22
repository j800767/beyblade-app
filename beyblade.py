import streamlit as st
import pandas as pd
import os
import random

st.set_page_config(page_title="戰鬥陀螺 LOL瑞士輪系統", page_icon="🌀", layout="wide")

DATA_FILE = "beyblade_registrations.csv"
SCORE_FILE = "tournament_scores.csv"
ADMIN_PASSWORD = "admin"  

def load_data():
    if os.path.exists(DATA_FILE): return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["選手名稱", "陀螺1_上蓋", "陀螺1_固鎖", "陀螺1_軸心", "陀螺2_上蓋", "陀螺2_固鎖", "陀螺2_軸心", "陀螺3_上蓋", "陀螺3_固鎖", "陀螺3_軸心", "陀螺4_上蓋", "陀螺4_固鎖", "陀螺4_軸心"])

def save_data(df): df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

# 📝 核心防呆檢查函式
def check_inputs(name, b1, r1, bit1, b2, r2, bit2, b3, r3, bit3, b4, r4, bit4, is_edit=False, original_name=""):
    if not name.strip(): return False, "❌ 選手名稱不能留空！"
    if not is_edit or (is_edit and name.strip() != original_name):
        if name.strip() in df_registrations["選手名稱"].values:
            return False, f"❌ 選手名稱【{name.strip()}】已經有人登記過了！"
    banned_keywords = ["天馬", "神杖", "鯊魚", "pegasus", "rod", "shark"]
    blades = [str(b1), str(b2), str(b3), str(b4)]
    for idx, b in enumerate(blades, 1):
        for banned in banned_keywords:
            if banned in b.lower(): return False, f"❌ 登記失敗！第 {idx} 顆陀螺的上蓋【{b}】屬於禁用零件（天馬/神杖/鯊魚）！"
    ratchets = [r for r in [str(r1).strip(), str(r2).strip(), str(r3).strip(), str(r4).strip()] if r]
    if len(ratchets) != len(set(ratchets)): return False, "❌ 登記失敗！4 顆陀螺的「固鎖 (Ratchet)」存在重複零件，請重新配置！"
    bits = [b for b in [str(bit1).strip(), str(bit2).strip(), str(bit3).strip(), str(bit4).strip()] if b]
    if len(bits) != len(set(bits)): return False, "❌ 登記失敗！4 顆陀螺的「軸心 (Bit)」存在重複零件，請重新配置！"
    return True, ""

df_registrations = load_data()
tab1, tab2, tab3 = st.tabs(["📝 選手零件登記與名單管理", "🏆 LOL版瑞士輪控制台", "📖 大賽官方規則說明圖"])

st.sidebar.header("🔑 管理者驗證專區")
admin_input = st.sidebar.text_input("輸入管理密碼", type="password")
is_admin = (admin_input == ADMIN_PASSWORD)

if is_admin: st.sidebar.success("🔓 管理員權限已全開。")
else: st.sidebar.info("🔒 目前為訪客唯讀模式。")

# ════════════════════════════════════════════════════════════
# 【分頁一：選手登記與名單管理】
# ════════════════════════════════════════════════════════════
with tab1:
    st.title("🌀 戰鬥陀螺 8人零件登記與後台管理")
    st.markdown("### 📝 4分制規則：3勝晉級四強 / 3敗直接淘汰。固鎖與軸心不可重複。禁用：天馬、神杖、鯊魚。")
    
    st.subheader("➕ 新增選手登記")
    with st.form("reg_form"):
        player_name = st.text_input("👤 選手名稱 / 綽號")
        c1, c2 = st.columns(2)
        with c1:
            b1, r1, bit1 = st.text_input("1_上蓋"), st.text_input("1_固鎖"), st.text_input("1_軸心")
            b3, r3, bit3 = st.text_input("3_上蓋"), st.text_input("3_固鎖"), st.text_input("3_軸心")
        with c2:
            b2, r2, bit2 = st.text_input("2_上蓋"), st.text_input("2_固鎖"), st.text_input("2_軸心")
            b4, r4, bit4 = st.text_input("4_上蓋"), st.text_input("4_固鎖"), st.text_input("4_軸心")
        submit_btn = st.form_submit_button("🚀 提交登記")

    if submit_btn:
        success, error_msg = check_inputs(player_name, b1, r1, bit1, b2, r2, bit2, b3, r3, bit3, b4, r4, bit4, is_edit=False)
        if not success: st.error(error_msg)
        else:
            df_registrations = pd.concat([df_registrations, pd.DataFrame([{"選手名稱": player_name.strip(), "陀螺1_上蓋": b1, "陀螺1_固鎖": r1, "陀螺1_軸心": bit1, "陀螺2_上蓋": b2, "陀螺2_固鎖": r2, "陀螺2_軸心": bit2, "陀螺3_上蓋": b3, "陀螺3_固鎖": r3, "陀螺3_軸心": bit3, "陀螺4_上蓋": b4, "陀螺4_固鎖": r4, "陀螺4_軸心": bit4}])], ignore_index=True)
            save_data(df_registrations)
            st.success(f"🎉 成功登記選手：{player_name.strip()}！"); st.rerun()

    st.write("---")
    st.subheader("📊 目前已登記選手名單")
    if not df_registrations.empty: st.dataframe(df_registrations)
    else: st.info("目前尚無選手登記資料。")

    if is_admin and not df_registrations.empty:
        st.write("---")
        st.subheader("🛠️ 管理員專屬：名單單獨修改/刪除後台")
        all_players = df_registrations["選手名稱"].tolist()
        selected_player = st.selectbox("🎯 請選擇要操作的選手", all_players)
        p_row = df_registrations[df_registrations["選手名稱"] == selected_player].iloc[0]
        
        col_edit, col_del = st.columns([3, 1])
        with col_edit:
            st.markdown(f"✏️ **修改選手【{selected_player}】的零件與名稱**")
            edit_name = st.text_input("修改選手名稱", value=str(p_row["選手名稱"]))
            ec1, ec2 = st.columns(2)
            with ec1:
                eb1 = st.text_input("修改 1_上蓋", value=str(p_row["陀螺1_上蓋"]))
                er1 = st.text_input("修改 1_固鎖", value=str(p_row["陀螺1_固鎖"]))
                ebit1 = st.text_input("修改 1_軸心", value=str(p_row["陀螺1_軸心"]))
                eb3 = st.text_input("修改 3_上蓋", value=str(p_row["陀螺3_上蓋"]))
                er3 = st.text_input("修改 3_固鎖", value=str(p_row["陀螺3_固鎖"]))
                ebit3 = st.text_input("修改 3_軸心", value=str(p_row["陀螺3_軸心"]))
            with ec2:
                eb2 = st.text_input("修改 2_上蓋", value=str(p_row["陀螺2_上蓋"]))
                er2 = st.text_input("修改 2_固鎖", value=str(p_row["陀螺2_固鎖"]))
                ebit2 = st.text_input("修改 2_軸心", value=str(p_row["陀螺2_軸心"]))
                eb4 = st.text_input("修改 4_上蓋", value=str(p_row["陀螺4_上蓋"]))
                er4 = st.text_input("修改 4_固鎖", value=str(p_row["陀螺4_固鎖"]))
                ebit4 = st.text_input("修改 4_軸心", value=str(p_row["陀螺4_軸心"]))
                
            if st.button("💾 儲存修改內容", type="primary"):
                success, error_msg = check_inputs(edit_name, eb1, er1, ebit1, eb2, er2, ebit2, eb3, er3, ebit3, eb4, er4, ebit4, is_edit=True, original_name=selected_player)
                if not success: st.error(error_msg)
                else:
                    df_registrations = df_registrations[df_registrations["選手名稱"] != selected_player]
                    df_registrations = pd.concat([df_registrations, pd.DataFrame([{"選手名稱": edit_name.strip(), "陀螺1_上蓋": eb1, "陀螺1_固鎖": er1, "陀螺1_軸心": ebit1, "陀螺2_上蓋": eb2, "陀螺2_固鎖": er2, "陀螺2_軸心": ebit2, "陀螺3_上蓋": eb3, "陀螺3_固鎖": er3, "陀螺3_軸心": ebit3, "陀螺4_上蓋": eb4, "陀螺4_固鎖": er4, "陀螺4_軸心": ebit4}])], ignore_index=True)
                    save_data(df_registrations)
                    st.success(f"🎉 選手【{selected_player}】的資料已成功更新！"); st.rerun()
                
        with col_del:
            st.markdown("🗑️ **危險特區**")
            if st.button(f"❌ 僅刪除選手 {selected_player}", type="secondary"):
                df_registrations = df_registrations[df_registrations["選手名稱"] != selected_player]
                save_data(df_registrations)
                st.warning(f"已單獨刪除選手：{selected_player}"); st.rerun()
        st.write("---")
        if st.button("🗑️ ⚠️ 毀滅級：清空所有選手報名資料 (全清空)"):
            if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
            st.rerun()

# ════════════════════════════════════════════════════════════
# 【分頁二：LOL 瑞士輪核心控制台】
# ════════════════════════════════════════════════════════════
with tab2:
    st.title("🏆 LOL世界賽制：3勝晉級四強 / 3敗淘汰控制台")
    
    raw_players = df_registrations["選手名稱"].tolist()
    while len(raw_players) < 8: raw_players.append(f"選手_{len(raw_players)+1}")
    players_list = raw_players[:8]

    if "lol_swiss" not in st.session_state:
        if os.path.exists(SCORE_FILE):
            try: st.session_state.lol_swiss = pd.read_csv(SCORE_FILE).to_dict(orient="records")[0]
            except: pass
        if "lol_swiss" not in st.session_state:
            st.session_state.lol_swiss = {
                "stage": "swiss", "round": 1, "matches_num": 4, 
                "m1_p1": players_list[0], "m1_p2": players_list[1], "m1_s1": 0, "m1_s2": 0, "m1_tag": "0-0戰績組",
                "m2_p1": players_list[2], "m2_p2": players_list[3], "m2_s1": 0, "m2_s2": 0, "m2_tag": "0-0戰績組",
                "m3_p1": players_list[4], "m3_p2": players_list[5], "m3_s1": 0, "m3_s2": 0, "m3_tag": "0-0戰績組",
                "m4_p1": players_list[6], "m4_p2": players_list[7], "m4_s1": 0, "m4_s2": 0, "m4_tag": "0-0戰績組",
                "history": "", 
                "sf1_s1": 0, "sf1_s2": 0, "sf2_s1": 0, "sf2_s2": 0, "f_s1": 0, "f_s2": 0, "bm_s1": 0, "bm_s2": 0,
                "qualified": "", "eliminated": "" 
            }

    lw = st.session_state.lol_swiss
    def save_lw(): pd.DataFrame([lw]).to_csv(SCORE_FILE, index=False)

    if is_admin:
        st.sidebar.subheader("🎲 大賽初始化")
        if st.sidebar.button("💥 生成第一輪隨機對戰組合", type="primary"):
            random.shuffle(players_list)
            lw["stage"] = "swiss"
            lw["round"] = 1
            lw["matches_num"] = 4
            for idx in range(1, 5):
                lw[f"m{idx}_p1"] = players_list[(idx-1)*2]
                lw[f"m{idx}_p2"] = players_list[(idx-1)*2+1]
                lw[f"m{idx}_s1"] = lw[f"m{idx}_s2"] = 0
                lw[f"m{idx}_tag"] = "0-0 戰績組"
            lw["history"] = ""
            lw["qualified"] = ""
            lw["eliminated"] = ""
            save_lw(); st.rerun()
        if st.sidebar.button("🔄 全大賽完全歸零重置"):
            if os.path.exists(SCORE_FILE): os.remove(SCORE_FILE)
            if "lol_swiss" in st.session_state: del st.session_state.lol_swiss
            st.rerun()

    def get_current_records():
        records = {p: {"w": 0, "l": 0, "diff": 0} for p in players_list}
        if lw["history"]:
            for m in lw["history"].split(";"):
                if not m: continue
                pa, pb, sa, sb = m.split(",")
                sa, sb = int(sa), int(sb)
                if sa > sb: records[pa]["w"] += 1; records[pb]["l"] += 1
                else: records[pb]["w"] += 1; records[pa]["l"] += 1
                records[pa]["diff"] += (sa - sb); records[pb]["diff"] += (sb - sa)
        return records

    records = get_current_records()

    if lw["stage"] == "swiss":
        st.header(f"📍 LOL瑞士輪預賽：第 【{lw['round']}】 輪 (4分制)")
        
        cols = st.columns(2)
        for i in range(int(lw["matches_num"])):
            idx = i + 1
            p1_key, p2_key = f"m{idx}_p1", f"m{idx}_p2"
            s1_key, s2_key = f"m{idx}_s1", f"m{idx}_s2"
            tag_key = f"m{idx}_tag"
            
            tag_val = lw.get(tag_key, "戰績對決")
            
            with cols[i % 2]:
                st.subheader(f"⚔️ 對決 {idx} ({tag_val})")
                st.write(f"**{lw[p1_key]}** vs **{lw[p2_key]}**")
                lw[s1_key] = st.number_input(f"{lw[p1_key]} 分數", min_value=0, max_value=4, value=int(lw[s1_key]), key=f"lw_s1_{idx}", disabled=not is_admin)
                lw[s2_key] = st.number_input(f"{lw[p2_key]} 分數", min_value=0, max_value=4, value=int(lw[s2_key]), key=f"lw_s2_{idx}", disabled=not is_admin)

        if is_admin:
            save_lw()
            if st.button("💾 確定本輪打完！由系統自動動態配對下一輪", type="primary"):
                new_hist = []
                for i in range(int(lw["matches_num"])):
                    idx = i + 1
                    new_hist.append(f"{lw[f'm{idx}_p1']},{lw[f'm' + str(idx) + '_p2']},{lw[f'm' + str(idx) + '_s1']},{lw[f'm' + str(idx) + '_s2']}")
                lw["history"] = (lw["history"] + ";" + ";".join(new_hist)) if lw["history"] else ";".join(new_hist)
                
                current_rec = get_current_records()
                q_list = [p for p, r in current_rec.items() if r["w"] == 3]
                e_list = [p for p, r in current_rec.items() if r["l"] == 3]
                lw["qualified"] = ",".join(q_list)
                lw["eliminated"] = ",".join(e_list)
                
                if len(q_list) >= 4:
                    lw["stage"] = "playoffs"
                else:
                    lw["round"] += 1
                    active_players = [p for p in players_list if p not in q_list and p not in e_list]
                    
                    groups = {}
                    for p in active_players:
                        groups.setdefault(current_rec[p]["w"], []).append(p)
                    
                    next_matches = []
                    sorted_keys = sorted(groups.keys(), reverse=True)
                    
                    for k in sorted_keys:
                        random.shuffle(groups[k])
                    
                    for k in sorted_keys:
                        if len(groups[k]) % 2 != 0:
                            for next_k in sorted_keys:
                                if next_k < k and len(groups[next_k]) > 0:
                                    cross_player = groups[next_k].pop(0)
                                    lucky_player = groups[k].pop(0)
                                    next_matches.append((lucky_player, cross_player, f"{k}勝-{next_k}勝 跨界戰"))
                                    break
                        
                        while len(groups[k]) >= 2:
                            p1 = groups[k].pop(0)
                            p2 = groups[k].pop(0)
                            next_matches.append((p1, p2, f"{k}勝{current_rec[p1]['l']}敗 同戰績組"))
                    
                    flat_remain = []
                    for k, v in groups.items(): flat_remain.extend(v)
                    while len(flat_remain) >= 2:
                        p1, p2 = flat_remain.pop(0), flat_remain.pop(0)
                        next_matches.append((p1, p2, f"中段混合組"))
                    
                    lw["matches_num"] = len(next_matches)
                    for i, (pa, pb, tag_text) in enumerate(next_matches):
                        idx = i + 1
                        lw[f"m{idx}_p1"] = pa
                        lw[f"m{idx}_p2"] = pb
                        lw[f"m{idx}_s1"] = lw[f"m{idx}_s2"] = 0
                        lw[f"m{idx}_tag"] = tag_text
                        
                save_lw(); st.rerun()

    st.write("---")
    c_board1, c_board2 = st.columns([1, 2])
    with c_board1:
        st.subheader("📢 核心戰績狀態公告")
        q_names = lw["qualified"].split(",") if lw["qualified"] else []
        e_names = lw["eliminated"].split(",") if lw["eliminated"] else []
        st.success(f"👑 **已成功晉級四強 ({len(q_names)}/4):**\n" + "\n".join([f"* {name} (3勝)" for name in q_names if name]))
        st.error(f"💀 **已不幸遭到淘汰 ({len(e_names)}/4):**\n" + "\n".join([f"* {name} (3敗)" for name in e_names if name]))
    
    with c_board2:
        st.subheader("📊 每位選手即時詳細戰績表")
        df_show = pd.DataFrame.from_dict(records, orient="index").reset_index().rename(columns={"index": "選手名稱", "w": "勝場", "l": "敗場", "diff": "淨勝分差"})
        st.dataframe(df_show.sort_values(by=["勝場", "淨勝分差"], ascending=False).reset_index(drop=True))

    if lw["stage"] == "playoffs" or len(lw["qualified"].split(",")) >= 4:
        st.write("---")
        st.header("🔥 終極決賽圈：核心四強單敗淘汰賽 (4分制)")
        top_4 = [p for p in lw["qualified"].split(",") if p]
        while len(top_4) < 4: top_4.append(f"決賽選手_{len(top_4)+1}")
        rank1, rank2, rank3, rank4 = top_4[0], top_4[1], top_4[2], top_4[3]
        
        col_sf1, col_sf2 = st.columns(2)
        with col_sf1:
            st.subheader("🏆 四強準決賽 A")
            st.write(f"**強者 A** `{rank1}` vs **強者 D** `{rank4}`")
            lw["sf1_s1"] = st.number_input(f"{rank1} 得分", min_value=0, max_value=4, value=int(lw["sf1_s1"]), key="lol_sf1_1", disabled=not is_admin)
            lw["sf1_s2"] = st.number_input(f"{rank4} 得分", min_value=0, max_value=4, value=int(lw["sf1_s2"]), key="lol_sf1_2", disabled=not is_admin)
            sf1_winner = rank1 if lw["sf1_s1"] > lw["sf1_s2"] else rank4
            sf1_loser = rank4 if lw["sf1_s1"] > lw["sf1_s2"] else rank1
        with col_sf2:
            st.subheader("🏆 四強準決賽 B")
            st.write(f"**強者 B** `{rank2}` vs **強者 C** `{rank3}`")
            lw["sf2_s1"] = st.number_input(f"{rank2} 得分 ", min_value=0, max_value=4, value=int(lw["sf2_s1"]), key="lol_sf2_1", disabled=not is_admin)
            lw["sf2_s2"] = st.number_input(f"{rank3} 得分 ", min_value=0, max_value=4, value=int(lw["sf2_s2"]), key="lol_sf2_2", disabled=not is_admin)
            sf2_winner = rank2 if lw["sf2_s1"] > lw["sf2_s2"] else rank3
            sf2_loser = rank3 if lw["sf2_s1"] > lw["sf2_s2"] else rank2

        st.write("---")
        st.header("✨ 最終榮譽戰")
        col_bm, col_f = st.columns(2)
        with col_bm:
            st.subheader("🥉 季軍賽 (銅牌戰)")
            st.write(f"`{sf1_loser}` vs `{sf2_loser}`")
            lw["bm_s1"] = st.number_input(f"{sf1_loser} 決賽得分1", min_value=0, max_value=4, value=int(lw["bm_s1"]), key="lol_bm_1", disabled=not is_admin)
            lw["bm_s2"] = st.number_input(f"{sf2_loser} 決賽得分2", min_value=0, max_value=4, value=int(lw["bm_s2"]), key="lol_bm_2", disabled=not is_admin)
        with col_f:
            st.subheader("🥇 🚀 總冠軍賽 (金牌戰)")
            st.write(f"👑 `{sf1_winner}` vs 👑 `{sf2_winner}`")
            lw["f_s1"] = st.number_input(f"{sf1_winner} 決賽得分3", min_value=0, max_value=4, value=int(lw["f_s1"]), key="lol_f_1", disabled=not is_admin)
            lw["f_s2"] = st.number_input(f"{sf2_winner} 決賽得分4", min_value=0, max_value=4, value=int(lw["f_s2"]), key="lol_f_2", disabled=not is_admin)

        if is_admin: save_lw()

        if lw["f_s1"] > 0 or lw["f_s2"] > 0:
            st.write("---")
            st.balloons()
            st.header("🎉 👑 第一屆 戰鬥陀螺 BX 英雄聯盟版大賽 最終榮譽榜 👑 🎉")
            champion = sf1_winner if lw["f_s1"] > lw["f_s2"] else sf2_winner
            second_place = sf2_winner if lw["f_s1"] > lw["f_s2"] else sf1_winner
            third_place = sf1_loser if lw["bm_s1"] > lw["bm_s2"] else sf2_loser
            c1, c2, c3 = st.columns(3)
            c1.metric("🥇 總冠軍 (金牌)", champion)
            c2.metric("🥈 亞軍 (銀牌)", second_place)
            c3.metric("🥉 季軍 (銅牌)", third_place)

# ════════════════════════════════════════════════════════════
# 【分頁三：大賽官方規則與 go-shoot 對照說明圖】
# ════════════════════════════════════════════════════════════
with tab3:
    st.title("📖 戰鬥陀螺 BX 8人瑞士輪賽事官方指南")
    st.info("💡 主辦人與選手可隨時點閱本頁，對照 go-shoot 網站之產品規格與瑞士輪賽制走向。")
    
    st.subheader("📊 1. 8人 LOL標準瑞士輪賽事走向示意圖")
    swiss_flowchart = '''
【 8人 LOL標準瑞士輪賽事走向示意圖 】

第一輪 (0-0)        第二輪             第三輪             第四輪             第五輪
─────────────────────────────────────────────────────────────────────────────────────────
[A,B,C,D,E,F,G,H]
     │
     ├── 贏家 (4人) ─► [1-0 組]
     │                    │
     │                    ├── 贏家 (2人) ─► [2-0 組]
     │                    │                    │
     │                    │                    ├── 贏家 (1人) ──►【3-0 晉級四強】(第1位)
     │                    │                    │
     │                    └── 輸家 (2人) ┐     └── 輸家 (1人) ┐
     │                                   │                    │
     │                                   ├─► [2-1 組] (3人) ◄─┘
     │                                   │      │
     │                    ┌── 贏家 (2人) ┘      ├── 2-1 互咬贏 ──►【3-1 晉級四強】
     │                    │                     │
     └── 輸家 (4人) ─► [0-1 組]                  ├── 跨界戰(2-1勝)►【3-1 晉級四強】
                          │                     │
                          ├── 贏家 (2人) ──► [1-1 組] (4人)  │ (若2-1輸或1-2互咬贏)
                          │                     │            │
                          └── 輸家 (2人) ┐     └── 兩兩互咬 ──┴─► [2-2 終極生死組] (2人或4人)
                                         │                                │
                                         ├─► [1-2 組] (3人) ◄─┐            └── 贏家 ──►【3-2 晉級四強】
                                         │      │            │                  (輸家 2-3 淘汰)
                                         │      ├── 跨界戰(1-2勝)►┘
                          ┌── 贏家 (2人) ┘      │
                          │                     ├── 1-2 互咬輸 ──►【1-3 淘汰出局】
                          │                     │
                          └── 輸家 (2人) ─────► [0-2 組]      │
                                                 │            │
                                                 └── 輸家 (1人) ──►【0-3 淘汰出局】
─────────────────────────────────────────────────────────────────────────────────────────
核心規則提要：
累積【3勝】直接晉級四強！ │ 累積【3敗】直接淘汰出局！
    '''
    st.code(swiss_flowchart, language="text")
    
    st.write("---")
    st.subheader("🚫 2. 賽事禁用零件卡表（對照 go-shoot 商品編號）")
    
    banned_data = {
        "官方產品編號": ["UX-02 / BX-35", "BX-14 / BX-22 / BX-31", "BX-01 / BX-17 / BX-21"],
        "禁用 Blade (刃擊環) 名稱": ["神杖獅鷲 / 神杖鯨魚 (Rod)", "鯊魚狂之 (Shark)", "天馬疾風 (Pegasus)"],
        "限制說明": ["環境強度過高，本次賽事全面禁用", "環境強度過高，本次賽事全面禁用", "環境強度過高，本次賽事全面禁用"]
    }
    st.table(pd.DataFrame(banned_data))
    
    st.write("---")
    st.subheader("🔄 3. 4分制 Deck 零件唯一性防呆規範")
    
    col_rule1, col_rule2 = st.columns(2)
    with col_rule1:
        st.markdown('''
        #### ［ 陀螺三層結構 ］
        * **BLADE 刃擊環 (最上層)**：
          * 💡 允許重複（例如：可同時帶兩顆 獅子之爪）。
        * **RATCHET 固鎖輪盤 (中層)**：
          * 🚫 **全 4 顆絕對不可重複**（例如 5-60、9-60 在整套 Deck 裡只能各出現一次）。
        * **BIT 軸心 (底層)**：
          * 🚫 **全 4 顆絕對不可重複**（例如 F軸、B軸 只能各出現一次）。
        ''')
    with col_rule2:
        st.warning('''
        ⚠️ **特別提醒（一體型與特殊部件規範）：**
        若選手登記包含如 **UX-04（異色魔龍）** 等自帶「Ratchet一體型」的特殊結構陀螺，該台陀螺將直接視為已佔用該款固鎖規格。選手其餘的 3 顆陀螺將不得再使用任何相同規格之固鎖部件。
        ''')
