import json
import math
from collections import Counter
print("2")
# 讀取 JSON 檔案(之後連結json檔)
with open("D:/mahjongproject/game_data.json", "r", encoding="utf-8") as f:
    game_data = json.load(f)
print("3")
# 解析 JSON 內容(底下的代號之後改)
# hand_list = input("請輸入手牌（以空格分隔每張牌）：")
# hand = hand_list.split()
hand = game_data["players"]["1"]["hand"]
melds = game_data["players"]["1"]["melds"]
riichi = game_data["players"]["1"]["Riichi"]
self_wind = game_data["players"]["1"]["Wind"]
discarded = game_data["players"]["1"]["discarded"]
total_tiles = game_data["Total_tiles"]
banker = game_data["Banker"]
dora = game_data["dora"]
step = game_data["Step"]
field_wind = game_data["field_wind"]
first_turn_draw = 0
riichi_turn_draw = 0
yaku = {}
print("4")
# 1. 計算符數 (基礎 20符)
fu = 20
is_menzenchin = len(melds) == 0
OneNine_Tiles = {"Wan_1", "Wan_9", "Tong_1", "Tong_9", "Taio_1", "Taio_9" }
Wind_Tiles = {"Feng_E", "Feng_S", "Feng_W", "Feng_N"}
SanYuan_Tiles = {"SanYuan_G", "SanYuan_W", "SanYuan_R"}
all_Word_tiles = Wind_Tiles | SanYuan_Tiles
all_old_tiles = OneNine_Tiles | all_Word_tiles

# 定義紅寶牌列表（你可以放所有紅寶牌的名字）
aka_dora_tiles = {"Wan_5_R", "Tong_5_R", "Taio_5_R"}
    
# 在初始化時做處理
aka_dora_count = sum(1 for tile in hand if tile in aka_dora_tiles)

def first_turn(step):
    if step == 1:
        first_turn_draw +=1 
    return first_turn_draw

def normalize_tile(tile):
    """將紅寶牌轉為普通牌，否則原樣回傳"""
    if tile.endswith("_R"):
        return tile[:-2]  # 移除 _R，變成普通牌
    return tile
print("5")
hand = [normalize_tile(tile) for tile in hand]
melds = [[normalize_tile(tile) for tile in meld] for meld in melds]

def has_word_tile_pair(hand, all_Word_tiles):
    """檢查手牌中是否有字牌雀頭（對子）"""
    tile_counts = Counter(hand)
    return any(tile in all_Word_tiles and count >= 2 for tile, count in tile_counts.items())

def has_one_nine_tile(hand, OneNine_Tiles):
    """判斷是否包含19牌"""
    return any(tile in OneNine_Tiles for tile in hand)

def is_riichi(riichi):
    """ 判斷是否立直 """
    return riichi is True

def is_tanyao(hand, melds, OneNine_Tiles, all_Word_tiles):
    """ 判斷是否為斷么九：全數 2-8 的數牌 """
    yaochuu = OneNine_Tiles | all_Word_tiles
    return all(tile not in yaochuu for tile in hand + [tile for meld in melds for tile in meld])

def is_menzen_tsumo(win_type, melds): #思考
    """ 判斷是否為門清自摸：門清且自摸 """
    return win_type == "tsumo" and len(melds)==0

def is_jikaze(self_wind, hand):
    """ 判斷是否為自風牌：刻子或槓子為自己的風 """
    return hand.count(self_wind) >= 3

def is_bakaze(field_wind, hand):
    """ 判斷是否為場風牌：刻子或槓子為場風 """
    return hand.count(field_wind) >= 3

def is_sangenpai(hand, SanYuan_Tiles):
    """ 判斷是否為三元牌：刻子或槓子為 白、發、中 """
    return any(hand.count(tile) >= 3 for tile in SanYuan_Tiles)

def is_pinfu(hand, melds, win_type, self_wind, field_wind, all_Word_tiles):
    """ 判斷是否為平和：門清、只有順子、單一雀頭（且非自風、場風、三元牌）、自摸 """
    if melds or win_type != "tsumo":
        return False

    tile_counts = Counter(hand)
    pairs = [tile for tile, count in tile_counts.items() if count == 2]

    # 必須只有一對雀頭，且不是字牌
    if len(pairs) != 1 or pairs[0] in all_Word_tiles or pairs[0] in {self_wind, field_wind}:
        return False

    # 不可以有刻子
    if any(count == 3 for count in tile_counts.values()):
        return False

    return True

