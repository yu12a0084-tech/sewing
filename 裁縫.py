import streamlit as st
import numpy as np

# --- 1. データベース (商材・特性・周期・誤差) ---
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

SKILLS = {"通常ぬい": 5, "かげんぬい": 10, "2倍ぬい": 9, "3倍ぬい": 12, "ねらいぬい": 16, "水平ぬい": 10, "大滝のぼり": 10, "精神統一": 7, "しつけがけ": 13, "ぬいパワーシフト": 7}

# --- 2. 計算・推奨ロジック ---
def calculate_crit(base, turn, item_type, hissatsu):
    rate = base * 8.0 # ねらいぬい想定
    if item_type == "虹" and turn % 8 == 0: rate *= 7.0
    if hissatsu: rate *= 2.0
    return min(rate, 100.0)

def get_ai_action(diffs, turn, power, item_type, crit):
    # 最大の差があるマスのインデックス
    idx = np.argmax(diffs)
    val = diffs[idx]
    target_label = f"マス{idx+1}"
    
    if item_type == "再生" and turn % 4 == 0 and 12 <= val <= 16:
        return f"💤 **【{target_label}】放置推奨**：再生（戻り）でピッタリを狙えます。"
    
    if crit >= 40.0 and 15 <= val <= 35:
        return f"🎯 **【{target_label}】に「ねらいぬい」**：会心で即完結のチャンス！"

    if power == "最強":
        if val >= 108: return f"⚔️ **【{target_label}】に「3倍ぬい」**：最x3コンボ圏内へ。"
        return f"⚔️ **【{target_label}】に「通常/2倍」**：最強パワーを無駄なく消費。"
    
    if val >= 81: return f"🧵 **【{target_label}】を削る**：強x3コンボ(81)の準備。"
    if 1 <= val <= 6: return f"🤏 **【{target_label}】に「かげんぬい」**：最終調整。"
    if val == 0: return "✨ 全マス基準値内です。仕上げましょう。"
    
    return f"🧵 **【{target_label}】を中心に調整**：次のコンボパワーを待ちます。"

# --- 3. UI構築 ---
st.set_page_config(page_title="裁縫AI完全版", layout="wide")

with st.sidebar:
    st.header("⚙️ 環境設定")
    selected_name = st.selectbox("装備品", list(ITEM_DB.keys()))
    needle_crit = st.slider("針会心率(%)", 0.0, 7.0, 4.3, 0.1)
    data = ITEM_DB[selected_name]

    if 'current_item' not in st.session_state or st.session_state.current_item != selected_name:
        st.session_state.current_item, st.session_state.board = selected_name, np.zeros(9)
        st.session_state.turn, st.session_state.focus, st.session_state.hissatsu = 1, 250, False
        st.rerun()

    st.session_state.hissatsu = st.checkbox("必殺チャージ中")
    
    st.divider()
    st.header("🔮 未来予測・環境推移")
    for i in range(5):
        f_t = st.session_state.turn + i
        f_p = data["cycle"][(f_t-1) % len(data["cycle"])]
        f_crit = calculate_crit(needle_crit, f_t, data["type"], st.session_state.hissatsu if i==0 else False)
        niji = "🌈(会↑+半)" if data["type"] == "虹" and f_t % 8 == 0 else "💧(半)" if data["type"] == "虹" and f_t % 4 == 0 else ""
        regen = "♻️(戻)" if data["type"] == "再生" and f_t % 4 == 0 else ""
        st.write(f"T{f_t}({f_p}){niji}{regen}: 会心{f_crit:.1f}%")

# --- 4. メイン表示 ---
targets = np.array(data["targets"])
diffs = targets - st.session_state.board[:len(targets)]
current_power = data["cycle"][(st.session_state.turn - 1) % len(data["cycle"])]
current_crit = calculate_crit(needle_crit, st.session_state.turn, data["type"], st.session_state.hissatsu)

st.title(f"🧵 {selected_name} ({data['type']}布)")

# AI推奨行動表示 (マス指定あり)
st.success(f"🤖 **AI推奨行動:** {get_ai_action(diffs, st.session_state.turn, current_power, data['type'], current_crit)}")

col_stat, col_grid = st.columns([1, 2])
with col_stat:
    total_err = np.sum(np.abs(diffs[targets > 0]))
    color = "green" if total_err <= data["limit"] else "red"
    st.metric("合計誤差", int(total_err), f"★3ボーダー: {data['limit']}以内", delta_color="inverse")
    st.session_state.focus = st.number_input("残り集中力", value=st.session_state.focus)
    
    st.divider()
    if st.button("⚡ 行動確定 (T+1)", use_container_width=True):
        st.session_state.turn += 1
        st.rerun()
    if st.button("🔄 数値同期 (T維持)", use_container_width=True): st.rerun()

with col_grid:
    cols = st.columns(data["shape"][1])
    for i, t in enumerate(targets):
        with cols[i % data["shape"][1]]:
            if t == 0: st.markdown("<div style='height:100px; background-color:#111; margin-bottom:10px;'></div>", unsafe_allow_html=True)
            else:
                d = diffs[i]
                bg = "#28a745" if d == 0 else "#dc3545" if abs(d) >= 5 else "#ffc107"
                with st.container(border=True):
                    st.markdown(f"<div style='background-color:{bg}; text-align:center; color:black; font-weight:bold;'>マス{i+1} 差 {int(d)}</div>", unsafe_allow_html=True)
                    st.session_state.board[i] = st.number_input(f"入力{i}", value=int(st.session_state.board[i]), key=f"c_{i}", label_visibility="collapsed")
                    st.caption(f"目標:{int(t)}")
