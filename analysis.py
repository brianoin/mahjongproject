from collections import Counter

class MahjongAnalyzer:
    def __init__(self, model_path="best.pt"):
        self.model_path = model_path
        self.detector = None  # 先不載入 MahjongDetection

    def initialize_detector(self):
        """延遲載入 MahjongDetection，避免循環導入"""
        if self.detector is None:
            from YOLO import MahjongDetection  # ✅ 改從 `detection_core.py` 匯入
            self.detector = MahjongDetection(self.model_path)

    def analyze_real_time(self, frame):
        """確保 `detector` 已初始化後，再進行分析"""
        self.initialize_detector()
        detected_tiles = self.detector.detect_tiles(frame)
        cropped_regions = self.detector.crop_mahjong_tiles(frame)

        visible_tiles = {
            'self_hand': self.extract_tiles(cropped_regions, 'player_hand'),
            'discards': {
                'self': self.extract_tiles(cropped_regions, 'player_discard'),
                'p2': self.extract_tiles(cropped_regions, 'opponent_1_discard'),
                'p3': self.extract_tiles(cropped_regions, 'opponent_2_discard'),
                'p4': self.extract_tiles(cropped_regions, 'opponent_3_discard')
            },
        }

        return self.analyze_game_situation({'game_state': {'visible_tiles': visible_tiles}})

    def extract_tiles(self, cropped_regions, region_key):
        """從裁切區域中提取麻將牌"""
        if region_key in cropped_regions:
            detections = self.detector.detect_tiles(cropped_regions[region_key]['region'])
            return [det['class'] for det in detections]
        return []

    def analyze_game_situation(self, game_state):
        """分析遊戲局面，提供策略建議"""
        visible_tiles = game_state['game_state']['visible_tiles']
        discard_danger = self.calculate_discard_danger(visible_tiles)

        return {
            'discard_danger': discard_danger,
            'visible_tiles': visible_tiles
        }

    def calculate_discard_danger(self, visible_tiles):
        """計算當下打出去的牌的危險程度"""
        discard_danger = {}

        # 🔹 分析玩家打出的牌
        for player, tiles in visible_tiles['discards'].items():
            for tile in tiles:
                discard_danger[tile] = discard_danger.get(tile, 0) + 5

        return discard_danger
