import cv2
import mss
import numpy as np
from ultralytics import YOLO
import time
import json  # 匯入 json 模組

class MahjongDetection:
    def __init__(self, mid_model_path, tile_model_path):
        """初始化 YOLO 模型"""
        self.mid_model = YOLO(mid_model_path)
        self.tile_model = YOLO(tile_model_path)  # 用於辨識手牌、捨牌、吃碰槓的模型
        self.players_winds = {}
        self.dealer = None  # 儲存當前庄家

    def detect_mid(self, frame):
        """使用 mid_model 检测玩家中间牌"""
        results = self.mid_model(frame)
        detections = []
        banker_detected = None

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
        return detections, banker_detected

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

        Regions_Tiles = {
            'player1_hand': {'region': frame[900:1070, 200:1460].copy(), 'description': '1_hand'},
            'player1_discard': {'region': frame[520:770, 750:1150].copy(), 'description': '1_discard'},
            'player1_melds': {'region': frame[920:1080, 1580:1920].copy(), 'description': '1_melds'},

            'player2_discard': {'region': frame[270:550, 1130:1410].copy(), 'description': '2_discard'},
            'player2_melds': {'region': frame[0:210, 1480:1670].copy(), 'description': '2_melds'},

            'player3_discard': {'region': frame[110:310, 770:1140].copy(), 'description': '3_discard'},
            'player3_melds': {'region': frame[0:110, 320:650].copy(), 'description': '3_melds'},

            'player4_discard': {'region': frame[270:570, 520:780].copy(), 'description': '4_discard'},
            'player4_melds': {'region': frame[710:1060, 50:220].copy(), 'description': '4_melds'},

            'dora_indicator': {'region': frame[20:200, 0:330].copy(), 'description': 'dora'}
        }

        return Regions_Mid, Regions_Tiles
    
    def determine_winds(self, dealer_description):
        """根据庄家描述确定所有玩家的风位"""
        wind_order = ["東", "南", "西", "北"]

        # 将庄家的 description 转换为整数
        dealer_index = int(dealer_description) - 1  # '1' -> 0, '2' -> 1, '3' -> 2, '4' -> 3

        # 计算所有玩家风位
        self.players_winds = {str(i + 1): wind_order[(i - dealer_index) % 4] for i in range(4)}

    def save_to_json(self, Tiles_Results, riichi_states):
        """將結果儲存為 JSON 文件"""
        results = {
            "Banker": self.dealer, 
            "dora": Tiles_Results["dora_indicator"],
            "players": {
                "1": {"hand": Tiles_Results["player1_hand"], "discarded": Tiles_Results["player1_discard"], "melds": Tiles_Results["player1_melds"], "riichi": riichi_states["1"], "wind": self.players_winds.get("1", "")},
                "2": {"discarded": Tiles_Results["player2_discard"], "melds": Tiles_Results["player2_melds"], "riichi": riichi_states["2"], "wind": self.players_winds.get("2", "")},
                "3": {"discarded": Tiles_Results["player3_discard"], "melds": Tiles_Results["player3_melds"], "riichi": riichi_states["3"], "wind": self.players_winds.get("3", "")},
                "4": {"discarded": Tiles_Results["player4_discard"], "melds": Tiles_Results["player4_melds"], "riichi": riichi_states["4"], "wind": self.players_winds.get("4", "")}
            }
        }

        with open("mahjong_data.json", "w", encoding="utf-8") as json_file:
            json.dump(results, json_file, ensure_ascii=False, indent=4)

    def process_frame(self, frame, riichi_states):
        """处理每一帧图像并进行中间牌的检测"""
        Regions_Mid = self.crop_regions(frame)

        mid_results = {}
        banker_detected = None
        step_player_detected = None  # 新增行動玩家變數

        for player_key, player_info in Regions_Mid.items():
            player_description = player_info['description']
            detections, banker = self.detect_mid(player_info['region'])
            mid_results[player_description] = detections

            if banker:
                banker_detected = player_description  # 記錄庄家 '1', '2', '3', '4'

            # **新增：檢測當前行動的玩家**
            for detection in detections:
                if detection['class'] == 'Step':  # 假設行動指示燈標籤為 'Step'
                    step_player_detected = player_description

        if banker_detected:
            self.dealer = banker_detected

        # 偵測手牌、捨牌、吃碰槓
        Tiles_Results = {}
        for player_key, player_info in Regions_Mid.items():
            player_description = player_info['description']
            if player_description != 'dora':
                Tiles_Results[player_key] = self.detect_tiles(player_info['region'])

        # 儲存結果到 JSON
        self.save_to_json(Tiles_Results, riichi_states)

        return mid_results, banker_detected, Regions_Mid, step_player_detected


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
    riichi_states = {"1": False, "2": False, "3": False, "4": False}  # 初始時，所有玩家都沒立直

    while True:
        frame = capture_screen(region={"top": 0, "left": 0, "width": 1920, "height": 1080})

        current_time = time.time()
        if current_time - last_detect_time >= detection_interval:
            mid_results, banker_detected, Regions_Tiles, step_player_detected = detector.process_frame(frame, riichi_states)

            # 如果检测到新的庄家，更新风位
            if banker_detected and banker_detected != dealer:
                dealer_num = int(banker_detected)  # 直接转换字符串 '1', '2', '3', '4' 为整数
                dealer = banker_detected
                detector.determine_winds(dealer_num)

            # 打印检测结果
            print(f"庄家: {dealer}, 玩家风位:")
            for player_num, wind in detector.players_winds.items():
                print(f"  玩家{player_num}: {wind}")

            # 打印检测到的中间牌
            print("检测到的中间牌区域：")
            for player_key, detections in mid_results.items():
                print(f"{player_key}:")
                for detection in detections:
                    print(f"  类别: {detection['class']}, 信心值: {detection['confidence']:.2f}")

            # **更新當前行動的玩家**
            if step_player_detected:
                step_player = step_player_detected  # 更新 step_player

            last_detect_time = current_time

        cv2.imshow("Screen Capture", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("程序結束...")
            break

    cv2.destroyAllWindows()
