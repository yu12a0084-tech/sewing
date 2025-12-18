import tkinter as tk
from tkinter import ttk, messagebox
import math
import copy

# ==========================================
# 1. 定数・データベース定義
# ==========================================

# 基準値データベース
TARGETS = {
    "叡聖_頭": {"values": [0, 450, 0, 140, 300, 400, 0, 0, 0], "type": "Regen", "mask": [0, 2]},
    "叡聖_体上": {"values": [240, 150, 170, 130, 110, 90, 80, 130, 110], "type": "Regen", "mask": []},
    "叡聖_腕": {"values": [180, 130, 350, 230, 100, 120, 0, 0, 0], "type": "Regen", "mask": [6, 7, 8]},
    "叡聖_足": {"values": [450, 240, 130, 410, 0, 0, 0, 0, 0], "type": "Regen", "mask": [4, 5, 6, 7, 8]},
    "原始獣_頭": {"values": [0, 180, 0, 120, 180, 120, 0, 0, 0], "type": "Regen", "mask": [0, 2]},
    "原始獣_体上": {"values": [95, 40, 95, 60, 60, 60, 75, 40, 75], "type": "Regen", "mask": []},
    "原始獣_体下": {"values": [70, 70, 90, 90, 140, 140, 0, 0, 0], "type": "Regen", "mask": [6, 7, 8]},
    "原始獣_腕": {"values": [100, 50, 150, 100, 50, 150, 0, 0, 0], "type": "Regen", "mask": [6, 7, 8]},
    "原始獣_足": {"values": [170, 170, 130, 130, 0, 0, 0, 0, 0], "type": "Regen", "mask": [4, 5, 6, 7, 8]},
    "練習用_皮手": {"values": [15, 15, 15, 15, 15, 15, 0, 0, 0], "type": "Normal", "mask": [6, 7, 8]}
}

# 消費集中力
COSTS = {
    "ぬう": 5, "かげんぬい": 10, "糸ほぐし": 16,
    "水平ぬい": 10, "大滝のぼり": 10, "たすきぬい": 7,
    "2倍ぬい": 24, "3倍ぬい": 36, "精神統一": 7,
    "しつけがけ": 0 # ここでは計算上のコストとして扱わない（特殊処理）
}

# ダメージテーブル (画像データより転記)
# key: (Power, ActionType) -> [v1, v2, v3, v4, v5, v6, v7]
# ActionType: 'normal', 'weak'(kagen), 'reverse'(hogushi), 'double', 'triple'
DMG_TABLE_NORMAL = {
    # 弱い
    ("弱い", "normal"): [6, 7, 7, 8, 8, 9, 9],
    ("弱い", "weak"): [3, 4, 4, 4, 4, 5, 5],
    ("弱い", "reverse"): [-3, -3, -3, -3, -4, -4, -4], # 糸ほぐし(概算:負の値)
    ("弱い", "double"): [12, 13, 14, 15, 16, 17, 18],
    ("弱い", "triple"): [18, 20, 21, 23, 24, 26, 27],
    # 普通
    ("普通", "normal"): [12, 13, 14, 15, 16, 17, 18],
    ("普通", "weak"): [6, 7, 7, 8, 8, 9, 9],
    ("普通", "reverse"): [-6, -6, -7, -7, -8, -8, -9],
    ("普通", "double"): [24, 26, 28, 30, 32, 34, 36],
    ("普通", "triple"): [36, 39, 42, 45, 48, 51, 54],
    # 強い
    ("強い", "normal"): [18, 20, 21, 23, 24, 26, 27],
    ("強い", "weak"): [9, 11, 11, 12, 12, 14, 14],
    ("強い", "reverse"): [-9, -9, -10, -11, -12, -12, -13],
    ("強い", "double"): [36, 39, 42, 45, 48, 51, 54],
    ("強い", "triple"): [54, 59, 63, 68, 72, 77, 81],
    # 最強
    ("最強", "normal"): [24, 26, 28, 30, 32, 34, 36],
    ("最強", "weak"): [12, 13, 14, 15, 16, 17, 18],
    ("最強", "reverse"): [-12, -13, -14, -15, -16, -17, -18],
    ("最強", "double"): [48, 52, 56, 60, 64, 68, 72],
    ("最強", "triple"): [72, 78, 84, 90, 96, 102, 108],
}

