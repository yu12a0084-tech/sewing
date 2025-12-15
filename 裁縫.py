import streamlit as st
import numpy as np

# --- 1. データ定義 (レベル・スキル) ---
ALL_SKILLS = {
    "通常縫い": {"cost": 5, "lv": 1},
    "加減縫い": {"cost": 10, "lv": 3},
    "水平縫い": {"cost": 10, "lv": 7},
    "たすき縫い": {"cost": 7, "lv": 11},
    "垂直縫い": {"cost": 10, "lv": 15},
    "2倍縫い": {"cost": 9, "lv": 19},
    "3倍縫い": {"cost": 12, "lv": 23},
    "精神統一": {"cost": 7, "lv": 27},
    "糸ほぐし": {"cost": 16, "lv": 31},
    "逆たすき縫い": {"cost": 7, "lv": 35},
    "巻き込み縫い": {"cost": 18, "lv": 41},
    "しつけがけ": {"cost": 24, "lv": 47},
}

# ぬいパワーの定義
POWERS = ["弱い", "普通", "強い", "最強", "激強"]

# --- 2. 初期化 ---
if 'level' not in st.session_state: st.session_state.level = 70
if 'pattern' not in st.session_state: st.session_state.pattern = ["普通", "強い", "最強", "弱い"]
if 'pattern_idx' not in st.session_state: st.session_state.pattern_idx = 0
if 'board' not in st.session_state: st.session_state.board = np.zeros((3, 3))
if 'targets' not in st.session_state: st.session_state.targets = np.full((3, 3), 100)
if 'fixed_turns' not in st.session_state: st.session_state.fixed_turns = 0
if 'is_shifted' not in st.session_state: st.session_state.is_shifted = False

# --- 3. サイドバー：レベルと商材 ---
st.set_page_config(page_title="DQX裁縫アシストPro+", layout="wide")

with st.sidebar:
    st.header("👤 職人データ")
    st.session_state.level = st.number_input("職人レベル", 1, 80, st.session_state.level)
    available_skills = {name: d['cost'] for name, d in ALL_SKILLS.items() if d['lv'] <= st.session_state.level}
    
    st.divider()
    st.header("⚙️ ぬいパワー周期設定")
    pattern_input = st.text_input("基本周期 (カンマ区切り)", value=",".join(st.session_state.pattern))
    if st.button("周期を保存"):
        st.session_state.pattern = [p.strip() for p in pattern_input.split(",") if p.strip()]
        st.session_state.pattern_idx = 0
        st.rerun()

# --- 4. メイン画面：パワーシフト管理 ---
st.title("🧵 裁縫アシスト [パワーシフト対応]")

col_info1, col_info2 = st.columns([2, 1])

with col_info2:
    st.header("📊 現在の状態")
    
    # 周期上の予定パワー
    idx = st.session_state.pattern_idx % len(st.session_state.pattern)
    planned_power = st.session_state.pattern[idx]
    
    # 【重要】パワーシフト反映エリア
    st.subheader("⚡ ぬいパワー操作")
    current_power = st.selectbox(
        "現在の実ぬいパワー (ズレたら修正)", 
        POWERS, 
        index=POWERS.index(planned_power) if planned_power in POWERS else 1
    )
    
    # シフトが発生しているかの警告
    if current_power != planned_power:
        st.error(f"⚠️ パワーシフト発生中！\n(予定: {planned_power} → 実測: {current_power})")
        if st.button("このパワーを周期に強制上書き"):
            st.session_state.pattern[idx] = current_power
            st.success("周期を更新しました")
    else:
        st.success(f"ぬいパワー: {current_power} (周期通り)")

    st.session_state.focus = st.number_input("集中力", value=st.session_state.get('focus', 150))
    if st.session_state.fixed_turns > 0:
        st.warning(f"精神統一中 (残り {st.session_state.fixed_turns} 回)")

with col_info1:
    # 盤面表示 (4/6/9マスはこれまでのロジックを継承)
    st.subheader("📍 盤面 (上:現在値 / 下:基準値)")
    rows, cols = 3, 3 # 例として9マス
    grid = st.columns(cols)
    for r in range(rows):
        for c in range(cols):
            with grid[c]:
                diff = st.session_state.targets[r,c] - st.session_state.board[r,c]
                color = "green" if diff == 0 else "red" if diff < 0 else "orange" if diff <= 6 else "white"
                with st.container(border=True):
                    st.markdown(f"**残り: :{color}[{int(diff)}]**")
                    st.session_state.board[r,c] = st.number_input(f"現{r}{c}", value=int(st.session_state.board[r,c]), key=f"b_{r}_{c}", label_visibility="collapsed")
                    st.session_state.targets[r,c] = st.number_input(f"基{r}{c}", value=int(st.session_state.targets[r,c]), key=f"t_{r}_{c}", label_visibility="collapsed")

# --- 5. 実行とターン進行 ---
st.divider()
selected_skill = st.selectbox("使用特技", list(available_skills.keys()))

c1, c2, c3 = st.columns([1, 1, 1])

with c1:
    if st.button("⚡ 特技実行 (ターン進行)"):
        # 集中力消費
        st.session_state.focus -= available_skills[selected_skill]
        
        # 精神統一
        if selected_skill == "精神統一":
            st.session_state.fixed_turns = 3
        
        # ターン進行
        if st.session_state.fixed_turns > 0:
            st.session_state.fixed_turns -= 1
        else:
            st.session_state.pattern_idx += 1
        st.rerun()

with c2:
    if st.button("🔄 数値修正 (ターン維持)"):
        st.rerun()

with c3:
    if st.button("⏭️ 1ターン飛ばす (環境のみ進める)"):
        st.session_state.pattern_idx += 1
        st.rerun()

# 再生布の注記
if "再生" in st.sidebar.selectbox("布特性", ["【なし】", "【再生布】", "【虹布】", "【光布】"], key="cloth_type"):
    st.info("**再生布:** 4ターン毎に「最も縫い進んだ箇所」を手動修正してください。")
