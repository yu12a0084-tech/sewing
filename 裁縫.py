import streamlit as st
import numpy as np
import math

# --- 1. 定数とスキルデータベース ---
AVG_NORMAL = 15.0
AVG_UNRAVEL = -7.5

SKILL_DB = {
    "通常縫い": {"id": 1, "cost": 5, "ratio": 1.0, "type": "pos"},
    "加減縫い": {"id": 2, "cost": 10, "ratio": 0.5, "type": "pos"},
    "糸ほぐし": {"id": 3, "cost": 16, "ratio": -1.0, "type": "pos"},
    "2倍縫い":  {"id": 4, "cost": 9, "ratio": 2.0, "type": "pos"},
    "3倍縫い":  {"id": 5, "cost": 12, "ratio": 3.0, "type": "pos"},
    "水平縫い": {"id": 6, "cost": 10, "ratio": 1.0, "type": "line_h"},
    "垂直縫い": {"id": 7, "cost": 10, "ratio": 1.0, "type": "line_v"},
    "精神統一": {"id": 8, "cost": 7, "ratio": 0.0, "type": "buff"},
    "パワーシフト": {"id": 9, "cost": 7, "ratio": 0.0, "type": "buff"},
}

ENV_MULT = {"普通": 1.0, "弱い": 0.5, "強い": 1.5, "最強": 2.0}

# --- 2. セッション状態の初期化 (ブラウザを閉じない限り保持) ---
if 'initialized' not in st.session_state:
    st.session_state.board = np.zeros((3, 3), dtype=int)
    st.session_state.targets = np.full((3, 3), 100)
    st.session_state.focus = 150
    st.session_state.env_idx = 0
    st.session_state.pattern = ["最強", "普通", "弱い", "普通", "強い", "普通"]
    st.session_state.fixed_turns = 0
    st.session_state.learning_bias = 0.0
    st.session_state.last_diff = 0
    st.session_state.initialized = True

# --- 3. ヘルパー関数 ---
def get_targets(skill_name, r, c):
    stype = SKILL_DB[skill_name]["type"]
    if stype == "pos": return [(r, c)]
    if stype == "line_h": return [(r, i) for i in range(3)]
    if stype == "line_v": return [(i, c) for i in range(3)]
    return []

def calc_total_diff(board, targets):
    return np.sum(np.abs(targets - board))

# --- 4. AIロジック (最強/弱い環境の優先度調整済み) ---
def find_best_move():
    best_score = -9999
    best_action = None
    current_diff = calc_total_diff(st.session_state.board, st.session_state.targets)
    curr_env = st.session_state.pattern[st.session_state.env_idx % len(st.session_state.pattern)]
    mult = ENV_MULT[curr_env]

    for name, data in SKILL_DB.items():
        if st.session_state.focus < data["cost"]: continue

        if data["type"] == "buff":
            # 精神統一の評価
            if name == "精神統一" and (curr_env in ["強い", "最強"]) and st.session_state.fixed_turns == 0:
                score = current_diff * 1.2 + st.session_state.learning_bias
                if score > best_score:
                    best_score, best_action = score, {"name": name, "r": 0, "c": 0}
            continue

        # 縫いスキルの評価
        for r in range(3):
            for c in range(3):
                targets = get_targets(name, r, c)
                if not targets: continue
                
                predicted_diff = current_diff
                base_val = AVG_UNRAVEL if name == "糸ほぐし" else AVG_NORMAL
                add_val = round(base_val * data["ratio"] * mult)

                for tr, tc in targets:
                    before = abs(st.session_state.targets[tr, tc] - st.session_state.board[tr, tc])
                    after = abs(st.session_state.targets[tr, tc] - (st.session_state.board[tr, tc] + add_val))
                    predicted_diff = predicted_diff - before + after
                
                improvement = current_diff - predicted_diff
                score = improvement * 10.0 - (data["cost"] * 0.5) + st.session_state.learning_bias
                
                # 「弱い」環境での微調整優先
                if curr_env == "弱い" and improvement > 0 and improvement < 10:
                    score += 20 

                if score > best_score:
                    best_score, best_action = score, {"name": name, "r": r, "c": c}
    return best_action

# --- 5. Web UIレイアウト ---
st.set_page_config(page_title="DQX裁縫アシストAI", layout="wide")
st.title("🧵 DQX 裁縫アシスト Webアプリ")

col1, col2 = st.columns([2, 1])

with col2:
    st.header("⚙ 状態設定")
    st.session_state.focus = st.number_input("集中力", value=st.session_state.focus)
    
    # 環境の明瞭化
    curr_env = st.session_state.pattern[st.session_state.env_idx % len(st.session_state.pattern)]
    next_env = st.session_state.pattern[(st.session_state.env_idx + 1) % len(st.session_state.pattern)]
    st.metric("現在の環境", curr_env, delta=f"次は {next_env}")
    
    if st.session_state.fixed_turns > 0:
        st.warning(f"精神統一中 (残り {st.session_state.fixed_turns} ターン)")

    if st.button("リセット"):
        st.session_state.clear()
        st.rerun()

with col1:
    st.header("📍 盤面入力")
    # 目標値と現在値の入力
    grid_cols = st.columns(3)
    for r in range(3):
        for c in range(3):
            with grid_cols[c]:
                diff = st.session_state.targets[r,c] - st.session_state.board[r,c]
                color = "red" if diff != 0 else "green"
                st.markdown(f"**マス({r},{c})** [差: :{color}[{diff}]]")
                st.session_state.board[r,c] = st.number_input(f"現在値", value=int(st.session_state.board[r,c]), key=f"b_{r}_{c}", label_visibility="collapsed")

# --- 6. AI推奨とアクション実行 ---
best = find_best_move()
st.divider()

if best:
    st.subheader(f"🤖 AI推奨: :{['blue','orange','red'][min(2, int(st.session_state.env_idx%3))]}[【{best['name']}】] (位置: {best['r']}, {best['c']})")
    
    # 行動実行ボタン
    if st.button(f"{best['name']} を実行して次へ"):
        # 学習用：実行前の誤差保存
        st.session_state.last_diff = calc_total_diff(st.session_state.board, st.session_state.targets)
        
        # 集中力消費
        st.session_state.focus -= SKILL_DB[best['name']]['cost']
        
        # 状態更新
        if best['name'] == "精神統一":
            st.session_state.fixed_turns = 3
        
        if st.session_state.fixed_turns > 0:
            st.session_state.fixed_turns -= 1
        else:
            st.session_state.env_idx += 1
            
        st.success("行動を記録しました。影響を受けたマスの数値を更新してください。")
        # ここで「影響を受けたマスの数値入力」を促すメッセージなどを出せます

st.write(f"現在の学習バイアス: {st.session_state.learning_bias:.2f}")

# 学習の実行 (誤差が変化したときに自動計算)
current_diff = calc_total_diff(st.session_state.board, st.session_state.targets)
if st.session_state.last_diff > 0 and current_diff != st.session_state.last_diff:
    improvement = st.session_state.last_diff - current_diff
    st.session_state.learning_bias += (improvement / 10.0)
    st.session_state.last_diff = current_diff