def is_chankan(win_type): #思考
    """ 判斷是否為搶槓（1番） """
    return win_type == "chankan"

def is_haitei(win_type, total_tiles): #思考
    """ 判斷是否為海底摸月（1番） """
    return win_type == "tsumo" and total_tiles == 0

def is_houtei(win_type, total_tiles): #思考
    """ 判斷是否為河底撈魚（1番） """
    return win_type == "ron" and total_tiles == 0
print("6")
def is_rinshan(win_type): #思考
    """ 判斷是否為槓上開花（1番） """
    return win_type == "tsumo"

def is_ippatsu(riichi, first_turn_draw, riichi_turn_draw):
    """ 判斷是否為一發（1番）：立直後一巡內和牌 """
    if riichi_turn_draw == first_turn_draw:
        ippatsu = True
    else:
        riichi_turn_draw == first_turn_draw
        ippatsu = False
    return riichi and ippatsu is True

def is_iipeikou(hand, melds):
    """ 判斷是否為一盃口：門清，兩個相同的順子 """
    if melds:
        return False

    # 統計每種 tile 的數量
    tile_counts = Counter(hand)

    # 檢查所有可能順子（例如 Wan_1 ~ Wan_7）
    sequences = []
    suits = ["Wan", "Tong", "Taio"]
    for suit in suits:
        for i in range(1, 8):  # 1 ~ 7 能組成順子
            first = f"{suit}_{i}"
            second = f"{suit}_{i+1}"
            third = f"{suit}_{i+2}"
            if tile_counts[first] >= 2 and tile_counts[second] >= 2 and tile_counts[third] >= 2:
                sequences.append((first, second, third))

    return len(sequences) >= 1  # 至少有一組重複順子即為一盃口

def is_double_riichi(riichi, first_turn_draw):
    """ 判斷是否為兩立直（2番）：第一巡立直 """
    return riichi and first_turn_draw == 1

def is_san_shoku_doukou(hand, melds):
    """ 判斷是否為三色同刻（2番）：萬、筒、索各一組相同數字的刻子 """
    all_tiles = hand + [t for meld in melds for t in meld]
    tile_counts = {}

    for tile in all_tiles:
        suit, num = tile.split("_")
        key = (num, suit)
        tile_counts[key] = tile_counts.get(key, 0) + 1

    # 建立：數字 → 出現刻子的花色集合
    doku_map = {}
    for (num, suit), count in tile_counts.items():
        if count >= 3:
            doku_map.setdefault(num, set()).add(suit)

    # 若某數字在三種花色都有刻子
    return any(len(suits) == 3 for suits in doku_map.values())

def is_san_kantsu(melds):
    """ 判斷是否為三槓子（2番） """
    return sum(1 for meld in melds if len(meld) == 4) >= 3

def is_toitoi(hand, melds):
    """ 判斷是否為對對和（2番）：全部為刻子或槓子，無順子 """
    # 計算手牌中的刻子
    hand_counter = Counter(hand)
    ankou = sum(1 for tile, count in hand_counter.items() if count >= 3)

    # 副露中全部為刻或槓（長度 3 or 4 且所有牌相同）
    for meld in melds:
        if len(set(meld)) != 1:
            return False

    # 確保手牌也不包含順子（此處簡化為只要刻子）
    return True

def is_san_anko(hand, melds):
    """ 判斷是否為三暗刻（2番）：有 3 組未副露的刻子 """
    hand_counter = Counter(hand)

    ankou_count = 0
    for tile, count in hand_counter.items():
        if count >= 3:
            if not any(tile in meld for meld in melds):
                ankou_count += 1

    return ankou_count == 3

def is_shou_sangen(hand, melds, SanYuan_Tiles):
    """判斷是否為小三元（2番）：兩組三元牌刻子/槓子 + 一個三元牌對子"""
    all_tiles = hand + [tile for meld in melds for tile in meld]
    counter = Counter(all_tiles)

    triplet_count = sum(1 for tile in SanYuan_Tiles if counter[tile] >= 3)
    pair_count = sum(1 for tile in SanYuan_Tiles if counter[tile] == 2)

    return triplet_count == 2 and pair_count == 1

def is_honroutou(hand, melds):
    """ 判斷是否為混老頭（2番）：全是么九與字牌 """
    yaochuu = OneNine_Tiles | all_Word_tiles
    all_tiles = hand + [tile for meld in melds for tile in meld]
    return all(tile in yaochuu for tile in all_tiles)

