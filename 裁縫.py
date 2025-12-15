import streamlit as st
import numpy as np

# --- 1. データベース設定 ---
ITEM_DB = {
    "原始獣のシャプカ (頭)": {"targets": [0, 180, 0, 120, 180, 120], "limit": 2, "shape": (2, 3), "type": "再生", "cycle": ["ふつう", "ランダム", "弱い", "最強", "強い"]},
    "原始獣のコート上": {"targets": [95, 40, 95, 60, 60, 60, 75, 40, 75], "limit": 8, "shape": (3, 3), "type": "再生", "cycle": ["ふつう", "ランダム", "弱い", "最強", "強い"]},
    "原始獣のコート下": {"targets": [70, 70, 90, 90, 140, 140], "limit": 4, "shape": (3, 2), "type": "再生", "cycle": ["ふつう", "ランダム", "弱い", "最強", "強い"]},
    "原始獣の腕輪": {"targets": [100, 50, 150, 100, 50, 150], "limit": 3, "shape": (2, 3), "type": "再生", "cycle": ["ふつう", "ランダム", "弱い", "最強", "強い"]},
    "原始獣の足": {"targets": [170, 170, 130, 130], "limit": 2, "shape": (2, 2), "type": "再生", "cycle": ["ふつう", "ランダム", "弱い", "最強", "強い"]},
    "叡聖のサークレット (頭)": {"targets": [0, 450, 0, 140, 300, 400], "limit": 2, "shape": (2, 3), "type": "虹", "cycle": ["弱い", "ランダム", "最強", "ランダム", "ランダム", "ふつう", "ふつう", "強い", "ランダム"]},
    "叡聖の博士服 (上)": {"targets": [240, 150, 170, 130, 110, 90, 80, 130, 110], "limit": 8, "shape": (3, 3), "type": "虹", "cycle": ["弱い", "ランダム", "最強", "ランダム", "ランダム", "ふつう", "ふつう", "強い", "ランダム"]},
    "叡聖のグローブ (腕)": {"targets": [180, 130, 350, 230, 100, 120], "limit": 3, "shape": (3, 2), "type": "虹", "cycle": ["弱い", "ランダム", "最強", "ランダム", "ランダム", "ふつう", "ふつう", "強い", "ランダム"]},
    "叡聖の深沓 (足)": {"targets": [450, 240, 130, 410], "limit": 2, "shape": (2, 2), "type": "虹", "cycle": ["弱い", "ランダム", "最強", "ランダム", "ランダム", "ふつう", "ふつう", "強い", "ランダム"]},
    "皮のてぶくろ": {"targets": [15, 15, 15, 15, 15, 15], "limit": 3, "shape": (2, 3), "type": "通常", "cycle": ["ふつう", "ふつう", "弱い"]}
}

SKILLS = {
    "通常ぬい": 5, "かげんぬい": 10, "2倍ぬい": 9, "3倍ぬい": 12, "ねらいぬい": 16,
    "水平ぬい": 10, "大滝のぼり": 10, "精神統一": 7, "待機(0消費)": 0
}

POWERS = ["弱い", "ふつう", "強い", "最強"]

# --- 2. 推奨行動エンジン（攻めと守りの精神統一） ---
def get_ai_action(diffs, turn, power, item_type, crit):
    idx = np.argmax(diffs)
    val = diffs[idx]
    target = f"マス{idx+1}"
    active_diffs = diffs[diffs > 0]
    total_remaining = np.sum(active_diffs)

    # 【1. 最強固定・一気削りの精神統一】
    # 残り数値が大きく、現在「最強」なら、精神統一で維持して3倍ぬいで一気に盤面を作る
    if power == "最強" and total_remaining > 250:
        return f"⚔️ **「精神統一」で【最強】を固定**：削り段階の最重要局面。最強を維持して「3倍ぬい」等で一気に盤面を作り変えましょう。"

    # 【2. 弱い固定・微調整の精神統一】
    if power == "弱い" and len(active_diffs) >= 2 and np.all(active_diffs <= 15):
        return f"🧘 **「精神統一」で【弱い】を固定**：微調整フェーズ。確実に誤差0へ追い込みましょう。"

    # パワー別削り/微調整
    if power == "最強":
        if val >= 108: return f"⚔️ **【{target}】に「3倍ぬい」**：最強パワーを最大限活用。"
        return f"⚔️ **【{target}】に「通常ぬい」**：調整しつつ削る。"
    
    if power == "弱い":
        if 1 <= val <= 6: return f"🤏 **【{target}】に「かげんぬい」**：極限微調整。"
        return f"🤏 **【{target}】に「通常ぬい」**：慎重な寄せ。"

    return f"🧵 **【{target}】に「通常ぬい」**（{power}）"

