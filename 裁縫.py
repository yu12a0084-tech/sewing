import streamlit as st
import numpy as np

# --- 1. 最初にならず全ての変数を初期化する ---
if 'pattern' not in st.session_state:
    st.session_state.pattern = ["最強", "普通", "弱い", "普通", "強い", "普通"]
if 'pattern_idx' not in st.session_state:
    st.session_state.pattern_idx = 0
if 'board' not in st.session_state:
    st.session_state.board = np.zeros((3, 3), dtype=int)
if 'targets' not in st.session_state:
    st.session_state.targets = np.full((3, 3), 100)
if 'focus' not in st.session_state:
    st.session_state.focus = 150
if 'fixed_turns' not in st.session_state:
    st.session_state.fixed_turns = 0

# --- 2. データ定義（スキルなど） ---
SKILL_DB = {
    "通常縫い": {"cost": 5, "ratio": 1.0, "type": "pos"},
    "加減縫い": {"cost": 10, "ratio": 0.5, "type": "pos"},
    "糸ほぐし": {"cost": 16, "ratio": -1.0, "type": "pos"},
    "2倍縫い":  {"cost": 9, "ratio": 2.0, "type": "pos"},
    "3倍縫い":  {"cost": 12, "ratio": 3.0, "type": "pos"},
    "水平縫い": {"cost": 10, "ratio": 1.0, "type": "line_h"},
    "垂直縫い": {"cost": 10, "ratio": 1.0, "type": "line_v"},
    "精神統一": {"cost": 7, "ratio": 0.0, "type": "buff"},
}
ENV_LIST = ["普通", "弱い", "強い", "最強"]

# --- 3. ここからサイドバーやメイン画面を書く ---
with st.sidebar:
    st.header("⚙ 環境設定")
    # ここに pattern_idx を使うコードを書いても、もうエラーになりません
    current_p_idx = st.session_state.pattern_idx % len(st.session_state.pattern)
    # ...残りのサイドバーコード...
# --- 3. サイドバー：環境設定機能 ---
with st.sidebar:
    st.header("⚙ 環境パターンの設定")
    
    # 推移パターンの編集（カンマ区切りで入力）
    pattern_text = st.text_input(
        "推移順序 (カンマ区切り)", 
        value=",".join(st.session_state.pattern),
        help="例: 最強,普通,弱い,普通"
    )
    if st.button("パターンを更新"):
        new_pattern = [p.strip() for p in pattern_text.split(",") if p.strip() in ENV_LIST]
        if new_pattern:
            st.session_state.pattern = new_pattern
            st.session_state.pattern_idx = 0
            st.success("パターンを更新しました")

    st.divider()
    st.header("🛠 現在の状態を手動修正")
    
    # 現在の環境を直接修正
    current_p_idx = st.session_state.pattern_idx % len(st.session_state.pattern)
    manual_env = st.selectbox(
        "現在の環境を強制変更", 
        ENV_LIST, 
        index=ENV_LIST.index(st.session_state.pattern[current_p_idx])
    )
    if st.button("現在の環境を確定"):
        # 選択した環境がパターンのどこにあるか探し、インデックスを合わせる
        if manual_env in st.session_state.pattern:
            st.session_state.pattern_idx = st.session_state.pattern.index(manual_env)
        st.success(f"環境を {manual_env} に固定しました")

    st.session_state.fixed_turns = st.number_input("精神統一残りターン", value=st.session_state.fixed_turns, min_value=0)

# --- 4. メイン画面のUI ---
st.title("🧵 DQX 裁縫アシスト (環境編集モデル)")

col1, col2 = st.columns([2, 1])

with col2:
    st.header("📊 ステータス")
    st.session_state.focus = st.number_input("残り集中力", value=st.session_state.focus)
    
    # 環境の明示（現在・次・その次）
    idx = st.session_state.pattern_idx
    pat = st.session_state.pattern
    curr_env = pat[idx % len(pat)]
    next_env = pat[(idx + 1) % len(pat)]
    
    st.metric("現在の環境", curr_env)
    st.info(f"次の環境予報: **{next_env}**")
    
    # 推移の可視化
    st.text(f"ループ順: {' → '.join(pat)}")

with col1:
    st.header("📍 盤面入力")
    grid_cols = st.columns(3)
    for r in range(3):
        for c in range(3):
            with grid_cols[c]:
                diff = st.session_state.targets[r,c] - st.session_state.board[r,c]
                st.markdown(f"**({r},{c})** 差分: `{diff}`")
                st.session_state.board[r,c] = st.number_input(
                    f"現在値_{r}_{c}", value=int(st.session_state.board[r,c]), 
                    key=f"b_{r}_{c}", label_visibility="collapsed"
                )

# --- 5. 実行処理 ---
st.divider()
exec_col1, exec_col2 = st.columns(2)

with exec_col1:
    selected_skill = st.selectbox("実行した特技", list(SKILL_DB.keys()))
    if st.button("特技を実行してターンを進める"):
        # 集中力消費
        st.session_state.focus -= SKILL_DB[selected_skill]['cost']
        
        # 精神統一の処理
        if selected_skill == "精神統一":
            st.session_state.fixed_turns = 3
        
        # ターン進行（精神統一中は環境を進めない）
        if st.session_state.fixed_turns > 0:
            st.session_state.fixed_turns -= 1
        else:
            st.session_state.pattern_idx += 1
        st.rerun()

with exec_col2:
    if st.button("🔄 数値のみ更新（ターン維持）"):
        st.rerun()

if st.button("⚠ 全リセット"):
    st.session_state.clear()
    st.rerun()

