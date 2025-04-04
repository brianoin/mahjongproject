import cv2
import json
import os
import numpy as np
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
        confidence_threshold = 0.5
        for result in results:
            for box in result.boxes.data:
                x1, y1, x2, y2, conf, cls = box
                if conf < confidence_threshold:  # 當信心值小於設定的閾值時，跳過該偵測
                    continue
                class_name = model.model.names[int(cls)] if hasattr(model, "model") else "unknown"
                detections.append({
                    'class': class_name,
                    'confidence': float(conf),
                    'bbox': [int(x1), int(y1), int(x2), int(y2)]
                })
        return detections

    def letterbox(self, image, target_size=(480, 540)):
        """將影像按比例縮放並加上 letterbox (黑邊填充)，以保持長寬比"""
        h, w = image.shape[:2]
        scale = min(target_size[0] / h, target_size[1] / w)  # 計算縮放比例
        new_h, new_w = int(h * scale), int(w * scale)

        # 重設影像大小
        resized_image = cv2.resize(image, (new_w, new_h))

        # 創建填充背景，填充色為黑色 (128 可更改為其他顏色)
        padded_image = np.full((target_size[0], target_size[1], 3), 128, dtype=np.uint8)

        # 把縮放後的影像放置到填充的區域中
        padded_image[(target_size[0] - new_h) // 2:(target_size[0] - new_h) // 2 + new_h,
                     (target_size[1] - new_w) // 2:(target_size[1] - new_w) // 2 + new_w] = resized_image

        return padded_image

    def crop_mahjong_tiles(self, frame):
        """裁剪影像，回傳 `Tiles` 和 `Mid` 需要偵測的區域，並應用 letterbox"""
        Regions_Tiles = {
            'player1_hand': frame[900:1070, 200:1460].copy(),
            'player1_discard': frame[520:770, 750:1150].copy(),
            'player1_melds': frame[920:1080, 1580:1920].copy(),
            
            'player2_discard': frame[270:550, 1130:1410].copy(),
            'player2_melds': frame[0:210, 1480:1670].copy(),
            
            'player3_discard': frame[110:310, 770:1140].copy(),
            'player3_melds': frame[0:110, 320:650].copy(),
            
            'player4_discard': frame[270:570, 520:780].copy(),
            'player4_melds': frame[710:1060, 50:220].copy(),
            
            'dora_indicator': frame[20:200, 0:330].copy(),
            
            'Player1_Mid': frame[490:535, 790:1050].copy(),
            'Player2_Mid': frame[360:540, 1065:1130].copy(),
            'Player3_Mid': frame[315:355, 870:1115].copy(),
            'Player4_Mid': frame[315:480, 805:860].copy()
        }

        Regions_Mid = {
        }

        # 在裁剪區域上加入 letterbox
        for key, region in Regions_Tiles.items():
            Regions_Tiles[key] = self.letterbox(region)

        for key, region in Regions_Mid.items():
            Regions_Mid[key] = self.letterbox(region)
            
        Regions_Tiles['Player1_Mid'] = self.letterbox(Regions_Tiles['Player1_Mid'])
        
        Regions_Tiles['Player2_Mid'] = cv2.rotate(Regions_Tiles['Player2_Mid'], cv2.ROTATE_90_CLOCKWISE)
        Regions_Tiles['Player2_Mid'] = self.letterbox(Regions_Tiles['Player2_Mid'])
        
        Regions_Tiles['Player3_Mid'] = cv2.rotate(Regions_Tiles['Player3_Mid'], cv2.ROTATE_180)
        Regions_Tiles['Player3_Mid'] = self.letterbox(Regions_Tiles['Player3_Mid'])
        
        Regions_Tiles['Player4_Mid'] = cv2.rotate(Regions_Tiles['Player4_Mid'], cv2.ROTATE_90_COUNTERCLOCKWISE)
        Regions_Tiles['Player4_Mid'] = self.letterbox(Regions_Tiles['Player4_Mid'])

        return Regions_Tiles, Regions_Mid

    def save_detections_to_json(self, frame, json_path="D:/mahjongproject/mahjong_game.json", output_image_dir="D:/mahjongproject/cropped_images/"):
        """執行辨識並存成符合指定格式的 JSON 檔案"""
        results = {
            "dealer": 1,  # 預設為 1，可用 Mid 辨識確定
            "dora": [],
            "players": {
                "1": {"hand": [], "discarded": [], "melds": [], "riichi": False, "action_indicator": "thinking"},
                "2": {"discarded": [], "melds": [], "riichi": False, "action_indicator": "thinking"},
                "3": {"discarded": [], "melds": [], "riichi": False, "action_indicator": "thinking"},
                "4": {"discarded": [], "melds": [], "riichi": False, "action_indicator": "thinking"}
            },
            "Mid":{
                "1":[],
                "2":[],
                "3":[],
                "4":[],
            }
        }
        
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        os.makedirs(output_image_dir, exist_ok=True)  # 確保影像儲存的資料夾存在

        # 取得 `Tiles` 和 `Mid` 的區域
        Regions_Tiles, Regions_Mid = self.crop_mahjong_tiles(frame)

        # 1️⃣ 處理 `Tiles` 模型的偵測結果
        for region_name, cropped_frame in Regions_Tiles.items():
            detections = self.detect_tiles(cropped_frame, self.Tiles)

            # 儲存裁切後的影像
            cropped_image_path = os.path.join(output_image_dir, f"{region_name}_cropped.jpg")
            cv2.imwrite(cropped_image_path, cropped_frame)

            if region_name == "player1_hand":
                results["players"]["1"]["hand"] = [d["class"] for d in detections]
                
            elif region_name == "player1_discard":
                results["players"]["1"]["discarded"] = [d["class"] for d in detections]
                
            elif region_name == "player1_melds":
                results["players"]["1"]["melds"] = [d["class"] for d in detections]
                
            elif region_name == "player2_discard":
                results["players"]["2"]["discarded"] = [d["class"] for d in detections]
                
            elif region_name == "player2_melds":
                results["players"]["2"]["melds"] = [d["class"] for d in detections]
                
            elif region_name == "player3_discard":
                results["players"]["3"]["discarded"] = [d["class"] for d in detections]
                
            elif region_name == "player4_discard":
                results["players"]["4"]["discarded"] = [d["class"] for d in detections]
                
            elif region_name == "dora_indicator":
                results["dora"] = [d["class"] for d in detections]
                
            elif region_name == "Player1_Mid":
                results["Mid"]["1"] = [d["class"] for d in detections]
                
            elif region_name == "Player2_Mid":
                results["Mid"]["2"] = [d["class"] for d in detections]
                
            elif region_name == "Player3_Mid":
                results["Mid"]["3"] = [d["class"] for d in detections]
                
            elif region_name == "Player4_Mid":
                results["Mid"]["4"] = [d["class"] for d in detections]
        # 2️⃣ 存成 JSON
        with open(json_path, "w", encoding="utf-8") as json_file:
            json.dump(results, json_file, ensure_ascii=False, indent=4)

        print(f"✅ 已將辨識結果存入 {json_path}")
        print(f"✅ 已儲存裁切後的影像到 {output_image_dir}")

# 測試
if __name__ == "__main__":
    frame = cv2.imread("D:/mahjongproject/test2.jpg")  # 載入測試影像
    detector = MahjongDetection()
    detector.save_detections_to_json(frame)
