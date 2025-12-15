import streamlit as st
import numpy as np

# --- 1. 定数・環境定義 ---
# 独自周期：弱い→ランダム→最強→ランダム→ランダム→ふつう→ふつう→強い→ランダム
POWER_CYCLE = ["弱い", "ランダム", "最強", "ランダム", "ランダム", "ふつう", "ふつう", "強い", "ランダム"]
RANDOM_OPTIONS = ["弱い", "ふつう", "強い", "最強", "会心2倍"]

ITEM_DB = {
    "叡聖のサークレット (頭)": {"targets": [0, 0, 450, 140, 300, 400], "limit": 2, "rows": 3, "cols": 2, "type": "虹"},
    "叡聖の博士服 (上)": {"targets": [240, 150, 170, 130, 110, 90, 80, 130, 110], "limit": 8, "rows": 3, "cols": 3, "type": "虹"},
    "叡聖のグローブ (腕)": {"targets": [180, 130, 350, 230, 100, 120], "limit": 3, "rows": 3, "cols": 2, "type": "虹"},
    "叡聖の深沓 (足)": {"targets": [450, 240, 130, 410], "limit": 2, "rows": 2, "cols": 2, "type": "虹"},
}

# --- 2. 計算コア：期待値・CP・手数ロジック ---
def analyze_board(diffs, focus, turn, limit):
    """
    盤面状況から優先度をスコアリングする
    """
    scores = []
    abs_diffs = np.abs(diffs)
    total_err = np.sum(abs_diffs)
    
    for i, d in enumerate(diffs):
        if d == 0: continue # すでに0のマスは除外
        
        # 基礎優先度
        priority = 0
        reasons = []

        # A. ペナルティ回避ロジック (誤差5以上)
        if abs(d) >= 5:
            priority += 200  # 最優先
            reasons.append("ペナルティ(誤差5以上)回避")
        
        # B. 手数 vs CP 効率ロジック
        if focus < 20:
            # 集中力不足時：少ないコストで多マスを「5未満」に押し込めるか（手数重視）
            if abs(d) < 15:
                priority += 50
                reasons.append("手数重視：低コスト調整")
        else:
            # 集中力潤沢時：大きい数値を効率よく削る（CP重視）
            if abs(d) > 30:
                priority += 100
                reasons.append("CP重視：高効率削り")

        # C. 会心期待値 (虹ターン連動)
        if turn % 8 == 0: # 虹会心アップ
            if abs(d) > 50:
                priority += 150
                reasons.append("虹会心：吸い込み狙い")

        if priority > 0:
            scores.append({"idx": i, "score": priority, "reason": ", ".join(reasons)})
            
    return sorted(scores, key=lambda x: x['score'], reverse=True)

# --- 3. UI実装 ---
st.set_page_config(page_title="裁縫AI：逆算エンジン", layout="wide")

# 初期状態
if 'turn' not in st.session_state:
    st.session_state.update({
        'item_name': "叡聖のサークレット (頭)",
        'turn': 1,
        'focus': 250,
        'board': np.zeros(9)
    })

data = ITEM_DB[st.session_state.item_name]
targets = np.array(data["targets"])

st.title("🌌 裁縫AI：環境推移・逆算システム")

col_info, col_main = st.columns([1, 2])

with col_info:
    st.header("📈 未来予測ボード")
    # 周期と虹パターンの可視化
    for i in range(8):
        f_turn = st.session_state.turn + i
        f_power = POWER_CYCLE[(f_turn - 1) % 9]
        is_niji_half = f_turn % 8 == 4
        is_niji_crit = f_turn % 8 == 0
        
        status = ""
        if is_niji_half: status = "🌈(集中半減)"
        if is_niji_crit: status = "🌈(会心UP)"
        
        color = "green" if i == 0 else "white"
        st.markdown(f":{color}[T{f_turn}: {f_power} {status}]")

    st.divider()
    st.session_state.focus = st.number_input("残り集中力", value=st.session_state.focus)

with col_main:
    diffs = targets - st.session_state.board[:len(targets)]
    abs_diffs = np.abs(diffs)
    total_error = np.sum(abs_diffs[targets > 0])
    
    # 状態判定
    border = data["limit"]
    is_safe = total_error <= border
    color = "green" if is_safe else "red"
    st.subheader(f"合計絶対値誤差: :{color}[{int(total_error)}] / ★3境界: {border}")

    # AI推論の表示
    suggestions = analyze_board(diffs, st.session_state.focus, st.session_state.turn, border)
    if suggestions:
        top = suggestions[0]
        st.warning(f"🤖 **推奨アクション: マス{top['idx'] + 1}**\n\n理由: {top['reason']}")

    # 入力グリッド
    rows, cols_count = data["rows"], data["cols"]
    grid = st.columns(cols_count)
    for i, t in enumerate(targets):
        with grid[i % cols_count]:
            if t == 0:
                st.markdown("<div style='height:140px; background-color:#111; border-radius:5px;'></div>", unsafe_allow_html=True)
            else:
                d = diffs[i]
                bg_color = "#28a745" if d == 0 else "#dc3545" if abs(d) >= 5 else "#ffc107"
                with st.container(border=True):
                    st.markdown(f"<div style='background-color:{bg_color}; text-align:center; border-radius:3px; font-weight:bold;'>誤差: {int(d)}</div>", unsafe_allow_html=True)
                    st.session_state.board[i] = st.number_input(f"現在値", value=int(st.session_state.board[i]), key=f"cell_{i}", label_visibility="collapsed")
                    st.caption(f"基準:{int(t)}")

st.divider()
if st.button("⚡ 次のターンへ進む"):
    st.session_state.turn += 1
    st.rerun()
