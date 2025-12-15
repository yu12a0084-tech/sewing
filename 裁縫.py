import streamlit as st
import numpy as np

# --- 1. 商材データベース ---
ITEM_DB = {
    "叡聖の博士服 (上)": {"targets": [240, 150, 170, 130, 110, 90, 80, 130, 110], "limit": 8, "shape": (3, 3), "type": "虹", "cycle": ["弱い", "ランダム", "最強", "ランダム", "ランダム", "ふつう", "ふつう", "強い", "ランダム"]},
    "叡聖のサークレット (頭)": {"targets": [0, 450, 0, 140, 300, 400], "limit": 2, "shape": (2, 3), "type": "虹", "cycle": ["弱い", "ランダム", "最強", "ランダム", "ランダム", "ふつう", "ふつう", "強い", "ランダム"]},
    "原始獣のコート上": {"targets": [95, 40, 95, 60, 60, 60, 75, 40, 75], "limit": 8, "shape": (3, 3), "type": "再生", "cycle": ["ふつう", "ランダム", "弱い", "最強", "強い"]},
    "原始獣のシャプカ (頭)": {"targets": [0, 180, 0, 120, 180, 120], "limit": 2, "shape": (2, 3), "type": "再生", "cycle": ["ふつう", "ランダム", "弱い", "最強", "強い"]},
    "皮のてぶくろ": {"targets": [15, 15, 15, 15, 15, 15], "limit": 3, "shape": (2, 3), "type": "通常", "cycle": ["ふつう", "ふつう", "弱い"]}
}

SKILLS = {
    "通常ぬい": 5, "かげんぬい": 10, "2倍ぬい": 9, "3倍ぬい": 12, "ねらいぬい": 16,
    "水平ぬい": 10, "大滝のぼり": 10, "たすきぬい": 7, "精神統一": 7, "待機(0消費)": 0
}
POWERS = ["弱い", "ふつう", "強い", "最強"]

# --- 2. 思考エンジン：削りと微調整のロジック ---
def get_ai_action(diffs, turn, power, item_type, crit, random_target):
    idx = np.argmax(diffs)
    val = diffs[idx]
    target_name = f"マス{idx+1}"
    active_diffs = diffs[diffs > 0]
    total_remaining = np.sum(active_diffs)

    # 1. 最強時の精神統一（一気削り戦略）
    if power == "最強" and total_remaining > 200:
        return f"⚔️ **「精神統一」で【最強】を固定**：最強維持で「3倍ぬい」等を連打し、一気に盤面を作り変える最重要局面です。"

    # 2. 弱い時の精神統一（戦略的微調整）
    if power == "弱い" and len(active_diffs) >= 2 and np.all(active_diffs <= 18):
        return f"🧘 **「精神統一」で【弱い】を固定**：微調整フェーズ。「弱い」を維持して複数のマスを確実に誤差0へ追い込みましょう。"

    # 3. ランダムターゲット（環境）への即時対応
    if random_target is not None:
        t_val = diffs[random_target]
        t_name = f"マス{random_target + 1}"
        if item_type == "再生" and turn % 4 == 0:
            if 12 <= t_val <= 16: return f"♻️ **【{t_name}】は再生戻りで0確定**：他のマスを縫ってください。"
        if item_type == "虹" and turn % 8 == 0:
            return f"🌈 **【{t_name}】に「ねらいぬい」**：虹会心ターンを活かして本会心を狙うべきです。"

    # 4. パワー別・特技指定推奨
    if power == "最強":
        if val >= 108: return f"⚔️ **【{target_name}】に「3倍ぬい」**：最x3(108)コンボを活用。"
        if val >= 72: return f"⚔️ **【{target_name}】に「2倍ぬい」**：最x2(72)で調整。"
    elif power == "弱い":
        if 1 <= val <= 6: return f"🤏 **【{target_name}】に「かげんぬい」**：微調整の極み。"
        return f"🤏 **【{target_name}】に「通常ぬい」**：慎重に寄せ。"
    
    return f"🧵 **【{target_name}】に「通常ぬい」**（{power}）"

# --- 3. UI構築 ---
st.set_page_config(page_title="裁縫AI：究極完全版", layout="wide")

# セッション状態初期化
if 'focus' not in st.session_state: st.session_state.focus = 250
if 'turn' not in st.session_state: st.session_state.turn = 1
if 'board' not in st.session_state: st.session_state.board = np.zeros(9)