# --- 3. UI構築 ---
st.set_page_config(page_title="裁縫AI：最強削り＆微調整統合版", layout="wide")

if 'focus' not in st.session_state: st.session_state.focus = 250
if 'turn' not in st.session_state: st.session_state.turn = 1
if 'board' not in st.session_state: st.session_state.board = np.zeros(9)

def calc_state(turn, base_crit, item_type, hissatsu):
    crit = base_crit * 8.0
    if item_type == "虹" and turn % 8 == 0: crit *= 7.0
    if hissatsu: crit *= 2.0
    return min(crit, 100.0)

with st.sidebar:
    st.header("⚙️ 環境設定")
    selected_name = st.selectbox("商材", list(ITEM_DB.keys()))
    data = ITEM_DB[selected_name]
    
    if 'current_item' not in st.session_state or st.session_state.current_item != selected_name:
        st.session_state.current_item, st.session_state.board = selected_name, np.zeros(9)
        st.session_state.turn, st.session_state.focus = 1, 250
        st.rerun()

    needle_crit = st.slider("針会心(%)", 0.0, 7.0, 4.3, 0.1)
    hissatsu = st.checkbox("必殺チャージ")

    st.divider()
    st.subheader("📈 未来予測推移")
    for i in range(8):
        f_t = st.session_state.turn + i
        f_p = data["cycle"][(f_t-1) % len(data["cycle"])]
        f_c = calc_state(f_t, needle_crit, data["type"], hissatsu if i==0 else False)
        tags = []
        if data["type"] == "虹":
            if f_t % 4 == 0: tags.append("💧(半)")
            if f_t % 8 == 0: tags.append("🌈(会7倍)")
        if data["type"] == "再生" and f_t % 4 == 0: tags.append("♻️(戻)")
        st.write(f"**T{f_t}**: {f_p} {''.join(tags)} / 会心:{f_c:.1f}%")

# --- 4. メイン表示 ---
targets = np.array(data["targets"])
diffs = targets - st.session_state.board[:len(targets)]
exp_p = data["cycle"][(st.session_state.turn - 1) % len(data["cycle"])]
current_power = st.selectbox("パワー確定", POWERS, index=POWERS.index(exp_p) if exp_p in POWERS else 1)
current_crit = calc_state(st.session_state.turn, needle_crit, data["type"], hissatsu)

st.title(f"🧵 {selected_name}")
st.success(f"🤖 **AI推奨:** {get_ai_action(diffs, st.session_state.turn, current_power, data['type'], current_crit)}")

col_stat, col_grid = st.columns([1, 2])
with col_stat:
    total_err = np.sum(np.abs(diffs[targets > 0]))
    st.metric("合計誤差", int(total_err), f"ボーダー:{data['limit']}")
    st.metric("集中力", int(st.session_state.focus))
    
    st.divider()
    used_skill = st.selectbox("使用した特技", list(SKILLS.keys()))
    if st.button("⚡ 行動確定", use_container_width=True):
        cost = SKILLS[used_skill]
        if data["type"] == "虹" and st.session_state.turn % 4 == 0: cost //= 2
        st.session_state.focus -= cost
        st.session_state.turn += 1
        st.rerun()

with col_grid:
    cols_n = data["shape"][1]
    grid_cols = st.columns(cols_n)
    for i, t in enumerate(targets):
        with grid_cols[i % cols_n]:
            if t != 0:
                d = diffs[i]
                bg = "#28a745" if d == 0 else "#dc3545" if abs(d) >= 5 else "#ffc107"
                with st.container(border=True):
                    st.markdown(f"<div style='background-color:{bg}; text-align:center; color:black; font-weight:bold;'>マス{i+1} 差 {int(d)}</div>", unsafe_allow_html=True)
                    st.session_state.board[i] = st.number_input(f"入力{i}", value=int(st.session_state.board[i]), key=f"c_{i}", label_visibility="collapsed")
