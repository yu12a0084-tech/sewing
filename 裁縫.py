import streamlit as st
import numpy as np

# --- 1. 商材データベース (基準値・誤差・周期・特性) ---
ITEM_DB = {
    "原始獣のシャプカ (頭)": {"targets": [0, 180, 0, 120, 180, 120], "limit": 2, "shape": (2, 3), "type": "再生", "cycle": ["ふつう", "ランダム", "弱い", "最強", "強い"]},
    "原始獣のコート上": {"targets": [95, 40, 95, 60, 60, 60, 75, 40, 75], "limit": 8, "shape": (3, 3), "type": "再生", "cycle": ["ふつう", "ランダム", "弱い", "最強", "強い"]},
    "原始獣のコート下": {"targets": [70, 70, 90, 90, 140, 140], "limit": 4, "shape": (3, 2), "type": "再生", "cycle": ["ふつう", "ランダム", "弱い", "最強", "強い"]},
    "原始獣の腕輪": {"targets": [100, 50, 150, 100, 50, 150], "limit": 3, "shape": (2, 3), "type": "再生", "cycle": ["ふつう", "ランダム", "弱い", "最強", "強い"]},
    "原始獣の足": {"targets": [170, 170, 130, 130], "limit": 2, "shape": (2, 2), "type": "再生", "cycle": ["ふつう", "ランダム", "弱い", "最強", "強い"]},
    "皮のてぶくろ": {"targets": [15, 15, 15, 15, 15, 15], "limit": 3, "shape": (2, 3), "type": "通常", "cycle": ["ふつう", "ふつう", "弱い"]},
    "叡聖のサークレット (頭)": {"targets": [0, 450, 0, 140, 300, 400], "limit": 2, "shape": (2, 3), "type": "虹", "cycle": ["弱い", "ランダム", "最強", "ランダム", "ランダム", "ふつう", "ふつう", "強い", "ランダム"]},
    "叡聖の博士服 (上)": {"targets": [240, 150, 170, 130, 110, 90, 80, 130, 110], "limit": 8, "shape": (3, 3), "type": "虹", "cycle": ["弱い", "ランダム", "最強", "ランダム", "ランダム", "ふつう", "ふつう", "強い", "ランダム"]},
    "叡聖のグローブ (腕)": {"targets": [180, 130, 350, 230, 100, 120], "limit": 3, "shape": (3, 2), "type": "虹", "cycle": ["弱い", "ランダム", "最強", "ランダム", "ランダム", "ふつう", "ふつう", "強い", "ランダム"]},
    "叡聖の深沓 (足)": {"targets": [450, 240, 130, 410], "limit": 2, "shape": (2, 2), "type": "虹", "cycle": ["弱い", "ランダム", "最強", "ランダム", "ランダム", "ふつう", "ふつう", "強い", "ランダム"]},
}

# --- 2. 集中力・特技データ ---
SKILLS = {
    "通常ぬい": 5, "かげんぬい": 10, "2倍ぬい": 9, "3倍ぬい": 12, "ねらいぬい": 16,
    "水平ぬい": 10, "大滝のぼり": 10, "精神統一": 7, "しつけがけ": 13, "ぬいパワーシフト": 7
}

# --- 3. 判定ロジック ---
def get_recommendation(diff, turn, power, item_type, crit_rate):
    if crit_rate > 40.0 and diff >= 15: return "🎯 ねらいぬい推奨（高会心ターン）"
    if diff >= 116: return "🧵 最強x3 + 弱 (116) 圏内"
    if diff >= 89: return "🧵 強x3 + 弱 (89) 圏内"
    if diff >= 80: return "🧵 最x2 + 弱 (80) 圏内"
    if diff >= 53: return "🧵 普+強 + 弱 (53) 圏内"
    if item_type == "再生" and turn % 4 == 0 and diff <= 16: return "♻️ 再生戻り待ち（放置推奨）"
    if 1 <= diff <= 6: return "🤏 かげんぬい調整"
    return "⚖️ 状況維持・次ターン待機"

def calculate_crit_rate(base, turn, item_type, hissatsu):
    rate = base * (8.0 if True else 1.0) # ねらいぬいベース
    if item_type == "虹" and turn % 8 == 0: rate *= 7.0
    if hissatsu: rate *= 2.0
    return min(rate, 100.0)

# --- 4. UIメイン ---
st.set_page_config(page_title="裁縫コンプリートAI", layout="wide")

with st.sidebar:
    st.header("🛠 環境設定")
    selected_name = st.selectbox("装備選択", list(ITEM_DB.keys()))
    needle_crit = st.slider("針会心率(%)", 0.0, 7.0, 4.3, 0.1)
    data = ITEM_DB[selected_name]

    if 'current_item' not in st.session_state or st.session_state.current_item != selected_name:
        st.session_state.current_item, st.session_state.board = selected_name, np.zeros(9)
        st.session_state.turn, st.session_state.focus, st.session_state.hissatsu = 1, 250, False
        st.rerun()

    st.session_state.hissatsu = st.checkbox("必殺チャージ")
    if st.session_state.hissatsu and st.button("🌟 必殺発動"):
        st.session_state.turn += 1
        st.rerun()

# --- 5. メイン画面 ---
targets = np.array(data["targets"])
diffs = targets - st.session_state.board[:len(targets)]
power = data["cycle"][(st.session_state.turn - 1) % len(data["cycle"])]
crit = calculate_crit_rate(needle_crit, st.session_state.turn, data["type"], st.session_state.hissatsu)

st.title(f"{selected_name} ({data['type']}布)")
st.info(f"🤖 **AI推奨:** {get_recommendation(np.max(diffs), st.session_state.turn, power, data['type'], crit)}")

col_stat, col_grid = st.columns([1, 2])

with col_stat:
    total_err = np.sum(np.abs(diffs[targets > 0]))
    st.metric("合計誤差", int(total_err), f"ボーダー: {data['limit']}")
    st.session_state.focus = st.number_input("集中力", value=st.session_state.focus)
    
    # 虹布特殊消費
    selected_skill = st.selectbox("特技確認", list(SKILLS.keys()))
    cost = SKILLS[selected_skill]
    if data["type"] == "虹" and st.session_state.turn % 4 == 0: cost //= 2
    st.write(f"現在ターンの消費: **{cost}**")

    st.divider()
    if st.button("⚡ 行動確定(T+1)", use_container_width=True):
        st.session_state.turn += 1
        st.rerun()
    if st.button("🔄 数値同期(T維持)", use_container_width=True): st.rerun()

with col_grid:
    grid_cols = st.columns(data["shape"][1])
    for i, t in enumerate(targets):
        with grid_cols[i % data["shape"][1]]:
            if t == 0: st.markdown("<div style='height:100px; background-color:#111; margin-bottom:10px;'></div>", unsafe_allow_html=True)
            else:
                d = diffs[i]
                bg = "#28a745" if d == 0 else "#dc3545" if abs(d) >= 5 else "#ffc107"
                with st.container(border=True):
                    st.markdown(f"<div style='background-color:{bg}; text-align:center; color:black; font-weight:bold;'>差 {int(d)}</div>", unsafe_allow_html=True)
                    st.session_state.board[i] = st.number_input(f"V{i}", value=int(st.session_state.board[i]), key=f"c_{i}", label_visibility="collapsed")
                    st.caption(f"目標:{int(t)}")
