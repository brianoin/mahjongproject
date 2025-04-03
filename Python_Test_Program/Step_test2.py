import cv2
import mss
import numpy as np
from ultralytics import YOLO
import time
import json
import os

class MahjongDetection:
    def __init__(self, mid_model_path, tiles_model_path, json_file_path):
        """初始化 YOLO 模型"""
        self.mid_model = YOLO(mid_model_path)  # 行動指示燈模型
        self.tiles_model = YOLO(tiles_model_path)  # 麻將牌偵測模型
        self.json_file_path = json_file_path #json檔儲存路徑
        self.previous_turn = None  # 記錄上一位玩家
        self.init_json() #json檔初始化
        
    def init_json(self):
        """初始化 JSON 檔案，如果存在則刪除舊檔案，創建新的空白檔案"""
        try:
            # 如果 JSON 檔案存在，先刪除
            if os.path.exists(self.json_file_path):
                os.remove(self.json_file_path)
                print(f"舊的 JSON 檔案已刪除：{self.json_file_path}")

            # 創建新的空白 JSON 檔案
            data = {
                "Banker": None,  # 初始無莊家
                "dora": [],
                "players": {
                    "1": {"hand": [], "discarded": [], "melds": []},
                    "2": {"discarded": [], "melds": []},
                    "3": {"discarded": [], "melds": []},
                    "4": {"discarded": [], "melds": []}
                }
            }

            # 寫入新的 JSON 檔案
            with open(self.json_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"已創建新的 JSON 檔案：{self.json_file_path}")

        except Exception as e:
            print(f"初始化 JSON 時發生錯誤: {e}")

    def crop_regions(self, frame):
        """裁剪所有區域"""
        Regions_Mid = {
            'Player1_Mid': {'region': frame[490:535, 790:1050].copy(), 'description': '1'},
            'Player2_Mid': {'region': frame[360:540, 1065:1130].copy(), 'description': '2'},
            'Player3_Mid': {'region': frame[315:355, 870:1115].copy(), 'description': '3'},
            'Player4_Mid': {'region': frame[315:480, 805:860].copy(), 'description': '4'}
        }

        # 旋轉
        Regions_Mid['Player2_Mid']['region'] = cv2.rotate(Regions_Mid['Player2_Mid']['region'], cv2.ROTATE_90_CLOCKWISE)
        Regions_Mid['Player3_Mid']['region'] = cv2.rotate(Regions_Mid['Player3_Mid']['region'], cv2.ROTATE_180)
        Regions_Mid['Player4_Mid']['region'] = cv2.rotate(Regions_Mid['Player4_Mid']['region'], cv2.ROTATE_90_COUNTERCLOCKWISE)

        Regions_Tiles = {
            1: {
                'player1_hand': {'region': frame[900:1070, 200:1460].copy(), 'description': '1_hand'},
                'player1_discard': {'region': frame[520:770, 750:1150].copy(), 'description': '1_discard'},
                'player1_melds': {'region': frame[920:1080, 1580:1920].copy(), 'description': '1_melds'},
            },
            2: {
                'player2_discard': {'region': frame[270:550, 1130:1410].copy(), 'description': '2_discard'},
                'player2_melds': {'region': frame[0:210, 1480:1670].copy(), 'description': '2_melds'},
            },
            3: {
                'player3_discard': {'region': frame[110:310, 770:1140].copy(), 'description': '3_discard'},
                'player3_melds': {'region': frame[0:110, 320:650].copy(), 'description': '3_melds'},
            },
            4: {
                'player4_discard': {'region': frame[270:570, 520:780].copy(), 'description': '4_discard'},
                'player4_melds': {'region': frame[710:1060, 50:220].copy(), 'description': '4_melds'},
            }
        }

        Regions_Tiles_Dora = {
            'dora_indicator': {'region': frame[20:200, 0:330].copy(), 'description': 'dora'}
        }

        return Regions_Mid, Regions_Tiles, Regions_Tiles_Dora

    def detect_mid(self, frame):
        """偵測行動指示燈"""
        Regions_Mid, _, _ = self.crop_regions(frame)
        action_player = None

        for player_key, player_info in Regions_Mid.items():
            player_num = int(player_info['description'])  # 玩家編號
            results = self.mid_model(player_info['region'])

            for result in results:
                for box in result.boxes.data:
                    x1, y1, x2, y2, conf, cls = box
                    class_name = self.mid_model.model.names[int(cls)]
                    if class_name == 'step' and conf > 0.5:
                        action_player = player_num
                        break
                if action_player:
                    break

        return action_player

    def detect_tiles(self, frame, step):
        """偵測對應的 Regions_Tiles 並進行麻將牌辨識"""
        _, Regions_Tiles, _ = self.crop_regions(frame)

        if step not in Regions_Tiles:
            return {}

        regions = Regions_Tiles[step]
        detected_tiles = {}

        for key, value in regions.items():
            region = value['region']
            results = self.tiles_model(region)

            tile_list = []
            for result in results:
                for box in result.boxes.data:
                    x1, y1, x2, y2, conf, cls = box
                    class_name = self.tiles_model.model.names[int(cls)]
                    if conf > 0.5:
                        tile_list.append(class_name)

            detected_tiles[key] = tile_list

        return detected_tiles

    def detect_dora(self, frame):
        """偵測寶牌區域"""
        _, _, Regions_Tiles_Dora = self.crop_regions(frame)
        region = Regions_Tiles_Dora['dora_indicator']['region']
        results = self.tiles_model(region)

        dora_tiles = []
        for result in results:
            for box in result.boxes.data:
                x1, y1, x2, y2, conf, cls = box
                class_name = self.tiles_model.model.names[int(cls)]
                if conf > 0.5:
                    dora_tiles.append(class_name)

        return dora_tiles

    def update_json(self, step, detected_tiles, dora_tiles):
        """更新 JSON 檔案中的部分資料，確保不覆蓋整個檔案，只修改必要的部分"""
        try:
            # 讀取現有 JSON 檔案
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 更新當前行動玩家的資料
            player_key = str(step)

            if player_key == "1":
                data["players"][player_key]["hand"] = detected_tiles.get("player1_hand", [])
                new_discarded = detected_tiles.get("player1_discard", [])
                prev_discarded = data["players"][player_key]["discarded"]

                # **比較新舊棄牌數量，選擇較多的那個**
                data["players"][player_key]["discarded"] = new_discarded if len(new_discarded) >= len(prev_discarded) else prev_discarded
                data["players"][player_key]["melds"] = detected_tiles.get("player1_melds", [])
            
            elif player_key in ["2", "3", "4"]:
                new_discarded = detected_tiles.get(f"player{player_key}_discard", [])
                prev_discarded = data["players"][player_key]["discarded"]

                # **比較新舊棄牌數量，選擇較多的那個**
                data["players"][player_key]["discarded"] = new_discarded if len(new_discarded) >= len(prev_discarded) else prev_discarded
                data["players"][player_key]["melds"] = detected_tiles.get(f"player{player_key}_melds", [])

            # 更新寶牌區域
            data["dora"] = dora_tiles

            # 將更新後的資料寫回 JSON 檔案
            with open(self.json_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            print(f"JSON 檔案已更新：{self.json_file_path}")

        except Exception as e:
            print(f"更新 JSON 時發生錯誤: {e}")

def capture_screen(region=None):
    """使用 mss 庫捕獲屏幕畫面"""
    with mss.mss() as sct:
        monitor = region if region else sct.monitors[1]
        img = sct.grab(monitor)
        return cv2.cvtColor(np.array(img), cv2.COLOR_BGRA2BGR)

if __name__ == "__main__":
    detector = MahjongDetection(
        mid_model_path="D:/mahjongproject/Mid_Best.pt",
        tiles_model_path="D:/mahjongproject/Tiles_Best.pt",
        json_file_path="D:/mahjongproject/game_data.json"
    )
    
    last_detect_time = time.time()
    detection_interval = 5
    previous_turn = None  # 記錄上一位玩家

    while True:
        frame = capture_screen(region={"top": 0, "left": 0, "width": 1920, "height": 1080})
        current_time = time.time()

        if current_time - last_detect_time >= detection_interval:
            step = detector.detect_mid(frame)

            if step:
                # ✅ **如果行動指示燈變更，先偵測上一位玩家的牌**
                if previous_turn and previous_turn != step:
                    print(f"🔄 行動指示燈變更，補偵測上一位玩家 {previous_turn} 的牌...")
                    previous_tiles = detector.detect_tiles(frame, previous_turn)
                    for key, tiles in previous_tiles.items():
                        print(f"  {key}: {tiles}")

                    # ✅ 偵測寶牌
                    dora_tiles = detector.detect_dora(frame)
                    print(f"📌 寶牌區域偵測到的牌: {dora_tiles}")

                # ✅ **偵測當前玩家的牌**
                detected_tiles = detector.detect_tiles(frame, step)
                print(f"🎲 目前輪到玩家 {step}，偵測到的牌：")
                for key, tiles in detected_tiles.items():
                    print(f"  {key}: {tiles}")

                # ✅ **偵測寶牌**
                dora_tiles = detector.detect_dora(frame)
                print(f"📌 寶牌區域偵測到的牌: {dora_tiles}")

                # ✅ **使用 update_json() 來儲存數據**
                detector.update_json(step, detected_tiles, dora_tiles)

                # ✅ **記錄這次的行動玩家**
                previous_turn = step

            last_detect_time = current_time

        cv2.imshow("Screen Capture", frame)
        if cv2.waitKey(1) == ord("q"):
            print("❌ 程式結束...")
            break

    cv2.destroyAllWindows()