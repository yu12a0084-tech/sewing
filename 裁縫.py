import streamlit as st
import numpy as np

# --- 1. 商材・環境定義 ---
ITEM_DB = {
    "原始獣のシャプカ (頭)": {"targets": [0, 140, 0, 70, 90, 70], "limit": 2, "rows": 2, "cols": 3, "type": "再生"},
    "原始獣のコート下": {"targets": [70, 70, 90, 90, 140, 140], "limit": 4, "rows": 3, "cols": 2, "type": "再生"},
    "原始獣の腕帯": {"targets": [70, 70, 90, 90, 140, 140], "limit": 3, "rows": 3, "cols": 2, "type": "再生"},
    "原始獣のブーツ": {"targets": [140, 140, 70, 70], "limit": 2, "rows": 2, "cols": 2, "type": "再生"},
    "叡聖のサークレット (頭)": {"targets": [0, 450, 0, 140, 300, 400], "limit": 2, "rows": 2, "cols": 3, "type": "虹"},
    "叡聖の博士服 (上)": {"targets": [240, 150, 170, 130, 110, 90, 80, 130, 110], "limit": 8, "rows": 3, "cols": 3, "type": "虹"},
    "叡聖のグローブ (腕)": {"targets": [180, 130, 350, 230, 100, 120], "limit": 3, "rows": 3, "cols": 2, "type": "虹"},
    "叡聖の深沓 (足)": {"targets": [450, 240, 130, 410], "limit": 2, "rows": 2, "cols": 2, "type": "虹"},
}

POWER_CYCLE = ["弱い", "ランダム", "最強", "ランダム", "ランダム", "ふつう", "ふつう", "強い", "ランダム"]

def calculate_crit_rate(base, turn, power, is_nerai=False, hissatsu_active=False):
    """
    会心率 = (基礎 * (ねらい + 虹) * 必殺2倍) + 会心x2加算
    """
    nerai_mult = 8.0 if is_nerai else 1.0
    # 虹会心ターン：虹布かつ8nターン目
    is_niji_item = ITEM_DB[st.session_state.current_item]["type"] == "虹"
    niji_mult = 7.0 if (is_niji_item and turn % 8 == 0) else 0.0
    
    # 必殺技「使用後」は常に2倍
    hissatsu_mult = 2.0 if hissatsu_active else 1.0
    
    rate = base * (nerai_mult + niji_mult) * hissatsu_mult
    
    if power == "会心x2":
        rate += base
    return min(rate, 100.0)

# --- 2. UI構築 ---
st.set_page_config(page_title="裁縫AI：必殺・逆算統合", layout="wide")

if 'hissatsu_charged' not in st.session_state:
    st.session_state.hissatsu_charged = False
    st.session_state.hissatsu_active = False

with st.sidebar:
    st.header("⚙️ 基本設定")
    selected_name = st.selectbox("装備品", list(ITEM_DB.keys()))
    needle_crit = st.slider("針の基礎会心率 (%)", 0.0, 7.0, 4.3, 0.1)
    
    if 'current_item' not in st.session_state or st.session_state.current_item != selected_name:
        st.session_state.current_item = selected_name
        st.session_state.board = np.zeros(len(ITEM_DB[selected_name]["targets"]))
        st.session_state.turn = 1
        st.session_state.focus = 250
        st.session_state.hissatsu_charged = False
        st.session_state.hissatsu_active = False
        st.rerun()

    st.divider()
    st.header("✨ 必殺技管理")
    # チャージ入力
    st.session_state.hissatsu_charged = st.checkbox("必殺チャージ中！", value=st.session_state.hissatsu_charged)
    
    # 必殺技の使用（ボタン）
    if st.session_state.hissatsu_charged and not st.session_state.hissatsu_active:
        if st.button("🌟 必殺技を使用 (無我の境地)"):
            st.session_state.hissatsu_active = True
            st.session_state.hissatsu_charged = False
            st.session_state.turn += 1 # 必殺技使用で1ターン消費（集中力消費0）
            st.rerun()

    if st.session_state.hissatsu_active:
        st.success("🔥 無我の境地：発動中 (会心率2倍)")

    st.divider()
    st.header("🔮 未来の会心率")
    t = st.session_state.turn
    for i in range(5):
        f_t = t + i
        p = POWER_CYCLE[(f_t-1)%9]
        rate = calculate_crit_rate(needle_crit, f_t, p, False, st.session_state.hissatsu_active)
        nerai = calculate_crit_rate(needle_crit, f_t, p, True, st.session_state.hissatsu_active)
        st.write(f"T{f_t}({p}): {rate:.1f}% ({nerai:.1f}%)")

# --- 3. メインパネル ---
data = ITEM_DB[st.session_state.current_item]
targets = np.array(data["targets"])
diffs = targets - st.session_state.board[:len(targets)]
total_err = np.sum(np.abs(diffs[targets > 0]))

st.title(f"🧵 {st.session_state.current_item}")
col_stat, col_grid = st.columns([1, 2])

with col_stat:
    color = "green" if total_err <= data["limit"] else "red"
    st.header(f"誤差合計: :{color}[{int(total_err)}]")
    st.session_state.focus = st.number_input("残り集中力", value=st.session_state.focus)
    
    # 必殺の活用アドバイス
    if st.session_state.hissatsu_charged:
        st.warning("💡 必殺技を使えば、集中力0で次ターンへ遷移できます。")

with col_grid:
    grid = st.columns(data["cols"])
    for i, t in enumerate(targets):
        with grid[i % data["cols"]]:
            if t == 0:
                st.markdown("<div style='height:140px; background-color:#222; border-radius:10px;'></div>", unsafe_allow_html=True)
            else:
                d = diffs[i]
                bg = "#28a745" if d == 0 else "#dc3545" if abs(d) >= 5 else "#ffc107"
                with st.container(border=True):
                    st.markdown(f"<div style='background-color:{bg}; text-align:center; color:black; font-weight:bold;'>差分 {int(d)}</div>", unsafe_allow_html=True)
                    st.session_state.board[i] = st.number_input("値", value=int(st.session_state.board[i]), key=f"c_{i}", label_visibility="collapsed")

st.divider()
if st.button("⚡ 通常行動でターンを進める"):
    st.session_state.turn += 1
    st.rerun()