# しつけ状態（2倍）時のダメージテーブル (画像データより転記)
# 半加減縫い、巻込などは「ぬう」の倍率違いとして処理せず、厳密に定義
DMG_TABLE_SHITSUKE = {
    # 弱い
    ("弱い", "normal"): [12, 14, 14, 16, 16, 18, 18],
    ("弱い", "weak"): [6, 8, 8, 8, 8, 10, 10], # 半加減
    ("弱い", "reverse"): [-6, -6, -7, -7, -8, -8, -9],
    ("弱い", "double"): [24, 26, 28, 30, 32, 34, 36],
    ("弱い", "triple"): [36, 40, 42, 46, 48, 52, 54],
    # 普通
    ("普通", "normal"): [24, 26, 28, 30, 32, 34, 36],
    ("普通", "weak"): [12, 14, 14, 16, 16, 18, 18],
    ("普通", "reverse"): [-12, -12, -14, -14, -16, -16, -18],
    ("普通", "double"): [48, 52, 56, 60, 64, 68, 72],
    ("普通", "triple"): [72, 78, 84, 90, 96, 102, 108],
    # 強い
    ("強い", "normal"): [36, 40, 42, 46, 48, 52, 54],
    ("強い", "weak"): [18, 22, 22, 24, 24, 28, 28],
    ("強い", "reverse"): [-18, -18, -21, -21, -24, -24, -27],
    ("強い", "double"): [72, 78, 84, 90, 96, 102, 108],
    ("強い", "triple"): [108, 118, 126, 136, 144, 154, 162],
    # 最強
    ("最強", "normal"): [48, 52, 56, 60, 64, 68, 72],
    ("最強", "weak"): [24, 28, 28, 32, 32, 36, 36],
    ("最強", "reverse"): [-24, -24, -28, -28, -32, -32, -36],
    ("最強", "double"): [96, 104, 112, 120, 128, 136, 144],
    ("最強", "triple"): [144, 156, 168, 180, 192, 204, 216],
}

# ==========================================
# 2. ロジッククラス
# ==========================================

