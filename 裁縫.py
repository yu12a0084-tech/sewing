import streamlit as st
import numpy as np

# --- 1. 初期化 (Session State) ---
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

# --- 2. 商材・布特性データ定義 ---
# 一般的な数値をセットしていますが、その場で書き換え可能です
ITEM_PRESETS = {
    "【再生布】(原始獣・精霊等)": {
        "targets": [[140, 180, 140], [140, 180, 140], [140, 180, 140]],
        "pattern": ["普通", "強い", "最強", "弱い"],
        "focus": 160,
        "note": "4ターンごとに最も縫い進んだ箇所が再生します。"
    },
    "【虹布】(不思議・神託等)": {
        "targets": [[150, 150, 150], [150, 150, 150], [150, 150, 150]],
        "pattern": ["普通", "強い", "最強", "弱い"],
        "focus": 180,
        "note": "消費集中力が半分or1.5倍、かつ会心率がアップするターンがあります。"
    },
    "【光布】(賢者・道士等)": {
        "targets": [[130, 130, 130], [130, 130, 130], [130, 130, 130]],
        "pattern": ["普通", "強い", "最強", "弱い"],
        "focus": 160,
        "note": "数ターンごとにどこかのマスの会心率が大幅にアップします。"
    }
}

SKILL_DB = {
    "通常縫い": 5, "加減縫い": 10, "糸ほぐし": 16, "2倍縫い": 9, 
    "3倍縫い": 12, "水平縫い": 10, "垂直縫い": 10, "たすき縫い": 7, "精神統一": 7,
}
ENV_LIST = ["普通", "弱い", "強い", "最強", "激強", "ランダム"]

# --- 3. サイドバー：布特性の選択 ---
with st.sidebar:
    st.header("🧵 布の特性を選択")
    cloth_type = st.selectbox("作成する布の種類", list(ITEM_PRESETS.keys()))
    
    if st.button("特性データを反映"):
        preset = ITEM_PRESETS[cloth_type]
        st.session_state.targets = np.array(preset["targets"])
        st.session_state.board = np.zeros((3, 3), dtype=int)
        st.session_state.pattern = preset["pattern"]
        st.session_state.focus = preset["focus"]
        st.session_state.pattern_idx = 0
        st.session_state.fixed_turns = 0
        st.success(f"{cloth_type} 設定完了")
    
    st.info(ITEM_PRESETS[cloth_type]["note"])

    st.divider()
    st.header("⚙ 環境ループ編集")
    pattern_text = st.text_input("ループ順序", value=",".join(st.session_state.pattern))
    if st.button("パターン更新"):
        st.session_state.pattern = [p.strip() for p in pattern_text.split(",") if p.strip() in ENV_LIST]
    
    st.subheader("ターン微調整")
    c1, c2 = st.columns(2)
    if c1.button("⬅ 戻す"): st.session_state.pattern_idx -= 1; st.rerun()
    if c2.button("進める ➡"): st.session_state.pattern_idx += 1; st.rerun()

# --- 4. メイン画面 ---
st.title("裁縫アシスト [光・虹・再生布 特化]")

col1, col2 = st.columns([2, 1])

with col2:
    st.header("📊 状況")
    st.session_state.focus = st.number_input("残り集中力", value=st.session_state.focus)
    
    # 現在の環境
    idx = st.session_state.pattern_idx % len(st.session_state.pattern)
    current_env = st.session_state.pattern[idx]
    
    if current_env == "ランダム":
        st.warning("🎲 ランダム環境")
        current_env = st.radio("発生環境を選択", ["普通", "弱い", "強い", "最強"], horizontal=True)
    else:
        st.metric("現在のぬいパワー", current_env)

    # 精神統一の自動管理
    if st.session_state.fixed_turns > 0:
        st.warning(f"精神統一中 (残り {st.session_state.fixed_turns} 回)")
    
    next_env = st.session_state.pattern[(st.session_state.pattern_idx + 1) % len(st.session_state.pattern)]
    st.info(f"次回の予定: {next_env}")

with col1:
    st.header("📍 盤面 (目標まであといくつ？)")
    grid_cols = st.columns(3)
    for r in range(3):
        for c in range(3):
            with grid_cols[c]:
                target = st.session_state.targets[r,c]
                current = st.session_state.board[r,c]
                diff = target - current
                
                # 誤差表示
                if diff == 0: color = "green"; label = "OK"
                elif 0 < diff <= 4: color = "orange"; label = "圏内"
                elif diff < 0: color = "red"; label = "Over"
                else: color = "white"; label = ""

                st.markdown(f"**({r},{c})** 差: :{color}[**{diff}**] {label}")
                st.session_state.board[r,c] = st.number_input(
                    f"b{r}{c}", value=int(current), key=f"b_{r}_{c}", label_visibility="collapsed"
                )
                # 目標値もその場で微調整可能に
                st.session_state.targets[r,c] = st.number_input(
                    f"t{r}{c}", value=int(target), key=f"t_{r}_{c}", label_visibility="collapsed"
                )

# --- 5. 操作実行 ---
st.divider()
e1, e2 = st.columns(2)

with e1:
    selected_skill = st.selectbox("実行特技", list(SKILL_DB.keys()))
    if st.button("⚡ 特技実行 (ターン進行)"):
        st.session_state.focus -= SKILL_DB[selected_skill]
        if selected_skill == "精神統一":
            st.session_state.fixed_turns = 3
        
        if st.session_state.fixed_turns > 0:
            st.session_state.fixed_turns -= 1
        else:
            st.session_state.pattern_idx += 1
        st.rerun()

with e2:
    st.write("集中力やターンを変えずに更新")
    if st.button("🔄 数値確定 / AI再計算"):
        st.rerun()