def calc_crit(turn, base_crit, item_type, hissatsu):
    rate = base_crit * 8.0
    if item_type == "虹" and turn % 8 == 0: rate *= 7.0
    if hissatsu: rate *= 2.0
    return min(rate, 100.0)

with st.sidebar:
    st.header("⚙️ 職人設定")
    selected_name = st.selectbox("商材", list(ITEM_DB.keys()))
    data = ITEM_DB[selected_name]
    
    if 'current_item' not in st.session_state or st.session_state.current_item != selected_name:
        st.session_state.current_item = selected_name
        st.session_state.board, st.session_state.turn, st.session_state.focus = np.zeros(9), 1, 250
        st.rerun()

    needle_crit = st.slider("針会心(%)", 0.0, 7.0, 4.3, 0.1)
    hissatsu = st.checkbox("必殺チャージ")

    st.divider()
    st.subheader("🔮 未来の環境推移")
    for i in range(8):
        f_t = st.session_state.turn + i
        f_p = data["cycle"][(f_t-1) % len(data["cycle"])]
        f_c = calc_crit(f_t, needle_crit, data["type"], hissatsu if i==0 else False)
        tag = "🌈" if data["type"] == "虹" and f_t % 8 == 0 else "💧" if data["type"] == "虹" and f_t % 4 == 0 else "♻️" if data["type"] == "再生" and f_t % 4 == 0 else ""
        st.write(f"T{f_t}: {f_p} {tag} ({f_c:.1f}%)")

# --- 4. メインワークフロー ---
st.title(f"🧵 {selected_name} 指導中")

# 手順1: 現在のランダム要素の入力
st.subheader("1. ターンの環境を確定")
c_pow_col, c_env_col = st.columns(2)

with c_pow_col:
    exp_p = data["cycle"][(st.session_state.turn - 1) % len(data["cycle"])]
    if exp_p == "ランダム":
        current_power = st.radio("🎲 出現したパワーを選択", POWERS, index=1, horizontal=True)
    else:
        current_power = exp_p
        st.info(f"現在のパワー: **{current_power}**")

with c_env_col:
    random_target = None
    if st.session_state.turn % 4 == 0:
        st.warning(f"⚠️ {data['type']}特性の発生ターンです")
        t_options = [f"マス{i+1}" for i, t in enumerate(data["targets"]) if t > 0]
        selected_t = st.selectbox("対象マスを選択", ["未選択"] + t_options)
        if selected_t != "未選択":
            random_target = int(selected_t.replace("マス", "")) - 1

# 手順2: AI推奨行動の提示
targets = np.array(data["targets"])
diffs = targets - st.session_state.board[:len(targets)]
current_crit = calc_crit(st.session_state.turn, needle_crit, data["type"], hissatsu)

st.success(f"🤖 **AI推奨行動:** {get_ai_action(diffs, st.session_state.turn, current_power, data['type'], current_crit, random_target)}")

# 手順3: 数値入力と特技実行

col_grid, col_ctrl = st.columns([3, 2])

with col_grid:
    cols_n = data["shape"][1]
    grid_cols = st.columns(cols_n)
    for i, t in enumerate(targets):
        with grid_cols[i % cols_n]:
            if t != 0:
                d = diffs[i]
                bg = "#28a745" if d == 0 else "#dc3545" if abs(d) >= 10 else "#ffc107"
                with st.container(border=True):
                    st.markdown(f"<div style='background-color:{bg}; text-align:center; color:black; font-weight:bold;'>マス{i+1} 差:{int(d)}</div>", unsafe_allow_html=True)
                    st.session_state.board[i] = st.number_input(f"入力{i}", value=int(st.session_state.board[i]), key=f"c_{i}", label_visibility="collapsed")

with col_ctrl:
    st.markdown("### 2. 特技実行と記録")
    used_skill = st.selectbox("使用した特技", list(SKILLS.keys()))
    if st.button("⚡ 行動を確定して次ターンへ", use_container_width=True):
        cost = SKILLS[used_skill]
        if data["type"] == "虹" and st.session_state.turn % 4 == 0: cost //= 2
        st.session_state.focus -= cost
        st.session_state.turn += 1
        st.rerun()
    
    st.metric("集中力残り", int(st.session_state.focus))
    st.metric("合計誤差", int(np.sum(np.abs(diffs[targets > 0]))))
