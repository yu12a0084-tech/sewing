import streamlit as st
import numpy as np

# --- 1. 裁縫商材データベース (主要装備) ---
# targets: [左上, 右上, 左中, 右中, 左下, 右下] の順 (6マスの場合)
# targets: [左上, 中上, 右上, 左中, 中中, 右中, 左下, 中下, 右下] (9マスの場合)
ITEM_DB = {
    "【足】原始獣の足 (4マス)": {"rows": 2, "cols": 2, "targets": [120, 120, 120, 120], "limit": 4},
    "【足】妖炎魔女のくつ (4マス)": {"rows": 2, "cols": 2, "targets": [200, 200, 200, 200], "limit": 4},
    "【足】ロードリーブーツ (4マス)": {"rows": 2, "cols": 2, "targets": [210, 210, 210, 210], "limit": 4},
    "【頭】聖域の闘志 (6マス)": {"rows": 3, "cols": 2, "targets": [150, 150, 170, 170, 150, 150], "limit": 8},
    "【腕】空賊のグローブ (6マス)": {"rows": 3, "cols": 2, "targets": [140, 140, 160, 160, 140, 140], "limit": 8},
    "【体下】スパングル下 (9マス)": {"rows": 3, "cols": 3, "targets": [130, 130, 130, 150, 150, 150, 130, 130, 130], "limit": 12},
    "【体上】叡聖のコート上 (9マス)": {"rows": 3, "cols": 3, "targets": [180, 240, 180, 240, 270, 240, 180, 240, 180], "limit": 18},
    "【体上】蒼穹の兵団鎧 (9マス)": {"rows": 3, "cols": 3, "targets": [190, 250, 190, 250, 280, 250, 190, 250, 190], "limit": 18},
}

# --- 2. 状態管理 ---
if 'board' not in st.session_state:
    st.session_state.board = np.zeros((2, 2))
    st.session_state.targets = np.full((2, 2), 120)
    st.session_state.success_limit = 4

# --- 3. サイドバー：装備検索 ---
st.set_page_config(page_title="裁縫職人DBアシスト", layout="wide")

with st.sidebar:
    st.header("🔍 装備検索")
    search_q = st.text_input("装備名・部位を入力")
    
    # 検索フィルタリング
    options = [name for name in ITEM_DB.keys() if search_q in name]
    if not options: options = list(ITEM_DB.keys())
    
    selected_item = st.selectbox("装備を選択", options)
    
    if st.button("基準値を反映"):
        item_data = ITEM_DB[selected_item]
        st.session_state.board = np.zeros((item_data["rows"], item_data["cols"]))
        st.session_state.targets = np.array(item_data["targets"]).reshape(item_data["rows"], item_data["cols"])
        st.session_state.success_limit = item_data["limit"]
        st.session_state.item_name = selected_item
        st.rerun()

    st.divider()
    st.header("📊 大成功の条件")
    st.write(f"この商材の合計誤差制限: **{st.session_state.success_limit} 以内**")
    st.caption("※各マスの誤差の絶対値を足した合計です。")

# --- 4. メイン画面：盤面と大成功判定 ---
st.title(f"🧵 {st.session_state.get('item_name', '装備を選択してください')}")

col_board, col_status = st.columns([2, 1])

with col_status:
    # 現在の合計誤差を計算
    current_diffs = np.abs(st.session_state.targets - st.session_state.board)
    total_error = np.sum(current_diffs)
    
    st.header("✨ 大成功判定")
    error_color = "green" if total_error <= st.session_state.success_limit else "red"
    st.markdown(f"### 現在の合計誤差: :{error_color}[{int(total_error)}]")
    
    if total_error <= st.session_state.success_limit:
        st.success("🎯 大成功圏内です！")
    else:
        st.warning(f"あと {int(total_error - st.session_state.success_limit)} 下げる必要があります。")

    st.divider()
    # ぬいパワー表示と精神統一（以前のロジック）
    idx = st.session_state.get('pattern_idx', 0) % 4
    current_p = ["普通", "強い", "最強", "弱い"][idx]
    st.metric("現在のぬいパワー", current_p)

with col_board:
    rows, cols = st.session_state.board.shape
    grid_cols = st.columns(cols)
    
    for r in range(rows):
        for c in range(cols):
            with grid_cols[c]:
                t = st.session_state.targets[r,c]
                b = st.session_state.board[r,c]
                d = t - b
                
                # 誤差表示（絶対値ではなく、縫い進めるための残り数値）
                color = "green" if d == 0 else "orange" if 0 < d <= 4 else "red" if d < 0 else "white"
                
                with st.container(border=True):
                    st.markdown(f"<div style='text-align:center;'>残り: <b style='color:{color}; font-size:20px;'>{int(d)}</b></div>", unsafe_allow_html=True)
                    st.session_state.board[r,c] = st.number_input(f"現({r},{c})", value=int(b), key=f"b_{r}_{c}")
                    st.session_state.targets[r,c] = st.number_input(f"基({r},{c})", value=int(t), key=f"t_{r}_{c}")

# --- 5. 操作ボタン ---
st.divider()
st.caption("操作: [⚡実行] 集中力消費とターン進行 | [🔄修正] ターンを維持して数値だけ保存 | [⏭️飛ばす] ターンを1つ進める")
# (以下、ボタン処理)
