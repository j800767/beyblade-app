import os
import random
from functools import cmp_to_key
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd
import streamlit as st

# ==========================================
# 1. 基礎設定與檔案路徑
# ==========================================
st.set_page_config(
    page_title="第四屆 三重盃 戰鬥陀螺大賽", page_icon="💥", layout="wide"
)

REG_FILE = "players_registration.csv"  # 個人賽選手名單 (16人)
SWISS_MATCH_FILE = "swiss_matches.csv"  # 個人賽瑞士輪賽程檔案
FINALS_FILE = "finals_matches.csv"  # 個人賽八強單淘汰檔案

TEAM_DATA_FILE = "team_players_registration.csv"  # 團體賽名單檔案 (8組)
TEAM_MATCH_FILE = "team_matches.csv"  # 團體賽小組賽賽程檔案
TEAM_FINALS_FILE = "team_finals_matches.csv"  # 團體賽四強決賽檔案

ADMIN_PASSWORD = "admin"  # 管理員預設密碼
TEAM_NAMES = ["A組", "B組", "C組", "D組", "E組", "F組", "G組", "H組"]


# ==========================================
# 2. 資料存取與快取機制
# ==========================================
@st.cache_data
def load_registrations() -> pd.DataFrame:
    if os.path.exists(REG_FILE):
        df = pd.read_csv(REG_FILE).fillna("")
        if "編號" not in df.columns:
            df["編號"] = 0
        return df
    return pd.DataFrame(columns=["編號", "選手名稱"])


def save_registrations(df: pd.DataFrame) -> None:
    df.to_csv(REG_FILE, index=False, encoding="utf-8-sig")
    st.cache_data.clear()


@st.cache_data
def load_swiss_matches() -> Optional[pd.DataFrame]:
    if os.path.exists(SWISS_MATCH_FILE):
        return pd.read_csv(SWISS_MATCH_FILE).fillna("")
    return None


def save_swiss_matches(df: Optional[pd.DataFrame]) -> None:
    if df is not None:
        df.to_csv(SWISS_MATCH_FILE, index=False, encoding="utf-8-sig")
    elif os.path.exists(SWISS_MATCH_FILE):
        os.remove(SWISS_MATCH_FILE)
    st.cache_data.clear()


@st.cache_data
def load_finals() -> Optional[pd.DataFrame]:
    if os.path.exists(FINALS_FILE):
        df = pd.read_csv(FINALS_FILE).fillna("")
        for col in ["階段", "選手1", "選手2", "勝者", "敗者"]:
            if col in df.columns:
                df[col] = df[col].astype(str)
        return df
    return None


def save_finals(df: Optional[pd.DataFrame]) -> None:
    if df is not None:
        df.to_csv(FINALS_FILE, index=False, encoding="utf-8-sig")
    elif os.path.exists(FINALS_FILE):
        os.remove(FINALS_FILE)
    st.cache_data.clear()


@st.cache_data
def load_team_players() -> pd.DataFrame:
    if os.path.exists(TEAM_DATA_FILE):
        return pd.read_csv(TEAM_DATA_FILE).fillna("")
    return pd.DataFrame(columns=["組別", "選手1", "選手2", "分組"])


def save_team_players(df: pd.DataFrame) -> None:
    df.to_csv(TEAM_DATA_FILE, index=False, encoding="utf-8-sig")
    st.cache_data.clear()


@st.cache_data
def load_team_matches() -> Optional[pd.DataFrame]:
    if os.path.exists(TEAM_MATCH_FILE):
        return pd.read_csv(TEAM_MATCH_FILE).fillna("")
    return None


def save_team_matches(df: Optional[pd.DataFrame]) -> None:
    if df is not None:
        df.to_csv(TEAM_MATCH_FILE, index=False, encoding="utf-8-sig")
    elif os.path.exists(TEAM_MATCH_FILE):
        os.remove(TEAM_MATCH_FILE)
    st.cache_data.clear()


@st.cache_data
def load_team_finals() -> Optional[pd.DataFrame]:
    if os.path.exists(TEAM_FINALS_FILE):
        return pd.read_csv(TEAM_FINALS_FILE).fillna("")
        for col in ["階段", "隊伍1", "隊伍2", "勝隊", "敗隊"]:
            if col in df.columns:
                df[col] = df[col].astype(str)
        return df
    return None


def save_team_finals(df: Optional[pd.DataFrame]) -> None:
    if df is not None:
        df.to_csv(TEAM_FINALS_FILE, index=False, encoding="utf-8-sig")
    elif os.path.exists(TEAM_FINALS_FILE):
        os.remove(TEAM_FINALS_FILE)
    st.cache_data.clear()


df_reg = load_registrations()
df_swiss = load_swiss_matches()
df_finals = load_finals()
df_team_p = load_team_players()
df_team_m = load_team_matches()
df_team_f = load_team_finals()

player_map = (
    dict(zip(df_reg["編號"], df_reg["選手名稱"])) if not df_reg.empty else {}
)


# ==========================================
# 3. 計算邏輯 (瑞士輪 & 團體小組賽)
# ==========================================
def calculate_swiss_cutoff_standings_16() -> Tuple[
    Dict[int, int],
    Dict[int, int],
    List[int],
    List[int],
    List[int],
    Set[Tuple[int, int]],
]:
    wins = {p_id: 0 for p_id in range(1, 17)}
    losses = {p_id: 0 for p_id in range(1, 17)}
    played_pairs = set()

    if df_swiss is not None:
        for _, r in df_swiss.iterrows():
            w = int(r["勝者_編號"])
            p1, p2 = int(r["選手A_編號"]), int(r["選手B_編號"])

            if p1 != 0 and p2 != 0:
                played_pairs.add(tuple(sorted([p1, p2])))

            if w != 0:
                l = p2 if w == p1 else p1
                wins[w] += 1
                losses[l] += 1

    qualified = []
    eliminated = []
    active = []

    for p_id in range(1, 17):
        if wins[p_id] >= 3:
            qualified.append(p_id)
        elif losses[p_id] >= 3:
            eliminated.append(p_id)
        else:
            active.append(p_id)

    active.sort(key=lambda x: (wins[x], -losses[x]), reverse=True)
    return wins, losses, qualified, eliminated, active, played_pairs


