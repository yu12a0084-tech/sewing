import streamlit as st
import numpy as np

# --- 1. 拡張商材データベース ---
# 頂いた「原始獣」「叡聖」の基準値・配置・特性を完全網羅
ITEM_DB = {
    "叡聖のサークレット (頭)": {"targets": [0, 0, 450, 140, 300, 400], "limit": 2, "rows": 3, "cols": 2, "type": "虹"},
    "叡聖の博士服 (上)": {"targets": [240, 150, 170, 130, 110, 90, 80, 130, 110], "limit": 8, "rows": 3, "cols": 3, "type": "虹"},
    "叡聖のグローブ (腕)": {"targets": [180, 130, 350, 230, 100, 120], "limit": 3, "rows": 3, "cols": 2, "type": "虹"},
    "叡聖の深沓 (足)": {"targets": [450, 240, 130, 410], "limit": 2, "rows": 2, "cols": 2, "type": "虹"},
    "原始獣のコート下": {"targets": [70, 70, 90, 90, 140, 140], "limit": 4, "rows": 3, "cols": 2, "type": "再生"},
    "原始獣の腕帯": {"targets": [70, 70, 90, 90, 140, 140], "limit": 3, "rows": 3, "cols": 2, "type": "再生"},
    "原始獣のブーツ": {"targets": [140, 140, 70, 70], "limit": 2, "rows": 2, "cols": 2, "type": "再生"}
}

# 周期定義
POWER_CYCLE = ["弱い", "ランダム", "最強", "ランダム", "ランダム", "ふつう", "ふつう", "強い", "ランダム"]

# --- 2. 優先順位・逆算ロジック ---
def analyze_priority(diffs, focus, turn, limit):
    scores = []
    abs_diffs = np.abs(diffs)
    
    for i, d in enumerate(diffs):
        if d == 0: continue
        p = 0
        reasons = []

        # A. ペナルティ回避 (誤差5以上)
        if abs(d) >= 5:
            p += 200
            reasons.append("誤差5以上ペナルティ回避")
        
        # B. 手数 vs CP 効率 (マリア・ロジック)
        if focus < 20:
            if abs(d) < 15: # 低コストで刻める
                p += 50
                reasons.append("手数重視(分散調整)")
        else:
            if abs(d) > 30: # 集中力があるなら大きく削る
                p += 100
                reasons.append("CP効率重視(一撃)")

        # C. 虹布特性の同期 (4nターン)
        if turn % 8 == 0: # 会心UP
            if abs(d) > 50: p += 150; reasons.append("虹会心吸い込み狙い")

        if p > 0:
            scores.append({"idx": i, "score": p, "reason": " / ".join(reasons)})
            
    return sorted(scores, key=lambda x: x['score'], reverse=True)

# --- 3. メインUI ---
st.set_page_config(page_title="裁縫超越AI：マルチ商材対応", layout="wide")

# 商材選択（サイドバー）
with st.sidebar:
    st.header("📦 商材検索・選択")
    # 検索機能付きセレクトボックス
    selected_name = st.selectbox("作成する装備を選択", list(ITEM_DB.keys()))
    
    # 選択が変更されたらリセット
    if 'current_item' not in st.session_state or st.session_state.current_item != selected_name:
        st.session_state.current_item = selected_name
        st.session_state.board = np.zeros(len(ITEM_DB[selected_name]["targets"]))
        st.session_state.turn = 1
        st.session_state.focus = 250
        st.rerun()

    st.divider()
    st.header("📈 環境予測")
    for i in range(5):
        t = st.session_state.turn + i
        p = POWER_CYCLE[(t-1)%9]
        is_niji = ITEM_DB[selected_name]["type"] == "虹"
        status = "🌈(会心)" if is_niji and t%8==0 else "🌈(半分)" if is_niji and t%8==4 else ""
        color = "green" if i==0 else "white"
        st.markdown(f":{color}[T{t}: {p} {status}]")

# メインパネル
data = ITEM_DB[st.session_state.current_item]
targets = np.array(data["targets"])
st.title(f"🧵 {st.session_state.current_item}")

col_status, col_grid = st.columns([1, 2])

with col_status:
    # 誤差計算
    diffs = targets - st.session_state.board[:len(targets)]
    abs_errs = np.abs(diffs[targets > 0])
    total_err = np.sum(abs_errs)
    
    # ★3判定
    border = data["limit"]
    color = "green" if total_err <= border else "red"
    st.header(f"合計誤差: :{color}[{int(total_err)}]")
    st.write(f"★3許容ボーダー: {border} 以内")
    
    st.session_state.focus = st.number_input("残り集中力", value=st.session_state.focus)

    # AIナビゲーション
    advices = analyze_priority(diffs, st.session_state.focus, st.session_state.turn, border)
    if advices:
        top = advices[0]
        st.info(f"🤖 **AI推奨アクション**\n\n**マス {top['idx']+1}** を狙ってください。\n\n理由: {top['reason']}")

with col_grid:
    rows, cols_count = data["rows"], data["cols"]
    grid = st.columns(cols_count)
    for i, t in enumerate(targets):
        with grid[i % cols_count]:
            if t == 0:
                st.markdown("<div style='height:140px; background-color:#111; border-radius:10px;'></div>", unsafe_allow_html=True)
            else:
                d = diffs[i]
                # 視覚的な警告（ペナルティ圏内は赤）
                bg = "#28a745" if d == 0 else "#dc3545" if abs(d) >= 5 else "#ffc107"
                with st.container(border=True):
                    st.markdown(f"<div style='background-color:{bg}; text-align:center; font-weight:bold; color:black;'>差分: {int(d)}</div>", unsafe_allow_html=True)
                    st.session_state.board[i] = st.number_input(f"現在値", value=int(st.session_state.board[i]), key=f"cell_{i}", label_visibility="collapsed")
                    st.caption(f"基準: {int(t)}")

st.divider()
if st.button("⚡ 次のターンへ進む"):
    st.session_state.turn += 1
    st.rerun()
