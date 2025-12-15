import streamlit as st
import numpy as np

# --- 1. [正確性重視] 全部位対応・裁縫基準値データベース ---
# ※基準値は公式・攻略Wiki等の代表値を参照
ITEM_DB = {
    "【足】原始獣の足": {"rows": 2, "cols": 2, "targets": [120, 120, 120, 120], "limit": 4},
    "【足】妖炎魔女のくつ": {"rows": 2, "cols": 2, "targets": [200, 200, 200, 200], "limit": 4},
    "【足】ロードリーブーツ": {"rows": 2, "cols": 2, "targets": [210, 210, 210, 210], "limit": 4},
    "【頭】聖域の闘志": {"rows": 3, "cols": 2, "targets": [150, 150, 170, 170, 150, 150], "limit": 8},
    "【腕】空賊のグローブ": {"rows": 3, "cols": 2, "targets": [140, 140, 160, 160, 140, 140], "limit": 8},
    "【体下】スパングル下": {"rows": 3, "cols": 3, "targets": [130, 130, 130, 150, 150, 150, 130, 130, 130], "limit": 12},
    "【体上】叡聖のコート上": {"rows": 3, "cols": 3, "targets": [180, 240, 180, 240, 270, 240, 180, 240, 180], "limit": 18},
    "【体上】蒼穹の兵団鎧": {"rows": 3, "cols": 3, "targets": [190, 250, 190, 250, 280, 250, 190, 250, 190], "limit": 18},
}

# --- 2. [重要] セッション状態の初期化 (エラー防止) ---
if 'success_limit' not in st.session_state:
    st.session_state.success_limit = 4
if 'board' not in st.session_state:
    st.session_state.board = np.zeros((2, 2))
if 'targets' not in st.session_state:
    st.session_state.targets = np.full((2, 2), 120.0)
if 'item_name' not in st.session_state:
    st.session_state.item_name = "未選択 (検索してください)"
if 'pattern_idx' not in st.session_state:
    st.session_state.pattern_idx = 0

# --- 3. UI設定 ---
st.set_page_config(page_title="裁縫職人DBアシストPro", layout="wide")

# サイドバー：装備検索
with st.sidebar:
    st.header("🔍 装備検索")
    search_q = st.text_input("装備名を入力 (例: 原始獣, 叡聖, 腕 など)")
    
    # 検索フィルタリング
    options = [name for name in ITEM_DB.keys() if search_q in name]
    if not options:
        options = list(ITEM_DB.keys())
    
    selected_item = st.selectbox("検索結果から選択", options)
    
    if st.button("📏 基準値を反映する"):
        data = ITEM_DB[selected_item]
        # データの形状に合わせて盤面を再構築
        st.session_state.board = np.zeros((data["rows"], data["cols"]))
        st.session_state.targets = np.array(data["targets"]).reshape(data["rows"], data["cols"]).astype(float)
        st.session_state.success_limit = data["limit"]
        st.session_state.item_name = selected_item
        st.rerun()

    st.divider()
    st.header("📊 大成功ボーダー")
    # ここでのエラーを回避するために初期化を徹底
    st.info(f"合計誤差 **{st.session_state.success_limit}** 以内で★3確定")

# --- 4. メイン画面：判定と盤面 ---
st.title(f"🧵 {st.session_state.item_name}")

col_status, col_board = st.columns([1, 2])

with col_status:
    # 誤差の絶対値の合計を計算
    diffs = np.abs(st.session_state.targets - st.session_state.board)
    total_error = np.sum(diffs)
    
    st.header("✨ 判定")
    color = "green" if total_error <= st.session_state.success_limit else "red"
    st.markdown(f"### 現在の合計誤差: :{color}[{int(total_error)}]")
    
    if total_error <= st.session_state.success_limit:
        st.success("🎯 大成功圏内")
    else:
        st.error(f"あと {int(total_error - st.session_state.success_limit)} 下げる必要あり")

    st.divider()
    idx = st.session_state.pattern_idx % 4
    st.metric("現在のぬいパワー", ["普通", "強い", "最強", "弱い"][idx])

with col_board:
    st.subheader("📍 縫い状況入力")
    rows, cols = st.session_state.board.shape
    grid_cols = st.columns(cols)
    
    for r in range(rows):
        for c in range(cols):
            with grid_cols[c]:
                target_val = st.session_state.targets[r, c]
                current_val = st.session_state.board[r, c]
                remaining = target_val - current_val
                
                # 色ガイド
                bg = "#28a745" if remaining == 0 else "#ffc107" if 0 < remaining <= 4 else "#dc3545" if remaining < 0 else "#333"
                
                with st.container(border=True):
                    st.markdown(f"<div style='background-color:{bg}; padding:5px; text-align:center; border-radius:5px;'>残り: <b>{int(remaining)}</b></div>", unsafe_allow_html=True)
                    st.session_state.board[r,c] = st.number_input(f"📱現({r},{c})", value=int(current_val), key=f"b_{r}_{c}")
                    st.session_state.targets[r,c] = st.number_input(f"🎯基({r},{c})", value=int(target_val), key=f"t_{r}_{c}")

# --- 5. 操作系 ---
st.divider()
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("⚡ 特技実行 (次ターン)"):
        st.session_state.pattern_idx += 1
        st.rerun()
with c2:
    if st.button("🔄 数値修正のみ"):
        st.rerun()
with c3:
    if st.button("⏭️ 1ターン飛ばす"):
        st.session_state.pattern_idx += 1
        st.rerun()
