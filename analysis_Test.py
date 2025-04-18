import json
from collections import defaultdict

# 讀取遊戲資料
def read_game_data(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

# 提取所有玩家的已知牌
def extract_known_tiles(data):
    known_tiles = []
    for pid in ["1", "2", "3", "4"]:
        player = data["players"][pid]
        known_tiles += player.get("discarded", [])
        known_tiles += player.get("hand", [])
        for meld in player.get("melds", []):
            if isinstance(meld, str):
                known_tiles.append(meld)
            elif isinstance(meld, dict) and "tiles" in meld:
                known_tiles += meld["tiles"]
    return known_tiles

# 計算剩餘牌
def calculate_remaining_tiles(all_tiles, known_tiles):
    remaining_tiles = {tile: all_tiles.get(tile, 0) for tile in all_tiles}
    for tile in known_tiles:
        if tile in remaining_tiles:
            remaining_tiles[tile] -= 1
    remaining_tiles = {tile: count for tile, count in remaining_tiles.items() if count > 0}
    return remaining_tiles

# 危險度估算 + 最安全出牌
def estimate_danger(self_hand, visible_discards, remaining_tiles, tenpai_info):
    danger_scores = {}

    for tile in self_hand:
        score = 0.0
        for pid in ["p2", "p3", "p4"]:
            info = tenpai_info.get(pid, {})
            if info.get("is_tenpai", False) and tile in info.get("wait_tiles", {}):
                score += info["wait_tiles"][tile]

        score += remaining_tiles.get(tile, 0) * 0.1

        if any(tile in visible_discards[pid] for pid in visible_discards):
            score *= 0.5

        danger_scores[tile] = round(score, 3)

    sorted_tiles = sorted(danger_scores.items(), key=lambda x: x[1])
    safe_discards = [tile for tile, _ in sorted_tiles[:3]]

    sorted_tiles_dangers = sorted(danger_scores.items(), key=lambda x: x[1], reverse=True)
    danger_discards = [tile for tile, _ in sorted_tiles_dangers[:3]]

    return {
        "safe_discards": safe_discards,
        "danger_score": danger_scores,
        "danger_discard": danger_discards
    }

# 取得場上所有可見棄牌
def get_visible_discards(data):
    return {
        "p1": data["players"]["1"].get("discarded", []),
        "p2": data["players"]["2"].get("discarded", []),
        "p3": data["players"]["3"].get("discarded", []),
        "p4": data["players"]["4"].get("discarded", [])
    }

# 推測對手是否聽牌以及可能的等牌
def predict_tenpai(data, remaining_tiles, self_hand, visible_discards, danger_info):
    tenpai_info = {}
    for pid in ["2", "3", "4"]:
        player = data["players"][pid]
        discarded_set = set(player.get("discarded", []))
        melds = player.get("melds", [])
        is_tenpai = player.get("Riichi", False) or len(melds) > 0

        wait_tiles = {}

        if is_tenpai:
            for tile, count in remaining_tiles.items():
                if tile in discarded_set:
                    continue

                score = count

                times_discarded = sum(p.get("discarded", []).count(tile) for p in data["players"].values())
                score *= 0.7 if times_discarded > 0 else 1.0

                tile_suit = ''.join(filter(str.isalpha, tile))
                meld_suits = [m[:len(tile_suit)] for m in sum([m if isinstance(m, list) else [m] for m in melds], [])]
                if any(tile_suit in ms for ms in meld_suits):
                    score *= 1.2

                if any(c.isdigit() for c in tile):
                    num = int(''.join(filter(str.isdigit, tile)))
                    if 3 <= num <= 7:
                        score *= 1.2
                    elif num in [1, 9]:
                        score *= 0.8
                else:
                    score *= 0.8

                if tile in self_hand:
                    score *= 0.8

                if tile in danger_info["danger_discard"]:
                    score *= 0.1

                wait_tiles[tile] = round(score, 2)

                if 13 - len(melds) == 4:
                    score *= 0.2

        tenpai_info[f"p{pid}"] = {
            "is_tenpai": is_tenpai,
            "wait_tiles": wait_tiles
        }

    return tenpai_info

# 主程式
def main():
    file_path = r"C:\Users\brian\Downloads\game_data.json"
    output_path = r"C:\Users\brian\Downloads\analysis.json"

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

    visible_discards = get_visible_discards(data)
    self_hand = data["players"]["1"].get("hand", [])

    # 初步先預估危險，給聽牌判斷參考
    dummy_tenpai = {f"p{pid}": {"is_tenpai": False, "wait_tiles": {}} for pid in ["2", "3", "4"]}
    danger_info = estimate_danger(self_hand, visible_discards, remaining_tiles, dummy_tenpai)

    # 再根據危險資訊預測聽牌
    tenpai_info = predict_tenpai(data, remaining_tiles, self_hand, visible_discards, danger_info)

    # 最後再重新評估危險
    danger_info = estimate_danger(self_hand, visible_discards, remaining_tiles, tenpai_info)

    output_data = {
        "remaining_tiles": remaining_tiles,
        "tenpai_prediction": tenpai_info,
        "danger_estimation": danger_info
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
