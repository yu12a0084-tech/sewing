import streamlit as st
import numpy as np

# --- 1. 商材データベース ---
ITEM_DB = {
    "叡聖の博士服 (上)": {"targets": [240, 150, 170, 130, 110, 90, 80, 130, 110], "limit": 8, "shape": (3, 3), "type": "虹", "cycle": ["弱い", "ランダム", "最強", "ランダム", "ランダム", "ふつう", "ふつう", "強い", "ランダム"]},
    "叡聖のサークレット (頭)": {"targets": [0, 450, 0, 140, 300, 400], "limit": 2, "shape": (2, 3), "type": "虹", "cycle": ["弱い", "ランダム", "最強", "ランダム", "ランダム", "ふつう", "ふつう", "強い", "ランダム"]},
    "原始獣のコート上": {"targets": [95, 40, 95, 60, 60, 60, 75, 40, 75], "limit": 8, "shape": (3, 3), "type": "再生", "cycle": ["ふつう", "ランダム", "弱い", "最強", "強い"]},
}

SKILLS = {
    "通常ぬい": 5, "かげんぬい": 10, "2倍ぬい": 9, "3倍ぬい": 12, "ねらいぬい": 16,
    "水平ぬい": 10, "大滝のぼり": 10, "たすきぬい": 7, "精神統一": 7, "待機(0消費)": 0
}
POWERS = ["弱い", "ふつう", "強い", "最強"]

# --- 2. 状態管理の初期化 ---
if 'focus' not in st.session_state: st.session_state.focus = 250
if 'turn' not in st.session_state: st.session_state.turn = 1
if 'board' not in st.session_state: st.session_state.board = np.zeros(9)
if 'fix_power' not in st.session_state: st.session_state.fix_power = None
if 'fix_turns' not in st.session_state: st.session_state.fix_turns = 0

# --- 3. 状態計算ロジック ---
def get_current_power(data):
    if st.session_state.fix_turns > 0:
        return st.session_state.fix_power
    cycle = data["cycle"]
    return cycle[(st.session_state.turn - 1) % len(cycle)]

def get_ai_action(diffs, power, item_type, turn):
    idx = np.argmax(diffs)
    val = diffs[idx]
    target_name = f"マス{idx+1}"
    active_diffs = diffs[diffs > 0]
    total_remaining = np.sum(active_diffs)
    
    # 虹特性：8ターン周期の会心2倍
    is_crit_turn = (item_type == "虹" and turn % 8 == 0)

    # 精神統一推奨
    if st.session_state.fix_turns == 0:
        if power == "最強" and total_remaining > 200:
            return "⚔️ **「精神統一」推奨**：最強を固定。削り効率を最大化します。"
        if power == "弱い" and len(active_diffs) >= 2 and np.all(active_diffs <= 18):
            return "🧘 **「精神統一」推奨**：弱い固定。確実に誤差0へ追い込みます。"

    # 特殊ターン推奨
    if is_crit_turn:
        return f"🎯 **【会心2倍ターン！】** {target_name}に「ねらいぬい」等の勝負手を推奨。"

    if power == "最強":
        if val >= 108: return f"⚔️ **【{target_name}】に「3倍ぬい」**"
    elif power == "弱い":
        if 1 <= val <= 6: return f"🤏 **【{target_name}】に「かげんぬい」**"
    
    return f"🧵 **【{target_name}】に「通常ぬい」**"

# --- 4. UI構築 ---
st.set_page_config(page_title="裁縫AI：最終究極完全版", layout="wide")
st.title("🧵 裁縫職人AI：最終究極完全版")

with st.sidebar:
    st.header("⚙️ システム設定")
    selected_name = st.selectbox("製作アイテム", list(ITEM_DB.keys()))
    data = ITEM_DB[selected_name]
    
    # アイテム変更時のリセット
    if st.session_state.get('current_item') != selected_name:
        st.session_state.current_item = selected_name
        st.session_state.board, st.session_state.turn, st.session_state.focus = np.zeros(9), 1, 250
        st.session_state.fix_power, st.session_state.fix_turns = None, 0
        st.rerun()
    
    if st.button("🔄 盤面リセット"):
        st.session_state.board, st.session_state.turn, st.session_state.focus = np.zeros(9), 1, 250
        st.session_state.fix_power, st.session_state.fix_turns = None, 0
        st.rerun()

# 環境計算
raw_power = get_current_power(data)
is_half_focus = (data["type"] == "虹" and st.session_state.turn % 4 == 0)
is_crit_up = (data["type"] == "虹" and st.session_state.turn % 8 == 0)

# パワー表示
if st.session_state.fix_turns > 0:
    st.warning(f"🧘 **精神統一継続中:** {raw_power} (あと {st.session_state.fix_turns} 回行動可能)")
    current_power = raw_power
elif raw_power == "ランダム":
    current_power = st.radio("🎲 ランダム環境の決定", POWERS, index=1, horizontal=True)
else:
    current_power = raw_power
    st.info(f"現在のパワー: **{current_power}**")

# 特性ステータス表示

cols_info = st.columns(2)
with cols_info[0]:
    if is_half_focus: st.error("💧 **消費集中力半分！**")
with cols_info[1]:
    if is_crit_up: st.error("🔥 **会心率2倍ターン！**")

# --- メインエリア ---
diffs = np.array(data["targets"]) - st.session_state.board[:len(data["targets"])]
st.success(f"🤖 **AI推奨:** {get_ai_action(diffs, current_power, data['type'], st.session_state.turn)}")

col_grid, col_ctrl = st.columns([3, 2])

with col_grid:
    grid_cols = st.columns(data["shape"][1])
    for i, t in enumerate(data["targets"]):
        if t == 0: continue
        with grid_cols[i % data["shape"][1]]:
            d = diffs[i]
            bg = "#28a745" if d == 0 else "#dc3545" if abs(d) >= 10 else "#ffc107"
            with st.container(border=True):
                st.markdown(f"<div style='background-color:{bg}; text-align:center; color:black; font-weight:bold;'>マス{i+1} 差:{int(d)}</div>", unsafe_allow_html=True)
                st.session_state.board[i] = st.number_input(f"入力{i}", value=int(st.session_state.board[i]), key=f"c_{i}", label_visibility="collapsed")

with col_ctrl:
    st.markdown("### 🛠 行動確定")
    used_skill = st.selectbox("実行特技", list(SKILLS.keys()))
    
    if st.button("⚡ ターン終了", use_container_width=True):
        cost = SKILLS[used_skill]
        if is_half_focus: cost //= 2
        st.session_state.focus -= cost
        
        # 精神統一カウント処理（実質2ターン維持）
        if used_skill == "精神統一":
            st.session_state.fix_power = current_power
            st.session_state.fix_turns = 2
        elif st.session_state.fix_turns > 0:
            st.session_state.fix_turns -= 1
            if st.session_state.fix_turns == 0:
                st.session_state.fix_power = None
        
        st.session_state.turn += 1
        st.rerun()

    st.divider()
    st.metric("集中力", int(st.session_state.focus))
    st.metric("合計誤差", int(np.sum(np.abs(diffs[diffs!=0]))))
