import cv2
import mss
import numpy as np
from ultralytics import YOLO
import os
import time
import json

class MahjongDetection:
    def __init__(self, mid_model_path, tile_model_path):
        """初始化 YOLO 模型"""
        self.mid_model = YOLO(mid_model_path)
        self.tile_model = YOLO(tile_model_path)  # 用於辨識手牌、捨牌、吃碰槓的模型
        self.players_winds = {}

    def detect_mid(self, frame):
        """使用 mid_model 檢測玩家中間牌"""
        results = self.mid_model(frame)
        detections = []
        banker_detected = None
        step_player_detected = None  # 新增行動指示燈偵測

        for result in results:
            for box in result.boxes.data:
                x1, y1, x2, y2, conf, cls = box
                class_name = self.mid_model.model.names[int(cls)]
                if conf > 0.5:  # 設定信心值閾值
                    detections.append({
                        'class': class_name,
                        'confidence': conf.item(),
                        'bbox': [int(x1), int(y1), int(x2), int(y2)]
                    })

                    if class_name == 'Banker':  # 假設 'Banker' 是莊家的標記
                        banker_detected = True
                    
                    if class_name == 'Step':  # 假設 'Step' 代表當前行動的玩家
                        step_player_detected = True

        return detections, banker_detected, step_player_detected

    def detect_tiles(self, frame):
        """使用 tile_model 辨識手牌、捨牌、吃碰槓"""
        results = self.tile_model(frame)
        detections = []
        
        for result in results:
            for box in result.boxes.data:
                x1, y1, x2, y2, conf, cls = box
                class_name = self.tile_model.model.names[int(cls)]
                if conf > 0.5:
                    detections.append({
                        'class': class_name,
                        'confidence': conf.item(),
                        'bbox': [int(x1), int(y1), int(x2), int(y2)]
                    })
        return detections

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

        Regions_Tiles1 = {
            'player1_hand': {'region': frame[900:1070, 200:1460].copy(), 'description': '1_hand'},
            'player1_discard': {'region': frame[520:770, 750:1150].copy(), 'description': '1_discard'},
            'player1_melds': {'region': frame[920:1080, 1580:1920].copy(), 'description': '1_melds'},
        }
        Regions_Tiles2 = {
            'player2_discard': {'region': frame[270:550, 1130:1410].copy(), 'description': '2_discard'},
            'player2_melds': {'region': frame[0:210, 1480:1670].copy(), 'description': '2_melds'},

        }
        Regions_Tiles3 = {
            'player3_discard': {'region': frame[110:310, 770:1140].copy(), 'description': '3_discard'},
            'player3_melds': {'region': frame[0:110, 320:650].copy(), 'description': '3_melds'},

        }
        Regions_Tiles4 = {
            'player4_discard': {'region': frame[270:570, 520:780].copy(), 'description': '4_discard'},
            'player4_melds': {'region': frame[710:1060, 50:220].copy(), 'description': '4_melds'},
        
        }
        
        Regions_Tiles_Dora = {
            'dora_indicator': {'region': frame[20:200, 0:330].copy(), 'description': 'dora'}
        }

        return Regions_Mid, Regions_Tiles1, Regions_Tiles2, Regions_Tiles3, Regions_Tiles4, Regions_Tiles_Dora
    
    def determine_winds(self, dealer_description):
        """根據庄家描述確定所有玩家的風位"""
        wind_order = ["東", "南", "西", "北"]

        dealer_index = int(dealer_description) - 1  
        self.players_winds = {str(i + 1): wind_order[(i - dealer_index) % 4] for i in range(4)}

    def save_to_json(self, file_path, new_data, step_player):
        """檢查 JSON 檔案是否存在，存在則更新，不存在則創建"""

        # 確保目錄存在
        folder = os.path.dirname(file_path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)

        # 如果 JSON 檔案存在，則讀取舊資料
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    existing_data = {}  # 如果 JSON 檔案損壞，則重置為空字典
        else:
            existing_data = {}  # 如果檔案不存在，則創建一個新的字典

        # **僅更新當前行動玩家的資訊**
        if step_player in new_data["players"]:
            player_data = new_data["players"][step_player]
            
            # 只保留 **辨識到的牌名**
            for key in ["hand", "discard", "melds"]:
                player_data[key] = [tile["class"] for tile in player_data[key]]  

            # 更新對應玩家的資料
            existing_data["players"] = existing_data.get("players", {})
            existing_data["players"][step_player] = player_data

        # 更新 **莊家、寶牌資訊**
        existing_data["dealer"] = new_data["dealer"]
        existing_data["dora"] = new_data["dora"]

        # 寫入更新後的 JSON 檔案
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)

        print(f"✅ JSON 資料已更新（行動玩家 {step_player}）: {file_path}")

