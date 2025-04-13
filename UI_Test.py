from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import json
import os

class TransparentOverlay(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.analysis_timer = QtCore.QTimer()
        self.image_labels = {}
        self.init_ui()
        self.init_timer()

    def init_ui(self):
        self.setGeometry(0, 0, 1920, 1080)
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)

        # 建立聽牌機率顯示的 Label
        self.tenpai_labels = {}
        self.image_labels = {}
        positions = {"p2": (1725, 460), "p3": (1340, 210), "p4": (40, 450)}  # 可調整位置

        for player, (x, y) in positions.items():
            label = QtWidgets.QLabel('', self)
            label.setStyleSheet("color: white; font-size: 20px;")
            label.move(x, y)
            self.tenpai_labels[player] = label

            for player, pos in positions.items():
                labels = []
                for i in range(3):
                    img_label = QtWidgets.QLabel(self)
                    img_label.setGeometry(pos[0] + i * 30, pos[1] + 30, 25, 40)
                    img_label.setStyleSheet("background: transparent;")
                    labels.append(img_label)
                self.image_labels[player] = labels
                
        self.recommend_label = QtWidgets.QLabel("推薦打牌：", self)
        self.recommend_label.setStyleSheet("color: white; font-size: 20px;")
        self.recommend_label.move(390, 630)
        self.recommend_label.hide()
    
        # 控制按鈕區塊
        self.button_start = QtWidgets.QPushButton("開始讀取", self)
        self.button_stop = QtWidgets.QPushButton("停止讀取", self)
        self.button_close = QtWidgets.QPushButton("關閉", self)

        # 按鈕樣式
        for btn in [self.button_start, self.button_stop, self.button_close]:
            btn.setStyleSheet("background-color: rgba(255,255,255,180); font-size: 14px;")

        self.button_start.move(1620, 10)
        self.button_stop.move(1720, 10)
        self.button_close.move(1820, 10)

        self.button_start.clicked.connect(self.start_timer)
        self.button_stop.clicked.connect(self.stop_timer)
        self.button_close.clicked.connect(QtWidgets.QApplication.quit)

    def init_timer(self):
        self.analysis_timer.setInterval(1000)  # 每秒
        self.analysis_timer.timeout.connect(self.load_analysis_data)

    def start_timer(self):
        self.analysis_timer.start()
        self.recommend_label.show()
    def stop_timer(self):
        self.analysis_timer.stop()

    def load_analysis_data(self):
        try:
            with open(r"D:/mahjongproject/analysis.json", "r", encoding="utf-8") as file:
                data = json.load(file)
                chances = data["opponent_tenpai_chance"]

                recommended_tile = "Wan_1"  # 這裡你之後可以改成從 analysis.json 取得
                self.recommend_label.setText(f"推薦打牌：{recommended_tile}")
                # ✅ 手動指定 mock 的可能聽牌
                self.mock_waits = {
                    "p2": ["Wan_1", "Wan_2"],
                    "p3": ["Tong_5_R","SanYuan_W"],
                    "p4": ["Feng_E"]
                }

                for player in ["p2", "p3", "p4"]:
                    chance = chances.get(player, 0)
                    self.tenpai_labels[player].setText(f"{player} 聽牌機率: {chance}%")

                    # 顯示 mock_waits 中的第一張牌
                    waits_list = self.mock_waits.get(player, [])[:3]
                    for i in range(3):
                        if i < len(waits_list):
                            tile_name = waits_list[i]
                            tile_path = os.path.join("D:/mahjongproject/MahJongPicture", f"{tile_name}.png")
                            if os.path.exists(tile_path):
                                pixmap = QtGui.QPixmap(tile_path).scaled(25, 40, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                                self.image_labels[player][i].setPixmap(pixmap)
                            else:
                                self.image_labels[player][i].clear()
                        else:
                            self.image_labels[player][i].clear()
        except Exception as e:
            print("讀取 analysis.json 失敗:", e)
            for player in ["p2", "p3", "p4"]:
                self.tenpai_labels[player].setText(f"{player} 資料讀取失敗")
                self.image_labels[player].clear()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    overlay = TransparentOverlay()
    overlay.show()
    sys.exit(app.exec_())

