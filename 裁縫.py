import streamlit as st
import numpy as np

# --- 1. 商材・特性・周期データベース ---
ITEM_DB = {
    "皮のてぶくろ": {"targets": [15, 15, 15, 15, 15, 15], "limit": 3, "shape": (2, 3), "type": "通常", "cycle": ["ふつう", "ふつう", "弱い"]},
    "原始獣のシャプカ (頭)": {"targets": [0, 180, 0, 120, 180, 120], "limit": 2, "shape": (2, 3), "type": "再生", "cycle": ["ふつう", "ランダム", "弱い", "最強", "強い"]},
    "原始獣のコート上": {"targets": [95, 40, 95, 60, 60, 60, 75, 40, 75], "limit": 8, "shape": (3, 3), "type": "再生", "cycle": ["ふつう", "ランダム", "弱い", "最強", "強い"]},
    "原始獣のコート下": {"targets": [70, 70, 90, 90, 140, 140], "limit": 4, "shape": (3, 2), "type": "再生", "cycle": ["ふつう", "ランダム", "弱い", "最強", "強い"]},
    "原始獣の腕輪": {"targets": [100, 50, 150, 100, 50, 150], "limit": 3, "shape": (2, 3), "type": "再生", "cycle": ["ふつう", "ランダム", "弱い", "最強", "強い"]},
    "原始獣の足": {"targets": [170, 170, 130, 130], "limit": 2, "shape": (2, 2), "type": "再生", "cycle": ["ふつう", "ランダム", "弱い", "最強", "強い"]},
    "叡聖のサークレット (頭)": {"targets": [0, 450, 0, 140, 300, 400], "limit": 2, "shape": (2, 3), "type": "虹", "cycle": ["弱い", "ランダム", "最強", "ランダム", "ランダム", "ふつう", "ふつう", "強い", "ランダム"]},
    "叡聖の博士服 (上)": {"targets": [240, 150, 170, 130, 110, 90, 80, 130, 110], "limit": 8, "shape": (3, 3), "type": "虹", "cycle": ["弱い", "ランダム", "最強", "ランダム", "ランダム", "ふつう", "ふつう", "強い", "ランダム"]},
    "叡聖のグローブ (腕)": {"targets": [180, 130, 350, 230, 100, 120], "limit": 3, "shape": (3, 2), "type": "虹", "cycle": ["弱い", "ランダム", "最強", "ランダム", "ランダム", "ふつう", "ふつう", "強い", "ランダム"]},
    "叡聖の深沓 (足)": {"targets": [450, 240, 130, 410], "limit": 2, "shape": (2, 2), "type": "虹", "cycle": ["弱い", "ランダム", "最強", "ランダム", "ランダム", "ふつう", "ふつう", "強い", "ランダム"]},
}

def calculate_crit_rate(base, turn, power, item_type, is_nerai=False, hissatsu_active=False):
    nerai_mult = 8.0 if is_nerai else 1.0
    # 虹特性: 8の倍数ターンのみ会心率7倍
    niji_crit_mult = 7.0 if (item_type == "虹" and turn % 8 == 0) else 0.0
    hissatsu_mult = 2.0 if hissatsu_active else 1.0
    
    rate = base * (nerai_mult + niji_crit_mult) * hissatsu_mult
    if power == "会心x2": rate += base
    return min(rate, 100.0)

# --- 2. UI ---
st.set_page_config(page_title="裁縫AI：虹布・再生布同期", layout="wide")

with st.sidebar:
    st.header("⚙️ 環境設定")
    selected_name = st.selectbox("装備品", list(ITEM_DB.keys()))
    needle_crit = st.slider("針の基礎会心率 (%)", 0.0, 7.0, 4.3, 0.1)
    
    if 'current_item' not in st.session_state or st.session_state.current_item != selected_name:
        st.session_state.current_item = selected_name
        st.session_state.board = np.zeros(9)
        st.session_state.turn = 1
        st.session_state.focus = 250
        st.session_state.hissatsu_active = False
        st.rerun()

    data = ITEM_DB[selected_name]
    
    st.session_state.hissatsu_charged = st.checkbox("必殺チャージ")
    if st.session_state.hissatsu_charged and st.button("🌟 必殺技発動"):
        st.session_state.hissatsu_active = True
        st.session_state.turn += 1
        st.rerun()

    st.divider()
    st.header("🔮 未来予測")
    t = st.session_state.turn
    for i in range(5):
        f_t = t + i
        p = data["cycle"][(f_t-1) % len(data["cycle"])]
        rate = calculate_crit_rate(needle_crit, f_t, p, data["type"], False, st.session_state.hissatsu_active)
        nerai = calculate_crit_rate(needle_crit, f_t, p, data["type"], True, st.session_state.hissatsu_active)
        
        # 虹布の表示ロジック修正
        niji_info = ""
        if data["type"] == "虹":
            if f_t % 8 == 0: niji_info = "🌈(会心↑+半減)"
            elif f_t % 4 == 0: niji_info = "💧(半減)"
        
        regen_info = "♻️(戻り)" if data["type"] == "再生" and f_t % 4 == 0 else ""
        st.write(f"T{f_t}({p}){niji_info}{regen_info}: {rate:.1f}% ({nerai:.1f}%)")

# --- 3. メインパネル ---
targets = np.array(data["targets"])
rows, cols = data["shape"]
diffs = targets - st.session_state.board[:len(targets)]
total_err = np.sum(np.abs(diffs[targets > 0]))

st.title(f"🧵 {selected_name} ({data['type']}布)")

col_stat, col_grid = st.columns([1, 2])

with col_stat:
    color = "green" if total_err <= data["limit"] else "red"
    st.header(f"誤差合計: :{color}[{int(total_err)}]")
    st.session_state.focus = st.number_input("集中力", value=st.session_state.focus)
    
    # ターンごとの警告
    t = st.session_state.turn
    if data["type"] == "虹":
        if t % 8 == 0: st.success("🌈 虹：会心率大幅UP ＆ 消費集中力半分！")
        elif t % 4 == 0: st.info("💧 虹：消費集中力半分ターン")
    elif data["type"] == "再生" and t % 4 == 0:
        st.warning("♻️ 再生：このターンの終わりに数値が戻ります")

    st.divider()
    if st.button("⚡ 行動確定 (T+1)", use_container_width=True):
        st.session_state.turn += 1
        st.rerun()
    if st.button("🔄 数値同期 (T維持)", use_container_width=True):
        st.rerun()

with col_grid:
    grid_cols = st.columns(cols)
    for i, t in enumerate(targets):
        with grid_cols[i % cols]:
            if t == 0:
                st.markdown("<div style='height:120px; background-color:#111; border-radius:10px;'></div>", unsafe_allow_html=True)
            else:
                d = diffs[i]
                bg = "#28a745" if d == 0 else "#dc3545" if abs(d) >= 5 else "#ffc107"
                with st.container(border=True):
                    st.markdown(f"<div style='background-color:{bg}; text-align:center; color:black; font-weight:bold;'>差 {int(d)}</div>", unsafe_allow_html=True)
                    st.session_state.board[i] = st.number_input(f"現在{i}", value=int(st.session_state.board[i]), key=f"c_{i}", label_visibility="collapsed")
                    st.caption(f"目標:{int(t)}")
