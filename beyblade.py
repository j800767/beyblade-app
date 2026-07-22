import streamlit as st
import pandas as pd
import random

# ==========================================
# 1. 網頁基本配置
# ==========================================
st.set_page_config(
    page_title="三重盃 7人單循環+4強決賽系統", 
    page_icon="🏆", 
    layout="wide"
)

st.title("🏆 三重盃 7人單循環 + 4強淘汰賽系統")
st.caption("單公盤專用 ｜ 4選3 備戰與禁卡驗證 ｜ 即時積分榜與決賽自動生成")
st.write("---")

# 限制零件關鍵字 (小寫以利進行不分大小寫比對)
RESTRICTED_KEYWORDS = ["魔導神杖", "鮫鯊狂鱗", "空力天馬", "rod", "shark", "aero"]

# 預賽 21 場固定賽程表 (經過排程最佳化，減少連續上場)
SCHEDULE_21 = [
    (1, 2), (3, 4), (5, 6), (7, 1), (2, 3),
    (4, 5), (6, 7), (1, 3), (2, 4), (5, 7),
    (6, 1), (3, 5), (2, 6), (4, 7), (1, 5),
    (2, 7), (3, 6), (1, 4), (2, 5), (3, 7), (4, 6)
]

# ==========================================
# 2. 初始化 Session State
# ==========================================
if "df_reg" not in st.session_state:
    st.session_state.df_reg = pd.DataFrame(columns=[
        "選手名稱", 
        "陀螺1_上蓋", "陀螺1_固鎖", "陀螺1_軸心",
        "陀螺2_上蓋", "陀螺2_固鎖", "陀螺2_軸心",
        "陀螺3_上蓋", "陀螺3_固鎖", "陀螺3_軸心",
        "陀螺4_上蓋", "陀螺4_固鎖", "陀螺4_軸心"
    ])

if "players" not in st.session_state:
    st.session_state.players = {}  # {id: name}
if "match_results" not in st.session_state:
    st.session_state.match_results = {} # match_index: winner_id
if "head_to_head" not in st.session_state:
    st.session_state.head_to_head = {} # (p1, p2): winner_id

# ==========================================
# 3. 側邊欄：禁卡規範說明
# ==========================================
with st.sidebar:
    st.header("🚫 禁卡與備戰規範")
    st.markdown("""
    ⚠️ **個人禁卡限制**：
    * 個人的 4 顆陀螺中，【魔導神杖 / 鮫鯊狂鱗 / 空力天馬】**總共只能出現 1 顆**！
    * 個人的**固鎖（Ratchet）**與**軸心（Bit）**不可重複。
    * 比賽時採用 **4選3** 備戰規則。
    """)
    st.write("---")

# ==========================================
# 4. Tab 1: 選手改造登記（4選3 備戰規則）
# ==========================================
tabs = st.tabs(["📝 選手登記與管理", "⚔️ 預賽對戰（21場）", "📋 裝備對照總表", "📊 即時積分榜", "👑 4強決賽"])

