import streamlit as st
import numpy as np
import pandas as pd

# --- 1. マリアさんの資料に基づく数値出現データ（重み付けの概念） ---
# 中央付近（15前後）の出現率が高く、端（12, 18）は低いことを考慮
BASE_DISTRIBUTION = {
    "通常": {12:1, 13:2, 14:3, 15:4, 16:3, 17:2, 18:1},  # 重み付けの例
    "加減": {6:1, 7:2, 8:2, 9:1},
}

POWER_RATES = {"弱い": 0.5, "普通": 1.0, "強い": 1.5, "最強": 2.0}

def calculate_distribution(skill, power, is_shitsuke):
    """
    指定された条件下での全出現パターンとその重みを計算する
    """
    if "加減" in skill:
        base = BASE_DISTRIBUTION["加減"]
    else:
        base = BASE_DISTRIBUTION["通常"]
    
    rate = POWER_RATES[power]
    shitsuke_mult = 2.0 if is_shitsuke else 1.0
    
    # 倍率を掛けた後の出現数値を計算
    dist = {}
    for v, weight in base.items():
        # DQXの計算式：基本値 × ぬいパワー倍率(端数切捨て) × しつけ倍率
        res = int(int(v * rate) * shitsuke_mult)
        dist[res] = dist.get(res, 0) + weight
    
    return dist

# --- 2. AI：次の一手推奨ロジック ---
def get_best_move(target_diff, power, is_shitsuke, available_skills):
    best_skill = None
    best_score = -1
    
    for skill_name in available_skills:
        if "縫い" not in skill_name: continue
        
        dist = calculate_distribution(skill_name, power, is_shitsuke)
        total_weight = sum(dist.values())
        
        # スコア計算：誤差0になる確率 + 誤差内に収まる期待値
        success_prob = dist.get(target_diff, 0) / total_weight
        
        # 暫定的な評価スコア（誤差0への近さと成功率の組み合わせ）
        if success_prob > best_score:
            best_score = success_prob
            best_skill = skill_name
            
    return best_skill, best_score

# --- 3. UI表示：表の見方の修正 ---
st.set_page_config(page_title="マリアの裁縫アシストPro [分布対応]", layout="wide")

st.title("🧵 裁縫アシスト：数値分布＆AI推奨モデル")

with st.sidebar:
    st.header("📖 表の読み方（修正済）")
    st.info("""
    **【重要】確率の偏りについて**
    表の数値は「一律」ではありません。
    - **中央値に近いほど** 出現しやすくなります。
    - **しつけがけ時** は、2倍された結果が飛び飛びになるため、狙える数値が限定されます。
    - **AI推奨** は、これら「出やすい数値」を優先して計算しています。
    """)

# --- 4. メイン画面：AI推奨と盤面 ---
col_main, col_ai = st.columns([2, 1])

with col_ai:
    st.header("🤖 AI推奨の分析")
    # 選択中のマスの残り数値に対して、最適な特技を提示
    # (例：ターゲットマスを選択するUI)
    selected_target = st.selectbox("分析するマス", ["(0,0)", "(0,1)", "(0,2)", "(1,0)..."])
    
    # 現在の状態を取得してAI計算
    r, c = 0, 0 # 選択されたインデックス
    diff = st.session_state.targets[r,c] - st.session_state.board[r,c]
    
    power = st.session_state.get('current_power', '普通')
    is_s = st.session_state.get('is_shitsuke_active', 0) > 0
    
    best_s, prob = get_best_move(diff, power, is_s, ALL_SKILLS.keys())
    
    if best_s:
        st.success(f"推奨：**{best_s}**")
        st.write(f"この手で誤差0になる相対確率：{prob*100:.1f}%")
    else:
        st.write("最適な手が見つかりません。削りを優先してください。")

with col_main:
    # 盤面表示 (以前のUIを継承)
    # 誤差0-4を黄色、0を緑にする表示を維持
    pass
