import streamlit as st
import numpy as np

# --- 1. データベース設定 (全商材) ---
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

SKILLS = {
    "通常ぬい": 5, "かげんぬい": 10, "2倍ぬい": 9, "3倍ぬい": 12, "ねらいぬい": 16,
    "水平ぬい": 10, "大滝のぼり": 10, "精神統一": 7, "しつけがけ": 13, "待機(0消費)": 0
}

POWERS = ["弱い", "ふつう", "強い", "最強"]

# --- 2. 推奨行動エンジン ---
def get_ai_action(diffs, turn, power, item_type, crit):
    idx = np.argmax(diffs)
    val = diffs[idx]
    target = f"マス{idx+1}"
    
    # 誤差調整が必要なマス（0より大きいマス）を抽出
    active_diffs = diffs[diffs > 0]
    
    # 【戦略的精神統一】
    # 全ての残っているマスが微調整圏内(12以下)であり、
    # 弱いパワーが来ているなら「精神統一」で固定して、1マスずつ確実に埋めることを推奨。
    if power == "弱い" and len(active_diffs) >= 2 and np.all(active_diffs <= 15):
        return f"🧘 **「精神統一」を推奨**：全てのマスが微調整圏内です。「弱い」を維持して確実に誤差0を狙いましょう。"

    if val <= 0: return "✨ 基準値到達。合計誤差を確認してください。"

    # 弱いパワーの活用：微調整
    if power == "弱い":
        if 1 <= val <= 6: return f"🤏 **【{target}】に「かげんぬい」**：誤差0への最終微調整。"
        return f"🤏 **【{target}】に「通常ぬい」**：弱(9〜13)で慎重に寄せ。"

    # 最強パワーの活用：積極削り
    if power == "最強":
        if val >= 108: return f"⚔️ **【{target}】に「3倍ぬい」**：削り優先(108〜)。"
        if val >= 72:  return f"⚔️ **【{target}】に「2倍ぬい」**：削り優先(72〜)。"
        return f"⚔️ **【{target}】に「通常ぬい」**：削り＆寄せ。"

    # 強パワーの活用
    if power == "強い":
        if val >= 81: return f"🧵 **【{target}】に「3倍ぬい」**"
        return f"🧵 **【{target}】に「通常ぬい」**"

    return f"🧵 **【{target}】に「通常ぬい」**（{power}）"

# --- 3. UI構築 ---
st.set_page_config(page_title="裁縫AI：最終微調整特化版", layout="wide")

if 'focus' not in st.session_state: st.session_state.focus = 250
if 'turn' not in st.session_state: st.session_state.turn = 1
if 'board' not in st.session_state: st.session_state.board = np.zeros(9)

with st.sidebar:
    st.header("⚙️ 環境設定")
    selected_name = st.selectbox("商材", list(ITEM_DB.keys()))
    data = ITEM_DB[selected_name]
    
    # リセット処理
    if 'current_item' not in st.session_state or st.session_state.current_item != selected_name:
        st.session_state.current_item, st.session_state.board = selected_name, np.zeros(9)
        st.session_state.turn, st.session_state.focus = 1, 250
        st.rerun()

    # ランダム対応
    exp_p = data["cycle"][(st.session_state.turn - 1) % len(data["cycle"])]
    if exp_p == "ランダム":
        current_power = st.radio("選ばれたパワー", POWERS, index=1, horizontal=True)
    else:
        current_power = exp_p
        st.info(f"現在のパワー: **{current_power}**")

    needle_crit = st.slider("針会心(%)", 0.0, 7.0, 4.3, 0.1)
    hissatsu = st.checkbox("必殺チャージ")

# --- 4. メイン表示 ---
targets = np.array(data["targets"])
diffs = targets - st.session_state.board[:len(targets)]
current_crit = (needle_crit * 8.0) * (7.0 if data["type"] == "虹" and st.session_state.turn % 8 == 0 else 1.0) * (2.0 if hissatsu else 1.0)

st.title(f"🧵 {selected_name} ({data['type']}布)")

# AI推奨行動：精神統一の戦略的活用を含む
st.success(f"🤖 **AI推奨行動:** {get_ai_action(diffs, st.session_state.turn, current_power, data['type'], current_crit)}")

col_stat, col_grid = st.columns([1, 2])
with col_stat:
    total_err = np.sum(np.abs(diffs[targets > 0]))
    st.metric("合計誤差", int(total_err), f"ボーダー: {data['limit']}")
    st.metric("集中力", int(st.session_state.focus))
    
    st.divider()
    used_skill = st.selectbox("使用した特技", list(SKILLS.keys()))
    if st.button("⚡ 行動を確定して次へ", use_container_width=True):
        cost = SKILLS[used_skill]
        if data["type"] == "虹" and st.session_state.turn % 4 == 0: cost //= 2
        st.session_state.focus -= cost
        st.session_state.turn += 1
        st.rerun()

with col_grid:
    cols_n = data["shape"][1]
    cols = st.columns(cols_n)
    for i, t in enumerate(targets):
        with cols[i % cols_n]:
            if t != 0:
                d = diffs[i]
                bg = "#28a745" if d == 0 else "#dc3545" if abs(d) >= 5 else "#ffc107"
                with st.container(border=True):
                    st.markdown(f"<div style='background-color:{bg}; text-align:center; color:black; font-weight:bold;'>マス{i+1} 差 {int(d)}</div>", unsafe_allow_html=True)
                    st.session_state.board[i] = st.number_input(f"入力{i}", value=int(st.session_state.board[i]), key=f"c_{i}", label_visibility="collapsed")
