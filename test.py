import cv2
import json
import numpy as np
import os
from ultralytics import YOLO

class MahjongDetection:
    def __init__(self, Tiles_model_path="D:/mahjongproject/Tiles_Best.pt", Mid_model_path="D:/mahjongproject/Mid_Best.pt"):
        """初始化兩個 YOLO 模型"""
        self.Tiles = YOLO(Tiles_model_path)
        self.Mid = YOLO(Mid_model_path)

    def detect_tiles(self, frame, model):
        """使用指定的 YOLO 模型進行偵測"""
        results = model(frame)
        detections = []
        for result in results:
            for box in result.boxes.data:
                x1, y1, x2, y2, conf, cls = box
                class_name = model.model.names[int(cls)] if hasattr(model, "model") else "unknown"
                detections.append({
                    'class': class_name,
                    'confidence': float(conf),
                    'bbox': [int(x1), int(y1), int(x2), int(y2)]
                })
        return detections

    def crop_mahjong_tiles(self, frame):
        """裁剪影像，回傳 `Tiles` 和 `Mid` 需要偵測的區域"""
        Regions_Tiles = {
            'player_hand': frame[900:1070, 200:1460].copy(),
            'player_discard': frame[520:770, 750:1150].copy(),
            'opponent_1_discard': frame[270:550, 1130:1410].copy(),
            'opponent_2_discard': frame[110:310, 770:1140].copy(),
            'opponent_3_discard': frame[270:570, 520:780].copy(),
            'dora_indicator': frame[20:200, 0:330].copy(),
            'melds_player': frame[920:1080, 1580:1920].copy(),
            'melds_opponent_1': frame[0:210, 1480:1670].copy(),
            'melds_opponent_2': frame[0:110, 320:650].copy(),
            'melds_opponent_3': frame[710:1060, 50:220].copy(),
        }

        Regions_Mid = {
            'Player1_Mid': frame[900:1070, 200:1460].copy(),
            'Player2_Mid': frame[250:500, 1500:1800].copy(),
            'Player3_Mid': frame[100:300, 500:900].copy(),
            'Player4_Mid': frame[700:1000, 50:300].copy(),
        }

        return Regions_Tiles, Regions_Mid

    def extract_melds(self, detections):
        """將吃碰槓的牌轉換成陣列格式"""
        melds = []
        for d in detections:
            melds.append(d["class"])
        return [melds[i:i+3] for i in range(0, len(melds), 3)]  # 假設吃碰槓都是 3 張一組

    def save_detections_to_json(self, frame, json_path="D:/mahjongproject/mahjong_game.json"):
        """執行辨識並存成符合指定格式的 JSON 檔案"""
        results = {
            "dealer": 1,  # 預設為 1，可用 Mid 辨識確定
            "dora": [],
            "players": {
                "1": {"hand": [], "discarded": [], "melds": [], "riichi": False, "action_indicator": "thinking"},
                "2": {"discarded": [], "melds": [], "riichi": False, "action_indicator": "thinking"},
                "3": {"discarded": [], "melds": [], "riichi": False, "action_indicator": "thinking"},
                "4": {"discarded": [], "melds": [], "riichi": False, "action_indicator": "thinking"}
            }
        }
        
        os.makedirs(os.path.dirname(json_path), exist_ok=True)

        # 取得 `Tiles` 和 `Mid` 的區域
        Regions_Tiles, Regions_Mid = self.crop_mahjong_tiles(frame)

        # 1️⃣ 處理 `Tiles` 模型的偵測結果
        for region_name, cropped_frame in Regions_Tiles.items():
            detections = self.detect_tiles(cropped_frame, self.Tiles)

            if region_name == "player_hand":
                results["players"]["1"]["hand"] = [d["class"] for d in detections]
            elif region_name == "player_discard":
                results["players"]["1"]["discarded"] = [d["class"] for d in detections]
            elif region_name == "opponent_1_discard":
                results["players"]["2"]["discarded"] = [d["class"] for d in detections]
            elif region_name == "opponent_2_discard":
                results["players"]["3"]["discarded"] = [d["class"] for d in detections]
            elif region_name == "opponent_3_discard":
                results["players"]["4"]["discarded"] = [d["class"] for d in detections]
            elif region_name == "dora_indicator":
                results["dora"] = [d["class"] for d in detections]
            # elif region_name.startswith("melds_"):
            #     player_key = region_name.split("_")[-1]
            #     results["players"][player_key]["melds"] = self.extract_melds(detections)

        # 2️⃣ 處理 `Mid` 模型的偵測結果 (例如莊家判定)
        # for region_name, cropped_frame in Regions_Mid.items():
        #     detections = self.detect_tiles(cropped_frame, self.Mid)
        #     if region_name.startswith("Player") and detections:
        #         player_num = region_name[-1]
        #         results["dealer"] = int(player_num)  # 偵測莊家

        # 3️⃣ 存成 JSON
        with open(json_path, "w", encoding="utf-8") as json_file:
            json.dump(results, json_file, ensure_ascii=False, indent=4)

        print(f"✅ 已將辨識結果存入 {json_path}")

# 測試
if __name__ == "__main__":
    frame = cv2.imread("D:/mahjongproject/mahjong_test.jpg")  # 載入測試影像
    detector = MahjongDetection()
    detector.save_detections_to_json(frame)