def generate_cutoff_next_round_pairs_16(current_round: int) -> List[Dict]:
    (
        wins,
        losses,
        qualified,
        eliminated,
        active,
        played_pairs,
    ) = calculate_swiss_cutoff_standings_16()

    def backtrack(
        candidates: List[int],
    ) -> Optional[List[Tuple[int, int]]]:
        if not candidates:
            return []

        p1 = candidates[0]
        for idx in range(1, len(candidates)):
            p2 = candidates[idx]
            pair = tuple(sorted([p1, p2]))
            if pair not in played_pairs:
                remaining = candidates[1:idx] + candidates[idx + 1 :]
                res = backtrack(remaining)
                if res is not None:
                    return [(p1, p2)] + res

        return None

    new_pairs = backtrack(active)

    if new_pairs is None:
        new_pairs = []
        temp_candidates = active.copy()
        while len(temp_candidates) >= 2:
            p1 = temp_candidates.pop(0)
            match_found = False
            for i, p2 in enumerate(temp_candidates):
                pair = tuple(sorted([p1, p2]))
                if pair not in played_pairs:
                    new_pairs.append((p1, temp_candidates.pop(i)))
                    match_found = True
                    break
            if not match_found:
                new_pairs.append((p1, temp_candidates.pop(0)))

    match_data = []
    for p1, p2 in new_pairs:
        p1_record = f"{wins[p1]}-{losses[p1]}"
        p2_record = f"{wins[p2]}-{losses[p2]}"
        group_label = (
            f"戰績 {p1_record} 區"
            if p1_record == p2_record
            else f"跨組區 ({p1_record} vs {p2_record})"
        )
        match_data.append({
            "輪次": current_round,
            "組別標籤": group_label,
            "選手A_編號": p1,
            "選手B_編號": p2,
            "勝者_編號": 0,
        })

    return match_data


def calculate_group_standings(
    group_teams: List[str],
) -> Tuple[Dict[str, int], Dict[str, int], List[str]]:
    t_wins = {t: 0 for t in group_teams}
    t_losses = {t: 0 for t in group_teams}
    h2h = {}

    if df_team_m is not None:
        for _, r in df_team_m.iterrows():
            t1, t2 = r["隊伍A"], r["隊伍B"]
            w = r["勝隊"]
            if t1 in group_teams and t2 in group_teams and w in group_teams:
                t_wins[w] += 1
                l = t2 if w == t1 else t1
                t_losses[l] += 1
                h2h[(t1, t2)] = w
                h2h[(t2, t1)] = w

    def compare_teams(t1: str, t2: str) -> int:
        if t_wins[t1] != t_wins[t2]:
            return 1 if t_wins[t1] > t_wins[t2] else -1
        if (t1, t2) in h2h:
            return 1 if h2h[(t1, t2)] == t1 else -1
        return 0

    ranked_teams = sorted(
        group_teams, key=cmp_to_key(compare_teams), reverse=True
    )
    return t_wins, t_losses, ranked_teams


# ==========================================
# 4. 側邊欄與權限控制
# ==========================================
if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False

st.sidebar.header("🔑 管理者驗證專區")
is_admin_check = st.sidebar.checkbox(
    "開啟管理員控制權限", value=st.session_state["is_admin"]
)

if is_admin_check != st.session_state["is_admin"]:
    st.session_state["is_admin"] = is_admin_check

if st.session_state["is_admin"]:
    admin_input = st.sidebar.text_input(
        "輸入管理密碼", type="password", key="pwd_input"
    )
    if admin_input == ADMIN_PASSWORD:
        st.sidebar.success("🔓 管理員已授權")
    else:
        st.sidebar.info("💡 預設密碼為: admin")

is_admin = st.session_state["is_admin"]


# ==========================================
# 5. 主頁面：個人賽與團體賽切換
# ==========================================
main_tab1, main_tab2 = st.tabs(
    ["👤 個人賽 (16人 3勝晉級八強)", "👥 團體賽 (8隊 巔峰組/涅槃組+四強)"]
)