class SewingLogic:
    def __init__(self):
        self.target_values = [0] * 9
        self.current_values = [0] * 9 # 現在の累積ダメージ
        self.shitsuke_flags = [False] * 9 # しつけがかかっているか
        self.item_type = "Regen"
        self.mask_indices = [] # 存在しないマス
        self.turn = 1
        
    def set_target(self, item_name):
        data = TARGETS[item_name]
        self.target_values = data["values"]
        self.item_type = data["type"]
        self.mask_indices = data["mask"]
        self.current_values = [0] * 9
        self.shitsuke_flags = [False] * 9
        self.turn = 1

    def get_remaining(self, idx):
        if idx in self.mask_indices: return 999
        return self.target_values[idx] - self.current_values[idx]

    def get_damage_dist(self, power, action_type, is_shitsuke):
        """指定された条件下でのダメージ分布（7パターン）を返す"""
        if power == "会心×2": power = "普通" # 会心×2は基礎ダメ普通と同じ
        
        table = DMG_TABLE_SHITSUKE if is_shitsuke else DMG_TABLE_NORMAL
        
        # ActionTypeの正規化
        key_action = "normal"
        if action_type == "かげんぬい": key_action = "weak"
        elif action_type == "糸ほぐし": key_action = "reverse"
        elif action_type == "2倍ぬい": key_action = "double"
        elif action_type == "3倍ぬい": key_action = "triple"
        elif action_type in ["ぬう", "水平ぬい", "大滝のぼり", "たすきぬい"]: key_action = "normal"
        
        return table.get((power, key_action), [0]*7)

    def simulate_action(self, action_name, target_indices, power, current_remains, shitsuke_flags):
        """
        アクションを実行した結果の「期待値スコア」を計算する
        target_indices: 対象となるマスのインデックスリスト
        """
        
        # 評価用変数の初期化
        total_score = 0
        
        # 7パターンの乱数をシミュレーションするのは計算量が爆発するため、
        # 「各マスごとの期待値」の和として簡易計算する
        # ※本来は全パターンの組み合わせだが、簡易AIとしては平均値で評価
        
        temp_remains = list(current_remains)
        
        # 対象マスの処理
        for idx in target_indices:
            if idx in self.mask_indices: continue
            
            is_shitsuke = shitsuke_flags[idx]
            dist = self.get_damage_dist(power, action_name, is_shitsuke)
            
            # このマスに対するアクションの良さを評価
            avg_dmg = sum(dist) / len(dist)
            
            # 会心考慮（簡易）: 会心が出たら残り数値にピタリ止まる
            # 会心率をざっくり計算 (power='最強'なら高い等)
            # ここでは厳密な確率計算より「残り数値への寄り方」を重視
            
            current_rem = temp_remains[idx]
            
            # 糸ほぐしの場合
            if action_name == "糸ほぐし":
                # マイナスダメージ＝回復
                # 戻りすぎて基準値を超えないようにキャップが必要だが、今は単純計算
                predicted_rem = current_rem - avg_dmg # マイナスを引く＝増える
            else:
                predicted_rem = current_rem - avg_dmg

            temp_remains[idx] = predicted_rem

        # 全体評価（誤差の絶対値の合計）
        score = 0
        for r in temp_remains:
            if r == 999: continue
            score += abs(r)
            
            # ボーナス評価
            # 0に近いほど高評価、マイナス（削りすぎ）はペナルティ大
            if r == 0: score -= 20 # ぴったり賞
            if r < -2 and action_name != "糸ほぐし": score += 50 # 削りすぎペナルティ
            
            # 調整しやすい数値への誘導 (4, 8など)
            if 3 <= r <= 5: score -= 5
            if 7 <= r <= 9: score -= 3

        return score, temp_remains

    def get_best_move(self, power, concentration, user_remains, user_shitsuke):
        """最善手を探す"""
        candidates = []
        
        # 定義：行動パターン
        single_moves = ["ぬう", "かげんぬい", "2倍ぬい", "3倍ぬい", "糸ほぐし", "しつけがけ"]
        # 範囲技定義 (インデックスリスト)
        ranges = {
            "水平(上)": [0, 1, 2], "水平(中)": [3, 4, 5], "水平(下)": [6, 7, 8],
            "大滝(左)": [0, 3, 6], "大滝(中)": [1, 4, 7], "大滝(右)": [2, 5, 8],
            "たすき(正)": [0, 4, 8], "たすき(逆)": [2, 4, 6]
        }

        # 1. 単体行動の評価
        for mv in single_moves:
            cost = COSTS.get(mv, 0)
            if mv == "しつけがけ": cost = 5 # 暫定コスト(本当は次ターンの倍加)

            if concentration < cost: continue
            
            for i in range(9):
                if i in self.mask_indices: continue
                # しつけ済みに重ねてしつけは無意味
                if mv == "しつけがけ" and user_shitsuke[i]: continue 
                
                # スコア計算
                if mv == "しつけがけ":
                    # しつけは「次のターン2倍で縫う」ことを仮定して評価
                    # 実際にはダメージを与えないので、現状維持スコアだが、
                    # 未来の期待値を加味する必要がある。
                    # 簡易的に「残り数値の半分」をスコアとする（大きな数値を削る準備）
                    score = sum([abs(x) for x in user_remains if x != 999]) - (user_remains[i] / 3)
                    new_rem = user_remains
                else:
                    score, new_rem = self.simulate_action(mv, [i], power, user_remains, user_shitsuke)
                
                candidates.append({
                    "name": f"{mv} @マス{i+1}",
                    "score": score,
                    "cost": cost,
                    "target": [i]
                })

        # 2. 範囲行動の評価
        for r_name, r_indices in ranges.items():
            base_name = r_name[:2]
            # 水平、大滝は「ぬう」系と同じ扱い
            act_type = "水平ぬい" if "水平" in r_name else "大滝のぼり" if "大滝" in r_name else "たすきぬい"
            cost = COSTS[act_type]
            
            if concentration < cost: continue
            
            # 有効なマスが1つ以上あるか
            valid_indices = [idx for idx in r_indices if idx not in self.mask_indices]
            if not valid_indices: continue
            
            score, new_rem = self.simulate_action(act_type, valid_indices, power, user_remains, user_shitsuke)
            
            candidates.append({
                "name": r_name,
                "score": score,
                "cost": cost,
                "target": valid_indices
            })
            
        # 3. 精神統一 (パワー維持)
        # 評価が難しいが、現在のパワーが「最強」または「会心x2」なら高評価
        if concentration >= 7:
            base_score = sum([abs(x) for x in user_remains if x != 999])
            unified_score = base_score
            if power == "最強" or power == "会心×2":
                unified_score -= 15 # ボーナス
            candidates.append({
                "name": "精神統一",
                "score": unified_score,
                "cost": 7,
                "target": []
            })

        # ソート (スコアが小さい＝誤差が小さい＝良い)
        candidates.sort(key=lambda x: x["score"])
        
        return candidates[:5] # Top 5

