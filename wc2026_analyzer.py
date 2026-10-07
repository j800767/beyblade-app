import random
import time
import streamlit as st

# ==========================================
# 1. 網頁基本配置
# ==========================================
st.set_page_config(
    page_title="三重盃 雙人團體賽 16人隨機分組系統",
    page_icon="🎲",
    layout="centered",
)

# 標題與簡介
st.title("🎲 三重盃 雙人團體賽 - 16人盲抽分組系統")
st.markdown(
    "本系統專門用於將 **16 位獨立選手** 隨機打散，並兩兩隨機分配至 A、B、C、"
    "D、E、F、G、H 八個組別中。"
)
st.write("---")

# ==========================================
# 2. 初始化 Session State (用來維持抽籤結果)
# ==========================================
if "team_draw_result" not in st.session_state:
    st.session_state.team_draw_result = None

# ==========================================
# 3. 選手名單輸入區 (4x4 矩陣排版)
# ==========================================
st.subheader("📝 步驟 1：請輸入參賽的 16 位選手名稱")

col1, col2, col3, col4 = st.columns(4)
with col1:
    p1 = st.text_input("選手 1", value="選手A")
    p5 = st.text_input("選手 5", value="選手E")
    p9 = st.text_input("選手 9", value="選手I")
    p13 = st.text_input("選手 13", value="選手M")
with col2:
    p2 = st.text_input("選手 2", value="選手B")
    p6 = st.text_input("選手 6", value="選手F")
    p10 = st.text_input("選手 10", value="選手J")
    p14 = st.text_input("選手 14", value="選手N")
with col3:
    p3 = st.text_input("選手 3", value="選手C")
    p7 = st.text_input("選手 7", value="選手G")
    p11 = st.text_input("選手 11", value="選手K")
    p15 = st.text_input("選手 15", value="選手O")
with col4:
    p4 = st.text_input("選手 4", value="選手D")
    p8 = st.text_input("選手 8", value="選手H")
    p12 = st.text_input("選手 12", value="選手L")
    p16 = st.text_input("選手 16", value="選手P")

st.write("<br>", unsafe_allow_html=True)

# ==========================================
# 4. 隨機分組核心邏輯
# ==========================================
st.subheader("🔥 步驟 2：執行隨機命運分組")

# 收集所有輸入的 16 位選手
players_list = [
    p1.strip(),
    p2.strip(),
    p3.strip(),
    p4.strip(),
    p5.strip(),
    p6.strip(),
    p7.strip(),
    p8.strip(),
    p9.strip(),
    p10.strip(),
    p11.strip(),
    p12.strip(),
    p13.strip(),
    p14.strip(),
    p15.strip(),
    p16.strip(),
]

# 防呆驗證：檢查留空與重複
has_empty = any(not p for p in players_list)
has_duplicate = len(players_list) != len(set(players_list))

if has_empty:
    st.error("❌ 錯誤：請確保 16 位選手的名稱都有輸入，不可留空！")
elif has_duplicate:
    st.error("❌ 錯誤：偵測到重複的選手名稱，請確認名字是否有輸入重複！")
else:
    # 抽籤按鈕
    if st.button(
        "🎲 啟動盲抽！隨機打散分組", type="primary", use_container_width=True
    ):
        # 複製名單進行洗牌
        shuffled_players = players_list.copy()

        # 營造現場緊張感特效
        with st.spinner("🔮 正在瘋狂洗牌中... 決定命運的時刻..."):
            random.shuffle(shuffled_players)
            time.sleep(2.0)  # 2秒大螢幕動畫效果

        # 將隨機洗牌後的 16 個人，每兩個人封裝成一組（共 8 組）
        st.session_state.team_draw_result = {
            "A組": [shuffled_players[0], shuffled_players[1]],
            "B組": [shuffled_players[2], shuffled_players[3]],
            "C組": [shuffled_players[4], shuffled_players[5]],
            "D組": [shuffled_players[6], shuffled_players[7]],
            "E組": [shuffled_players[8], shuffled_players[9]],
            "F組": [shuffled_players[10], shuffled_players[11]],
            "G組": [shuffled_players[12], shuffled_players[13]],
            "H組": [shuffled_players[14], shuffled_players[15]],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        }
        st.toast("🎉 16位選手隨機分組完成！", icon="🎊")

# ==========================================
# 5. 分組結果大螢幕展現
# ==========================================
if st.session_state.team_draw_result:
    res = st.session_state.team_draw_result

    st.write("---")
    st.subheader("📊 隨機抽籤組別結果")
    st.caption(f"⏱️ 抽籤完成時間：{res['timestamp']}")

    # 使用 2 欄配置展示 A~H 組（左欄 A, C, E, G，右欄 B, D, F, H）
    r_col1, r_col2 = st.columns(2)

    with r_col1:
        st.info(
            f"### 🛡️ 團體【 A 組 】\n\n"
            f"👤 **隊員 1**： {res['A組'][0]}\n\n"
            f"👤 **隊員 2**： {res['A組'][1]}"
        )
        st.write("<br>", unsafe_allow_html=True)
        st.info(
            f"### 🛡️ 團體【 C 組 】\n\n"
            f"👤 **隊員 1**： {res['C組'][0]}\n\n"
            f"👤 **隊員 2**： {res['C組'][1]}"
        )
        st.write("<br>", unsafe_allow_html=True)
        st.info(
            f"### 🛡️ 團體【 E 組 】\n\n"
            f"👤 **隊員 1**： {res['E組'][0]}\n\n"
            f"👤 **隊員 2**： {res['E組'][1]}"
        )
        st.write("<br>", unsafe_allow_html=True)
        st.info(
            f"### 🛡️ 團體【 G 組 】\n\n"
            f"👤 **隊員 1**： {res['G組'][0]}\n\n"
            f"👤 **隊員 2**： {res['G組'][1]}"
        )

    with r_col2:
        st.info(
            f"### 🛡️ 團體【 B 組 】\n\n"
            f"👤 **隊員 1**： {res['B組'][0]}\n\n"
            f"👤 **隊員 2**： {res['B組'][1]}"
        )
        st.write("<br>", unsafe_allow_html=True)
        st.info(
            f"### 🛡️ 團體【 D 組 】\n\n"
            f"👤 **隊員 1**： {res['D組'][0]}\n\n"
            f"👤 **隊員 2**： {res['D組'][1]}"
        )
        st.write("<br>", unsafe_allow_html=True)
        st.info(
            f"### 🛡️ 團體【 F 組 】\n\n"
            f"👤 **隊員 1**： {res['F組'][0]}\n\n"
            f"👤 **隊員 2**： {res['F組'][1]}"
        )
        st.write("<br>", unsafe_allow_html=True)
        st.info(
            f"### 🛡️ 團體【 H 組 】\n\n"
            f"👤 **隊員 1**： {res['H組'][0]}\n\n"
            f"👤 **隊員 2**： {res['H組'][1]}"
        )

    # 重置按鈕
    st.write("<br>", unsafe_allow_html=True)
    if st.button(
        "🔄 重置名單 / 重新分組", type="secondary", use_container_width=True
    ):
        st.session_state.team_draw_result = None
        st.rerun()

# ==========================================
# 6. 頁尾宣告
# ==========================================
st.write("---")
st.caption("⚡ 三重盃 專用獨立 16人隨機分組工具 v2.0")