# ==========================================
# 👥 團體賽主區塊 (8隊 小組+四強)
# ==========================================
with main_tab2:
    st.title("👥 第四屆 三重盃戰鬥陀螺大賽 - 團體賽")
    st.caption("【團體賽】8 隊分為巔峰組、涅槃組單循環 | 各組前 2 名晉級四強交叉淘汰賽")

    t_tab1, t_tab2, t_tab3, t_tab4 = st.tabs([
        "📝 隊伍與選手登記",
        "⚔️ 循環賽對戰控制台",
        "🏆 四強決賽",
        "📊 團體賽積分榜",
    ])

    with t_tab1:
        st.header("📝 團體賽隊伍與選手登記 (A~H 組)")
        if df_team_p.empty:
            df_team_p = pd.DataFrame({
                "組別": TEAM_NAMES,
                "選手1": [""] * 8,
                "選手2": [""] * 8,
                "分組": ["未分配"] * 8,
            })
        elif "分組" not in df_team_p.columns:
            df_team_p["分組"] = "未分配"

        if is_admin:
            with st.form("team_p_form"):
                st.info("請為 A~H 組各登記 2 位選手名稱：")
                updated_rows = []
                for t in TEAM_NAMES:
                    curr_p1 = (
                        df_team_p.loc[df_team_p["組別"] == t, "選手1"].values[0]
                        if t in df_team_p["組別"].values
                        else ""
                    )
                    curr_p2 = (
                        df_team_p.loc[df_team_p["組別"] == t, "選手2"].values[0]
                        if t in df_team_p["組別"].values
                        else ""
                    )
                    curr_group = (
                        df_team_p.loc[df_team_p["組別"] == t, "分組"].values[0]
                        if t in df_team_p["組別"].values
                        else "未分配"
                    )

                    group_tag = "⚪ 未分配"
                    if curr_group == "巔峰組":
                        group_tag = "🔴 巔峰組"
                    elif curr_group == "涅槃組":
                        group_tag = "🔵 涅槃組"

                    c1, c2, c3 = st.columns([1, 2, 2])
                    with c1:
                        st.markdown(f"### **{t}** ({group_tag})")
                    with c2:
                        p1_val = st.text_input(
                            f"{t} - 選手 1", value=curr_p1, key=f"tp1_{t}"
                        )
                    with c3:
                        p2_val = st.text_input(
                            f"{t} - 選手 2", value=curr_p2, key=f"tp2_{t}"
                        )
                    updated_rows.append({
                        "組別": t,
                        "選手1": p1_val.strip(),
                        "選手2": p2_val.strip(),
                        "分組": curr_group,
                    })

                if st.form_submit_button("💾 儲存團體賽名單", type="primary"):
                    df_team_p = pd.DataFrame(updated_rows)
                    save_team_players(df_team_p)
                    st.success("🎉 團體賽隊伍名單儲存成功！")
                    st.rerun()

            st.write("---")
            col_draw, col_init = st.columns(2)
            with col_draw:
                if st.button("🎲 隨機抽籤分配【巔峰組/涅槃組】", use_container_width=True):
                    shuffled_teams = TEAM_NAMES.copy()
                    random.shuffle(shuffled_teams)

                    pinnacle_teams = shuffled_teams[:4]
                    nirvana_teams = shuffled_teams[4:]

                    for t in TEAM_NAMES:
                        g_val = "巔峰組" if t in pinnacle_teams else "涅槃組"
                        df_team_p.loc[df_team_p["組別"] == t, "分組"] = g_val

                    save_team_players(df_team_p)
                    save_team_matches(None)  # 重置賽程
                    save_team_finals(None)
                    st.toast("🎲 隨機抽籤完成！巔峰組與涅槃組已重新分配！")
                    st.rerun()

            with col_init:
                if st.button(
                    "🚀 初始化團體賽對戰表", type="primary", use_container_width=True
                ):
                    pinnacle_teams = df_team_p[df_team_p["分組"] == "巔峰組"][
                        "組別"
                    ].tolist()
                    nirvana_teams = df_team_p[df_team_p["分組"] == "涅槃組"][
                        "組別"
                    ].tolist()

                    if len(pinnacle_teams) != 4 or len(nirvana_teams) != 4:
                        st.error(
                            "❌ 請先點擊【🎲 隨機抽籤分配【巔峰組/涅槃組】】以確定分組隊伍！"
                        )
                    else:

                        def make_schedule(teams, label):
                            return [
                                (teams[0], teams[1], label),
                                (teams[2], teams[3], label),
                                (teams[0], teams[2], label),
                                (teams[1], teams[3], label),
                                (teams[0], teams[3], label),
                                (teams[1], teams[2], label),
                            ]

                        pinnacle_sched = make_schedule(pinnacle_teams, "巔峰組")
                        nirvana_sched = make_schedule(nirvana_teams, "涅槃組")

                        t_matches = []
                        idx = 1
                        for t1, t2, g_label in pinnacle_sched + nirvana_sched:
                            t_matches.append({
                                "場次": idx,
                                "分組": g_label,
                                "隊伍A": t1,
                                "隊伍B": t2,
                                "勝隊": "未完賽",
                            })
                            idx += 1

                        save_team_matches(pd.DataFrame(t_matches))
                        save_team_finals(None)
                        st.success("🎉 團體賽小組循環賽程生成完畢！")
                        st.rerun()
        else:
            st.dataframe(df_team_p, use_container_width=True, hide_index=True)

    with t_tab2:
        st.header("⚔️ 團體賽小組循環對戰控制台")
        if df_team_m is None or df_team_m.empty:
            st.warning(
                "⏳ 請先在「隊伍與選手登記」分頁點擊【初始化團體賽對戰表】！"
            )
        else:
            for m_idx, r in df_team_m.iterrows():
                m_num = int(r["場次"])
                g_label = r["分組"]
                t1, t2 = r["隊伍A"], r["隊伍B"]
                w_team = r["勝隊"]

                p1_str = (
                    f"({df_team_p.loc[df_team_p['組別']==t1, '選手1'].values[0]} & {df_team_p.loc[df_team_p['組別']==t1, '選手2'].values[0]})"
                    if not df_team_p.empty
                    else ""
                )
                p2_str = (
                    f"({df_team_p.loc[df_team_p['組別']==t2, '選手1'].values[0]} & {df_team_p.loc[df_team_p['組別']==t2, '選手2'].values[0]})"
                    if not df_team_p.empty
                    else ""
                )

                st.write(
                    f"#### 🥊 場次 {m_num} 【{g_label}】：**🔴 {t1}** {p1_str} 🆚"
                    f" **🔵 {t2}** {p2_str}"
                )

                if is_admin:
                    c1, c2, c3 = st.columns([3, 3, 2])
                    with c1:
                        if st.button(
                            f"🏆 {t1} 獲勝",
                            key=f"tm_btn_a_{m_idx}",
                            use_container_width=True,
                            type="primary" if w_team == t1 else "secondary",
                        ):
                            df_team_m.at[m_idx, "勝隊"] = t1
                            save_team_matches(df_team_m)
                            st.toast(f"場次 {m_num}：{t1} 勝出！")
                            st.rerun()
                    with c2:
                        if st.button(
                            f"🏆 {t2} 獲勝",
                            key=f"tm_btn_b_{m_idx}",
                            use_container_width=True,
                            type="primary" if w_team == t2 else "secondary",
                        ):
                            df_team_m.at[m_idx, "勝隊"] = t2
                            save_team_matches(df_team_m)
                            st.toast(f"場次 {m_num}：{t2} 勝出！")
                            st.rerun()
                    with c3:
                        st.caption(f"目前勝隊：`{w_team}`")
                else:
                    st.write(f"比賽結果：`{w_team}`")
                st.write("---")

    with t_tab3:
        st.header("🏆 團體賽 四強交叉決賽")
        completed_tm = (
            sum(1 for w in df_team_m["勝隊"] if w in TEAM_NAMES)
            if df_team_m is not None
            else 0
        )

        pinnacle_teams = (
            df_team_p[df_team_p["分組"] == "巔峰組"]["組別"].tolist()
            if not df_team_p.empty and "分組" in df_team_p.columns
            else []
        )
        nirvana_teams = (
            df_team_p[df_team_p["分組"] == "涅槃組"]["組別"].tolist()
            if not df_team_p.empty and "分組" in df_team_p.columns
            else []
        )

        if (
            df_team_m is None
            or completed_tm < 12
            or len(pinnacle_teams) != 4
            or len(nirvana_teams) != 4
        ):
            st.warning(f"⏳ 團體預賽尚未結束（已完成 {completed_tm}/12 場）")
        else:
            _, _, ranked_a = calculate_group_standings(pinnacle_teams)
            _, _, ranked_b = calculate_group_standings(nirvana_teams)

            a1, a2 = ranked_a[0], ranked_a[1]
            b1, b2 = ranked_b[0], ranked_b[1]

            st.success(
                f"🎉 四強晉級隊伍：巔峰組（第一名：{a1}、第二名：{a2}） |"
                f" 涅槃組（第一名：{b1}、第二名：{b2}）"
            )

            if df_team_f is None or df_team_f.empty:
                finals_data = [
                    {
                        "階段": "準決賽1",
                        "隊伍1": a1,
                        "隊伍2": b2,
                        "勝隊": "",
                        "敗隊": "",
                    },
                    {
                        "階段": "準決賽2",
                        "隊伍1": b1,
                        "隊伍2": a2,
                        "勝隊": "",
                        "敗隊": "",
                    },
                    {
                        "階段": "季軍賽",
                        "隊伍1": "待定",
                        "隊伍2": "待定",
                        "勝隊": "",
                        "敗隊": "",
                    },
                    {
                        "階段": "冠軍賽",
                        "隊伍1": "待定",
                        "隊伍2": "待定",
                        "勝隊": "",
                        "敗隊": "",
                    },
                ]
                df_team_f = pd.DataFrame(finals_data)
                save_team_finals(df_team_f)

            sf1_w = df_team_f.loc[df_team_f["階段"] == "準決賽1", "勝隊"].values[
                0
            ]
            sf2_w = df_team_f.loc[df_team_f["階段"] == "準決賽2", "勝隊"].values[
                0
            ]

            st.write("---")
            st.subheader("🥊 1. 準決賽 (Semi-Finals)")
            col_tf1, col_tf2 = st.columns(2)

            with col_tf1:
                st.markdown(
                    f"##### ⚔️ 準決賽 1：**🔴 {a1} (巔峰1)** 🆚 **🔵 {b2} (涅槃2)**"
                )
                if is_admin:
                    opts_tf1 = ["請選擇勝隊...", a1, b2]
                    curr_tf1 = sf1_w if sf1_w in opts_tf1 else "請選擇勝隊..."
                    sel_tf1 = st.selectbox(
                        "選擇準決賽 1 勝隊：",
                        opts_tf1,
                        index=opts_tf1.index(curr_tf1),
                        key="tf1_sel",
                    )
                    if sel_tf1 != "請選擇勝隊..." and sel_tf1 != sf1_w:
                        loser_tf1 = b2 if sel_tf1 == a1 else a1
                        df_team_f.loc[
                            df_team_f["階段"] == "準決賽1", "勝隊"
                        ] = str(sel_tf1)
                        df_team_f.loc[
                            df_team_f["階段"] == "準決賽1", "敗隊"
                        ] = str(loser_tf1)

                        sf2_l_curr = df_team_f.loc[
                            df_team_f["階段"] == "準決賽2", "敗隊"
                        ].values[0]
                        sf2_w_curr = df_team_f.loc[
                            df_team_f["階段"] == "準決賽2", "勝隊"
                        ].values[0]

                        if loser_tf1 and sf2_l_curr:
                            df_team_f.loc[
                                df_team_f["階段"] == "季軍賽", "隊伍1"
                            ] = str(loser_tf1)
                            df_team_f.loc[
                                df_team_f["階段"] == "季軍賽", "隊伍2"
                            ] = str(sf2_l_curr)
                        if sel_tf1 and sf2_w_curr:
                            df_team_f.loc[
                                df_team_f["階段"] == "冠軍賽", "隊伍1"
                            ] = str(sel_tf1)
                            df_team_f.loc[
                                df_team_f["階段"] == "冠軍賽", "隊伍2"
                            ] = str(sf2_w_curr)

                        save_team_finals(df_team_f)
                        st.rerun()
                else:
                    st.write(f"勝隊：`{sf1_w if sf1_w else '比賽中'}`")

            with col_tf2:
                st.markdown(
                    f"##### ⚔️ 準決賽 2：**🔴 {b1} (涅槃1)** 🆚 **🔵 {a2} (巔峰2)**"
                )
                if is_admin:
                    opts_tf2 = ["請選擇勝隊...", b1, a2]
                    curr_tf2 = sf2_w if sf2_w in opts_tf2 else "請選擇勝隊..."
                    sel_tf2 = st.selectbox(
                        "選擇準決賽 2 勝隊：",
                        opts_tf2,
                        index=opts_tf2.index(curr_tf2),
                        key="tf2_sel",
                    )
                    if sel_tf2 != "請選擇勝隊..." and sel_tf2 != sf2_w:
                        loser_tf2 = a2 if sel_tf2 == b1 else b1
                        df_team_f.loc[
                            df_team_f["階段"] == "準決賽2", "勝隊"
                        ] = str(sel_tf2)
                        df_team_f.loc[
                            df_team_f["階段"] == "準決賽2", "敗隊"
                        ] = str(loser_tf2)

                        sf1_l_curr = df_team_f.loc[
                            df_team_f["階段"] == "準決賽1", "敗隊"
                        ].values[0]
                        sf1_w_curr = df_team_f.loc[
                            df_team_f["階段"] == "準決賽1", "勝隊"
                        ].values[0]

                        if loser_tf2 and sf1_l_curr:
                            df_team_f.loc[
                                df_team_f["階段"] == "季軍賽", "隊伍1"
                            ] = str(sf1_l_curr)
                            df_team_f.loc[
                                df_team_f["階段"] == "季軍賽", "隊伍2"
                            ] = str(loser_tf2)
                        if sel_tf2 and sf1_w_curr:
                            df_team_f.loc[
                                df_team_f["階段"] == "冠軍賽", "隊伍1"
                            ] = str(sf1_w_curr)
                            df_team_f.loc[
                                df_team_f["階段"] == "冠軍賽", "隊伍2"
                            ] = str(sel_tf2)

                        save_team_finals(df_team_f)
                        st.rerun()
                else:
                    st.write(f"勝隊：`{sf2_w if sf2_w else '比賽中'}`")

            st.write("---")
            st.subheader("🥇 2. 總決賽 (Finals)")
            col_t3rd, col_t1st = st.columns(2)

            tp3_1 = str(
                df_team_f.loc[df_team_f["階段"] == "季軍賽", "隊伍1"].values[0]
            )
            tp3_2 = str(
                df_team_f.loc[df_team_f["階段"] == "季軍賽", "隊伍2"].values[0]
            )
            tp3_w = str(
                df_team_f.loc[df_team_f["階段"] == "季軍賽", "勝隊"].values[0]
            )

            tp1_1 = str(
                df_team_f.loc[df_team_f["階段"] == "冠軍賽", "隊伍1"].values[0]
            )
            tp1_2 = str(
                df_team_f.loc[df_team_f["階段"] == "冠軍賽", "隊伍2"].values[0]
            )
            tp1_w = str(
                df_team_f.loc[df_team_f["階段"] == "冠軍賽", "勝隊"].values[0]
            )

            with col_t3rd:
                st.markdown("##### 🥉 季軍賽 (3rd Place)")
                if tp3_1 != "待定" and tp3_2 != "待定":
                    st.write(f"🔴 **{tp3_1}** VS 🔵 **{tp3_2}**")
                    if is_admin:
                        opts_t3 = ["請選擇勝隊...", tp3_1, tp3_2]
                        curr_t3 = tp3_w if tp3_w in opts_t3 else "請選擇勝隊..."
                        sel_t3 = st.selectbox(
                            "選擇季軍隊伍：",
                            opts_t3,
                            index=opts_t3.index(curr_t3),
                            key="t3_sel",
                        )
                        if sel_t3 != "請選擇勝隊..." and sel_t3 != tp3_w:
                            loser_t3 = tp3_2 if sel_t3 == tp3_1 else tp3_1
                            df_team_f.loc[
                                df_team_f["階段"] == "季軍賽", "勝隊"
                            ] = str(sel_t3)
                            df_team_f.loc[
                                df_team_f["階段"] == "季軍賽", "敗隊"
                            ] = str(loser_t3)
                            save_team_finals(df_team_f)
                            st.rerun()
                    else:
                        st.write(f"勝隊：`{tp3_w if tp3_w else '比賽中'}`")

            with col_t1st:
                st.markdown("##### 👑 冠軍賽 (Championship)")
                if tp1_1 != "待定" and tp1_2 != "待定":
                    st.write(f"🔴 **{tp1_1}** VS 🔵 **{tp1_2}**")
                    if is_admin:
                        opts_t1 = ["請選擇勝隊...", tp1_1, tp1_2]
                        curr_t1 = tp1_w if tp1_w in opts_t1 else "請選擇勝隊..."
                        sel_t1 = st.selectbox(
                            "選擇總冠軍隊伍：",
                            opts_t1,
                            index=opts_t1.index(curr_t1),
                            key="t1_sel",
                        )
                        if sel_t1 != "請選擇勝隊..." and sel_t1 != tp1_w:
                            loser_t1 = tp1_2 if sel_t1 == tp1_1 else tp1_1
                            df_team_f.loc[
                                df_team_f["階段"] == "冠軍賽", "勝隊"
                            ] = str(sel_t1)
                            df_team_f.loc[
                                df_team_f["階段"] == "冠軍賽", "敗隊"
                            ] = str(loser_t1)
                            save_team_finals(df_team_f)
                            st.rerun()
                    else:
                        st.write(f"勝隊：`{tp1_w if tp1_w else '比賽中'}`")

            if tp1_w and tp3_w and tp1_w != "" and tp3_w != "":
                st.write("---")
                st.balloons()
                t_champ = df_team_f.loc[
                    df_team_f["階段"] == "冠軍賽", "勝隊"
                ].values[0]
                t_runner = df_team_f.loc[
                    df_team_f["階段"] == "冠軍賽", "敗隊"
                ].values[0]
                t_third = df_team_f.loc[
                    df_team_f["階段"] == "季軍賽", "勝隊"
                ].values[0]
                t_fourth = df_team_f.loc[
                    df_team_f["階段"] == "季軍賽", "敗隊"
                ].values[0]

                st.success(f"""
                ### 🎉 團體賽最終榮譽榜：
                * 🥇 **總冠軍**：{t_champ}
                * 🥈 **亞軍**：{t_runner}
                * 🥉 **季軍**：{t_third}
                * 🏅 **殿軍**：{t_fourth}
                """)

    with t_tab4:
        st.header("📊 團體賽小組積分榜")
        if df_team_m is not None:
            pinnacle_teams = (
                df_team_p[df_team_p["分組"] == "巔峰組"]["組別"].tolist()
                if not df_team_p.empty and "分組" in df_team_p.columns
                else []
            )
            nirvana_teams = (
                df_team_p[df_team_p["分組"] == "涅槃組"]["組別"].tolist()
                if not df_team_p.empty and "分組" in df_team_p.columns
                else []
            )

            if len(pinnacle_teams) == 4 and len(nirvana_teams) == 4:
                c_a, c_b = st.columns(2)
                with c_a:
                    st.subheader("🔴 巔峰組 (Pinnacle Group)")
                    w_a, l_a, r_a = calculate_group_standings(pinnacle_teams)
                    tb_a = [
                        {
                            "排名": f"第 {i} 名",
                            "隊伍": t,
                            "勝": w_a[t],
                            "敗": l_a[t],
                        }
                        for i, t in enumerate(r_a, 1)
                    ]
                    st.table(tb_a)
                with c_b:
                    st.subheader("🔵 涅槃組 (Nirvana Group)")
                    w_b, l_b, r_b = calculate_group_standings(nirvana_teams)
                    tb_b = [
                        {
                            "排名": f"第 {i} 名",
                            "隊伍": t,
                            "勝": w_b[t],
                            "敗": l_b[t],
                        }
                        for i, t in enumerate(r_b, 1)
                    ]
                    st.table(tb_b)
            else:
                st.info("💡 請先進行【巔峰組/涅槃組】隨機抽籤分配與對戰表初始化！")

