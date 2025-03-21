import json
import math

# 讀取 JSON 檔案(之後連結json檔)
with open("game_data.json", "r", encoding="utf-8") as f:
    game_data = json.load(f)

# 解析 JSON 內容(底下的代號之後改)
hand = game_data["hand"]
melds = game_data["melds"]
winning_tile = game_data["winningTile"]
win_type = game_data["winType"]
yaku = game_data["yaku"]
#需要新增自風/場風 self_wind/field_wind

# 1. 計算符數 (基礎 20符)
fu = 20

OneNine_Tiles = {"一萬", "九萬", "一筒", "九筒", "一索", "九索" }
Wind_Tiles = {"東", "南", "西", "北"}
Word_Tiles = {"白", "發", "中"}

# 加算副露與刻子符數
def calculate_fu(hand):
    fu = 20  # 基礎符數

    # 雀頭加符
    pair = [tile for tile in hand if hand.count(tile) == 2][0]  # 找出將牌
    if pair in Word_Tiles:  # 役牌將頭(名子之後改)
        fu += 2
    if pair in Wind_Tiles and

    # 刻子、槓子加符
    for tile in set(hand):
        count = hand.count(tile)
        multiplier = 2 if tile in OneNine_Tiles or tile in Word_Tiles or tile in Wind_Tiles else 1  # 幺九牌或字牌加倍
        if count == 3 and tile not in melds:
            fu += 4 * multiplier  # 暗刻
        elif count == 4 and tile not in melds:
            fu += 16 * multiplier  # 暗槓
        elif count == 3 and tile in melds:
            fu += 2 * multiplier  # 明刻
        elif count == 4 and tile in melds:
            fu += 8 * multiplier  # 明槓

    # 和牌方式
    if win_type == "ron":  # 榮和
        fu += 10
    elif win_type == "tsumo":  # 自摸
        fu += 2

    return math.ceil(fu / 10) * 10  # 符向上取整到10的倍數

fu = calculate_fu(hand)

# 2. 計算翻數 (直接加總 yaku)
han = sum(yaku.values())

# 3. 計算基本點數
base_points = fu * (2 ** (han + 2))

# 4. 計算得點
def calculate_points(base_points, is_parent):
    if base_points >= 8000:  # 滿貫以上
        return 8000 if not is_parent else 12000
    return base_points * (6 if is_parent else 4)

is_parent = game_data["player"] == 1  # 假設親家是玩家1
final_points = calculate_points(base_points, is_parent)

print(f"符數: {fu}, 翻數: {han}, 基本點數: {base_points}, 得點: {final_points}")