# ==========================================
# 3. GUI クラス
# ==========================================

class DQXSewingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DQX裁縫シミュレーター (GUI版)")
        self.logic = SewingLogic()
        
        # 変数
        self.var_item = tk.StringVar(value="叡聖_体上")
        self.var_power = tk.StringVar(value="ふつう")
        self.var_cp = tk.IntVar(value=150) # 集中力
        self.var_level = tk.IntVar(value=80)
        self.var_turn = tk.IntVar(value=1)
        self.cells = [] # Entry Widgets
        self.labels_target = [] # Target Value Labels
        self.shitsuke_vars = [] # BooleanVars for Checkbuttons
        
        # レイアウト構築
        self.create_widgets()
        self.on_item_change() # 初期化

    def create_widgets(self):
        # --- 上部設定エリア ---
        frame_top = ttk.LabelFrame(self.root, text="設定・状態", padding=10)
        frame_top.pack(fill="x", padx=5, pady=5)
        
        # 商材選択
        ttk.Label(frame_top, text="商材:").grid(row=0, column=0)
        cb_item = ttk.Combobox(frame_top, textvariable=self.var_item, values=list(TARGETS.keys()), state="readonly")
        cb_item.grid(row=0, column=1, padx=5)
        cb_item.bind("<<ComboboxSelected>>", lambda e: self.on_item_change())
        
        # 集中力
        ttk.Label(frame_top, text="集中力:").grid(row=0, column=2)
        ttk.Entry(frame_top, textvariable=self.var_cp, width=5).grid(row=0, column=3, padx=5)
        
        # 縫いパワー (ランダム環境対応のため手動変更可)
        ttk.Label(frame_top, text="現在のパワー:").grid(row=0, column=4)
        powers = ["弱い", "普通", "強い", "最強", "会心×2"]
        cb_power = ttk.Combobox(frame_top, textvariable=self.var_power, values=powers, state="readonly", width=8)
        cb_power.grid(row=0, column=5, padx=5)
        
        # ターン数
        ttk.Label(frame_top, text="ターン:").grid(row=0, column=6)
        lbl_turn = ttk.Label(frame_top, textvariable=self.var_turn)
        lbl_turn.grid(row=0, column=7, padx=5)

        # --- メイングリッドエリア (3x3) ---
        frame_grid = ttk.LabelFrame(self.root, text="布の状態 (現在値 / 基準値)", padding=10)
        frame_grid.pack(pady=5)
        
        for r in range(3):
            for c in range(3):
                idx = r * 3 + c
                
                # フレーム
                f_cell = ttk.Frame(frame_grid, borderwidth=1, relief="solid")
                f_cell.grid(row=r, column=c, padx=5, pady=5)
                
                # 基準値表示
                lbl_t = ttk.Label(f_cell, text="0", font=("Arial", 8), foreground="gray")
                lbl_t.pack(anchor="n")
                self.labels_target.append(lbl_t)
                
                # 現在値入力 (ユーザーが結果を入力)
                entry = ttk.Entry(f_cell, width=5, font=("Arial", 14, "bold"), justify="center")
                entry.pack(pady=2)
                entry.insert(0, "0")
                self.cells.append(entry)
                
                # しつけチェック
                chk_var = tk.BooleanVar(value=False)
                chk = ttk.Checkbutton(f_cell, text="しつけ", variable=chk_var)
                chk.pack(anchor="s")
                self.shitsuke_vars.append(chk_var)
                
                # 残り数値表示用ラベル（動的に更新）
                # ここでは簡易化のため省略し、計算ボタンで表示

        # --- 操作ボタンエリア ---
        frame_action = ttk.Frame(self.root, padding=10)
        frame_action.pack(fill="x")
        
        ttk.Button(frame_action, text="AI提案 (解析)", command=self.analyze).pack(side="left", padx=10)
        ttk.Button(frame_action, text="ターン経過 (+1)", command=self.next_turn).pack(side="left", padx=10)
        ttk.Button(frame_action, text="リセット", command=self.on_item_change).pack(side="right", padx=10)

        # --- 結果表示エリア ---
        self.txt_result = tk.Text(self.root, height=10, width=60)
        self.txt_result.pack(padx=10, pady=10)

    def on_item_change(self):
        item = self.var_item.get()
        self.logic.set_target(item)
        
        # GUIリセット
        self.var_turn.set(1)
        self.var_cp.set(150)
        self.var_power.set("普通")
        
        for i, val in enumerate(self.logic.target_values):
            # マスク処理
            if i in self.logic.mask_indices:
                self.cells[i].delete(0, tk.END)
                self.cells[i].insert(0, "-")
                self.cells[i].config(state="disabled")
                self.labels_target[i].config(text="-")
                self.shitsuke_vars[i].set(False)
            else:
                self.cells[i].config(state="normal")
                self.cells[i].delete(0, tk.END)
                self.cells[i].insert(0, "0") # 初期ダメージ0
                self.labels_target[i].config(text=f"/{val}")
                self.shitsuke_vars[i].set(False)
        
        self.txt_result.delete("1.0", tk.END)
        self.txt_result.insert(tk.END, f"【{item}】をセットしました。\n")

    def get_current_state(self):
        # GUIから現在の状態を取得
        current_damages = []
        user_shitsuke = []
        
        for i in range(9):
            if i in self.logic.mask_indices:
                current_damages.append(0)
                user_shitsuke.append(False)
                continue
            
            try:
                val = int(self.cells[i].get())
            except ValueError:
                val = 0
            current_damages.append(val)
            user_shitsuke.append(self.shitsuke_vars[i].get())
            
        return current_damages, user_shitsuke

    def analyze(self):
        current_damages, user_shitsuke = self.get_current_state()
        
        # 残り数値リストの作成
        remains = []
        target_vals = self.logic.target_values
        
        total_error = 0
        txt_remains = "残り数値: \n"
        
        for i in range(9):
            if i in self.logic.mask_indices:
                remains.append(999)
                txt_remains += " [ × ] "
            else:
                rem = target_vals[i] - current_damages[i]
                remains.append(rem)
                total_error += abs(rem)
                txt_remains += f" [{rem:3}] "
            if (i+1) % 3 == 0: txt_remains += "\n"
            
        power = self.var_power.get()
        cp = self.var_cp.get()
        turn = self.var_turn.get()
        
        # AI解析
        best_moves = self.logic.get_best_move(power, cp, remains, user_shitsuke)
        
        # 結果表示
        res = f"--- ターン{turn} / {power} / CP:{cp} ---\n"
        res += f"現在の合計誤差(絶対値): {total_error}\n"
        res += txt_remains
        
        # 再生布チェック
        if self.logic.item_type == "Regen":
            if turn % 4 == 0:
                res += "★警告: このターン終了時に【再生】が発動します！(最大ダメージ箇所 -12~16)\n"
            else:
                res += f"※再生まであと {4 - (turn % 4)} ターン\n"

        res += "\n【推奨アクション TOP3】\n"
        for i, move in enumerate(best_moves[:3]):
            res += f"{i+1}. {move['name']} (消費{move['cost']}) -> 評価スコア:{move['score']:.1f}\n"
            
        self.txt_result.delete("1.0", tk.END)
        self.txt_result.insert(tk.END, res)

    def next_turn(self):
        # ターンを経過させ、パワーを更新する（簡易ローテーション）
        t = self.var_turn.get()
        self.var_turn.set(t + 1)
        
        # パワー遷移ロジック（ランダム環境の場合はユーザー手動推奨だが、一応の周期を入れる）
        # 原始獣など: 普通→？→弱い→最強→強い... は商材によるので、
        # ここでは「ユーザーが自分でプルダウンを変える」ことを前提とし、
        # アナウンスのみ行う。
        self.txt_result.insert(tk.END, "\nターンを進めました。実際の縫いパワーに合わせてプルダウンを変更してください。\n")

# ==========================================
# メイン実行
# ==========================================

if __name__ == "__main__":
    root = tk.Tk()
    app = DQXSewingApp(root)
    root.mainloop()