# ==========================================
# 👤 個人賽主區塊 (16人 3勝晉級八強)
# ==========================================
with main_tab1:
    st.title("💥 第四屆 三重盃戰鬥陀螺大賽 - 個人賽")
    st.caption(
        "【個人賽】限定 16 人 瑞士輪淘汰賽 (率先滿 3 勝者晉級八強，先滿 3 敗者淘汰)"
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 選手報名與抽籤",
        "⚔️ 預賽：瑞士輪控制台",
        "🗓️ 預賽賽程對戰表",
        "🏆 決賽：八強單淘汰賽",
        "📊 即時戰績榜",
    ])

    # --- Tab 1: 報名與抽籤 ---
    with tab1:
        st.header("📝 選手報名 (限定 16 人)")
        if is_admin:
            with st.form("reg_form_16", clear_on_submit=True):
                col_name, col_btn = st.columns([3, 1])
                with col_name:
                    name = st.text_input("輸入選手名稱*")
                with col_btn:
                    st.markdown("<br>", unsafe_allow_html=True)
                    submit_reg = st.form_submit_button(
                        "📥 新增選手", use_container_width=True
                    )

                if submit_reg:
                    if not name.strip():
                        st.error("❌ 名稱不能為空！")
                    elif name.strip() in df_reg["選手名稱"].values:
                        st.error(f"❌ 選手【{name}】已在名單中！")
                    elif len(df_reg) >= 16:
                        st.error("❌ 個人賽限定 16 人，已滿額！")
                    else:
                        new_p = {"編號": 0, "選手名稱": name.strip()}
                        df_reg = pd.concat(
                            [df_reg, pd.DataFrame([new_p])], ignore_index=True
                        )
                        save_registrations(df_reg)
                        st.success(f"🎉 選手【{name}】報名成功！")
                        st.rerun()

        st.subheader(f"👥 已報名選手名單 (共 {len(df_reg)} / 16 人)")
        if not df_reg.empty:
            st.dataframe(df_reg[["編號", "選手名稱"]], use_container_width=True)

        if is_admin and len(df_reg) == 16 and (df_reg["編號"] == 0).all():
            if st.button(
                "🎲 確定隨機產生 1~16 號編號與第 1 輪對戰",
                type="primary",
                use_container_width=True,
            ):
                shuffled_df = df_reg.sample(frac=1).reset_index(drop=True)
                shuffled_df["編號"] = list(range(1, 17))
                df_reg = shuffled_df
                save_registrations(df_reg)

                p_ids = list(range(1, 17))
                random.shuffle(p_ids)

                round1_matches = []
                for i in range(0, 16, 2):
                    round1_matches.append({
                        "輪次": 1,
                        "組別標籤": "戰績 0-0 區",
                        "選手A_編號": p_ids[i],
                        "選手B_編號": p_ids[i + 1],
                        "勝者_編號": 0,
                    })

                save_swiss_matches(pd.DataFrame(round1_matches))
                st.success("🎉 16 人隨機抽籤完成！第 1 輪對戰已自動產生！")
                st.rerun()

    # --- Tab 2: 控制台 ---
    with tab2:
        st.header("⚔️ 預賽：瑞士輪控制台 (3勝晉級八強 / 3敗淘汰)")
        if df_swiss is None or (df_reg["編號"] == 0).all():
            st.warning("⏳ 請先集滿 16 人並完成盲抽！")
        else:
            (
                wins,
                losses,
                qualified,
                eliminated,
                active,
                _,
            ) = calculate_swiss_cutoff_standings_16()

            current_max_round = int(df_swiss["輪次"].max())
            r_matches = df_swiss[df_swiss["輪次"] == current_max_round]
            completed_r_count = sum(1 for w in r_matches["勝者_編號"] if w != 0)
            total_r_matches = len(r_matches)

            if qualified:
                q_list = [f"{p}號 {player_map.get(p, '')}" for p in qualified]
                qualified_str = ", ".join(q_list)
            else:
                qualified_str = "無"

            if eliminated:
                e_list = [f"{p}號 {player_map.get(p, '')}" for p in eliminated]
                eliminated_str = ", ".join(e_list)
            else:
                eliminated_str = "無"

            st.info(
                f"### 📍 當前進行：第 {current_max_round} 輪 (該輪進度：{completed_r_count} / {total_r_matches} 場)\n"
                f"* 🏆 **已晉級八強 ({len(qualified)}/8 人)**：{qualified_str}\n"
                f"* ❌ **已淘汰 ({len(eliminated)} 人)**：{eliminated_str}"
            )

            for m_idx, row in r_matches.iterrows():
                p1_id, p2_id, w_id = (
                    int(row["選手A_編號"]),
                    int(row["選手B_編號"]),
                    int(row["勝者_編號"]),
                )
                p1_str = f"{p1_id}號 {player_map.get(p1_id, '')}"
                p2_str = f"{p2_id}號 {player_map.get(p2_id, '')}"

                st.write(
                    f"#### 🥊 【{row['組別標籤']}】 **🔴 {p1_str}** 🆚 **🔵"
                    f" {p2_str}**"
                )

                if is_admin:
                    c1, c2, c3 = st.columns([2, 2, 3])
                    with c1:
                        if st.button(
                            f"🏆 {p1_str} 獲勝",
                            key=f"r{current_max_round}_{m_idx}_p1",
                            use_container_width=True,
                            type="primary"
                            if w_id == p1_id
                            else "secondary",
                        ):
                            df_swiss.at[m_idx, "勝者_編號"] = p1_id
                            save_swiss_matches(df_swiss)
                            st.rerun()
                    with c2:
                        if st.button(
                            f"🏆 {p2_str} 獲勝",
                            key=f"r{current_max_round}_{m_idx}_p2",
                            use_container_width=True,
                            type="primary"
                            if w_id == p2_id
                            else "secondary",
                        ):
                            df_swiss.at[m_idx, "勝者_編號"] = p2_id
                            save_swiss_matches(df_swiss)
                            st.rerun()
                    with c3:
                        st.caption(
                            f"勝者： `{player_map.get(w_id, '未登記')}`"
                        )
                st.write("---")

            if is_admin and completed_r_count == total_r_matches:
                if len(qualified) < 8 and len(active) >= 2:
                    if st.button(
                        f"🚀 生成第 {current_max_round + 1} 輪對戰"
                        f" (剩餘 {len(active)} 人比賽中)",
                        type="primary",
                        use_container_width=True,
                    ):
                        next_m = generate_cutoff_next_round_pairs_16(
                            current_max_round + 1
                        )
                        df_swiss = pd.concat(
                            [df_swiss, pd.DataFrame(next_m)],
                            ignore_index=True,
                        )
                        save_swiss_matches(df_swiss)
                        st.rerun()
                elif len(qualified) >= 8:
                    st.success(
                        "🎉 八強晉級名單已滿 8 人！請至【決賽】頁面開打八強淘汰賽！"
                    )

    # --- Tab 3: 對戰表 ---
    with tab3:
        st.header("🗓️ 預賽對戰紀錄")
        if df_swiss is not None:
            for r in range(1, int(df_swiss["輪次"].max()) + 1):
                st.subheader(f"🌀 第 {r} 輪")
                r_df = df_swiss[df_swiss["輪次"] == r]
                disp = []
                for _, row in r_df.iterrows():
                    p1_id, p2_id, w_id = (
                        int(row["選手A_編號"]),
                        int(row["選手B_編號"]),
                        int(row["勝者_編號"]),
                    )
                    disp.append({
                        "組別": row["組別標籤"],
                        "選手 A": f"{p1_id}號 {player_map.get(p1_id, '')}",
                        "選手 B": f"{p2_id}號 {player_map.get(p2_id, '')}",
                        "獲勝者": (
                            player_map.get(w_id, "⏳ 待定")
                            if w_id != 0
                            else "⏳ 待定"
                        ),
                    })
                st.dataframe(
                    pd.DataFrame(disp),
                    use_container_width=True,
                    hide_index=True,
                )

    # --- Tab 4: 決賽 ---
    with tab4:
        st.header("🏆 八強單淘汰決賽")
        (
            wins,
            losses,
            qualified,
            eliminated,
            active,
            _,
        ) = calculate_swiss_cutoff_standings_16()

        if len(qualified) < 8:
            st.warning(
                f"⏳ 預賽尚未篩選出 8 位 3 勝選手（目前已有 {len(qualified)} / 8 位晉級）"
            )
        else:
            q_names = [f"{p}號 {player_map.get(p, '')}" for p in qualified[:8]]
            st.success(f"🎉 晉級八強選手：{', '.join(q_names)}")

            if is_admin:
                draw_btn_text = (
                    "🎲 進行八強隨機抽籤 / 重新對調"
                    if df_finals is not None and not df_finals.empty
                    else "🎲 進行八強隨機抽籤"
                )
                if st.button(draw_btn_text, type="primary"):
                    shuffled_8 = qualified[:8].copy()
                    random.shuffle(shuffled_8)

                    s = [str(player_map.get(p, "")) for p in shuffled_8]
                    finals_data = [
                        {
                            "階段": "半準決賽1",
                            "選手1": s[0],
                            "選手2": s[1],
                            "勝者": "",
                            "敗者": "",
                        },
                        {
                            "階段": "半準決賽2",
                            "選手1": s[2],
                            "選手2": s[3],
                            "勝者": "",
                            "敗者": "",
                        },
                        {
                            "階段": "半準決賽3",
                            "選手1": s[4],
                            "選手2": s[5],
                            "勝者": "",
                            "敗者": "",
                        },
                        {
                            "階段": "半準決賽4",
                            "選手1": s[6],
                            "選手2": s[7],
                            "勝者": "",
                            "敗者": "",
                        },
                        {
                            "階段": "準決賽A",
                            "選手1": "待定",
                            "選手2": "待定",
                            "勝者": "",
                            "敗者": "",
                        },
                        {
                            "階段": "準決賽B",
                            "選手1": "待定",
                            "選手2": "待定",
                            "勝者": "",
                            "敗者": "",
                        },
                        {
                            "階段": "季軍賽",
                            "選手1": "待定",
                            "選手2": "待定",
                            "勝者": "",
                            "敗者": "",
                        },
                        {
                            "階段": "冠軍賽",
                            "選手1": "待定",
                            "選手2": "待定",
                            "勝者": "",
                            "敗者": "",
                        },
                    ]
                    df_finals = pd.DataFrame(finals_data)
                    save_finals(df_finals)
                    st.toast("🎲 八強對戰組合已產生！")
                    st.rerun()

            if df_finals is None or df_finals.empty:
                st.info(
                    "💡 請管理員點擊上方【🎲 進行八強隨機抽籤】以產生對戰圖！"
                )
            else:
                for col in ["階段", "選手1", "選手2", "勝者", "敗者"]:
                    df_finals[col] = df_finals[col].astype(str)

                st.write("---")
                st.subheader("🥊 1. 八強半準決賽 (Quarter-Finals)")
                col1, col2, col3, col4 = st.columns(4)

                q_stages = ["半準決賽1", "半準決賽2", "半準決賽3", "半準決賽4"]
                q_cols = [col1, col2, col3, col4]

                for idx, stage in enumerate(q_stages):
                    with q_cols[idx]:
                        p1 = df_finals.loc[
                            df_finals["階段"] == stage, "選手1"
                        ].values[0]
                        p2 = df_finals.loc[
                            df_finals["階段"] == stage, "選手2"
                        ].values[0]
                        w = df_finals.loc[
                            df_finals["階段"] == stage, "勝者"
                        ].values[0]

                        st.markdown(f"##### ⚔️ {stage}")
                        st.write(f"🔴 **{p1}** VS 🔵 **{p2}**")

                        if is_admin:
                            opts = ["請選擇勝者...", p1, p2]
                            curr = w if w in opts else "請選擇勝者..."
                            sel = st.selectbox(
                                f"勝者 ({stage})：",
                                opts,
                                index=opts.index(curr),
                                key=f"sel_{stage}",
                            )
                            if sel != "請選擇勝者..." and sel != w:
                                loser = p2 if sel == p1 else p1
                                df_finals.loc[
                                    df_finals["階段"] == stage, "勝者"
                                ] = str(sel)
                                df_finals.loc[
                                    df_finals["階段"] == stage, "敗者"
                                ] = str(loser)

                                w1 = df_finals.loc[
                                    df_finals["階段"] == "半準決賽1", "勝者"
                                ].values[0]
                                w2 = df_finals.loc[
                                    df_finals["階段"] == "半準決賽2", "勝者"
                                ].values[0]
                                w3 = df_finals.loc[
                                    df_finals["階段"] == "半準決賽3", "勝者"
                                ].values[0]
                                w4 = df_finals.loc[
                                    df_finals["階段"] == "半準決賽4", "勝者"
                                ].values[0]

                                if w1 and w2:
                                    df_finals.loc[
                                        df_finals["階段"] == "準決賽A", "選手1"
                                    ] = str(w1)
                                    df_finals.loc[
                                        df_finals["階段"] == "準決賽A", "選手2"
                                    ] = str(w2)
                                if w3 and w4:
                                    df_finals.loc[
                                        df_finals["階段"] == "準決賽B", "選手1"
                                    ] = str(w3)
                                    df_finals.loc[
                                        df_finals["階段"] == "準決賽B", "選手2"
                                    ] = str(w4)

                                save_finals(df_finals)
                                st.rerun()
                        else:
                            st.write(f"勝者：`{w if w else '比賽中'}`")

                st.write("---")
                st.subheader("🥊 2. 準決賽 (Semi-Finals)")
                col_sfa, col_sfb = st.columns(2)

                sf_a_p1 = df_finals.loc[
                    df_finals["階段"] == "準決賽A", "選手1"
                ].values[0]
                sf_a_p2 = df_finals.loc[
                    df_finals["階段"] == "準決賽A", "選手2"
                ].values[0]
                sf_a_w = df_finals.loc[
                    df_finals["階段"] == "準決賽A", "勝者"
                ].values[0]

                sf_b_p1 = df_finals.loc[
                    df_finals["階段"] == "準決賽B", "選手1"
                ].values[0]
                sf_b_p2 = df_finals.loc[
                    df_finals["階段"] == "準決賽B", "選手2"
                ].values[0]
                sf_b_w = df_finals.loc[
                    df_finals["階段"] == "準決賽B", "勝者"
                ].values[0]

                with col_sfa:
                    st.markdown("##### ⚔️ 準決賽 A")
                    st.write(f"🔴 **{sf_a_p1}** VS 🔵 **{sf_a_p2}**")
                    if is_admin and sf_a_p1 != "待定" and sf_a_p2 != "待定":
                        opts_a = ["請選擇勝者...", sf_a_p1, sf_a_p2]
                        curr_a = sf_a_w if sf_a_w in opts_a else "請選擇勝者..."
                        sel_a = st.selectbox(
                            "選擇準決賽 A 勝者：",
                            opts_a,
                            index=opts_a.index(curr_a),
                            key="sel_sfa",
                        )
                        if sel_a != "請選擇勝者..." and sel_a != sf_a_w:
                            loser_a = sf_a_p2 if sel_a == sf_a_p1 else sf_a_p1
                            df_finals.loc[
                                df_finals["階段"] == "準決賽A", "勝者"
                            ] = str(sel_a)
                            df_finals.loc[
                                df_finals["階段"] == "準決賽A", "敗者"
                            ] = str(loser_a)

                            sf_b_l = df_finals.loc[
                                df_finals["階段"] == "準決賽B", "敗者"
                            ].values[0]
                            sf_b_w_curr = df_finals.loc[
                                df_finals["階段"] == "準決賽B", "勝者"
                            ].values[0]

                            if loser_a and sf_b_l and sf_b_l != "":
                                df_finals.loc[
                                    df_finals["階段"] == "季軍賽", "選手1"
                                ] = str(loser_a)
                                df_finals.loc[
                                    df_finals["階段"] == "季軍賽", "選手2"
                                ] = str(sf_b_l)
                            if sel_a and sf_b_w_curr and sf_b_w_curr != "":
                                df_finals.loc[
                                    df_finals["階段"] == "冠軍賽", "選手1"
                                ] = str(sel_a)
                                df_finals.loc[
                                    df_finals["階段"] == "冠軍賽", "選手2"
                                ] = str(sf_b_w_curr)

                            save_finals(df_finals)
                            st.rerun()
                    else:
                        st.write(f"勝者：`{sf_a_w if sf_a_w else '未決定'}`")

                with col_sfb:
                    st.markdown("##### ⚔️ 準決賽 B")
                    st.write(f"🔴 **{sf_b_p1}** VS 🔵 **{sf_b_p2}**")
                    if is_admin and sf_b_p1 != "待定" and sf_b_p2 != "待定":
                        opts_b = ["請選擇勝者...", sf_b_p1, sf_b_p2]
                        curr_b = sf_b_w if sf_b_w in opts_b else "請選擇勝者..."
                        sel_b = st.selectbox(
                            "選擇準決賽 B 勝者：",
                            opts_b,
                            index=opts_b.index(curr_b),
                            key="sel_sfb",
                        )
                        if sel_b != "請選擇勝者..." and sel_b != sf_b_w:
                            loser_b = sf_b_p2 if sel_b == sf_b_p1 else sf_b_p1
                            df_finals.loc[
                                df_finals["階段"] == "準決賽B", "勝者"
                            ] = str(sel_b)
                            df_finals.loc[
                                df_finals["階段"] == "準決賽B", "敗者"
                            ] = str(loser_b)

                            sf_a_l = df_finals.loc[
                                df_finals["階段"] == "準決賽A", "敗者"
                            ].values[0]
                            sf_a_w_curr = df_finals.loc[
                                df_finals["階段"] == "準決賽A", "勝者"
                            ].values[0]

                            if loser_b and sf_a_l and sf_a_l != "":
                                df_finals.loc[
                                    df_finals["階段"] == "季軍賽", "選手1"
                                ] = str(sf_a_l)
                                df_finals.loc[
                                    df_finals["階段"] == "季軍賽", "選手2"
                                ] = str(loser_b)
                            if sel_b and sf_a_w_curr and sf_a_w_curr != "":
                                df_finals.loc[
                                    df_finals["階段"] == "冠軍賽", "選手1"
                                ] = str(sf_a_w_curr)
                                df_finals.loc[
                                    df_finals["階段"] == "冠軍賽", "選手2"
                                ] = str(sel_b)

                            save_finals(df_finals)
                            st.rerun()
                    else:
                        st.write(f"勝者：`{sf_b_w if sf_b_w else '未決定'}`")

                st.write("---")
                st.subheader("🥇 3. 總決賽 (Finals)")
                col_3rd, col_1st = st.columns(2)

                p3_1 = str(
                    df_finals.loc[
                        df_finals["階段"] == "季軍賽", "選手1"
                    ].values[0]
                )
                p3_2 = str(
                    df_finals.loc[
                        df_finals["階段"] == "季軍賽", "選手2"
                    ].values[0]
                )
                p3_w = str(
                    df_finals.loc[
                        df_finals["階段"] == "季軍賽", "勝者"
                    ].values[0]
                )

                p1_1 = str(
                    df_finals.loc[
                        df_finals["階段"] == "冠軍賽", "選手1"
                    ].values[0]
                )
                p1_2 = str(
                    df_finals.loc[
                        df_finals["階段"] == "冠軍賽", "選手2"
                    ].values[0]
                )
                p1_w = str(
                    df_finals.loc[
                        df_finals["階段"] == "冠軍賽", "勝者"
                    ].values[0]
                )

                with col_3rd:
                    st.markdown("##### 🥉 季軍賽 (3rd Place)")
                    if p3_1 != "待定" and p3_2 != "待定":
                        st.write(f"🔴 **{p3_1}** VS 🔵 **{p3_2}**")
                        if is_admin:
                            opts_3 = ["請選擇勝者...", p3_1, p3_2]
                            curr_3 = (
                                p3_w if p3_w in opts_3 else "請選擇勝者..."
                            )
                            sel_3 = st.selectbox(
                                "選擇季軍賽勝者：",
                                opts_3,
                                index=opts_3.index(curr_3),
                                key="p3_sel",
                            )
                            if sel_3 != "請選擇勝者..." and sel_3 != p3_w:
                                loser_3 = p3_2 if sel_3 == p3_1 else p3_1
                                df_finals.loc[
                                    df_finals["階段"] == "季軍賽", "勝者"
                                ] = str(sel_3)
                                df_finals.loc[
                                    df_finals["階段"] == "季軍賽", "敗者"
                                ] = str(loser_3)
                                save_finals(df_finals)
                                st.rerun()
                        else:
                            st.write(f"勝者：`{p3_w if p3_w else '未決定'}`")

                with col_1st:
                    st.markdown("##### 👑 冠軍賽 (Championship)")
                    if p1_1 != "待定" and p1_2 != "待定":
                        st.write(f"🔴 **{p1_1}** VS 🔵 **{p1_2}**")
                        if is_admin:
                            opts_1 = ["請選擇勝者...", p1_1, p1_2]
                            curr_1 = (
                                p1_w if p1_w in opts_1 else "請選擇勝者..."
                            )
                            sel_1 = st.selectbox(
                                "選擇冠軍賽勝者：",
                                opts_1,
                                index=opts_1.index(curr_1),
                                key="p1_sel",
                            )
                            if sel_1 != "請選擇勝者..." and sel_1 != p1_w:
                                loser_1 = p1_2 if sel_1 == p1_1 else p1_1
                                df_finals.loc[
                                    df_finals["階段"] == "冠軍賽", "勝者"
                                ] = str(sel_1)
                                df_finals.loc[
                                    df_finals["階段"] == "冠軍賽", "敗者"
                                ] = str(loser_1)
                                save_finals(df_finals)
                                st.rerun()
                        else:
                            st.write(f"勝者：`{p1_w if p1_w else '未決定'}`")

                if p1_w and p3_w and p1_w != "" and p3_w != "":
                    st.write("---")
                    st.balloons()
                    champion = df_finals.loc[
                        df_finals["階段"] == "冠軍賽", "勝者"
                    ].values[0]
                    runner_up = df_finals.loc[
                        df_finals["階段"] == "冠軍賽", "敗者"
                    ].values[0]
                    third_place = df_finals.loc[
                        df_finals["階段"] == "季軍賽", "勝者"
                    ].values[0]
                    fourth_place = df_finals.loc[
                        df_finals["階段"] == "季軍賽", "敗者"
                    ].values[0]

                    st.success(f"""
                    ### 🎉 個人賽最終前 4 強榮譽榜：
                    * 🥇 **冠軍**：{champion}
                    * 🥈 **亞軍**：{runner_up}
                    * 🥉 **季軍**：{third_place}
                    * 🏅 **殿軍**：{fourth_place}
                    """)

    # --- Tab 5: 戰績榜 ---
    with tab5:
        st.header("📊 即時選手戰績榜")
        if df_swiss is not None:
            (
                wins,
                losses,
                qualified,
                eliminated,
                active,
                _,
            ) = calculate_swiss_cutoff_standings_16()

            all_p_sorted = sorted(
                range(1, 17), key=lambda x: (wins[x], -losses[x]), reverse=True
            )

            tb = []
            for p_id in all_p_sorted:
                st_str = "🟢 進行中"
                if p_id in qualified:
                    st_str = "🏆 已晉級八強"
                elif p_id in eliminated:
                    st_str = "❌ 已淘汰"

                tb.append({
                    "編號": f"{p_id} 號",
                    "選手名稱": player_map.get(p_id, ""),
                    "勝場": wins[p_id],
                    "敗場": losses[p_id],
                    "當前狀態": st_str,
                })
            st.table(tb)
