import cv2
import os
import time
import mss
import numpy as np

class MahjongCropper:
    def __init__(self):
        # 設定存放裁切圖片的資料夾
        self.output_folder = "D:/mahjongproject/cropped_images"
        os.makedirs(self.output_folder, exist_ok=True)

    def compute_dst_size(self, src_points):
        """根據平行四邊形的角點計算目標大小 (寬, 高)"""
        p1, p2, p3, p4 = np.array(src_points)
        
        # 計算上邊和下邊的寬度
        width_top = np.linalg.norm(p2 - p1)   # 上邊長度
        width_bottom = np.linalg.norm(p4 - p3)  # 下邊長度
        width = int(max(width_top, width_bottom))  # 取較大值，避免扭曲

        # 計算左邊和右邊的高度
        height_left = np.linalg.norm(p3 - p1)   # 左邊長度
        height_right = np.linalg.norm(p4 - p2)  # 右邊長度
        height = int(max(height_left, height_right))  # 取較大值，避免扭曲

        return (width, height)

    def perspective_crop(self, img, src_points):
        """使用透視變換擷取平行四邊形區域，並自動轉換為固定大小的矩形"""
        dst_size = self.compute_dst_size(src_points)  # 計算目標大小
        
        dst_points = np.float32([
            [0, 0], 
            [dst_size[0], 0], 
            [0, dst_size[1]], 
            [dst_size[0], dst_size[1]]
        ])
        
        # 計算透視變換矩陣
        matrix = cv2.getPerspectiveTransform(np.float32(src_points), dst_points)
        
        # 透視變換
        warped = cv2.warpPerspective(img, matrix, dst_size)
        #warped = cv2.rotate(warped, cv2.ROTATE_90_CLOCKWISE)
        return warped

    def crop_regions(self, frame):
        """裁剪所有區域"""
        a1=5
        a2=9
        a3=3
        a4=9
        Regions_Tiles = {
            1: {
                'player1_melds': {
                    #前兩個不動。最一開始四個為一組 x越來越小 y不變 1810 910 1475 1485 1260 
                    'src_points': [(1810, 910), (1840, 1045), (1475-a1*75, 910), (1485-a1*75, 1045)],
                    'description': '1_melds'
                }
            },
            2: {
                'player2_melds': {
                    #前兩個不動。最一開始四個為一組 x越來越大 y越來越大
                    'src_points': [(1465, 35), (1570, 35), (1510+a2*13, 180+a2*40), (1615+a2*13, 180+a2*40)],
                    'description': '2_melds'
                }
            },
            3: {
                'player3_melds': {
                    #前兩個不動。最一開始四個為一組 x越來越大 y不變 755 760 140/3 47
                    'src_points': [(395, 30), (375, 110), (620+a3*50, 30), (615+a3*50, 110)],
                    'description': '3_melds'
                }
            },
            4: {
                'player4_melds': {
                    #後兩個不動。最一開始四個為一組 x越來越大 y越來越小
                    'src_points': [(135+a4*15, 690-a4*45), (290+a4*15, 690-a4*45), (45, 975), (200, 975)],
                    'description': '4_melds'
                }
            }
        }
        
        # 遍歷所有要擷取的區域
        for player in Regions_Tiles:
            for key in Regions_Tiles[player]:
                src_points = Regions_Tiles[player][key]['src_points']
                
                # 透視變換（自動計算 dst_size）
                Regions_Tiles[player][key]['region'] = self.perspective_crop(frame, src_points)
        return Regions_Tiles
    
sct = mss.mss()

# 初始化 MahjongCropper 類別
cropper = MahjongCropper()

monitor = {"top": 0, "left": 0, "width": 1920, "height": 1080}
# 擷取螢幕畫面
screenshot = np.array(sct.grab(monitor))  # 讀取螢幕畫面
frame = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)  # 轉換顏色格式 (去除透明通道)

# 裁切區域
Regions_Tiles = cropper.crop_regions(frame)

# 存檔
for player, sections in Regions_Tiles.items():
    for key, info in sections.items():
        filename = os.path.join(cropper.output_folder, f"{key}.png")
        cv2.imwrite(filename, info['region'])
        print(f"已儲存 {filename}")

cv2.destroyAllWindows()