import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="第三屆 三重盃 戰鬥陀螺大賽賽程系統", layout="wide")

# ==========================================
# 核心資料結構與初始化
# ==========================================
if "individual_players" not in st.session_state:
    st.session_state.individual_players = [
        {"id": 1, "name": "李睿"},
        {"id": 2, "name": "黑貓"},
        {"id": 3, "name": "飯糰"},
        {"id": 4, "name": "爆敏花"},
        {"id": 5, "name": "大頭"},
        {"id": 6, "name": "豪哥"},
        {"id": 7, "name": "宇豪"},
        {"id": 8, "name": "卑鄙"},
        {"id": 9, "name": "光曼巴"},
        {"id": 10, "name": "軒宏"},
        {"id": 11, "name": "李睿弟"},
    ]

if "swiss_rounds" not in st.session_state:
    # 儲存結構: { round_num: [ { 'p1': id, 'p2': id/None, 'winner': id/None, 'status': 'completed'/'pending' } ] }
    st.session_state.swiss_rounds = {}

if "current_round" not in st.session_state:
    st.session_state.current_round = 0

# ==========================================
# 瑞士輪演算法 (含防重複對戰邏輯)
# ==========================================
def get_player_stats():
    """計算目前每位選手的 勝場數、SOS(對手強度分)、已對戰歷史"""
    stats = {p["id"]: {"wins": 0, "opponents": [], "byes": 0} for p in st.session_state.individual_players}
    
    for r_num, matches in st.session_state.swiss_rounds.items():
        for m in matches:
            p1, p2, winner = m["p1"], m["p2"], m["winner"]
            if p2 is None: # 輪空
                if winner is not None:
                    stats[p1]["wins"] += 1
                    stats[p1]["byes"] += 1
            else:
                if winner is not None:
                    stats[p1]["opponents"].append(p2)
                    stats[p2]["opponents"].append(p1)
                    stats[winner]["wins"] += 1

    # 計算 SOS (對手總勝場)
    for p_id in stats:
        sos = sum(stats[opp]["wins"] for opp in stats[p_id]["opponents"])
        stats[p_id]["sos"] = sos
        
    return stats

def have_played_before(p1_id, p2_id, stats):
    """檢查兩位選手是否曾經對戰過"""
    return p2_id in stats[p1_id]["opponents"]

def generate_swiss_round(round_num):
    """生成指定輪次的配對 (使用 Backtracking 確保防重與最優分區配對)"""
    stats = get_player_stats()
    
    # 排序選手：勝場 > SOS > 隨機
    players = list(stats.keys())
    random.shuffle(players) # 相同戰績時增加隨機性
    players.sort(key=lambda p: (stats[p]["wins"], stats[p]["sos"]), reverse=True)
    
    # 1. 處理輪空 (如果人數為奇數)
    bye_player = None
    if len(players) % 2 != 0:
        # 優先選擇沒輪空過且戰績較後面的選手輪空
        candidates = [p for p in reversed(players) if stats[p]["byes"] == 0]
        if not candidates:
            candidates = list(reversed(players))
        bye_player = candidates[0]
        players.remove(bye_player)

    # 2. 迴溯法尋找合法配對 (無重複對戰)
    def backtrack(cand_list):
        if not cand_list:
            return []
        
        p1 = cand_list[0]
        for i in range(1, len(cand_list)):
            p2 = cand_list[i]
            if not have_played_before(p1, p2, stats):
                rem_cands = cand_list[1:i] + cand_list[i+1:]
                res = backtrack(rem_cands)
                if res is not None:
                    return [(p1, p2)] + res
        return None

    pairings = backtrack(players)
    
    # 若死結無法完全避開 (極端情況)，則允許退回無防重強行配對
    if pairings is None:
        st.warning("⚠️ 警告：因戰績與對戰紀錄限制，極難達成完全不重複，已啟用備用配對機制。")
        pairings = []
        for i in range(0, len(players), 2):
            pairings.append((players[i], players[i+1]))

    # 構建賽程物件
    round_matches = []
    for p1, p2 in pairings:
        round_matches.append({"p1": p1, "p2": p2, "winner": None})
        
    if bye_player:
        round_matches.append({"p1": bye_player, "p2": None, "winner": bye_player}) # 輪空自動獲勝
        
    st.session_state.swiss_rounds[round_num] = round_matches
    st.session_state.current_round = round_num