with tabs[0]:
    st.header("選手改造登記（4選3 備戰規則）")
    st.markdown("⚠️ **個人禁卡限制**：個人的 4 顆陀螺中，【魔導神杖 / 鮫鯊狂鱗 / 空力天馬】**總共只能出現 1 顆**！且個人的固鎖與軸心不可重複。")
    
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
            df_reg = st.session_state.df_reg
            if not name.strip(): 
                st.error("❌ 登記失敗：名稱不能為空！")
            elif name.strip() in df_reg["選手名稱"].values: 
                st.error(f"❌ 選手【{name}】已登記！")
            else:
                ratchets = [r.strip() for r in [r1, r2, r3, r4] if r.strip()]
                bits = [b.strip() for b in [bit1, bit2, bit3, bit4] if b.strip()]
                
                if len(ratchets) != len(set(ratchets)) or len(bits) != len(set(bits)):
                    st.error("❌ 登記失敗：個人的 4 顆陀螺中「固鎖」或「軸心」有零件重複！")
                else:
                    all_blades = [str(b1).lower(), str(b2).lower(), str(b3).lower(), str(b4).lower()]
                    rest_count = sum(1 for b in all_blades if any(k in b for k in RESTRICTED_KEYWORDS))
                    
                    if rest_count > 1:
                        st.error(f"❌ 違規！個人的 4 顆內偵測到 {rest_count} 顆限制零件（神杖/鯊魚/天馬），限帶 1 顆！")
                    else:
                        new_player = {
                            "選手名稱": name.strip(),
                            "陀螺1_上蓋": b1, "陀螺1_固鎖": r1, "陀螺1_軸心": bit1,
                            "陀螺2_上蓋": b2, "陀螺2_固鎖": r2, "陀螺2_軸心": bit2,
                            "陀螺3_上蓋": b3, "陀螺3_固鎖": r3, "陀螺3_軸心": bit3,
                            "陀螺4_上蓋": b4, "陀螺4_固鎖": r4, "陀螺4_軸心": bit4,
                        }
                        st.session_state.df_reg = pd.concat([df_reg, pd.DataFrame([new_player])], ignore_index=True)
                        st.success(f"🎉 選手【{name}】成功通過驗證，完成登記！")
                        st.rerun()

    # 展示已登記名單與啟動賽事按鈕
    df_current = st.session_state.df_reg
    st.write("---")
    st.subheader(f"📋 目前已登記選手（{len(df_current)} / 7 人）")
    if not df_current.empty:
        st.dataframe(df_current[["選手名稱", "陀螺1_上蓋", "陀螺2_上蓋", "陀螺3_上蓋", "陀螺4_上蓋"]], use_container_width=True)

    if len(df_current) == 7 and not st.session_state.players:
        if st.button("🎲 滿 7 人！啟動盲抽編號並開始單循環賽", type="primary", use_container_width=True):
            p_names = df_current["選手名稱"].tolist()
            random.shuffle(p_names)
            st.session_state.players = {i + 1: name for i, name in enumerate(p_names)}
            st.toast("🎉 7 人抽籤完成，比賽開始！")
            st.rerun()

