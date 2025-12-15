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

# --- 3. メインレイアウト ---
st.set_page_config(page_title="DQX裁縫アシスト", layout="wide")
st.title(f"裁縫アシスト :blue[{st.session_state.get('cloth_type', '【選択してください】')}]")

# サイドバーで特性選択
with st.sidebar:
    st.header("🧵 基本設定")
    cloth_type = st.selectbox("布の種類", list(ITEM_PRESETS.keys()), key="cloth_type")
    if st.button("設定を反映してリセット"):
        preset = ITEM_PRESETS[cloth_type]
        st.session_state.targets = np.array(preset["targets"])
        st.session_state.board = np.zeros((3, 3), dtype=int)
        st.session_state.focus = preset["focus"]
        st.session_state.pattern_idx = 0
        st.session_state.fixed_turns = 0
        st.rerun()

# 再生布の重要注記（強調表示）
if st.session_state.get('cloth_type') == "【再生布】":
    st.warning("**⚠️ 再生布の重要ルール**：4ターンごとに最も縫い進んだ箇所が12〜16戻ります。再生を確認したら、手動で「現在値」を書き換え、下の「🔄 数値修正」を押してください。")

# --- 4. 盤面表示（ここを改良） ---
st.subheader("📍 盤面状況")

grid_cols = st.columns(3)
for r in range(3):
    for c in range(3):
        with grid_cols[c]:
            target = st.session_state.targets[r,c]
            current = st.session_state.board[r,c]
            diff = target - current
            
            # 色分けロジック
            if diff == 0: color = "green"; status = "🎉 完成"
            elif diff < 0: color = "red"; status = "⚠️ 縫いすぎ"
            elif diff <= 6: color = "orange"; status = "✨ 圏内"
            else: color = "gray"; status = "進行中"

            # カード風の囲い
            with st.container(border=True):
                st.markdown(f"### マス({r},{c})")
                st.markdown(f"**残り: :{color}[{diff}]** ({status})")
                
                # 入力エリア
                st.session_state.board[r,c] = st.number_input(
                    "📱 現在値 (ゲーム画面の値)", 
                    value=int(current), 
                    key=f"b_{r}_{c}"
                )
                
                st.divider() # 線を引いて区切る
                
                st.session_state.targets[r,c] = st.number_input(
                    "🎯 基準値 (ゴールの数値)", 
                    value=int(target), 
                    key=f"t_{r}_{c}"
                )

# --- 5. ステータスと操作 ---
st.divider()
col_left, col_right = st.columns([1, 1])

with col_left:
    st.header("📊 状態")
    st.session_state.focus = st.number_input("残り集中力", value=st.session_state.focus)
    idx = st.session_state.pattern_idx % len(st.session_state.pattern)
    st.metric("現在のぬいパワー", st.session_state.pattern[idx])
    
    if st.session_state.fixed_turns > 0:
        st.info(f"精神統一中 (残り {st.session_state.fixed_turns} 回)")

with col_right:
    st.header("⚡ アクション")
    selected_skill = st.selectbox("特技を選択", list(SKILL_COSTS.keys()))
    
    c1, c2 = st.columns(2)
    if c1.button("特技を実行して次へ"):
        st.session_state.focus -= SKILL_COSTS[selected_skill]
        if selected_skill == "精神統一": st.session_state.fixed_turns = 3
        
        if st.session_state.fixed_turns > 0:
            st.session_state.fixed_turns -= 1
        else:
            st.session_state.pattern_idx += 1
        st.rerun()

    if c2.button("🔄 数値修正 (再生反映)"):
        st.success("数値を更新しました")
