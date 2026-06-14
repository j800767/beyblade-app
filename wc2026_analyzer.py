import streamlit as st

# ==========================================
# 🎨 網頁基礎配置（嚴格放在第一行，保證首頁正常載入）
# ==========================================
st.set_page_config(
    page_title="2026 世界盃大數據運彩精算系統",
    page_icon="⚽",
    layout="wide"
)

import datetime
import io
import pandas as pd
import numpy as np
from scipy.stats import poisson
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

class WC2026BettingAnalyzer:
    def __init__(self):
        # 🏆 48國官方戰力權重矩陣
        self.power_index = {
            "法國": 94.2, "阿根廷": 93.8, "西班牙": 93.5, "英格蘭": 92.8, "葡萄牙": 91.5,
            "德國": 90.8, "荷蘭": 89.5, "義大利": 88.2, "比利時": 87.5, "克羅埃西亞": 86.0,
            "瑞士": 83.5, "丹麥": 82.8, "土耳其": 82.0, "烏克蘭": 80.5, "捷克": 79.5, "波赫": 76.5,
            "巴西": 94.5, "烏拉圭": 89.0, "哥倫比亞": 87.2, "厄瓜多": 82.5, "巴拉圭": 78.0, "秘魯": 76.0,
            "美國": 85.5, "墨西哥": 84.0, "加拿大": 78.8, "哥斯大黎加": 77.2, "牙買加": 75.8, "巴拿馬": 75.0,
            "摩洛哥": 86.8, "塞內加爾": 84.2, "奈及利亞": 81.5, "突尼西亞": 78.2, "阿爾及利亞": 78.0, 
            "埃及": 79.0, "喀麥隆": 77.5, "馬利": 74.8, "南非": 74.0,
            "日本": 84.8, "伊朗": 81.8, "南韓": 81.5, "澳洲": 80.2, "沙烏地阿拉伯": 77.0, 
            "卡達": 75.0, "烏茲別克": 74.5, "伊拉克": 73.8, "阿聯": 72.5, "紐西蘭": 71.0,
            "海地": 68.5, "蘇格蘭": 78.5
        }

    def fetch_live_odds(self, home_team: str, away_team: str) -> dict:
        h_idx = self.power_index.get(home_team, 80.0)
        a_idx = self
