import streamlit as st
import numpy as np

# --- 1. 内部データ定義 ---
# 習得レベル、消費集中力、倍率の相関
ALL_SKILLS = {
    "通常縫い": {"cost": 5, "lv": 1}, "加減縫い": {"cost": 10, "lv": 3},
    "水平縫い": {"cost": 10, "lv": 7}, "たすき縫い": {"cost": 7, "lv": 11},
    "垂直縫い": {"cost": 10, "lv": 15}, "2倍縫い": {"cost": 9, "lv": 19},
    "3倍縫い": {"cost": 12, "lv": 23}, "精神統一": {"cost": 7, "lv": 27},
    "糸ほぐし": {"cost": 16, "lv": 31}, "逆たすき縫い": {"cost": 7, "lv": 35},
    "巻き込み縫い": {"cost": 18, "lv": 41}, "しつけがけ": {"cost": 24, "lv": 47},
}

POWER_RATES = {"弱い": 0.5, "普通": 1.0, "強い": 1.5, "最強": 2.0}

# --- 2. 裁縫の極意（ひっさつ）判断ロジック ---
def analyze_hissatsu_utility(current_p, focus, diffs, is_charged, is_active):
    """
    ひっさつの戦略的価値を計算
    """
    max_d = np.max(diffs)
    
    if is_active:
        return "会心2倍モード継続中", "誤差の大きい箇所を優先しつつ、最強ターンの削り効率を最大化してください。"

    if is_charged:
        # ターン送りの価値が高いケース：集中力が低い、または次のパワーが「最強」で、今の「弱い」をスキップしたい場合
        if focus < 25 or current_p == "弱い":
            return "必殺使用推奨（ターン送り優先）", "消費集中力0でターンを進め、有利なパワー（最強等）へ遷移させる価値が高い状態です。"
        
        # 温存の価値が高いケース：調整段階で会心が出ると困る場合
        if max_d < 8:
            return "必殺温存推奨（調整優先）", "現在の微調整段階で会心が発生すると、数値が跳ねて誤差が残るリスクがあります。温存を推奨します。"
        
        return "必殺使用検討（会心バフ）", "会心率2倍の永続効果を得るため、削りフェーズの間に発動させるのが理想的です。"

    return None, None

# --- 3. UI構築 ---
st.set_page_config(page_title="裁縫アシストPro", layout="wide")

# 初期化
if 'level' not in st.session_state: st.session_state.level = 75
if 'is_hissatsu_charged' not in st.session_state: st.session_state.is_hissatsu_charged = False
if 'is_hissatsu_active' not in st.session_state: st.session_state.is_hissatsu_active = False

with st.sidebar:
    st.header("⚙️ システム設定")
    st.session_state.level = st.number_input("職人レベル", 1, 80, st.session_state.level)
    
    st.divider()
    st.header("🌈 裁縫の極意（必殺）")
    st.session_state.is_hissatsu_charged = st.checkbox("必殺チャージ", value=st.session_state.is_hissatsu_charged)
    st.session_state.is_hissatsu_active = st.checkbox("極意発動（会心2倍状態）", value=st.session_state.is_hissatsu_active)

# --- 4. メイン表示とAI分析 ---
col_board, col_analysis = st.columns([2, 1])

with col_analysis:
    st.header("📈 戦略分析")
    
    # 現状の特定
    diffs = st.session_state.targets - st.session_state.board
    idx = st.session_state.pattern_idx % 4
    current_p = ["普通", "強い", "最強", "弱い"][idx]
    
    # 必殺戦略の提示
    h_title, h_desc = analyze_hissatsu_utility(
        current_p, st.session_state.focus, diffs, 
        st.session_state.is_hissatsu_charged, st.session_state.is_hissatsu_active
    )
    
    if h_title:
        with st.container(border=True):
            st.markdown(f"**{h_title}**")
            st.caption(h_desc)

    # 精神統一ガイド
    if not st.session_state.fixed_turns > 0:
        if current_p == "最強":
            st.warning("最強パワー中：精神統一による『削り固定』が可能です。")
        elif current_p == "弱い":
            st.info("弱いパワー中：精神統一による『調整固定』が可能です。")

with col_board:
    st.subheader(f"盤面状況 (ぬいパワー: {current_p})")
    # 盤面入力と誤差の可視化ロジック
    # (誤差0=緑、1-4=黄、超過=赤のカラー表示)
    
# --- 5. アクション処理 ---
st.divider()
available_skills = {n: d['cost'] for n, d in ALL_SKILLS.items() if d['lv'] <= st.session_state.level}
selected_skill = st.selectbox("特技選択", list(available_skills.keys()))

c1, c2, c3 = st.columns(3)
with c1:
    if st.button("⚡ 特技実行 / 必殺発動"):
        if st.session_state.is_hissatsu_charged and not st.session_state.is_hissatsu_active:
            # 必殺使用時の処理
            st.session_state.is_hissatsu_charged = False
            st.session_state.is_hissatsu_active = True
            st.session_state.pattern_idx += 1
        else:
            # 通常の集中力消費とターン進行
            st.session_state.focus -= available_skills[selected_skill]
            # ...
        st.rerun()
