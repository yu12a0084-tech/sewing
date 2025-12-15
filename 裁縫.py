import streamlit as st
import numpy as np

# --- 1. 商材データベース ---
ITEM_DB = {
    "叡聖の博士服 (上)": {"targets": [240, 150, 170, 130, 110, 90, 80, 130, 110], "limit": 8, "shape": (3, 3), "type": "虹", "cycle": ["弱い", "ランダム", "最強", "ランダム", "ランダム", "ふつう", "ふつう", "強い", "ランダム"]},
    "叡聖のサークレット (頭)": {"targets": [0, 450, 0, 140, 300, 400], "limit": 2, "shape": (2, 3), "type": "虹", "cycle": ["弱い", "ランダム", "最強", "ランダム", "ランダム", "ふつう", "ふつう", "強い", "ランダム"]},
    "原始獣のコート上": {"targets": [95, 40, 95, 60, 60, 60, 75, 40, 75], "limit": 8, "shape": (3, 3), "type": "再生", "cycle": ["ふつう", "ランダム", "弱い", "最強", "強い"]},
    "皮のてぶくろ": {"targets": [15, 15, 15, 15, 15, 15], "limit": 3, "shape": (2, 3), "type": "通常", "cycle": ["ふつう", "ふつう", "弱い"]}
}

SKILLS = {
    "通常ぬい": 5, "かげんぬい": 10, "2倍ぬい": 9, "3倍ぬい": 12, "ねらいぬい": 16,
    "水平ぬい": 10, "大滝のぼり": 10, "たすきぬい": 7, "精神統一": 7, "待機(0消費)": 0
}
POWERS = ["弱い", "ふつう", "強い", "最強"]

# --- 2. セッション状態の初期化 ---
if 'focus' not in st.session_state: st.session_state.focus = 250
if 'turn' not in st.session_state: st.session_state.turn = 1
if 'cycle_idx' not in st.session_state: st.session_state.cycle_idx = 0
if 'board' not in st.session_state: st.session_state.board = np.zeros(9)
if 'fix_power' not in st.session_state: st.session_state.fix_power = None
if 'fix_turns' not in st.session_state: st.session_state.fix_turns = 0

# --- 3. 補助関数 ---
def calc_crit(turn, base_crit, item_type, hissatsu):
    rate = base_crit * 8.0
    if item_type == "虹" and turn % 8 == 0: rate *= 7.0
    if hissatsu: rate *= 2.0
    return min(rate, 100.0)

def get_ai_action(diffs, turn, power, item_type, crit, random_target):
    idx = np.argmax(diffs)
    val = diffs[idx]
    target_name = f"マス{idx+1}"
    active_diffs = diffs[diffs > 0]
    total_remaining = np.sum(active_diffs)

    # 精神統一推奨
    if st.session_state.fix_turns == 0:
        if power == "最強" and total_remaining > 200:
            return f"⚔️ **「精神統一」で【最強】を固定**：削り一気上げ。3倍ぬいの準備を！"
        if power == "弱い" and len(active_diffs) >= 2 and np.all(active_diffs <= 18):
            return f"🧘 **「精神統一」で【弱い】を固定**：微調整フェーズ突入。確実に誤差0へ。"

    # ランダム環境対応
    if random_target is not None:
        if item_type == "再生" and turn % 4 == 0 and 12 <= diffs[random_target] <= 16:
            return f"♻️ **【マス{random_target+1}】は戻り待ち**：他を優先してください。"

    if power == "最強":
        if val >= 108: return f"⚔️ **【{target_name}】に「3倍ぬい」**"
    elif power == "弱い":
        if 1 <= val <= 6: return f"🤏 **【{target_name}】に「かげんぬい」**"
    
    return f"🧵 **【{target_name}】に「通常ぬい」**"

# --- 4. メインUI ---
st.set_page_config(page_title="裁縫AI：究極完全版", layout="wide")
st.title("🧵 裁縫職人AI：究極完全版")

with st.sidebar:
    st.header("⚙️ 設定")
    selected_name = st.selectbox("商材", list(ITEM_DB.keys()))
    data = ITEM_DB[selected_name]
    
    if st.session_state.get('current_item') != selected_name:
        st.session_state.current_item = selected_name
        st.session_state.board, st.session_state.turn, st.session_state.cycle_idx, st.session_state.focus = np.zeros(9), 1, 0, 250
        st.session_state.fix_power, st.session_state.fix_turns = None, 0
        st.rerun()

    needle_crit = st.slider("針会心(%)", 0.0, 7.0, 4.3, 0.1)
    hissatsu = st.checkbox("必殺チャージ")

# --- 状態計算 ---
cycle = data["cycle"]
if st.session_state.fix_turns > 0:
    current_power = st.session_state.fix_power
    st.info(f"🧘 **精神統一中:** {current_power} (残り {st.session_state.fix_turns}回)")
else:
    raw_p = cycle[st.session_state.cycle_idx % len(cycle)]
    if raw_p == "ランダム":
        current_power = st.radio("🎲 ランダム環境を選択", POWERS, index=1, horizontal=True)
    else:
        current_power = raw_p
        st.write(f"現在のパワー: **{current_power}**")

# 環境ターゲット入力
random_target = None
if st.session_state.turn % 4 == 0:
    st.warning(f"⚠️ {data['type']}特性発生ターン")
    t_opts = [f"マス{i+1}" for i, t in enumerate(data["targets"]) if t > 0]
    sel_t = st.selectbox("対象マスを選択", ["未選択"] + t_opts)
    if sel_t != "未選択": random_target = int(sel_t.replace("マス", "")) - 1

# --- 実行 ---
diffs = np.array(data["targets"]) - st.session_state.board[:len(data["targets"])]
c_crit = calc_crit(st.session_state.turn, needle_crit, data["type"], hissatsu)

st.success(f"🤖 **AI推奨:** {get_ai_action(diffs, st.session_state.turn, current_power, data['type'], c_crit, random_target)}")

col_g, col_c = st.columns([3, 2])
with col_g:
    grid_cols = st.columns(data["shape"][1])
    for i, t in enumerate(data["targets"]):
        if t == 0: continue
        with grid_cols[i % data["shape"][1]]:
            d = diffs[i]
            bg = "#28a745" if d == 0 else "#dc3545" if abs(d) >= 10 else "#ffc107"
            with st.container(border=True):
                st.markdown(f"<div style='background-color:{bg}; text-align:center; color:black;'>マス{i+1} 差:{int(d)}</div>", unsafe_allow_html=True)
                st.session_state.board[i] = st.number_input(f"V{i}", value=int(st.session_state.board[i]), key=f"c_{i}", label_visibility="collapsed")

with col_c:
    used_skill = st.selectbox("使用特技", list(SKILLS.keys()))
    if st.button("⚡ 行動確定", use_container_width=True):
        cost = SKILLS[used_skill]
        if data["type"] == "虹" and st.session_state.turn % 4 == 0: cost //= 2
        st.session_state.focus -= cost
        
        # 精神統一の処理
        if used_skill == "精神統一":
            st.session_state.fix_power = current_power
            st.session_state.fix_turns = 3
        elif st.session_state.fix_turns > 0:
            st.session_state.fix_turns -= 1
        
        # ターンと周期の進展
        if st.session_state.fix_turns == 0:
            st.session_state.cycle_idx += 1
        
        st.session_state.turn += 1
        st.rerun()

    st.metric("集中力残り", int(st.session_state.focus))
    st.metric("合計誤差", int(np.sum(np.abs(diffs[diffs!=0]))))
