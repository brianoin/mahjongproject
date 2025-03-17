import cv2
import numpy as np
from ultralytics import YOLO

class MahjongDetection:
    def __init__(self, model_path="best.pt", source=0):
        """初始化模型"""
        self.model = YOLO(model_path)
        self.source = source

    def detect_tiles(self, frame):
        """使用 YOLO 進行辨識"""
        results = self.model(frame)
        detections = []

        for result in results:
            for box in result.boxes.data:
                x1, y1, x2, y2, conf, cls = box
                detections.append({
                    'class': result.names[int(cls)],
                    'confidence': float(conf),
                    'bbox': [int(x1), int(y1), int(x2), int(y2)]
                })

        return detections

    def crop_mahjong_tiles(self, frame):
        """切割畫面中特定區域"""
        regions = {
            'player_hand': {
                'region': frame[900:1070, 200:1460].copy(),
                'description': '玩家手牌'
            },
            'player_discard': {
                'region': frame[520:770, 750:1150].copy(),
                'description': '玩家捨牌'
            },
            'opponent_1_hand': {
                'region': frame[230:820, 1480:1760].copy(),
                'description': '對手1手牌'
            },
            'opponent_1_discard': {
                'region': frame[270:550, 1130:1410].copy(),
                'description': '對手1捨牌'
            },
            'opponent_2_hand': {
                'region': frame[40:120, 800:1350].copy(),
                'description': '對手2手牌'
            },
            'opponent_2_discard': {
                'region': frame[110:310, 770:1140].copy(),
                'description': '對手2捨牌'
            },
            'opponent_3_hand': {
                'region': frame[100:600, 230:450].copy(),
                'description': '對手3手牌'
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
        
        return regions
