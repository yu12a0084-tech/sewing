import streamlit as st
import numpy as np

# --- 1. 初期化 (Session State) ---
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
if 'random_mode' not in st.session_state:
    st.session_state.random_mode = False

# --- 2. データ定義 ---
SKILL_DB = {
    "通常縫い": 5, "加減縫い": 10, "糸ほぐし": 16, "2倍縫い": 9, 
    "3倍縫い": 12, "水平縫い": 10, "垂直縫い": 10, "精神統一": 7,
}
ENV_LIST = ["普通", "弱い", "強い", "最強", "ランダム"]
PRESETS = {
    "虹のオーブ等": ["最強", "普通", "弱い", "普通", "強い", "普通"],
    "光の糸等": ["普通", "強い", "最強", "激強"], # 必要に応じて追加
    "ランダム入り": ["最強", "ランダム", "弱い", "普通"]
}

# --- 3. サイドバー：操作性向上 ---
with st.sidebar:
    st.header("⚙ 環境・パターン設定")
    
    # プリセット選択
    st.subheader("パターン選択")
    preset_name = st.selectbox("プリセットから選ぶ", list(PRESETS.keys()))
    if st.button("このパターンを適用"):
        st.session_state.pattern = PRESETS[preset_name]
        st.session_state.pattern_idx = 0
        st.session_state.fixed_turns = 0
        st.rerun()

    # 直接編集
    pattern_text = st.text_input("推移順序（自由編集）", value=",".join(st.session_state.pattern))
    if st.button("手動更新"):
        st.session_state.pattern = [p.strip() for p in pattern_text.split(",") if p.strip() in ENV_LIST]
        st.rerun()

    st.divider()
    st.write(f"精神統一残り: **{st.session_state.fixed_turns}** ターン")
    if st.button("⚠ 全リセット"):
        st.session_state.clear()
        st.rerun()

# --- 4. メイン画面：環境表示 ---
st.title("🧵 裁縫アシスト Ver.2")

col1, col2 = st.columns([2, 1])

with col2:
    st.header("📊 状態")
    st.session_state.focus = st.number_input("集中力", value=st.session_state.focus)
    
    # 現在の環境決定
    idx = st.session_state.pattern_idx % len(st.session_state.pattern)
    base_env = st.session_state.pattern[idx]
    
    if base_env == "ランダム":
        st.warning("🎲 ランダム環境です！")
        current_env = st.radio("実際に発生した環境は？", ["普通", "弱い", "強い", "最強"], horizontal=True)
    else:
        current_env = base_env
        st.metric("現在の環境", current_env)

    next_idx = (st.session_state.pattern_idx + 1) % len(st.session_state.pattern)
    st.info(f"次回の予定: **{st.session_state.pattern[next_idx]}**")

with col1:
    st.header("📍 盤面入力")
    grid_cols = st.columns(3)
    for r in range(3):
        for c in range(3):
            with grid_cols[c]:
                diff = st.session_state.targets[r,c] - st.session_state.board[r,c]
                st.markdown(f"**({r},{c})** 差: `{diff}`")
                st.session_state.board[r,c] = st.number_input(
                    f"b{r}{c}", value=int(st.session_state.board[r,c]), 
                    key=f"b_{r}_{c}", label_visibility="collapsed"
                )

# --- 5. 実行ボタン ---
st.divider()
c1, c2 = st.columns(2)

with c1:
    selected_skill = st.selectbox("特技実行", list(SKILL_DB.keys()))
    if st.button("⚡ 実行して次へ"):
        # 集中力減算
        st.session_state.focus -= SKILL_DB[selected_skill]
        
        # 精神統一の処理
        if selected_skill == "精神統一":
            st.session_state.fixed_turns = 3 # 実行ターン含め3回固定
        
        # ターン進行
        if st.session_state.fixed_turns > 0:
            st.session_state.fixed_turns -= 1
        else:
            st.session_state.pattern_idx += 1
        st.rerun()

with c2:
    st.write("入力ミスを直したい時はこちら")
    if st.button("🔄 数値だけ反映（ターン進めない）"):
        st.success("数値を更新しました")
