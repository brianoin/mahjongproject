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
        self.image_tile_img = {}
        positions = {"p2": (1725, 460), "p3": (1340, 210), "p4": (40, 450)}  # 可調整位置

        for player, (x, y) in positions.items():
            self.tenpai_labels[player] = QtWidgets.QLabel(f"{player} 聽牌機率: 00%", self)
            self.tenpai_labels[player].setStyleSheet("color: white; font-size: 20px;")
            self.tenpai_labels[player].move(x, y)
            self.tenpai_labels[player].hide()
            
            self.image_tile_img[player] = []  # 先初始化為空 list
            
            for i in range(4):
                img_label = QtWidgets.QLabel(self)
                img_label.setGeometry(x + i * 30, y + 30, 25, 40)
                img_label.setStyleSheet("background: transparent;")
                self.image_tile_img[player].append(img_label)  # 加進 list

        # 顯示推薦打牌文字 Label
        self.recommend_label = QtWidgets.QLabel("推薦打牌：", self)
        self.recommend_label.setStyleSheet("color: white; font-size: 20px;")
        self.recommend_label.move(390, 620)
        self.recommend_label.hide()

        # 顯示推薦打牌圖片 Label
        self.recommend_tile_img = QtWidgets.QLabel(self)
        self.recommend_tile_img.setGeometry(390, 650, 25, 40)  # 可微調位置與大小
        self.recommend_tile_img.setStyleSheet("background: transparent;")
        self.recommend_tile_img.hide()

        # 控制按鈕區塊
        self.button_start = QtWidgets.QPushButton("開始讀取", self)
        self.button_stop = QtWidgets.QPushButton("停止讀取", self)
        self.button_close = QtWidgets.QPushButton("關閉", self)

        for btn in [self.button_start, self.button_stop, self.button_close]:
            btn.setStyleSheet("background-color: rgba(255,255,255,180); font-size: 14px;")

        self.button_start.move(1620, 10)
        self.button_stop.move(1720, 10)
        self.button_close.move(1820, 10)

        self.button_start.clicked.connect(self.start_timer)
        self.button_stop.clicked.connect(self.stop_timer)
        self.button_close.clicked.connect(QtWidgets.QApplication.quit)

    def init_timer(self):
        self.analysis_timer.setInterval(1000)
        self.analysis_timer.timeout.connect(self.load_analysis_data)

    def start_timer(self):
        self.analysis_timer.start()
        self.recommend_label.show()
        self.recommend_tile_img.show()
        for label in self.tenpai_labels.values():
            label.show() 

    def stop_timer(self):
        self.analysis_timer.stop()
        self.recommend_label.hide()
        self.recommend_tile_img.hide()
        for label in self.tenpai_labels.values():
                label.hide()
        for player_labels in self.image_tile_img.values():
            for img_label in player_labels:
                img_label.hide()
                
    def load_analysis_data(self):
        try:
            with open(r"D:/mahjongproject/analysis.json", "r", encoding="utf-8") as file:
                data = json.load(file)
                chances = {
                    pid: int(float(info.get("is_tenpai", "false") == "true") * 100)
                    for pid, info in data["tenpai_prediction"].items()
                }

                # 顯示推薦打牌文字與圖片
                recommended_tile = data.get("danger_estimation", {}).get("safe_discards", [""])[0]
                self.recommend_label.setText("推薦打牌：")

                tile_path = os.path.join("D:/mahjongproject/MahJongPicture", f"{recommended_tile}.png")
                if os.path.exists(tile_path):
                    pixmap = QtGui.QPixmap(tile_path).scaled(25, 40, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                    self.recommend_tile_img.setPixmap(pixmap)
                    self.recommend_tile_img.show()
                else:
                    self.recommend_tile_img.clear()

                # 顯示每位對手的聽牌機率與等牌圖片
                for player in ["p2", "p3", "p4"]:
                    chance = chances.get(player, 0)
                    self.tenpai_labels[player].setText(f"{player} 聽牌機率: {chance}%")
                    self.tenpai_labels[player].show()

                    danger_tiles = list(data["tenpai_prediction"][player].get("danger_tiles", {}).keys())[:4]

                    for i in range(4):
                        if i < len(danger_tiles):
                            tile_name = danger_tiles[i]
                            tile_path = os.path.join("D:/mahjongproject/MahJongPicture", f"{tile_name}.png")
                            if os.path.exists(tile_path):
                                pixmap = QtGui.QPixmap(tile_path).scaled(25, 40, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                                self.image_tile_img[player][i].setPixmap(pixmap)
                                self.image_tile_img[player][i].show()
                            else:
                                self.image_tile_img[player][i].clear()
                                self.image_tile_img[player][i].hide()
                        else:
                            self.image_tile_img[player][i].clear()
                            self.image_tile_img[player][i].hide()
        except Exception as e:
            print("讀取 analysis.json 失敗:", e)
            for player in ["p2", "p3", "p4"]:
                self.tenpai_labels[player].setText(f"{player} 資料讀取失敗")
                for label in self.image_tile_img[player]:
                    label.clear()
            self.recommend_tile_img.clear()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    overlay = TransparentOverlay()
    overlay.show()
    sys.exit(app.exec_())


