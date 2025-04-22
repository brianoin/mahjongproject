import json
from collections import defaultdict

# 讀取遊戲資料
def read_game_data(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

# 提取所有玩家的已知牌
def extract_known_tiles(data):
    known_tiles = []
    dora_tiles = [tile for tile in data.get("dora", []) if tile != "back"]
    known_tiles += dora_tiles
    for pid in ["1", "2", "3", "4"]:
        player = data["players"][pid]
        known_tiles += player.get("discarded", [])
        # known_tiles += player.get("hand", [])
        
        for tile in known_tiles:
            if tile.endswith("_R") and tile[:-2][-1] == "5":
                known_tiles.append(tile[:-2])  # 加上額外的普通 5 號牌（如 Wan_5）
        for meld in player.get("melds", []):
            if isinstance(meld, str):
                known_tiles.append(meld)
            elif isinstance(meld, dict) and "tiles" in meld:
                known_tiles += meld["tiles"]
    
    return known_tiles

def adjust_based_on_sequence_rules(tile, player_discards):
    # 適用於數牌（萬、索、筒）
    if not any(c.isdigit() for c in tile):
        return 1.0

    num = int(''.join(filter(str.isdigit, tile)))
    suit = ''.join(filter(str.isalpha, tile))
    
    adjustment = 1.0

    # 147 型：打出1、4、7會降低對其他兩張的需求
    related_147 = {
        1: [4],
        4: [1, 7],
        7: [4]
    }

    # 258 型（多為搭子也可跳過，但可拓展使用）
    related_258 = {
        2: [5],
        5: [2, 8],
        8: [5]
    }

    # 369 型
    related_369 = {
        3: [6],
        6: [3, 9],
        9: [6]
    }

    all_related = {**related_147, **related_258, **related_369}

    if num in all_related:
        for related_num in all_related[num]:
            related_tile = f"{suit}{related_num}"
            # 檢查是否打出過這些相關的牌
            if any(related_tile in discard for discard in player_discards):
                adjustment *= 0.85  # 危險度下降一點

    return adjustment

# 計算剩餘牌
def calculate_remaining_tiles(all_tiles, known_tiles):
    remaining_tiles = {tile: all_tiles.get(tile, 0) for tile in all_tiles}
    for tile in known_tiles:
        if tile in remaining_tiles:
            remaining_tiles[tile] -= 1
    remaining_tiles = {tile: count for tile, count in remaining_tiles.items() if count > 0}
    return remaining_tiles

#副露型分析
def analyze_melds(melds):
    honor_melds = 0
    suit_melds = {"Wan": 0, "Tong": 0, "Tiao": 0}
    for meld in melds:
        tiles = meld["tiles"] if isinstance(meld, dict) else [meld]
        for t in tiles:
            if t.startswith("Feng") or t.startswith("SanYuan"):
                honor_melds += 1
            else:
                suit = ''.join(filter(str.isalpha, t))
                suit_melds[suit] += 1
    return honor_melds, suit_melds

# 推測對手是否聽牌以及可能的等牌
def predict_tenpai(data, remaining_tiles, self_hand):
    tenpai_info = {}
    for pid in ["2", "3", "4"]:
        player = data["players"][pid]
        round_wind = data["field_wind"]
        player_seat_wind = player.get("Wind")
        discarded_set = set(player.get("discarded", []))
        melds = player.get("melds", [])
        is_tenpai = player.get("Riichi", False) or len(melds) > 0

        wait_tiles = {}

        # 加入副露分析：字牌 or 同花色越多 → 聽牌可能性越高
        honor_melds, suit_melds = analyze_melds(melds)

        if is_tenpai:
            for tile, count in remaining_tiles.items():
                if tile in discarded_set:
                    continue

                score = count
                tile_suit = ''.join(filter(str.isalpha, tile))

                # 基本加乘
                score *= adjust_based_on_sequence_rules(tile, player.get("discarded", []))

                # 自風與場風處理
                if tile.startswith("Feng"):
                    if tile == round_wind and tile == player_seat_wind:
                        score *= 1.15 * 1.15
                    elif tile == player_seat_wind or tile == round_wind:
                        score *= 1.15
                    else:
                        score *= 0.8

                # 棄牌同花色越多 → 危險下降
                suit_count = {"Wan": 0, "Tong": 0, "Tiao": 0}
                for t in player.get("discarded", []):
                    for s in suit_count:
                        if t.startswith(s):
                            suit_count[s] += 1
                suit_multiplier = max(0.5, 1.0 - 0.035 * suit_count.get(tile_suit, 0))
                score *= suit_multiplier

                # 打過的張數越多 → 危險下降
                discarded_count = 4 - remaining_tiles.get(tile, 0)
                score *= max(0.0, 1.0 - 0.1 * discarded_count)

                # 字牌張數多 → 視為役牌型，聽牌機率升高
                if tile.startswith("Feng") or tile.startswith("SanYuan"):
                    if remaining_tiles.get(tile, 0) >= 2:
                        score *= 1.25
                    if honor_melds >= 1:
                        score *= 1.15

                # 同花色副露越多 → 視為一色、清一色風格
                if tile_suit in suit_melds and suit_melds[tile_suit] >= 6:
                    score *= 1.3  # 高機率專門等此花色

                # 數字牌中心張加成
                if any(c.isdigit() for c in tile):
                    num = int(''.join(filter(str.isdigit, tile)))
                    if num in [4, 5, 6]:
                        score *= 1.25
                    elif num in [3, 7]:
                        score *= 1.75
                    elif num in [2, 8]:
                        score *= 1.1
                    elif num in [1, 9]:
                        score *= 0.85

                wait_tiles[tile] = round(score, 2)

            danger_tiles = dict(sorted(wait_tiles.items(), key=lambda item: item[1], reverse=True)[:4])

        tenpai_info[f"p{pid}"] = {
            "is_tenpai": is_tenpai,
            "danger_tiles": danger_tiles,
            "wait_tiles": wait_tiles
        }

    return tenpai_info


data = read_game_data()

#計算玩家等級
def classify_player_level(player):
    melds_count = len(player.get("melds", []))
    has_riichi = player.get("Riichi", False)

    if has_riichi and melds_count == 0:
        return "expert"
    elif melds_count >= 2:
        return "intermediate"
    else :
        return "newbie"
    
player_levels = {}
for pid in ["2","3","4"]:
    player_data = data["players"][pid]
    player_levels[f"p{pid}"] = classify_player_level(player_data)

# 危險度估算 + 最安全出牌
def estimate_danger(self_hand, tenpai_info, total_remaining, player_levels):

    #計算前中後期
    def get_phase_weight(remaining_tiles):
        if remaining_tiles >= 40:
            return 0.8
        elif remaining_tiles < 40 and remaining_tiles >= 15:
            return 1.0
        else:
            return 1.2
    danger_scores = {}
    phase_weight = get_phase_weight(total_remaining)

    for tile in self_hand:
        score = 0.0

        # 三家皆計算
        for pid in ["p2", "p3", "p4"]:
            score += tenpai_info[pid]["wait_tiles"].get(tile, 0.0)
            base_risk = tenpai_info[pid]["wait_tiles"].get(tile, 0.0)

            #加上對手等級判斷
            level = player_levels.get(pid, "newbie")
            if level == "expert":
                base_risk *= 1.3
            elif level == "newbie":
                base_risk *= 0.9
            
            score += base_risk

        # 三家平均後，乘上階段關係
        score = (score/ 3.0) * phase_weight
        danger_scores[tile] = round(score, 3)

    # 推薦最安全的2~3張牌（最低分）
    sorted_tiles = sorted(danger_scores.items(), key=lambda x: x[1])
    safe_discards = [tile for tile, _ in sorted_tiles[:3]]

    return {
        "safe_discards": safe_discards,
        "danger_score": danger_scores
    }

# 主程式
def main():
    file_path = r"C:/mahjongproject/game_data(1).json"
    output_path = r"C:/mahjongproject/analysis(1).json"

    data = read_game_data(file_path)

    all_tiles = {
        "Feng_E": 4, "Feng_N": 4, "Feng_S": 4, "Feng_W": 4,
        "SanYuan_G": 4, "SanYuan_R": 4, "SanYuan_W": 4,
        "Tiao1": 4, "Tiao2": 4, "Tiao3": 4, "Tiao4": 4, "Tiao5": 4, "Tiao6": 4, "Tiao7": 4, "Tiao8": 4, "Tiao9": 4,
        "Tong1": 4, "Tong2": 4, "Tong3": 4, "Tong4": 4, "Tong5": 4, "Tong6": 4, "Tong7": 4, "Tong8": 4, "Tong9": 4,
        "Wan1": 4, "Wan2": 4, "Wan3": 4, "Wan4": 4, "Wan5": 4, "Wan6": 4, "Wan7": 4, "Wan8": 4, "Wan9": 4
    }

    known_tiles = extract_known_tiles(data)
    remaining_tiles = calculate_remaining_tiles(all_tiles, known_tiles)
    
    raw_hand = data["players"]["1"].get("hand", [])
    self_hand = []
    for tile in raw_hand:
        if tile.endswith("_R") and tile[:-2][-1] == "5":
            # 赤寶牌 → 加入普通5號牌（如 Wan_5）
            self_hand.append(tile[:-2])
        else:
            self_hand.append(tile)
            
    tenpai_info = predict_tenpai(data, remaining_tiles, self_hand)
    danger_info = estimate_danger(self_hand, tenpai_info, total_remaining, player_levels)
    total_remaining = sum(remaining_tiles.values())

    output_data = {
        "remaining_tiles": remaining_tiles,
        "tenpai_prediction": tenpai_info,
        "danger_estimation": danger_info,
        "total_remaining" : total_remaining
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()