def is_chiitoitsu(hand):
    """ 判斷是否為七對子（2番）：7 組不同的對子 """
    return len(hand) == 14 and all(hand.count(tile) == 2 for tile in set(hand)) and len(set(hand)) == 7

def is_honchantaiyao(hand, melds):
    """ 判斷是否為混全帶么九（2番，副露減 1 番）"""
    yaochuu = OneNine_Tiles | all_Word_tiles
    all_tiles = hand + [tile for meld in melds for tile in meld]
    return all(tile in yaochuu for tile in all_tiles)

def is_ittsuu(hand, melds):
    """一氣通貫判斷：同花色的 123, 456, 789"""
    suits = {"Wan": [], "Tong": [], "Taio": []}
    
    # 蒐集所有 tile
    for tile in hand + [t for meld in melds for t in meld]:
        norm_tile = normalize_tile(tile)
        parts = norm_tile.split("_")
        if len(parts) == 2:
            suit, num = parts
            suits[suit].append(num)
    
    patterns = [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"]]
    
    for suit in suits:
        if all(all(p in suits[suit] for p in group) for group in patterns):
            return True
    return False

def is_san_shoku_doujun(hand, melds):
    """判斷是否為三色同順（萬筒索中相同數字的順子）"""
    from collections import defaultdict

    suit_map = {"Wan": set(), "Tong": set(), "Taio": set()}
    
    all_tiles = hand + [t for meld in melds for t in meld]
    for tile in all_tiles:
        norm = normalize_tile(tile)
        if "_" in norm:
            suit, num = norm.split("_")
            suit_map[suit].add(num)

    # 檢查是否有相同的三個數字在三種花色中都出現
    for num in map(str, range(1, 8)):  # 順子的起點最多到 7
        if all(num in suit_map[suit] for suit in suit_map):
            if all(str(int(num) + 1) in suit_map[suit] and str(int(num) + 2) in suit_map[suit] for suit in suit_map):
                return True
    return False

def is_two_peikou(hand, melds):
    """判斷是否為二盃口（門清兩組相同順子）"""
    if melds:
        return False

    from collections import Counter
    norm_hand = [normalize_tile(t) for t in hand]

    # 嘗試組成所有可能順子
    sequences = []
    for tile in norm_hand:
        if "_" in tile:
            suit, num = tile.split("_")
            try:
                n = int(num)
                if f"{suit}_{n+1}" in norm_hand and f"{suit}_{n+2}" in norm_hand:
                    sequences.append((suit, n))
            except:
                continue

    # 計算重複順子的個數
    seq_counts = Counter(sequences)
    return sum(1 for count in seq_counts.values() if count >= 2) >= 2

def is_jun_chi(hand, melds): 
    """判斷是否為純全帶么九：只有1、9牌組成的順子和刻子 + 1、9牌組成的雀頭"""
    all_tiles = hand + [tile for meld in melds for tile in meld]
    norm_tiles = [normalize_tile(t) for t in all_tiles]
    
    # 紀錄是否包含 1 或 9 牌
    one_nine_tiles = {"1", "9"}
    has_one_nine_pair = False
    has_one_nine_sets = False

    # 檢查刻子與順子
    for tile in norm_tiles:
        if "_" not in tile:
            continue
        suit, num = tile.split("_")
        if num in one_nine_tiles:
            if norm_tiles.count(tile) >= 3:  # 檢查刻子
                has_one_nine_sets = True
            elif (f"{suit}_1" in norm_tiles and f"{suit}_2" in norm_tiles and f"{suit}_3" in norm_tiles) or \
                 (f"{suit}_7" in norm_tiles and f"{suit}_8" in norm_tiles and f"{suit}_9" in norm_tiles):  # 檢查順子
                has_one_nine_sets = True

    # 檢查雀頭
    for tile in norm_tiles:
        if norm_tiles.count(tile) == 2 and tile.split("_")[1] in one_nine_tiles:
            has_one_nine_pair = True

    return has_one_nine_sets and has_one_nine_pair

def is_hon_ichihou(hand, melds): 
    """判斷是否為混一色：只有一種數牌 + 字牌"""
    norm_tiles = [normalize_tile(t) for t in hand + [t for meld in melds for t in meld]]
    suits = set()
    has_word = False

    for tile in norm_tiles:
        if "_" not in tile:
            continue
        suit, _ = tile.split("_")
        if suit in {"Wan", "Tong", "Taio"}:
            suits.add(suit)
        else:
            has_word = True

    return len(suits) == 1 and has_word

def is_suu_ankou_tanki(hand, melds):
    """ 四暗刻單騎：四暗刻且單騎 """
    return len(set(hand)) == 2 and all(hand.count(tile) == 3 for tile in set(hand)) and len(melds) == 0
print("7")
def is_kokushi_13men(hand):
    """ 國士無雙十三面：13種特定牌，並且聽牌有一張國士無雙牌 """
    
    # 確認手牌是否包含13種特定牌
    hand_set = set(hand)
    if len(hand) == 13 and hand_set == all_old_tiles:
        return True  # 這是國士無雙十三面
    return False

def is_pure_nine_gate(hand):
    """ 純正九連寶登：必須是九連寶登，並且無副露 """
    suits = {"Wan": [], "Tong": [], "Taio": []}  # 假設有這三種花色

    # 將手牌分類到不同的花色
    for tile in hand:
        norm_tile = normalize_tile(tile)
        suit, num = norm_tile.split("_")
        suits[suit].append(num)

    # 檢查每個花色是否符合純正九連寶登
    for suit, tiles in suits.items():
        if sorted(tiles) == ["1", "1", "1", "2", "3", "4", "5", "6", "7", "8", "9", "9", "9"]:
            return True
    return False

def is_da_si_xi(hand, melds, Wind_Tiles):
    """ 大四喜：東南西北四刻子 """
    hand_wind_count = {tile: hand.count(tile) for tile in Wind_Tiles}
    return all(count == 3 for count in hand_wind_count.values()) and len(melds) == 0  # 沒有副露

def is_qing_yi_se(hand, melds):
    """清一色：所有牌同一花色，副露減一番"""
    suits = {"Wan": 0, "Tong": 0, "Taio": 0}
    all_tiles = hand + [t for meld in melds for t in meld]

    for tile in all_tiles:
        if tile.startswith("Wan_"):
            suits["Wan"] += 1
        elif tile.startswith("Tong_"):
            suits["Tong"] += 1
        elif tile.startswith("Taio_"):
            suits["Taio"] += 1

    return list(suits.values()).count(0) == 2  # 只有一個花色有值

def is_green_yi_se(hand, melds):
    """綠一色：所有牌為綠色的數字或發"""
    green_tiles = {"Taio_2", "Taio_3", "Taio_4", "Taio_6", "Taio_8", "SanYuan_G"}
    all_tiles = hand + [t for meld in melds for t in meld]
    return all(tile in green_tiles for tile in all_tiles)

def is_kokushi_13(hand):
    """國士無雙：13種么九字牌 + 任意一對"""
    if len(hand) != 14:
        return False

    unique_tiles = set(hand)
    if not unique_tiles.issubset(all_old_tiles):
        return False

    # 檢查 13 種牌是否齊全，並且有一張重複（雀頭）
    if len(unique_tiles) == 13:
        for tile in all_old_tiles:
            if hand.count(tile) == 2:
                return True
    return False

def is_qing_lao_tou(hand, melds):
    """清老頭：只包含數牌中的1與9"""
    all_tiles = hand + [t for meld in melds for t in meld]
    return all(tile in OneNine_Tiles for tile in all_tiles)

def is_xiao_si_xi(hand, melds, Wind_Tiles):
    """小四喜：三個風刻，且一個風雀頭"""

    all_tiles = hand + [t for meld in melds for t in meld]
    wind_counts = {tile: all_tiles.count(tile) for tile in Wind_Tiles}

    return (
        sum(count >= 3 for count in wind_counts.values()) == 3 and
        any(count == 2 for count in wind_counts.values())
    )

def is_da_san_yuan(hand, melds, SanYuan_Tiles):
    """大三元：三個三元刻子"""
    all_tiles = hand + [t for meld in melds for t in meld]
    return all(all_tiles.count(tile) >= 3 for tile in SanYuan_Tiles)

def is_jiu_lian_bao(hand): #難搞
    """
    判斷是否為九連寶燈的聽牌（13張）
    """
    if len(hand) != 13:
        return False

    # 將牌按花色分類
    suits = {"Wan": [], "Tong": [], "Taio": []}
    for tile in hand:
        for suit in suits:
            if tile.startswith(suit):
                suits[suit].append(tile)

    # 確保只有一種花色
    used_suits = [s for s in suits if len(suits[s]) > 0]
    if len(used_suits) != 1:
        return False

    # 分析這一種花色的牌
    suit_tiles = [tile for tile in hand if tile.startswith(used_suits[0])]
    tile_nums = [int(tile.split('_')[1].replace('R', '')) for tile in suit_tiles]  # 移除紅5
    counter = Counter(tile_nums)

    # 檢查1~9是否至少各一張，且1和9中至少有一個有三張
    base_structure = all(counter[i] >= 1 for i in range(1, 10))
    has_1_or_9_triple = counter[1] >= 3 or counter[9] >= 3
    return base_structure and has_1_or_9_triple

def is_zi_yi_se(hand, melds, all_Word_tiles):
    """字一色：全部是字牌"""
    all_tiles = hand + [t for meld in melds for t in meld]
    return all(tile in all_Word_tiles for tile in all_tiles)

def is_tian_he(banker, first_turn_draw):
    """ 天和：莊家於第一巡摸牌即和牌 """
    return banker==1 and first_turn_draw==1

def is_di_he(banker, first_turn_draw):
    """ 地和：閒家第一巡和牌，且未被鳴牌打斷 """
    return not banker==1 and first_turn_draw==1

def is_suu_ankou(hand, melds):
    """ 四暗刻：門清狀態下，有四個暗刻（不包含副露） """
    if melds:
        return False  # 有副露不能算暗刻

    tile_counts = Counter(hand)
    triplet_count = sum(1 for count in tile_counts.values() if count >= 3)
    return triplet_count >= 4

def is_suu_kantsu(melds):
    """ 四槓子：有四個槓子（明槓或暗槓） """
    kantsu_count = sum(1 for meld in melds if len(meld) == 4)
    return kantsu_count == 4
print("8")
# 判斷所有役種
def check_yaku_one_han(hand, melds, field_wind, self_wind, riichi, yaku):
    """ 檢查所有一番役種 """
    has_pair = has_word_tile_pair(hand, all_Word_tiles)
    has_OneNine = has_one_nine_tile(hand, OneNine_Tiles)
    
    if is_menzenchin:
        
        if riichi:
            if is_riichi(riichi):
                yaku["立直"] = 1
            if is_double_riichi(riichi, first_turn_draw):
                yaku["兩立直"] = 2
            if is_ippatsu(riichi, first_turn_draw, riichi_turn_draw):
                yaku["一發"] = 1
                
        if first_turn_draw==1:
            if is_tian_he(banker, first_turn_draw):
                yaku["天和"] = 13
            if is_di_he(banker, first_turn_draw):
                yaku["地和"] = 13
                  
        # if is_menzen_tsumo(win_type, melds):
        #     yaku["門清自摸"] = 1
        # if is_pinfu(hand, melds, win_type, self_wind, field_wind, all_Word_tiles):
            # yaku["平和"] = 1
        if is_iipeikou(hand, melds):
            yaku["一盃口"] = 1
        if is_two_peikou(hand, melds):
            yaku["二盃口"] = 3
        if is_chiitoitsu(hand):
            yaku["七對子"] = 2
        if is_kokushi_13(hand):
            yaku["國士無雙"] = 13
        if is_jiu_lian_bao(hand):
            yaku["九連寶登"] = 13

        if is_suu_ankou(hand, melds):
            yaku["四暗刻"] = 13
        if is_suu_ankou_tanki(hand, melds):
            yaku["四暗刻單騎"] = 26
        if is_kokushi_13men(hand):
            yaku["國士無雙十三面"] = 26
        if is_pure_nine_gate(hand):
            yaku["純正九連寶登"] = 26
    
    if has_pair:
        if is_jikaze(self_wind, hand):
            yaku["自風牌"] = 1
        if is_bakaze(field_wind, hand):
            yaku["場風牌"] = 1
        if is_sangenpai(hand, SanYuan_Tiles):
            yaku["三元牌"] = 1    
        if is_shou_sangen(hand, melds, SanYuan_Tiles):
            yaku["小三元"] = 2
        if is_xiao_si_xi(hand, melds, Wind_Tiles):
            yaku["小四喜"] = 13
        if is_da_san_yuan(hand, melds, SanYuan_Tiles):
            yaku["大三元"] = 13
        if is_zi_yi_se(hand, melds, all_Word_tiles):
            yaku["字一色"] = 13
        if is_da_si_xi(hand, melds, Wind_Tiles):
            yaku["大四喜"] = 26
        if is_honroutou(hand, melds):
            yaku["混老頭"] = 2
        if is_hon_ichihou(hand, melds):
            yaku["混一色"] = 3 if not melds else 2  # 副露減 1 番
            
    if has_OneNine:
        if is_honchantaiyao(hand, melds):
            yaku["混全帶么九"] = 2 if not melds else 1  # 副露減 1 番
        if is_ittsuu(hand, melds):
            yaku["一氣通貫"] = 2 if not melds else 1  # 副露減 1 番
        if is_qing_lao_tou(hand, melds):
            yaku["清老頭"] = 13
        if is_jun_chi(hand, melds):
            yaku["純全代么九"] = 3 if not melds else 2  # 副露減 1 番
            
    if not has_OneNine:
        if is_tanyao(hand, melds, OneNine_Tiles, all_Word_tiles):
            yaku["斷么九"] = 1
        if is_green_yi_se(hand, melds):
            yaku["綠一色"] = 13
            
    # if total_tiles <=4:
    #     if is_haitei(win_type, total_tiles):
    #         yaku["海底摸月"] = 1
    #     if is_houtei(win_type, total_tiles):
    #         yaku["河底撈魚"] = 1

    if not has_pair:
        if is_qing_yi_se(hand, melds):
            yaku["清一色"] = 6 if not melds else 5  # 副露減一番
            
    # if is_chankan(win_type):
    #     yaku["搶槓"] = 1
    # if is_rinshan(win_type):
    #     yaku["槓上自摸"] = 1
    if is_san_shoku_doukou(hand, melds):
        yaku["三色同刻"] = 2
    if is_san_kantsu(melds):
        yaku["三槓子"] = 2
    if is_toitoi(hand, melds):
        yaku["對對和"] = 2
    if is_san_anko(hand, melds):
        yaku["三暗刻"] = 2
    if is_san_shoku_doujun(hand, melds):
        yaku["三色同順"] = 2 if not melds else 1  # 副露減 1 番
    if is_suu_kantsu(melds):
        yaku["四槓子"] = 13
    
    return yaku
print("9")
# 加算副露與刻子符數
def calculate_fu(hand):
    fu = 20  # 基礎符數

    # 雀頭加符
    pairs = list({tile for tile in hand if hand.count(tile) == 2})
    if pairs:
        pair = pairs[0]
    if pair in SanYuan_Tiles: #如果是字牌+2
        fu += 2
    if pair in self_wind: #如果是自風牌+2
        fu+=2
    if pair in field_wind: #如果是場風牌+2
        fu+=2

    # 刻子、槓子加符
    def is_tile_in_melds(tile, melds):
        return any(tile in meld for meld in melds)
    
    for tile in set(hand):
        count = hand.count(tile)
        multiplier = 2 if tile in OneNine_Tiles or tile in SanYuan_Tiles or tile in Wind_Tiles else 1  # 幺九牌或字牌加倍
        if count == 3 and not is_tile_in_melds(tile, melds):
            fu += 4 * multiplier  # 暗刻
        elif count == 4 and not is_tile_in_melds(tile, melds):
            fu += 16 * multiplier  # 暗槓
        elif count == 3 and is_tile_in_melds(tile, melds):
            fu += 2 * multiplier  # 明刻
        elif count == 4 and is_tile_in_melds(tile, melds):
            fu += 8 * multiplier  # 明槓

    # 和牌方式還未解決
    # if win_type == "ron":  # 榮和 
    #     fu += 10
    # elif win_type == "tsumo":  # 自摸
    #     fu += 2

    return math.ceil(fu / 10) * 10  # 符向上取整到10的倍數

def calculate_final_points(yaku, hand, banker):  
    
    fu = calculate_fu(hand)
    han = sum(yaku.values())
    base_points = fu * (2 ** (han + 2))
    
    if han >= 13:
        base = 8000
    elif han >= 11:
        base = 6000
    elif han >= 8:
        base = 4000
    elif han >= 6:
        base = 3000
    elif han >= 5 or base_points >= 2000:
        base = 2000
    else:
        base = base_points
    final_points = (base * (6 if banker == 1 else 4) // 100 ) *100
    
    print(f"符數: {fu}, 翻數: {han},得點: {final_points}")
print("10")

while True:
    if step == 1:
        
        check_yaku_one_han(hand, melds, field_wind, self_wind, riichi, yaku)
        calculate_fu(hand)
        calculate_final_points(yaku, hand, banker)