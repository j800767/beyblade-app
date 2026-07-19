import streamlit as st
import random
import time

# ==========================================
# 1. 網頁基本配置
# ==========================================
st.set_page_config(
    page_title="三重盃 雙人團體賽抽籤系統", 
    page_icon="🎲", 
    layout="centered"
)

# 標題與簡介
st.title("🎲 三重盃 雙人團體賽 - 盲抽賽程系統")
st.markdown("本系統專門用於隨機分配 A、B、C、D 四組隊伍之準決賽（4強）對戰組合。")
st.write("---")

# ==========================================
# 2. 初始化 Session State (用來維持抽籤結果)
# ==========================================
if "draw_result" not in st.session_state:
    st.session_state.draw_result = None

# ==========================================
# 3. 隊伍名稱輸入區
# ==========================================
st.subheader("📝 步驟 1：確認參賽的 4 支隊伍名稱")
st.caption("您可以直接使用預設的組別名稱，或是更改為實際的隊伍/選手暱稱。")

col1, col2 = st.columns(2)
with col1:
    team_a = st.text_input("隊伍 1 名稱", value="A組").strip()
    team_b = st.text_input("隊伍 2 名稱", value="B組").strip()
with col2:
    team_c = st.text_input("隊伍 3 名稱", value="C組").strip()
    team_d = st.text_input("隊伍 4 名稱", value="D組").strip()

st.write("<br>", unsafe_allow_html=True)

# ==========================================
# 4. 隨機抽籤核心邏輯
# ==========================================
st.subheader("🔥 步驟 2：執行隨機抽籤")

# 收集所有輸入的隊伍
teams_list = [team_a, team_b, team_c, team_d]

# 檢查是否有空格防呆
has_empty = any(not t for t in teams_list)

if has_empty:
    st.error("❌ 錯誤：請確保 4 個隊伍名稱皆有輸入，不可留空！")
else:
    # 抽籤按鈕
    if st.button("🎲 啟動盲抽！生成 4強單敗淘汰賽程", type="primary", use_container_width=True):
        # 複製一份名單進行洗牌
        shuffled_teams = teams_list.copy()
        
        # 現場緊張感特效：跑個倒數
        with st.spinner("🔮 陀螺劇烈碰撞中... 正在隨機重組賽程..."):
            random.shuffle(shuffled_teams)
            time.sleep(1.8) # 營造 1.8 秒的抽籤動畫時間
        
        # 將洗牌後的結果存入暫存器
        st.session_state.draw_result = {
            "SF1_A": shuffled_teams[0],
            "SF1_B": shuffled_teams[1],
            "SF2_A": shuffled_teams[2],
            "SF2_B": shuffled_teams[3],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        }
        st.toast("🎉 賽程抽籤完成！", icon="🎊")

# ==========================================
# 5. 賽程結果與視覺化樹狀圖展現
# ==========================================
if st.session_state.draw_result:
    res = st.session_state.draw_result
    
    st.write("---")
    st.subheader("📊 抽籤結果 ＆ 淘汰賽樹狀賽程表")
    st.caption(f"⏱️ 抽籤完成時間：{res['timestamp']}")
    
    # 樹狀圖視覺化排版 (左邊是準決賽，右邊是總決賽)
    t_col1, t_col2 = st.columns([1.2, 1])
    
    with t_col1:
        st.markdown("### 🧱 準決賽 (Semi-Finals)")
        
        # 準決賽 1 區塊
        st.info(
            f"**【 準決賽 1 】**\n\n"
            f" 🥊 **{res['SF1_A']}**\n"
            f" 🆚 \n"
            f" 🥊 **{res['SF1_B']}**"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 準決賽 2 區塊
        st.info(
            f"**【 準決賽 2 】**\n\n"
            f" 🥊 **{res['SF2_A']}**\n"
            f" 🆚 \n"
            f" 🥊 **{res['SF2_B']}**"
        )
        
    with t_col2:
        st.markdown("### 👑 總決賽 (Grand Final)")
        st.markdown("<br><br>", unsafe_allow_html=True) # 往下推齊中間
        
        st.warning(
            f"🏆 **【 冠軍爭奪戰 】**\n\n"
            f" 🥇 準決賽 1 勝者\n"
            f" 🆚 \n"
            f" 🥇 準決賽 2 勝者\n\n"
            f" ➡️  **爭奪總冠軍榮耀**"
        )
        
    # 重置按鈕
    st.write("<br>", unsafe_allow_html=True)
    if st.button("🔄 清除結果 / 重新抽籤", type="secondary", use_container_width=True):
        st.session_state.draw_result = None
        st.rerun()

# ==========================================
# 6. 頁尾宣告
# ==========================================
st.write("---")
st.caption("⚡ 三重盃 專用獨立簡易抽籤工具 v1.0")
