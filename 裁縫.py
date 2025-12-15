import streamlit as st
import numpy as np

# --- 1. スキル習得レベルの定義 ---
# ゲーム内の習得レベルに基づいたリスト
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

# --- 2. 初期化 ---
if 'level' not in st.session_state:
    st.session_state.level = 70
if 'board_type' not in st.session_state:
    st.session_state.board_type = "9マス (3x3)"

# (その他の初期化は前回同様)
if 'targets' not in st.session_state: st.session_state.targets = np.full((3, 3), 100)
if 'board' not in st.session_state: st.session_state.board = np.zeros((3, 3), dtype=int)
if 'pattern' not in st.session_state: st.session_state.pattern = ["普通", "強い", "最強", "弱い"]
if 'pattern_idx' not in st.session_state: st.session_state.pattern_idx = 0
if 'fixed_turns' not in st.session_state: st.session_state.fixed_turns = 0

# --- 3. サイドバー：レベル設定とスキル制限 ---
st.set_page_config(page_title="DQX裁縫アシストPro+", layout="wide")

with st.sidebar:
    st.header("👤 職人データ")
    st.session_state.level = st.number_input("職人レベルを入力", 1, 80, st.session_state.level)
    
    # 現在のレベルで使えるスキルを抽出
    available_skills = {name: data['cost'] for name, data in ALL_SKILLS.items() if data['lv'] <= st.session_state.level}
    
    st.success(f"習得済みスキル: {len(available_skills)}種類")
    with st.expander("習得済みリスト"):
        for s in available_skills.keys():
            st.write(f"・{s}")

    st.divider()
    st.header("📦 商材設定")
    new_board_type = st.selectbox("マスの数", ["4マス (2x2)", "6マス (2x3)", "9マス (3x3)"], index=2)
    cloth_type = st.selectbox("布特性", ["【再生布】", "【虹布】", "【光布】"])
    
    if st.button("設定を適用してリセット"):
        st.session_state.board_type = new_board_type
        # ...リセット処理(前回同様)...
        st.rerun()

# --- 4. メイン表示 ---
st.title(f"🧵 裁縫アシスト (Lv.{st.session_state.level}対応)")

# レベルに応じたスキル解放アドバイス
next_skills = {name: data['lv'] for name, data in ALL_SKILLS.items() if data['lv'] > st.session_state.level}
if next_skills:
    next_s_name = min(next_skills, key=next_skills.get)
    st.info(f"💡 次は **Lv.{next_skills[next_s_name]}** で「{next_s_name}」を習得します。")

# 再生布注記（前回同様）
if cloth_type == "【再生布】":
    st.warning("⚠️ **再生布の操作**: 再生が発生したら手動で数値を修正し「🔄 数値修正」を押してください。")

# 盤面表示 (前回同様のデザイン)
# ...省略(マス数に応じた動的生成)...

# --- 5. 操作実行 ---
st.divider()
col_stat, col_act = st.columns([1, 1])

with col_act:
    st.header("⚡ 特技実行")
    # ★ここがポイント：習得済みスキルのみをセレクトボックスに表示
    selected_skill = st.selectbox("使用する特技", list(available_skills.keys()))
    
    current_cost = available_skills[selected_skill]
    st.caption(f"消費集中力: {current_cost}")

    if st.button("実行して次へ"):
        st.session_state.focus -= current_cost
        # ...ターン進行処理(前回同様)...
        st.rerun()

with col_stat:
    st.header("📊 状態")
    st.session_state.focus = st.number_input("残り集中力", value=st.session_state.focus)
    # ...環境表示(前回同様)...
