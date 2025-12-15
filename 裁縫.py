import streamlit as st
import numpy as np

# --- 1. データベース設定 ---
ITEM_DB = {
    "原始獣のコート上": {"targets": [95, 40, 95, 60, 60, 60, 75, 40, 75], "limit": 8, "shape": (3, 3), "type": "再生", "cycle": ["ふつう", "ランダム", "弱い", "最強", "強い"]},
    "叡聖の博士服 (上)": {"targets": [240, 150, 170, 130, 110, 90, 80, 130, 110], "limit": 8, "shape": (3, 3), "type": "虹", "cycle": ["弱い", "ランダム", "最強", "ランダム", "ランダム", "ふつう", "ふつう", "強い", "ランダム"]},
    # 他の商材も同様
}

SKILLS = {
    "通常ぬい": 5, "かげんぬい": 10, "2倍ぬい": 9, "3倍ぬい": 12, "ねらいぬい": 16,
    "水平ぬい": 10, "大滝のぼり": 10, "精神統一": 7, "待機(0消費)": 0
}
POWERS = ["弱い", "ふつう", "強い", "最強"]

# --- 2. 思考ロジック ---
def get_ai_action(diffs, turn, power, item_type, crit, random_target):
    idx = np.argmax(diffs)
    val = diffs[idx]
    
    # ランダム環境ターゲットの個別対応
    if random_target is not None:
        target_val = diffs[random_target]
        t_name = f"マス{random_target + 1}"
        if item_type == "虹" and turn % 4 == 0: # 虹のランダム（会心・消費減は全体だが、ターゲット型ランダムの場合）
            return f"🌈 **【{t_name}】がランダム対象！** 集中力半減を活用して「ねらいぬい」等の重い技を叩き込むチャンス。"
        if item_type == "再生" and turn % 4 == 0:
            if 12 <= target_val <= 16:
                return f"♻️ **【{t_name}】は再生（戻り）で0になります。** 他のマスを優先してください。"

    # 最強固定の精神統一
    if power == "最強" and np.sum(diffs[diffs>0]) > 200:
        return f"⚔️ **「精神統一」で【最強】を固定！** 3倍ぬいで一気に基準値へ寄せます。"

    # 通常の推奨
    target = f"マス{idx+1}"
    if power == "最強" and val >= 108: return f"⚔️ **【{target}】に「3倍ぬい」**"
    if power == "弱い" and 1 <= val <= 6: return f"🤏 **【{target}】に「かげんぬい」**"
    
    return f"🧵 **【{target}】に「通常ぬい」**（{power}）"

# --- 3. メインUI ---
st.set_page_config(page_title="裁縫AI：ランダム環境対応版", layout="wide")

if 'focus' not in st.session_state: st.session_state.focus = 250
if 'turn' not in st.session_state: st.session_state.turn = 1
if 'board' not in st.session_state: st.session_state.board = np.zeros(9)

with st.sidebar:
    st.header("📋 設定")
    selected_name = st.selectbox("商材", list(ITEM_DB.keys()))
    data = ITEM_DB[selected_name]
    needle_crit = st.slider("針会心(%)", 0.0, 7.0, 4.3, 0.1)
    hissatsu = st.checkbox("必殺チャージ")
    
    st.divider()
    st.subheader("🔮 推移予測")
    # (推移表示ロジックは継続)

st.title(f"🧵 {selected_name}")

# --- 【手順1】ランダム環境の確定 ---
st.subheader("1. 現在の環境とターゲットを確認")
col_p, col_t = st.columns(2)

with col_p:
    exp_p = data["cycle"][(st.session_state.turn - 1) % len(data["cycle"])]
    current_power = st.radio("現在のパワー", POWERS, index=POWERS.index(exp_p) if exp_p in POWERS else 1, horizontal=True)

with col_t:
    # 環境特性（戻り・燃える等）がどのマスに来たかを選択
    is_random_turn = (st.session_state.turn % 4 == 0)
    random_target = None
    if is_random_turn:
        st.warning(f"⚠️ {data['type']}特性の発生ターンです。対象マスを選択してください")
        target_options = [f"マス{i+1}" for i, t in enumerate(data["targets"]) if t > 0]
        selected_t = st.selectbox("対象マス", ["未選択"] + target_options)
        if selected_t != "未選択":
            random_target = int(selected_t.replace("マス", "")) - 1

# --- 【手順2】AI推奨 ---
targets = np.array(data["targets"])
diffs = targets - st.session_state.board[:len(targets)]
current_crit = (needle_crit * 8.0) * (7.0 if data["type"] == "虹" and st.session_state.turn % 8 == 0 else 1.0) * (2.0 if hissatsu else 1.0)

st.success(f"🤖 **AI推奨行動:** {get_ai_action(diffs, st.session_state.turn, current_power, data['type'], current_crit, random_target)}")

# --- 【手順3】盤面と実行 ---
col_grid, col_ctrl = st.columns([3, 2])
# (以下、盤面入力と行動確定ボタンは同様)
