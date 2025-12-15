import streamlit as st
import numpy as np
import pandas as pd

# --- 1. 定義データ (ALL_SKILLS / 期待値分布) ---
ALL_SKILLS = {
    "通常縫い": {"cost": 5, "lv": 1}, "加減縫い": {"cost": 10, "lv": 3},
    "水平縫い": {"cost": 10, "lv": 7}, "たすき縫い": {"cost": 7, "lv": 11},
    "垂直縫い": {"cost": 10, "lv": 15}, "2倍縫い": {"cost": 9, "lv": 19},
    "3倍縫い": {"cost": 12, "lv": 23}, "精神統一": {"cost": 7, "lv": 27},
    "糸ほぐし": {"cost": 16, "lv": 31}, "逆たすき縫い": {"cost": 7, "lv": 35},
    "巻き込み縫い": {"cost": 18, "lv": 41}, "しつけがけ": {"cost": 24, "lv": 47},
}

POWER_RATES = {"弱い": 0.5, "普通": 1.0, "強い": 1.5, "最強": 2.0}

# --- 2. 状態初期化 ---
if 'board' not in st.session_state: st.session_state.board = np.zeros((3, 3))
if 'targets' not in st.session_state: st.session_state.targets = np.full((3, 3), 100)
if 'focus' not in st.session_state: st.session_state.focus = 150
if 'pattern_idx' not in st.session_state: st.session_state.pattern_idx = 0
if 'fixed_turns' not in st.session_state: st.session_state.fixed_turns = 0
if 'is_hissatsu_active' not in st.session_state: st.session_state.is_hissatsu_active = False

# --- 3. メインレイアウト ---
st.set_page_config(page_title="裁縫アシストPro", layout="wide")
st.title("🧵 裁縫職人専用 計算・戦略アシスト")

# サイドバー：設定と必殺技
with st.sidebar:
    st.header("👤 職人・商材設定")
    level = st.number_input("職人レベル", 1, 80, 75)
    item_type = st.selectbox("商材タイプ", ["原始獣 (再生布)", "叡聖 (虹布)", "その他"])
    
    st.divider()
    st.header("🌈 裁縫の極意（必殺）")
    charged = st.checkbox("必殺チャージ！")
    st.session_state.is_hissatsu_active = st.checkbox("極意発動（永続会心2倍）", value=st.session_state.is_hissatsu_active)
    
    st.divider()
    st.info("""
    **【表の見方と確率の偏り】**
    数値の出方は均等ではありません。中央値（例：普通で15）が最も出やすく、端（12や18）は低確率です。AIはこの「重み」を考慮して推奨を出します。
    """)

# メインエリア：上段（盤面入力）
st.subheader("📍 盤面入力（上：現在値 / 下：基準値）")
rows, cols = (2, 2) if "4" in item_type else (3, 2) if "6" in item_type else (3, 3)
st.session_state.board = st.session_state.board[:rows, :cols]
st.session_state.targets = st.session_state.targets[:rows, :cols]

grid_cols = st.columns(cols)
for r in range(rows):
    for c in range(cols):
        with grid_cols[c]:
            diff = st.session_state.targets[r,c] - st.session_state.board[r,c]
            
            # 誤差に応じた背景色分け (マリアさんの知恵：0-4が黄色)
            if diff == 0: color = "#28a745"; status = "会心OK"
            elif 0 < diff <= 4: color = "#ffc107"; status = "圏内"
            elif diff < 0: color = "#dc3545"; status = "Over"
            else: color = "#ffffff"; status = ""
            
            with st.container(border=True):
                st.markdown(f"<div style='background-color:{color}; color:black; text-align:center; border-radius:3px;'><b>残り: {int(diff)}</b><br>{status}</div>", unsafe_allow_html=True)
                st.session_state.board[r,c] = st.number_input(f"📱現状({r},{c})", value=int(st.session_state.board[r,c]), key=f"b_{r}_{c}")
                st.session_state.targets[r,c] = st.number_input(f"🎯基準({r},{c})", value=int(st.session_state.targets[r,c]), key=f"t_{r}_{c}")

# メインエリア：中段（AI戦略・状態）
st.divider()
col_stat, col_ai = st.columns([1, 1])

with col_stat:
    st.header("📊 状態管理")
    st.session_state.focus = st.number_input("残り集中力", value=st.session_state.focus)
    idx = st.session_state.pattern_idx % 4
    current_p = ["普通", "強い", "最強", "弱い"][idx]
    st.metric("現在のぬいパワー", current_p)
    if st.session_state.fixed_turns > 0:
        st.warning(f"精神統一中：残り {st.session_state.fixed_turns} ターン")

with col_ai:
    st.header("🤖 AI推奨アクション")
    # 戦略的推奨 (必殺、最強削り、弱い調整)
    if charged:
        st.success("推奨：**必殺技の使用を検討**")
        st.caption("消費0でパワーを次に送れるチャンスです。削りが必要なら会心バフ目的で使いましょう。")
    elif current_p == "最強" and st.session_state.fixed_turns == 0:
        st.warning("推奨：**精神統一（最強固定）**")
        st.caption("最強パワーで一気に削る『削りフェーズ』の定石です。")
    elif current_p == "弱い" and np.max(st.session_state.targets - st.session_state.board) < 15:
        st.info("推奨：**加減縫い / 精神統一（弱い固定）**")
        st.caption("誤差が小さいマスを、弱いパワーで慎重に詰める『調整フェーズ』です。")
    else:
        st.write("盤面の数値を入力すると、最適な特技が表示されます。")

# メインエリア：下段（操作ボタン）
st.divider()
available_skills = {n: d['cost'] for n, d in ALL_SKILLS.items() if d['lv'] <= level}
selected_skill = st.selectbox("特技を選択", list(available_skills.keys()))

btn_c1, btn_c2, btn_c3 = st.columns(3)
with btn_c1:
    if st.button("⚡ 特技を実行して次へ"):
        st.session_state.focus -= available_skills[selected_skill]
        if selected_skill == "精神統一": st.session_state.fixed_turns = 3
        
        # ターン進行
        if st.session_state.fixed_turns > 0: st.session_state.fixed_turns -= 1
        else: st.session_state.pattern_idx += 1
        st.rerun()

with btn_c2:
    if st.button("🔄 数値を手動修正 (ターン維持)"):
        st.rerun()

with btn_c3:
    if st.button("⏭️ 1ターン飛ばす"):
        st.session_state.pattern_idx += 1
        st.rerun()
