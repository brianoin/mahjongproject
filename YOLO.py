import cv2
import json
import numpy as np
from ultralytics import YOLO

class MahjongDetection:
    def __init__(self, Tiles_model_path="Tiles_Best.pt",Mid_model_path="Mid_Best.pt" ,source=0):
        """初始化模型"""
        self.Tiles = YOLO(Tiles_model_path)
        self.Mid = YOLO(Mid_model_path)
        self.source = source

    def detect_tiles(self, frame):
        """使用 YOLO 進行辨識"""
        results_Tiles = self.Tiles(frame)
        detections1 = self.process_results(results_Tiles)

        results_Mid = self.Mid(frame)
        detections2 = self.process_results(results_Mid)

        return{"Tiles_detections": detections1,"Mid_detections": detections2 }

    def process_results(self, results):
        """解析 YOLO 結果"""
        detections = []
        for result in results:
            for box in result.boxes.data:
                x1, y1, x2, y2, conf, cls = box
                class_name = self.Tiles.names[int(cls)] if hasattr(self.Tiles, "names") else "unknown"
                detections.append({
                    'class': class_name,
                    'confidence': float(conf),
                    'bbox': [int(x1), int(y1), int(x2), int(y2)]
                })
        return detections

    def crop_mahjong_tiles(self, frame):
        """切割畫面中特定區域"""
        Regions_Tiles = {
            'player_hand': {
                'region': frame[900:1070, 200:1460].copy(),
                'description': '玩家手牌'
            },
            'player_discard': {
                'region': frame[520:770, 750:1150].copy(),
                'description': '玩家捨牌'
            },
            'opponent_1_discard': {
                'region': frame[270:550, 1130:1410].copy(),
                'description': '對手1捨牌'
            },
            'opponent_2_discard': {
                'region': frame[110:310, 770:1140].copy(),
                'description': '對手2捨牌'
            },
            'opponent_3_discard': {
                'region': frame[270:570, 520:780].copy(),
                'description': '對手3捨牌'
            },
            'dora_indicator': {
                'region': frame[20:200, 0:330].copy(),
                'description': '寶牌指示牌'
            },
            'melds_player': {
                'region': frame[920:1080, 1580:1920].copy(),
                'description': '玩家吃碰槓'
            },
            'melds_opponent_1': {
                'region': frame[0:210, 1480:1670].copy(),
                'description': '對手1吃碰槓'
            },
            'melds_opponent_2': {
                'region': frame[0:110, 320:650].copy(),
                'description': '對手2吃碰槓'
            },
            'melds_opponent_3': {
                'region': frame[710:1060, 50:220].copy(),
                'description': '對手3吃碰槓'
            }
        }

        Regions_Mid={
            'Player1_Mid': {
                'region': frame[900:1070, 200:1460].copy(),
                'description': '玩家1面板'
            },
            'Player2_Mid': {
                'region': frame[900:1070, 200:1460].copy(),
                'description': '玩家2面板'
            },
            'Player3_Mid': {
                'region': frame[900:1070, 200:1460].copy(),
                'description': '玩家3面板'
            },
            'Player4_Mid': {
                'region': frame[900:1070, 200:1460].copy(),
                'description': '玩家4面板'
            }

        }
        
        return Regions_Tiles,Regions_Mid
    
    def save_detections_to_json(self, frame, json_path="mahjong_game.json"):
        """執行辨識並存成符合指定格式的 JSON 檔案"""
    results = {
        "dealer": 1,  # 預設為 1，你可以用影像分析確定
        "dora": [],  # 之後加入偵測結果
        "players": {
            "1": {"hand": [], "discarded": [], "melds": [], "riichi": False, "action_indicator": "thinking"},
            "2": {"discarded": [], "melds": [], "riichi": False, "action_indicator": "thinking"},
            "3": {"discarded": [], "melds": [], "riichi": False, "action_indicator": "thinking"},
            "4": {"discarded": [], "melds": [], "riichi": False, "action_indicator": "thinking"}
        }
    }

    # 1. 取得場上的各區域
    cropped_regions = self.crop_mahjong_tiles(frame)

    for region_name, cropped_frame in cropped_regions.items():
        detections = self.detect_tiles(cropped_frame)

        # 2. 根據區域更新 JSON
        if region_name == "player_hand":
            results["players"]["1"]["hand"] = [d["class"] for d in detections["Tiles_detections"]]
        elif region_name == "player_discard":
            results["players"]["1"]["discarded"] = [d["class"] for d in detections["Tiles_detections"]]
        elif region_name == "opponent_1_discard":
            results["players"]["2"]["discarded"] = [d["class"] for d in detections["Tiles_detections"]]
        elif region_name == "opponent_2_discard":
            results["players"]["3"]["discarded"] = [d["class"] for d in detections["Tiles_detections"]]
        elif region_name == "opponent_3_discard":
            results["players"]["4"]["discarded"] = [d["class"] for d in detections["Tiles_detections"]]
        elif region_name == "dora_indicator":
            results["dora"] = [d["class"] for d in detections["Tiles_detections"]]
        elif region_name == "melds_player":
            results["players"]["1"]["melds"] = self.extract_melds(detections["Tiles_detections"])
        elif region_name == "melds_opponent_1":
            results["players"]["2"]["melds"] = self.extract_melds(detections["Tiles_detections"])
        elif region_name == "melds_opponent_2":
            results["players"]["3"]["melds"] = self.extract_melds(detections["Tiles_detections"])
        elif region_name == "melds_opponent_3":
            results["players"]["4"]["melds"] = self.extract_melds(detections["Tiles_detections"])

    # 3. 存成 JSON
    with open(json_path, "w", encoding="utf-8") as json_file:
        json.dump(results, json_file, ensure_ascii=False, indent=4)

    print(f"✅ 已將辨識結果存入 {json_path}")
