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

    def get_remaining_tiles(self, game_state):
        all_tiles = [f"{i}{suit}" for suit in ['m', 'p', 's'] for i in range(1, 10)] + ['E', 'S', 'W', 'N', 'P', 'F', 'C']
        full_tile_count = {tile: 4 for tile in all_tiles}

        seen_tiles = []

        for player in game_state["players"]:
            seen_tiles.extend(player.get("hand", []))
            seen_tiles.extend(player.get("discards", []))
            for meld in player.get("melds", []):
                seen_tiles.extend(meld)

        seen_counter = Counter(seen_tiles)

        remaining = {}
        for tile in all_tiles:
            remaining_count = full_tile_count[tile] - seen_counter.get(tile, 0)
            if remaining_count > 0:
                remaining[tile] = remaining_count

        return remaining

    def is_dangerous_tile(self, tile):
        if tile[0].isdigit():
            num = int(tile[0])
            return 3 <= num <= 7
        else:
            return tile in ['P', 'F', 'C']

    def estimate_opponent_tenpai_chance(self, visible_tiles, game_state):
        tenpai_chance = {}
        for idx, player_id in enumerate(["p2", "p3", "p4"], start=2):
            player_data = game_state["players"][str(idx)]
            discards = player_data.get("discards", [])
            melds = player_data.get("melds", [])
            riichi_declared = player_data.get("Riichi", False)

            chance = 0
            if riichi_declared:
                chance += 80
            if len(melds) > 0:
                chance += 20
            if len(discards) >= 6:
                dangerous_discards = [t for t in discards if self.is_dangerous_tile(t)]
                if len(dangerous_discards) >= 3:
                    chance += 20

            tenpai_chance[player_id] = min(chance, 100)

        return tenpai_chance


def update_info():
    try:
        with open(r"D:/mahjongproject/game_data.json", "r", encoding="utf-8") as file:
            data = json.load(file)

        hand = data["players"]["1"]["hand"]
        melds = data["players"]["1"]["melds"]
        riichi = data["players"]["1"]["Riichi"]
        self_wind = data["players"]["1"]["Wind"]
        discarded = data["players"]["1"]["discarded"]
        total_tiles = data["total_tiles"]
        banker = data["Banker"]
        dora = data["dora"]
        field_wind = data["field_wind"]

        return data
    except Exception as e:
        print("讀取 JSON 失敗:", e)
    

game_state = update_info()

visible_tiles = {
    "discards": {
        "p2": game_state["players"]["2"]["discards"],
        "p3": game_state["players"]["3"]["discards"],
        "p4": game_state["players"]["4"]["discards"]
    },
    "self_hand": game_state["players"]["1"]["hand"]
}

analyzer = MahjongAnalyzer()
danger_map = analyzer.calculate_discard_danger(visible_tiles)
safest_discard = analyzer.get_safest_discard(visible_tiles["self_hand"], visible_tiles)
remaining_tiles = analyzer.get_remaining_tiles(game_state)
tenpai_chances = analyzer.estimate_opponent_tenpai_chance(visible_tiles, game_state)

"要寫到新的.json檔裡面"
# game_state["analysis"] = {
#     "remaining_tiles": remaining_tiles,
#     "discard_danger": danger_map,
#     "suggested_discard": safest_discard,
#     "opponent_tenpai_chance": tenpai_chances
# }

# output_path = r"D:/mahjongproject/game_data.json"
# with open(output_path, "w", encoding="utf-8") as f:
#     json.dump(game_state, f, ensure_ascii=False, indent=2)

# print(f"已將分析結果寫入 {output_path}")
