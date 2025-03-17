import cv2
from YOLO import MahjongDetection  # ✅ 只處理影像識別
from analysis import MahjongAnalyzer  # ✅ 負責分析危險度

TARGET_WIDTH, TARGET_HEIGHT = 1920, 1080



class MahjongDetector:
    def __init__(self, model_path="best.pt", source="gameplay.mp4"):  # 🔹 這裡可以設定遊戲影片路徑
        self.detector = MahjongDetection(model_path, source)
        self.analyzer = MahjongAnalyzer(model_path)  # 加入分析器

    def start_real_time_detection(self):
        cap = cv2.VideoCapture(self.detector.source)

        if not cap.isOpened():
            print("❌ 無法開啟影片/攝影機")
            return

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("❌ 影片播放完畢")
                break

            frame = cv2.resize(frame, (TARGET_WIDTH,TARGET_HEIGHT), interpolation=cv2.INTER_LINEAR)

            detections = self.detector.detect_tiles(frame)  # 🔹 YOLO 辨識牌
            cropped_regions = self.detector.crop_mahjong_tiles(frame)  # 🔹 切割不同區域
            analysis_result = self.analyzer.analyze_real_time(frame)  # 🔥 計算危險度
            discard_danger = analysis_result.get("discard_danger", {})

            # 🔥【關鍵】取得當下打出的牌（假設來自玩家手牌區域）
            current_discard = "5m"  # 這裡應該根據實際識別的牌來更新
            danger_level = discard_danger.get(current_discard, 0)

            # 設定顏色（綠=安全，黃=中等，紅=高危險）
            color = (0, 255, 0)  # 預設綠色
            if danger_level >= 5:
                color = (0, 165, 255)  # 黃色
            if danger_level >= 8:
                color = (0, 0, 255)  # 紅色

            # 🔥【畫面疊加資訊】
            cv2.putText(frame, f"打出: {current_discard} 危險度: {danger_level}",
                        (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

            # 🔹 標記偵測到的牌
            for det in detections:
                x1, y1, x2, y2 = det["bbox"]
                tile_name = det["class"]
                danger = discard_danger.get(tile_name, 0)

                # 顯示危險度標示
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"{tile_name} ({danger})", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            # 顯示畫面
            cv2.imshow("Mahjong Detection", frame)

            # 按 'q' 退出
            if cv2.waitKey(25) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    detector = MahjongDetector(model_path="best.pt", source="1-1.mp4")  # 🔥 這裡改成你的遊戲影片
    detector.start_real_time_detection()
