import streamlit as st
import numpy as np
import pandas as pd

# --- 1. [修正] 全スキルの定義 (関数の前に配置) ---
# DQX公式の習得レベルに基づいています
ALL_SKILLS = {
    "通常縫い": {"cost": 5, "lv": 1},
    "加減縫い": {"cost": 10, "lv": 3},
    "水平縫い": {"cost": 10, "lv": 7},
    "たすき縫い": {"cost": 7, "lv": 11},
    "垂直縫い": {"cost": 10, "lv": 15},
    "2倍縫い": {"cost": 9, "lv": 19},
    "3倍縫い": {"cost": 12, "lv": 23},
    "精神統一": {"cost": 7, "lv": 27},
    "糸ほぐし": {"cost": 16, "lv": 31},
    "逆たすき縫い": {"cost": 7, "lv": 35},
    "巻き込み縫い": {"cost": 18, "lv": 41},
    "しつけがけ": {"cost": 24, "lv": 47},
}

# ぬいパワー倍率
POWER_RATES = {"弱い": 0.5, "普通": 1.0, "強い": 1.5, "最強": 2.0}

# 縫い数値の出現分布 (中央値が出やすく、端が出にくい山なり分布をシミュレート)
# 12~18の場合、15(基準)が最も確率が高い
BASE_DIST = {
    "通常": {12:1, 13:2, 14:3, 15:4, 16:3, 17:2, 18:1},
    "加減": {6:1, 7:2, 8:2, 9:1},
}

# --- 2. 内部ロジック関数 ---

def calculate_distribution(skill_name, power, is_shitsuke):
    """特技と環境に応じた全出現数値とその重みを計算"""
    if "加減" in skill_name:
        base = BASE_DIST["加減"]
    else:
        base = BASE_DIST["通常"]
    
    # 3倍縫いなどは基本値をスライドさせて計算
    mult_skill = 2.0 if "2倍" in skill_name else 3.0 if "3倍" in skill_name else 1.0
    rate = POWER_RATES[power]
    shitsuke_mult = 2.0 if is_shitsuke else 1.0
    
    dist = {}
    for v, weight in base.items():
        # DQX計算式: int(int(基本値 * スキル倍率) * パワー倍率) * しつけ倍率
        # しつけがけは最終値を2倍にするため、奇数は出現しなくなる
        res = int(int(int(v * mult_skill) * rate) * shitsuke_mult)
        dist[res] = dist.get(res, 0) + weight
    return dist

def get_best_move(target_diff, power, is_shitsuke, current_level):
    """AIが現在の残り数値に対して最も『会心(0)』になる確率が高い手を提案"""
    available_list = [name for name, d in ALL_SKILLS.items() if d['lv'] <= current_level]
    
    best_skill = None
    max_prob = -1.0
    
    for s_name in available_list:
        if "縫い" not in s_name: continue
        
        dist = calculate_distribution(s_name, power, is_shitsuke)
        total_weight = sum(dist.values())
        
        # 誤差0にジャストフィットする重みを算出
        match_weight = dist.get(target_diff, 0)
        prob = match_weight / total_weight
        
        if prob > max_prob:
            max_prob = prob
            best_skill = s_name
            
    return best_skill, max_prob

# --- 3. Streamlit UI構築 ---

st.set_page_config(page_title="マリアの裁縫アシストPro", layout="wide")

# 初期化
if 'pattern_idx' not in st.session_state: st.session_state.pattern_idx = 0
if 'level' not in st.session_state: st.session_state.level = 70
if 'board' not in st.session_state: st.session_state.board = np.zeros((3, 3))
if 'targets' not in st.session_state: st.session_state.targets = np.full((3, 3), 100)
if 'is_shitsuke_active' not in st.session_state: st.session_state.is_shitsuke_active = 0

# --- メイン画面レイアウト ---
st.title("🧵 裁縫アシスト：AI分布最適化モデル")

with st.sidebar:
    st.header("👤 職人設定")
    st.session_state.level = st.number_input("職人レベル", 1, 80, st.session_state.level)
    cloth_type = st.selectbox("布特性", ["【再生布】", "【虹布】", "【光布】"])
    
    st.divider()
    st.info("💡 **表の考え方**\n数値は一律ではありません。中央値（普通なら15）が最も出やすく、端（12や18）は滅多に出ません。AIはこの『出やすさ』を考慮して計算しています。")

col_main, col_ai = st.columns([2, 1])

with col_ai:
    st.header("🤖 AI推奨")
    # 代表して最も誤差が大きいマス、または選択したマスを分析
    r_sel = st.selectbox("分析行", [0, 1, 2])
    c_sel = st.selectbox("分析列", [0, 1, 2])
    
    diff = st.session_state.targets[r_sel, c_sel] - st.session_state.board[r_sel, c_sel]
    p_idx = st.session_state.pattern_idx % 4 # デフォルト周期
    current_p = ["普通", "強い", "最強", "弱い"][p_idx]
    
    best_s, prob = get_best_move(diff, current_p, st.session_state.is_shitsuke_active > 0, st.session_state.level)
    
    if diff <= 0:
        st.write("このマスは完成、または縫いすぎです。")
    elif best_s and prob > 0:
        st.success(f"推奨特技: **{best_s}**")
        st.metric("誤差0への合致率(重み)", f"{prob*100:.1f}%")
    else:
        st.warning("ジャストで縫える手はありません。削りを優先しましょう。")

with col_main:
    # 盤面表示 (誤差表示ロジック含む)
    rows, cols = st.session_state.board.shape
    grids = st.columns(cols)
    for r in range(rows):
        for c in range(cols):
            with grids[c]:
                target = st.session_state.targets[r,c]
                current = st.session_state.board[r,c]
                d = target - current
                color = "green" if d == 0 else "orange" if 0 < d <= 4 else "red" if d < 0 else "white"
                
                with st.container(border=True):
                    st.markdown(f"**残り: :{color}[{int(d)}]**")
                    st.session_state.board[r,c] = st.number_input(f"📱現{r}{c}", value=int(current), key=f"b_{r}_{c}")
                    st.session_state.targets[r,c] = st.number_input(f"🎯基{r}{c}", value=int(target), key=f"t_{r}_{c}")

# --- 実行ボタン等 ---
# (前回同様のターン進行ロジック)
