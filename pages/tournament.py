import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="戰鬥陀螺大賽控制台", page_icon="🏆", layout="wide")

REG_FILE = "beyblade_registrations.csv"
SCORE_FILE = "tournament_scores.csv"

st.title("🏆 戰鬥陀螺大賽計分與晉級系統")
st.caption("客製化賽制：小組循環賽 ➡️ 敗部復活 ➡️ 核心四強 ➡️ 終極決賽")

# 1. 檢查並讀取報名資料
if not os.path.exists(REG_FILE):
    st.warning(f"⚠️ 找不到 `beyblade_registrations.csv` 檔案！請確保已有選手透過登記系統報名成功。")
    st.stop()

df_players = pd.read_csv(REG_FILE)
players_list = df_players["選手名稱"].tolist()

if len(players_list) < 6:
    st.error(f"❌ 目前登記人數只有 {len(players_list)} 人。本賽制專為 6 人設計，請等 6 人全部登記完成後再啟動控制台！")
    st.stop()
elif len(players_list) > 6:
    st.info(f"💡 目前有 {len(players_list)} 人登記，系統將自動取前 6 位參賽選手進行比賽。")
    players_list = players_list[:6]

# 2. 初始化比賽狀態
if "scores" not in st.session_state:
    if os.path.exists(SCORE_FILE):
        try:
            st.session_state.scores = pd.read_csv(SCORE_FILE).to_dict(orient="records")[0]
        except Exception:
            os.remove(SCORE_FILE)
    
    if "scores" not in st.session_state:
        st.session_state.scores = {
            "A1": players_list[0], "A2": players_list[1], "A3": players_list[2],
            "B1": players_list[3], "B2": players_list[4], "B3": players_list[5],
            "m1_s1": 0, "m1_s2": 0, "m2_s1": 0, "m2_s2": 0,
            "m3_s1": 0, "m3_s2": 0, "m4_s1": 0, "m4_s2": 0,
            "m5_s1": 0, "m5_s2": 0, "m6_s1": 0, "m6_s2": 0,
            "r1_s1": 0, "r1_s2": 0, "r2_s1": 0, "r2_s2": 0,
            "sf1_s1": 0, "sf1_s2": 0, "sf2_s1": 0, "sf2_s2": 0,
            "f_s1": 0, "f_s2": 0, "bm_s1": 0, "bm_s2": 0,
        }

def save_scores():
    pd.DataFrame([st.session_state.scores]).to_csv(SCORE_FILE, index=False)

s = st.session_state.scores

# 🎲 側邊欄抽籤調整
with st.sidebar:
    st.header("🎲 參賽名單與分組")
    st.write("若想微調分組，可在下方直接更換：")
    s["A1"] = st.selectbox("A組 1號", players_list, index=players_list.index(s["A1"]) if s["A1"] in players_list else 0)
    s["A2"] = st.selectbox("A組 2號", players_list, index=players_list.index(s["A2"]) if s["A2"] in players_list else 1)
    s["A3"] = st.selectbox("A組 3號", players_list, index=players_list.index(s["A3"]) if s["A3"] in players_list else 2)
    st.write("---")
    s["B1"] = st.selectbox("B組 1號", players_list, index=players_list.index(s["B1"]) if s["B1"] in players_list else 3)
    s["B2"] = st.selectbox("B組 2號", players_list, index=players_list.index(s["B2"]) if s["B2"] in players_list else 4)
    s["B3"] = st.selectbox("B組 3號", players_list, index=players_list.index(s["B3"]) if s["B3"] in players_list else 5)
    
    if st.button("💾 儲存目前所有比分狀態"):
        save_scores()
        st.success("比分已成功存檔！")
        
    if st.button("🔄 重設大賽（比分歸零）", type="primary"):
        if os.path.exists(SCORE_FILE):
            os.remove(SCORE_FILE)
        if "scores" in st.session_state:
            del st.session_state.scores
        st.rerun()

# 📍 第一階段：小組循環賽
st.header("📍 第一階段：小組循環賽 (常規賽 6 場)")
st.caption("請輸入每場對決最終的拿分結果")

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("🌀 A 組 (循環賽)")
    st.write(f"**【場次 1】** {s['A1']} vs {s['A2']}")
    c1, c2 = st.columns(2)
    s["m1_s1"] = c1.number_input(f"{s['A1']} 分數 ", min_value=0, max_value=5, value=int(s["m1_s1"]), key="m11")
    s["m1_s2"] = c2.number_input(f"{s['A2']} 分數 ", min_value=0, max_value=5, value=int(s["m1_s2"]), key="m12")
    
    st.write(f"**【場次 3】** {s['A2']} vs {s['A3']}")
    c1, c2 = st.columns(2)
    s["m3_s1"] = c1.number_input(f"{s['A2']} 分數 ", min_value=0, max_value=5, value=int(s["m3_s1"]), key="m31")
    s["m3_s2"] = c2.number_input(f"{s['A3']} 分數 ", min_value=0, max_value=5, value=int(s["m3_s2"]), key="m32")
    
    st.write(f"**【場次 5】** {s['A1']} vs {s['A3']}")
    c1, c2 = st.columns(2)
    s["m5_s1"] = c1.number_input(f"{s['A1']} 分數 ", min_value=0, max_value=5, value=int(s["m5_s1"]), key="m51")
    s["m5_s2"] = c2.number_input(f"{s['A3']} 分數 ", min_value=0, max_value=5, value=int(s["m5_s2"]), key="m52")

