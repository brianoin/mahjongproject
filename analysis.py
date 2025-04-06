import os
import cv2
import json
from collections import defaultdict, Counter
from FinalDetection import MahjongDetection

class MahjongAnalyzer:
    def calculate_discard_danger(self, visible_tiles):
        discard_danger = {}
        discard_counter = Counter()
        tile_seen_by_player = {'p2': set(), 'p3': set(), 'p4': set()}

        for player, tiles in visible_tiles['discards'].items():
            for tile in tiles:
                discard_counter[tile] += 1
                if player in tile_seen_by_player:
                    tile_seen_by_player[player].add(tile)

        upper_player = 'p4'
        lower_player = 'p2'
        upper_discards = visible_tiles['discards'].get(upper_player, [])

        all_tiles = [f"{i}{suit}" for suit in ['m', 'p', 's'] for i in range(1, 10)] + ['E', 'S', 'W', 'N', 'P', 'F', 'C']

        for tile in all_tiles:
            count = discard_counter[tile]

            if tile[0].isdigit():
                num = int(tile[0])
                if 4 <= num <= 6:
                    base_danger = 10
                elif num in [3, 7]:
                    base_danger = 6
                else:
                    base_danger = 3
            else:
                base_danger = 5

            player_safe = sum([1 for tiles in tile_seen_by_player.values() if tile in tiles])
            discard_penalty = count * 4 + player_safe * 3

            upper_to_lower_bonus = 0
            if tile in upper_discards and tile not in tile_seen_by_player[lower_player]:
                upper_to_lower_bonus = 4

            danger_score = base_danger - discard_penalty + upper_to_lower_bonus
            discard_danger[tile] = max(danger_score, 0)

        return discard_danger

    def get_safest_discard(self, hand_tiles, visible_tiles):
        danger_map = self.calculate_discard_danger(visible_tiles)
        safest_tile = None
        min_danger = float('inf')
        for tile in hand_tiles:
            danger = danger_map.get(tile, 10)
            if danger < min_danger:
                min_danger = danger
                safest_tile = tile
        return safest_tile

# 實際資料應從辨識結果載入
with open("game_state.json", "r", encoding="utf-8") as f:
    game_state = json.load(f)

analyzer = MahjongAnalyzer()

# 建立 visible_tiles 結構
visible_tiles = {
    "discards": {
        "p2": game_state["players"][1]["discards"],
        "p3": game_state["players"][2]["discards"],
        "p4": game_state["players"][3]["discards"]
    },
    "self_hand": game_state["players"][0]["hand"]
}

danger_map = analyzer.calculate_discard_danger(visible_tiles)
safest_discard = analyzer.get_safest_discard(visible_tiles["self_hand"], visible_tiles)

# 加入分析結果
game_state["analysis"] = {
    "discard_danger": danger_map,
    "suggested_discard": safest_discard
}

# 輸出更新後的 JSON
output_path = "game_state.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(game_state, f, ensure_ascii=False, indent=2)

print(f"已將分析結果寫入 {output_path}")

