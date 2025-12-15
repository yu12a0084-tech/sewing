import streamlit as st
import numpy as np

# --- 1. 初期化 ---
if 'targets' not in st.session_state:
    st.session_state.targets = np.full((3, 3), 100)
if 'board' not in st.session_state:
    st.session_state.board = np.zeros((3, 3), dtype=int)
if 'pattern' not in st.session_state:
    st.session_state.pattern = ["普通", "強い", "最強", "弱い"]
if 'pattern_idx' not in st.session_state:
    st.session_state.pattern_idx = 0
if 'focus' not in st.session_state:
    st.session_state.focus = 150
if 'fixed_turns' not in st.session_state:
    st.session_state.fixed_turns = 0

# --- 2. データ定義 ---
ITEM_PRESETS = {
    "【再生布】": {"targets": [[140, 180, 140], [140, 180, 140], [140, 180, 140]], "focus": 160},
    "【虹布】": {"targets": [[150, 150, 150], [150, 150, 150], [150, 150, 150]], "focus": 180},
    "【光布】": {"targets": [[130, 130, 130], [130, 130, 130], [130, 130, 130]], "focus": 160},
}
SKILL_COSTS = {
    "通常縫い": 5, "加減縫い": 10, "糸ほぐし": 16, "2倍縫い": 9, 
    "3倍縫い": 12, "水平縫い": 10, "垂直縫い": 10, "たすき縫い": 7, "精神統一": 7,
}

# --- 3. サイドバー ---
with st.sidebar:
    st.header("🧵 布特性設定")
    cloth_type = st.selectbox("布の種類を選択", list(ITEM_PRESETS.keys()))
    if st.button("設定を読み込む"):
        preset = ITEM_PRESETS[cloth_type]
        st.session_state.targets = np.array(preset["targets"])
        st.session_state.board = np.zeros((3, 3), dtype=int)
        st.session_state.focus = preset["focus"]
        st.session_state.pattern_idx = 0
        st.session_state.fixed_turns = 0
        st.rerun()

# --- 4. メイン画面 ---
st.title(f"裁縫アシスト :blue[{cloth_type}]")

# --- 🚨 再生布専用の重要注記エリア ---
if cloth_type == "【再生布】":
    st.warning("""
    **【再生布の操作について】** 再生布の場合、4ターンごとに「最も縫い進んだ箇所」が自動で12〜16戻ります。  
    このツールでは自動で数値を戻すことはしません（どれが再生したかゲーム画面で確認が必要なため）。  
    **再生が発生したら、該当するマスの数値を手動で書き換えてから「🔄 数値修正」を押してください。**
    """)
    
    # ターン経過による強調
    turn_num = st.session_state.pattern_idx + 1
    if turn_num % 4 == 0:
        st.error(f"📢 現在 第 {turn_num} ターン：**再生タイミングです！** 数値を確認してください。")

# --- メインレイアウト ---
col1, col2 = st.columns([2, 1])

with col2:
    st.header("📊 ステータス")
    st.session_state.focus = st.number_input("集中力", value=st.session_state.focus)
    idx = st.session_state.pattern_idx % len(st.session_state.pattern)
    st.metric("現在のぬいパワー", st.session_state.pattern[idx])
    
    if cloth_type == "【虹布】":
        st.session_state.special_effect = st.radio("集中力変化", ["なし", "消費集中力半分", "消費集中力1.5倍"])
    
    if st.session_state.fixed_turns > 0:
        st.info(f"精神統一中 (残り {st.session_state.fixed_turns} 回)")

with col1:
    st.header("📍 盤面入力")
    grid_cols = st.columns(3)
    for r in range(3):
        for c in range(3):
            with grid_cols[c]:
                diff = st.session_state.targets[r,c] - st.session_state.board[r,c]
                st.markdown(f"**({r},{c})** 差: **{diff}**")
                st.session_state.board[r,c] = st.number_input(f"現{r}{c}", value=int(st.session_state.board[r,c]), key=f"b_{r}_{c}", label_visibility="collapsed")
                st.session_state.targets[r,c] = st.number_input(f"目{r}{c}", value=int(st.session_state.targets[r,c]), key=f"t_{r}_{c}", label_visibility="collapsed")

# --- 5. 実行ボタン ---
st.divider()
selected_skill = st.selectbox("実行特技", list(SKILL_COSTS.keys()))

c1, c2 = st.columns(2)
with c1:
    if st.button("⚡ 実行 (ターン進行)"):
        # 集中力計算
        cost = SKILL_COSTS[selected_skill]
        if cloth_type == "【虹布】" and st.session_state.get('special_effect') == "消費集中力半分":
            cost //= 2
        elif cloth_type == "【虹布】" and st.session_state.get('special_effect') == "消費集中力1.5倍":
            cost = int(cost * 1.5)
        
        st.session_state.focus -= cost
        if selected_skill == "精神統一": st.session_state.fixed_turns = 3
        
        if st.session_state.fixed_turns > 0:
            st.session_state.fixed_turns -= 1
        else:
            st.session_state.pattern_idx += 1
        st.rerun()

with c2:
    if st.button("🔄 数値修正 (ターン維持)"):
        st.success("数値を反映しました。再生後の数値を元に再計算します。")
