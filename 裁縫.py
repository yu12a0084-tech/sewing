import streamlit as st
import numpy as np

# --- 1. データベース設定 ---
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
    "水平ぬい": 10, "滝のぼり": 8, "大滝のぼり": 10, "たすきぬい": 7, "逆たすきぬい": 7,
    "しつけがけ": 13, "精神統一": 7, "ぬいパワーシフト": 7, "糸ほぐし": 16, "巻きこみぬい": 13, "待機(0消費)": 0
}

POWERS = ["弱い", "ふつう", "強い", "最強"]

# --- 2. 推奨行動ロジック ---
def get_ai_action(diffs, turn, power, item_type, crit):
    idx = np.argmax(diffs)
    val = diffs[idx]
    target = f"マス{idx+1}"
    
    if power == "最強":
        if val >= 108: return f"⚔️ **【{target}】に「3倍ぬい」**：最x3(108)圏内。一気に削ります。"
        if val >= 72: return f"⚔️ **【{target}】に「2倍ぬい」**：最x2(72)で調整。オーバー注意。"
    
    if item_type == "再生" and turn % 4 == 0 and 12 <= val <= 16:
        return f"♻️ **【{target}】放置推奨**：再生(12〜16)戻りで0を狙えます。"
    
    if crit >= 40.0 and 15 <= val <= 35:
        return f"🎯 **【{target}】に「ねらいぬい」**：会心狙いの完結フェーズ。"

    if val >= 81 and power in ["強い", "最強"]: return f"🧵 **【{target}】に「3倍ぬい」**：強x3(81)削り。"
    if 1 <= val <= 6: return f"🤏 **【{target}】に「かげんぬい」**：微調整。"
    
    return f"⚖️ **【{target}】に「通常ぬい」** または「精神統一」などでパワー調整。"

# --- 3. UI構築 ---
st.set_page_config(page_title="裁縫AI：集中力/ランダム管理版", layout="wide")

if 'focus' not in st.session_state: st.session_state.focus = 250
if 'turn' not in st.session_state: st.session_state.turn = 1
if 'board' not in st.session_state: st.session_state.board = np.zeros(9)

with st.sidebar:
    st.header("⚙️ 設定")
    selected_name = st.selectbox("商材選択", list(ITEM_DB.keys()))
    data = ITEM_DB[selected_name]
    
    # 商材変更時にリセット
    if 'current_item' not in st.session_state or st.session_state.current_item != selected_name:
        st.session_state.current_item = selected_name
        st.session_state.board = np.zeros(9)
        st.session_state.turn = 1
        st.session_state.focus = 250
        st.rerun()

    # ランダムパワー確定機能
    expected_power = data["cycle"][(st.session_state.turn - 1) % len(data["cycle"])]
    if expected_power == "ランダム":
        st.warning("⚠️ パワーがランダムです。選ばれたものを選択してください")
        current_power = st.radio("実際に選ばれたパワー", POWERS, index=1, horizontal=True)
    else:
        current_power = expected_power
        st.info(f"現在のパワー: **{current_power}**")

    # 会心率
    needle_crit = st.slider("針会心(%)", 0.0, 7.0, 4.3, 0.1)
    hissatsu = st.checkbox("必殺チャージ")
    
    st.divider()
    st.header("🔮 未来予測")
    for i in range(5):
        f_t = st.session_state.turn + i
        f_p = data["cycle"][(f_t-1) % len(data["cycle"])]
        niji = "🌈" if data["type"] == "虹" and f_t % 8 == 0 else "💧" if data["type"] == "虹" and f_t % 4 == 0 else ""
        regen = "♻️" if data["type"] == "再生" and f_t % 4 == 0 else ""
        st.write(f"T{f_t}({f_p}){niji}{regen}")

# --- 4. メイン表示 ---
targets = np.array(data["targets"])
diffs = targets - st.session_state.board[:len(targets)]
current_crit = (needle_crit * 8.0) * (7.0 if data["type"] == "虹" and st.session_state.turn % 8 == 0 else 1.0) * (2.0 if hissatsu else 1.0)

st.title(f"🧵 {selected_name}")

# 推奨行動
st.success(f"🤖 **AI推奨行動:** {get_ai_action(diffs, st.session_state.turn, current_power, data['type'], current_crit)}")

col_stat, col_grid = st.columns([1, 2])

with col_stat:
    total_err = np.sum(np.abs(diffs[targets > 0]))
    st.metric("合計誤差", int(total_err), f"ボーダー: {data['limit']}")
    st.metric("残り集中力", int(st.session_state.focus))
    
    st.divider()
    st.subheader("🛠 行動確定")
    used_skill = st.selectbox("使用した特技を選択", list(SKILLS.keys()))
    
    if st.button("⚡ 特技実行 ＆ ターン進める", use_container_width=True):
        # 集中力消費計算
        cost = SKILLS[used_skill]
        if data["type"] == "虹" and st.session_state.turn % 4 == 0:
            cost //= 2
        st.session_state.focus -= cost
        st.session_state.turn += 1
        st.rerun()

    if st.button("🔄 数値同期のみ (ターン維持)", use_container_width=True):
        st.rerun()

with col_grid:
    cols_count = data["shape"][1]
    cols = st.columns(cols_count)
    for i, t in enumerate(targets):
        with cols[i % cols_count]:
            if t == 0:
                st.markdown("<div style='height:100px; background-color:#111;'></div>", unsafe_allow_html=True)
            else:
                d = diffs[i]
                bg = "#28a745" if d == 0 else "#dc3545" if abs(d) >= 5 else "#ffc107"
                with st.container(border=True):
                    st.markdown(f"<div style='background-color:{bg}; text-align:center; color:black; font-weight:bold;'>マス{i+1} 差 {int(d)}</div>", unsafe_allow_html=True)
                    st.session_state.board[i] = st.number_input(f"V{i}", value=int(st.session_state.board[i]), key=f"c_{i}", label_visibility="collapsed")