with col_b:
    st.subheader("🌀 B 組 (循環賽)")
    st.write(f"**【場次 2】** {s['B1']} vs {s['B2']}")
    c1, c2 = st.columns(2)
    s["m2_s1"] = c1.number_input(f"{s['B1']} 分數 ", min_value=0, max_value=5, value=int(s["m2_s1"]), key="m21")
    s["m2_s2"] = c2.number_input(f"{s['B2']} 分數 ", min_value=0, max_value=5, value=int(s["m2_s2"]), key="m22")
    
    st.write(f"**【場次 4】** {s['B2']} vs {s['B3']}")
    c1, c2 = st.columns(2)
    s["m4_s1"] = c1.number_input(f"{s['B2']} 分數 ", min_value=0, max_value=5, value=int(s["m4_s1"]), key="m41")
    s["m4_s2"] = c2.number_input(f"{s['B3']} 分數 ", min_value=0, max_value=5, value=int(s["m4_s2"]), key="m42")
    
    st.write(f"**【場次 6】** {s['B1']} vs {s['B3']}")
    c1, c2 = st.columns(2)
    s["m6_s1"] = c1.number_input(f"{s['B1']} 分數 ", min_value=0, max_value=5, value=int(s["m6_s1"]), key="m61")
    s["m6_s2"] = c2.number_input(f"{s['B3']} 分數 ", min_value=0, max_value=5, value=int(s["m6_s2"]), key="m62")

# 計算小組積分排名
def get_rank(p1, p2, p3, m1_1, m1_2, m2_1, m2_2, m3_1, m3_2):
    stats = {p1: {"wins": 0, "diff": 0}, p2: {"wins": 0, "diff": 0}, p3: {"wins": 0, "diff": 0}}
    if m1_1 > m1_2: stats[p1]["wins"]+=1
    elif m1_2 > m1_1: stats[p2]["wins"]+=1
    stats[p1]["diff"] += (m1_1 - m1_2)
    stats[p2]["diff"] += (m1_2 - m1_1)
    
    if m2_1 > m2_2: stats[p2]["wins"]+=1
    elif m2_2 > m2_1: stats[p3]["wins"]+=1
    stats[p2]["diff"] += (m2_1 - m2_2)
    stats[p3]["diff"] += (m2_2 - m2_1)
    
    if m3_1 > m3_2: stats[p1]["wins"]+=1
    elif m3_2 > m3_1: stats[p3]["wins"]+=1
    stats[p1]["diff"] += (m3_1 - m3_2)
    stats[p3]["diff"] += (m3_2 - m3_1)
    
    sorted_p = sorted(stats.items(), key=lambda x: (x[1]["wins"], x[1]["diff"]), reverse=True)
    return [sorted_p[0][0], sorted_p[1][0], sorted_p[2][0]]

rank_A = get_rank(s["A1"], s["A2"], s["A3"], s["m1_s1"], s["m1_s2"], s["m3_s1"], s["m3_s2"], s["m5_s1"], s["m5_s2"])
rank_B = get_rank(s["B1"], s["B2"], s["B3"], s["m2_s1"], s["m2_s2"], s["m4_s1"], s["m4_s2"], s["m6_s1"], s["m6_s2"])

st.write("---")
st.subheader("📊 目前小組排名預覽")
c_ra, c_rb = st.columns(2)
c_ra.info(f"**🥇 A組第一 (直升四強):** {rank_A[0]}  \n🥈 第二: {rank_A[1]} | 🥉 第三: {rank_A[2]}")
c_rb.info(f"**🥇 B組第一 (直升四強):** {rank_B[0]}  \n🥈 第二: {rank_B[1]} | 🥉 第三: {rank_B[2]}")

# 📍 第二階段：敗部復活挑戰賽
st.write("---")
st.header("🔥 第二階段：敗部復活挑戰賽")
st.caption("由兩組的第 2 名交叉對決第 3 名，贏家才能殺進最終四強！")

col_r1, col_r2 = st.columns(2)

with col_r1:
    st.subheader("⚔️ 敗部戰 1")
    st.write(f"**A組第二** `{rank_A[1]}` vs **B組第三** `{rank_B[2]}`")
    c1, c2 = st.columns(2)
    s["r1_s1"] = c1.number_input(f"{rank_A[1]} 分數", min_value=0, max_value=5, value=int(s["r1_s1"]), key="r11")
    s["r1_s2"] = c2.number_input(f"{rank_B[2]} 分數", min_value=0, max_value=5, value=int(s["r1_s2"]), key="r12")
    r1_winner = rank_A[1] if s["r1_s1"] > s["r1_s2"] else rank_B[2]

