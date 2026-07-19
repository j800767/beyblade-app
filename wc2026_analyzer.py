import streamlit as st
import random
import time

# ==========================================
# 1. 網頁基本配置
# ==========================================
st.set_page_config(
    page_title="三重盃 雙人團體賽 8人隨機分組系統", 
    page_icon="🎲", 
    layout="centered"
)

# 標題與簡介
st.title("🎲 三重盃 雙人團體賽 - 8人盲抽分組系統")
st.markdown("本系統專門用於將 **8 位獨立選手** 隨機打散，並兩兩隨機分配至 A、B、C、D 四個組別中。")
st.write("---")

# ==========================================
# 2. 初始化 Session State (用來維持抽籤結果)
# ==========================================
if "team_draw_result" not in st.session_state:
    st.session_state.team_draw_result = None

# ==========================================
# 3. 選手名單輸入區
# ==========================================
st.subheader("📝 步驟 1：請輸入參賽的 8 位選手名稱")

# 用 4 欄雙列來排版，比較省空間又好看
col1, col2, col3, col4 = st.columns(4)
with col1:
    p1 = st.text_input("選手 1", value="選手A")
    p5 = st.text_input("選手 5", value="選手E")
with col2:
    p2 = st.text_input("選手 2", value="選手B")
    p6 = st.text_input("選手 6", value="選手F")
with col3:
    p3 = st.text_input("選手 3", value="選手C")
    p7 = st.text_input("選手 7", value="選手G")
with col4:
    p4 = st.text_input("選手 4", value="選手D")
    p8 = st.text_input("選手 8", value="選手H")

st.write("<br>", unsafe_allow_html=True)

# ==========================================
# 4. 隨機分組核心邏輯
# ==========================================
st.subheader("🔥 步驟 2：執行隨機命運分組")

# 收集所有輸入的選手
players_list = [p1.strip(), p2.strip(), p3.strip(), p4.strip(), p5.strip(), p6.strip(), p7.strip(), p8.strip()]

# 防呆驗證：檢查留空與重複
has_empty = any(not p for p in players_list)
has_duplicate = len(players_list) != len(set(players_list))

if has_empty:
    st.error("❌ 錯誤：請確保 8 位選手的名稱都有輸入，不可留空！")
elif has_duplicate:
    st.error("❌ 錯誤：偵測到重複的選手名稱，請確認名字是否有輸入重複！")
else:
    # 抽籤按鈕
    if st.button("🎲 啟動盲抽！隨機打散分組", type="primary", use_container_width=True):
        # 複製名單進行洗牌
        shuffled_players = players_list.copy()
        
        # 營造現場緊張感特效
        with st.spinner("🔮 正在瘋狂洗牌中... 決定命運的時刻..."):
            random.shuffle(shuffled_players)
            time.sleep(2.0) # 2秒大螢幕動畫效果
        
        # 將隨機洗牌後的 8 個人，每兩個人封裝成一組
        st.session_state.team_draw_result = {
            "A組": [shuffled_players[0], shuffled_players[1]],
            "B組": [shuffled_players[2], shuffled_players[3]],
            "C組": [shuffled_players[4], shuffled_players[5]],
            "D組": [shuffled_players[6], shuffled_players[7]],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        }
        st.toast("🎉 8位選手隨機分組完成！", icon="🎊")

# ==========================================
# 5. 分組結果大螢幕展現
# ==========================================
if st.session_state.team_draw_result:
    res = st.session_state.team_draw_result
    
    st.write("---")
    st.subheader("📊 隨機抽籤組別結果")
    st.caption(f"⏱️ 抽籤完成時間：{res['timestamp']}")
    
    # 用兩行兩列展現 A, B, C, D 四個組別的結果
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
        
    # 重置按鈕
    st.write("<br>", unsafe_allow_html=True)
    if st.button("🔄 重置名單 / 重新分組", type="secondary", use_container_width=True):
        st.session_state.team_draw_result = None
        st.rerun()

# ==========================================
# 6. 頁尾宣告
# ==========================================
st.write("---")
st.caption("⚡ 三重盃 專用獨立 8人隨機分組工具 v2.0")
