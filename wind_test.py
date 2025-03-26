import cv2
import mss
import numpy as np
from ultralytics import YOLO
import time

class MahjongDetection:
    def __init__(self, mid_model_path):
        """初始化 YOLO 模型"""
        self.mid_model = YOLO(mid_model_path)
        self.players_winds = {}

    def detect_mid(self, frame):
        """使用 mid_model 检测玩家中间牌"""
        results = self.mid_model(frame)
        detections = []
        banker_detected = None

        for result in results:
            for box in result.boxes.data:
                x1, y1, x2, y2, conf, cls = box
                class_name = self.mid_model.model.names[int(cls)]
                if conf > 0.5:  # 设定信心值阈值
                    detections.append({
                        'class': class_name,
                        'confidence': conf.item(),
                        'bbox': [int(x1), int(y1), int(x2), int(y2)]
                    })

                    if class_name == 'Banker':  # 假设 'Banker' 是庄家的标记
                        banker_detected = True
        return detections, banker_detected

    def crop_and_rotate_regions(self, frame):
        """裁剪画面并旋转不同玩家的中间牌区域"""
        # 定义每个玩家的中间牌区域
        Regions_Mid = {
            'Player1_Mid': {'region': frame[490:535, 790:1050].copy(), 'description': '1'},
            'Player2_Mid': {'region': frame[360:540, 1065:1130].copy(), 'description': '2'},
            'Player3_Mid': {'region': frame[315:355, 870:1115].copy(), 'description': '3'},
            'Player4_Mid': {'region': frame[315:480, 805:860].copy(), 'description': '4'}
        }

        # 根据需要旋转区域
        Regions_Mid['Player2_Mid']['region'] = cv2.rotate(Regions_Mid['Player2_Mid']['region'], cv2.ROTATE_90_CLOCKWISE)
        Regions_Mid['Player3_Mid']['region'] = cv2.rotate(Regions_Mid['Player3_Mid']['region'], cv2.ROTATE_180)
        Regions_Mid['Player4_Mid']['region'] = cv2.rotate(Regions_Mid['Player4_Mid']['region'], cv2.ROTATE_90_COUNTERCLOCKWISE)

        return Regions_Mid

    def determine_winds(self, dealer_description):
        """根据庄家描述确定所有玩家的风位"""
        wind_order = ["東", "南", "西", "北"]

        # 将庄家的 description 转换为整数
        dealer_index = int(dealer_description) - 1  # '1' -> 0, '2' -> 1, '3' -> 2, '4' -> 3

        # 计算所有玩家风位
        self.players_winds = {str(i + 1): wind_order[(i - dealer_index) % 4] for i in range(4)}

    def process_frame(self, frame):
        """处理每一帧图像并进行中间牌的检测"""
        Regions_Mid = self.crop_and_rotate_regions(frame)

        mid_results = {}
        banker_detected = None

        for player_key, player_info in Regions_Mid.items():
            player_description = player_info['description']
            detections, banker = self.detect_mid(player_info['region'])
            mid_results[player_description] = detections

            if banker:
                banker_detected = player_description  # 记录庄家编号 '1', '2', '3', '4'

        return mid_results, banker_detected

def capture_screen(region=None):
    """使用 mss 库捕获屏幕图像"""
    with mss.mss() as sct:
        monitor = region if region else sct.monitors[1]  # 默认捕获主屏幕
        img = sct.grab(monitor)
        return cv2.cvtColor(np.array(img), cv2.COLOR_BGRA2BGR)  # 转为 OpenCV 格式

if __name__ == "__main__":
    # 创建 MahjongDetection 实例，传入 mid_model 路径
    detector = MahjongDetection(mid_model_path="D:/mahjongproject/Mid_Best.pt")

    last_detect_time = time.time()  # 记录最后检测的时间
    detection_interval = 5  # 每 5 秒检测一次
    dealer = None  # 暂无庄家

    while True:
        # 捕获屏幕画面
        frame = capture_screen(region={"top": 0, "left": 0, "width": 1920, "height": 1080})

        # 当前时间
        current_time = time.time()

        # 每 5 秒检测一次
        if current_time - last_detect_time >= detection_interval:
            mid_results, banker_detected = detector.process_frame(frame)

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

            # 更新最后检测时间
            last_detect_time = current_time

        # 显示捕获的画面
        cv2.imshow("Screen Capture", frame)

        # 按 'q' 键退出程序
        key = cv2.waitKey(1)
        if key == ord("q"):
            print("程序结束...")
            break

    cv2.destroyAllWindows()