with col_r2:
    st.subheader("⚔️ 敗部戰 2")
    st.write(f"**B組第二** `{rank_B[1]}` vs **A組第三** `{rank_A[2]}`")
    c1, c2 = st.columns(2)
    s["r2_s1"] = c1.number_input(f"{rank_B[1]} 分數", min_value=0, max_value=5, value=int(s["r2_s1"]), key="r21")
    s["r2_s2"] = c2.number_input(f"{rank_A[2]} 分數", min_value=0, max_value=5, value=int(s["r2_s2"]), key="r22")
    r2_winner = rank_B[1] if s["r2_s1"] > s["r2_s2"] else rank_A[2]

# 📍 第三階段：真正核心四強賽
st.write("---")
st.header("👑 第三階段：真正核心四強賽")
st.caption("小組第一名（勝部王座）迎戰從敗部復活賽殺上來的魔王！")

col_sf1, col_sf2 = st.columns(2)

with col_sf1:
    st.subheader("🏆 四強賽 A")
    st.write(f"**A組第一** `{rank_A[0]}` vs **敗部戰 2 勝者** `{r2_winner}`")
    c1, c2 = st.columns(2)
    s["sf1_s1"] = c1.number_input(f"{rank_A[0]} 分數", min_value=0, max_value=5, value=int(s["sf1_s1"]), key="sf11")
    s["sf1_s2"] = c2.number_input(f"{r2_winner} 分數", min_value=0, max_value=5, value=int(s["sf1_s2"]), key="sf12")
    sf1_winner = rank_A[0] if s["sf1_s1"] > s["sf1_s2"] else r2_winner
    sf1_loser = r2_winner if s["sf1_s1"] > s["sf1_s2"] else rank_A[0]

with col_sf2:
    st.subheader("🏆 四強賽 B")
    st.write(f"**B組第一** `{rank_B[0]}` vs **敗部戰 1 勝者** `{r1_winner}`")
    c1, c2 = st.columns(2)
    s["sf2_s1"] = c1.number_input(f"{rank_B[0]} 分數", min_value=0, max_value=5, value=int(s["sf2_s1"]), key="sf21")
    s["sf2_s2"] = c2.number_input(f"{r1_winner} 分數", min_value=0, max_value=5, value=int(s["sf2_s2"]), key="sf22")
    sf2_winner = rank_B[0] if s["sf2_s1"] > s["sf2_s2"] else r1_winner
    sf2_loser = r1_winner if s["sf2_s1"] > s["sf2_s2"] else rank_B[0]

# 📍 第四階段：榮譽決賽圈
st.write("---")
st.header("✨ 第四階段：榮譽決賽圈 (總冠軍 / 季軍賽)")

col_bm, col_f = st.columns(2)

with col_bm:
    st.subheader("🥉 季軍賽 (銅牌戰)")
    st.write(f"`{sf1_loser}` vs `{sf2_loser}`")
    c1, c2 = st.columns(2)
    s["bm_s1"] = c1.number_input(f"{sf1_loser} 分數", min_value=0, max_value=5, value=int(s["bm_s1"]), key="bm1")
    s["bm_s2"] = c2.number_input(f"{sf2_loser} 分數", min_value=0, max_value=5, value=int(s["bm_s2"]), key="bm2")

with col_f:
    st.subheader("🥇 🚀 總冠軍賽 (金牌戰)")
    st.write(f"👑 `{sf1_winner}` vs 👑 `{sf2_winner}`")
    c1, c2 = st.columns(2)
    s["f_s1"] = c1.number_input(f"{sf1_winner} 分數", min_value=0, max_value=5, value=int(s["f_s1"]), key="f1")
    s["f_s2"] = c2.number_input(f"{sf2_winner} 分數", min_value=0, max_value=5, value=int(s["f_s2"]), key="f2")

# 大賽結果頒獎台
if (s["f_s1"] > s["f_s2"] or s["f_s2"] > s["f_s1"]):
    st.write("---")
    st.balloons()
    st.header("🎉 👑 第一屆 戰鬥陀螺 BX 大賽 最終榮譽榜 👑 🎉")
    
    champion = sf1_winner if s["f_s1"] > s["f_s2"] else sf2_winner
    second_place = sf2_winner if s["f_s1"] > s["f_s2"] else sf1_winner
    third_place = sf1_loser if s["bm_s1"] > s["bm_s2"] else sf2_loser
    
    col_1, col_2, col_3 = st.columns(3)
    col_1.metric("🥇 總冠軍 (金牌)", champion)
    col_2.metric("🥈 亞軍 (銀牌)", second_place)
    col_3.metric("🥉 季軍 (銅牌)", third_place)
    
    save_scores()