def capture_screen(region=None):
    """使用 mss 擷取畫面"""
    with mss.mss() as sct:
        monitor = region if region else sct.monitors[1]
        img = sct.grab(monitor)
        return cv2.cvtColor(np.array(img), cv2.COLOR_BGRA2BGR)

if __name__ == "__main__":
    detector = MahjongDetection(mid_model_path="D:/mahjongproject/Mid_Best.pt",
                                tile_model_path="D:/mahjongproject/Tiles_Best.pt")

    last_detect_time = time.time()
    detection_interval = 5
    dealer = None
    step_player = None  

    while True:
        frame = capture_screen(region={"top": 0, "left": 0, "width": 1920, "height": 1080})
        Regions_Mid, Regions_Tiles1, Regions_Tiles2, Regions_Tiles3, Regions_Tiles4, Regions_Tiles_Dora = detector.crop_regions(frame)  

        current_time = time.time()
        if current_time - last_detect_time >= detection_interval:
            mid_results = {}
            banker_detected = None
            step_player_detected = None

            for player_key, player_info in Regions_Mid.items():
                player_description = player_info['description']
                detections, banker, step = detector.detect_mid(player_info['region'])
                mid_results[player_description] = detections

                if banker:
                    banker_detected = player_description  

                if step:
                    step_player_detected = player_description  

            if banker_detected and banker_detected != dealer:
                dealer = banker_detected
                detector.determine_winds(dealer)

            if step_player_detected:
                step_player = step_player_detected  

            game_data = {
                "dealer": dealer,
                "dora": None,  # 假設寶牌的偵測邏輯可以加在這裡
                "players": {}
            }

            if step_player:
                player_data = {
                    "hand": [],
                    "discard": [],
                    "melds": [],
                    "riichi": False,  # 如果有立直偵測，將其設為 True
                    "wind": detector.players_winds.get(step_player, "未知")
                }

                # 偵測每個玩家的手牌、捨牌與副露
                if step_player == "1":
                    target_regions = Regions_Tiles1
                elif step_player == "2":
                    target_regions = Regions_Tiles2
                elif step_player == "3":
                    target_regions = Regions_Tiles3
                elif step_player == "4":
                    target_regions = Regions_Tiles4
                else:
                    target_regions = {}

                # 偵測手牌、捨牌、吃碰槓
                for region_key, region_info in target_regions.items():
                    region = region_info['region']
                    detections = detector.detect_tiles(region)
                    if 'hand' in region_key:
                        player_data["hand"] = detections
                    elif 'discard' in region_key:
                        player_data["discard"] = detections
                    elif 'melds' in region_key:
                        player_data["melds"] = detections

                game_data["players"][step_player] = player_data

            # **即時更新 JSON 檔案**
            json_path ="D:/mahjongproject/MJStep.json"
            detector.save_to_json(json_path, game_data, step_player)

            last_detect_time = current_time

        cv2.imshow("Screen Capture", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("程序結束...")
            break

cv2.destroyAllWindows()