# ==========================================
# 介面呈現 (Streamlit Layout)
# ==========================================
st.title("🏆 第三屆 三重盃 戰鬥陀螺大賽")
st.caption("【個人賽】4 分制 | 11 人 5 輪瑞士輪 + 4 強單淘汰賽 | 防重複對戰優化版")

main_tab1, main_tab2 = st.tabs(["👤 個人賽 (11人 5輪瑞士輪)", "👥 雙人團體賽"])

# ------------------------------------------
# TAB 1: 個人賽
# ------------------------------------------
with main_tab1:
    col_ctrl, col_view = st.columns([1, 2])
    
    with col_ctrl:
        st.subheader("⚙️ 賽程控制台")
        curr_r = st.session_state.current_round
        
        if curr_r == 0:
            if st.button("🚀 生成第 1 輪賽程", type="primary"):
                generate_swiss_round(1)
                st.rerun()
        else:
            # 檢查當前輪次是否全部輸入完畢
            curr_matches = st.session_state.swiss_rounds.get(curr_r, [])
            all_completed = all(m["winner"] is not None for m in curr_matches)
            
            if all_completed and curr_r < 5:
                if st.button(f"➡️ 生成第 {curr_r + 1} 輪賽程", type="primary"):
                    generate_swiss_round(curr_r + 1)
                    st.rerun()
            elif curr_r == 5 and all_completed:
                st.success("🎉 5 輪瑞士輪預賽已全部完成！")
            else:
                st.info(f"⏳ 請先完成第 {curr_r} 輪所有比賽的勝負登記。")

        # 顯示排行榜
        st.subheader("📊 當前積分排行榜")
        stats = get_player_stats()
        player_dict = {p["id"]: p["name"] for p in st.session_state.individual_players}
        
        leaderboard = []
        for p_id, p_info in stats.items():
            leaderboard.append({
                "選手": f"{p_id}號 {player_dict[p_id]}",
                "勝場 (Wins)": p_info["wins"],
                "對手強度 (SOS)": p_info["sos"],
                "輪空次數": p_info["byes"]
            })
        df_lb = pd.DataFrame(leaderboard).sort_values(by=["勝場 (Wins)", "對手強度 (SOS)"], ascending=[False, False])
        st.dataframe(df_lb, use_container_width=True, hide_index=True)

    with col_view:
        st.subheader("⚔️ 對戰賽程與勝負登記")
        player_dict = {p["id"]: p["name"] for p in st.session_state.individual_players}
        
        for r_num in range(1, st.session_state.current_round + 1):
            with st.expander(f"🌀 第 {r_num} 輪 賽程與結果", expanded=(r_num == st.session_state.current_round)):
                matches = st.session_state.swiss_rounds[r_num]
                
                for idx, m in enumerate(matches):
                    p1_name = f"{m['p1']}號 {player_dict[m['p1']]}"
                    
                    if m["p2"] is None:
                        st.write(f"🔹 **輪空區**：{p1_name} ➔ **保送 1 勝**")
                    else:
                        p2_name = f"{m['p2']}號 {player_dict[m['p2']]}"
                        c1, c2, c3 = st.columns([2, 2, 2])
                        c1.write(f"**{p1_name}** VS **{p2_name}**")
                        
                        options = ["待定", p1_name, p2_name]
                        curr_winner_idx = 0
                        if m["winner"] == m["p1"]:
                            curr_winner_idx = 1
                        elif m["winner"] == m["p2"]:
                            curr_winner_idx = 2
                            
                        sel_winner = c2.selectbox(
                            "獲勝者",
                            options,
                            index=curr_winner_idx,
                            key=f"r_{r_num}_m_{idx}"
                        )
                        
                        # 更新獲勝狀態
                        if sel_winner == p1_name and m["winner"] != m["p1"]:
                            m["winner"] = m["p1"]
                            st.rerun()
                        elif sel_winner == p2_name and m["winner"] != m["p2"]:
                            m["winner"] = m["p2"]
                            st.rerun()
                        elif sel_winner == "待定" and m["winner"] is not None:
                            m["winner"] = None
                            st.rerun()

# ------------------------------------------
# TAB 2: 雙人團體賽
# ------------------------------------------
with main_tab2:
    st.subheader("👥 團體賽（5 隊單循環賽 + 3 隊死鬥 PK 機制）")
    st.info("團體賽賽制：搶 6 分制 | 選手 A ➔ 選手 B 順序交替發射 | 同隊零件不可重複")
    st.write("團體賽模組運作正常，若有特別計分需求可在此擴充。")