# ==========================================
# 5. 正式比賽控制區（7 人開賽後啟用）
# ==========================================
if st.session_state.players:
    
    # Tab 2: 預賽對戰（21場）
    with tabs[1]:
        completed_count = len(st.session_state.match_results)
        st.progress(completed_count / 21, text=f"預賽進度：{completed_count} / 21 場")
        
        selected_match_idx = st.number_input(
            "選擇場次：", min_value=1, max_value=21, 
            value=min(completed_count + 1, 21), step=1
        )
        
        p1_id, p2_id = SCHEDULE_21[selected_match_idx - 1]
        p1_name = st.session_state.players[p1_id]
        p2_name = st.session_state.players[p2_id]
        
        st.info(f"### 🥊 第 {selected_match_idx} 場對戰\n\n### **{p1_id}號 {p1_name}**  🆚  **{p2_id}號 {p2_name}**")
        
        # 顯示雙方登記的 4 顆陀螺
        df_p1 = st.session_state.df_reg[st.session_state.df_reg["選手名稱"] == p1_name].iloc[0]
        df_p2 = st.session_state.df_reg[st.session_state.df_reg["選手名稱"] == p2_name].iloc[0]
        
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.markdown(f"**🔴 {p1_id}號 {p1_name} 的 4 顆陀螺：**")
            for i in range(1, 5):
                st.write(f"{i}. {df_p1[f'陀螺{i}_上蓋']} {df_p1[f'陀螺{i}_固鎖']} {df_p1[f'陀螺{i}_軸心']}")
        with m_col2:
            st.markdown(f"**🔵 {p2_id}號 {p2_name} 的 4 顆陀螺：**")
            for i in range(1, 5):
                st.write(f"{i}. {df_p2[f'陀螺{i}_上蓋']} {df_p2[f'陀螺{i}_固鎖']} {df_p2[f'陀螺{i}_軸心']}")

        st.write("---")
        st.write("**請選擇本場勝者：**")
        c1, c2 = st.columns(2)
        
        current_winner = st.session_state.match_results.get(selected_match_idx)
        
        with c1:
            if st.button(f"🏆 {p1_name} 獲勝", use_container_width=True, type="primary" if current_winner == p1_id else "secondary"):
                st.session_state.match_results[selected_match_idx] = p1_id
                st.session_state.head_to_head[(p1_id, p2_id)] = p1_id
                st.session_state.head_to_head[(p2_id, p1_id)] = p1_id
                st.rerun()
        with c2:
            if st.button(f"🏆 {p2_name} 獲勝", use_container_width=True, type="primary" if current_winner == p2_id else "secondary"):
                st.session_state.match_results[selected_match_idx] = p2_id
                st.session_state.head_to_head[(p1_id, p2_id)] = p2_id
                st.session_state.head_to_head[(p2_id, p1_id)] = p2_id
                st.rerun()

    # Tab 3: 裝備對照總表
    with tabs[2]:
        st.subheader("📋 7 位選手改造裝備總表")
        st.dataframe(st.session_state.df_reg, use_container_width=True)

    # Tab 4: 即時積分榜
    with tabs[3]:
        st.subheader("🏆 預賽戰績積分榜")
        scores_calc = {i: 0 for i in range(1, 8)}
        for w_id in st.session_state.match_results.values():
            scores_calc[w_id] += 1
            
        def sort_key(p_id):
            wins = scores_calc[p_id]
            h2h_wins = sum(1 for (k, v) in st.session_state.head_to_head.items() if k[0] == p_id and v == p_id)
            return (wins, h2h_wins)

        ranked_ids = sorted(range(1, 8), key=sort_key, reverse=True)
        
        table_data = []
        for rank, p_id in enumerate(ranked_ids, 1):
            table_data.append({
                "排名": f"第 {rank} 名",
                "編號": f"{p_id} 號",
                "選手名稱": st.session_state.players[p_id],
                "勝場": f"{scores_calc[p_id]} 勝",
                "狀態": "🟢 晉級4強" if rank <= 4 else "🔴 淘汰"
            })
        st.table(table_data)

    # Tab 5: 4強決賽
    with tabs[4]:
        if len(st.session_state.match_results) < 21:
            st.warning("⚠️ 預賽 21 場尚未打完，打完後將自動生成 4 強決賽組合！")
        else:
            st.subheader("👑 4強單淘汰決賽")
            rank1 = st.session_state.players[ranked_ids[0]]
            rank2 = st.session_state.players[ranked_ids[1]]
            rank3 = st.session_state.players[ranked_ids[2]]
            rank4 = st.session_state.players[ranked_ids[3]]
            
            col_sf1, col_sf2 = st.columns(2)
            with col_sf1:
                st.info(f"**【 準決賽 A 】**\n\n🥊 **{rank1}** (第1) 🆚 **{rank4}** (第4)")
                sf1_win = st.radio("準決賽 A 勝者：", [rank1, rank4], key="sf1")
            with col_sf2:
                st.info(f"**【 準決賽 B 】**\n\n🥊 **{rank2}** (第2) 🆚 **{rank3}** (第3)")
                sf2_win = st.radio("準決賽 B 勝者：", [rank2, rank3], key="sf2")
                
            st.write("---")
            sf1_lose = rank4 if sf1_win == rank1 else rank1
            sf2_lose = rank3 if sf2_win == rank2 else rank2
            
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                st.warning(f"**🥉【 季軍戰 】**\n\n🥊 **{sf1_lose}** 🆚 **{sf2_lose}**")
                third = st.radio("季軍：", [sf1_lose, sf2_lose], key="third")
            with f_col2:
                st.success(f"**🏆【 冠軍戰 】**\n\n🥊 **{sf1_win}** 🆚 **{sf2_win}**")
                champion = st.radio("總冠軍：", [sf1_win, sf2_win], key="champ")
                
            st.balloons()
            st.markdown(f"## 🎉 恭喜 **{champion}** 獲得總冠軍！")
