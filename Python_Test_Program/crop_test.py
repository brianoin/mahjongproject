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

    def letterbox(self, img, new_shape=(480, 540)):
        """保持圖像大小不變，僅填充多餘的空白區域"""
        shape = img.shape[:2]  # 取得原圖大小 (height, width)
        
        # 計算填充區域 (dw: 左右填充量, dh: 上下填充量)
        dw, dh = new_shape[1] - shape[1], new_shape[0] - shape[0]  # 寬度差與高度差

        # 如果寬度或高度小於目標大小，則均勻分配填充
        dw, dh = dw // 2, dh // 2
        right, bottom = new_shape[1] - shape[1] - dw, new_shape[0] - shape[0] - dh

        # 如果填充量為負，設置為0，防止錯誤
        dw, dh = max(0, dw), max(0, dh)
        right, bottom = max(0, right), max(0, bottom)

        # 使用 cv2.copyMakeBorder 來填充空白區域
        img_padded = cv2.copyMakeBorder(img, dh, bottom, dw, right, cv2.BORDER_CONSTANT, value=(0, 0, 0))
        return img_padded
        
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
        
        size_mid = (70, 250)
        size_tiles = (540, 480)
        
        Regions_Mid = {
            'Player1_Mid': {'region': frame[490:535, 790:1050].copy(), 'description': '1'},
            'Player2_Mid': {'region': frame[360:540, 1065:1130].copy(), 'description': '2'},
            'Player3_Mid': {'region': frame[315:355, 870:1115].copy(), 'description': '3'},
            'Player4_Mid': {'region': frame[315:480, 805:860].copy(), 'description': '4'}
        }

        # 旋轉
        Regions_Mid['Player2_Mid']['region'] = cv2.rotate(Regions_Mid['Player2_Mid']['region'], cv2.ROTATE_90_CLOCKWISE)
        Regions_Mid['Player3_Mid']['region'] = cv2.rotate(Regions_Mid['Player3_Mid']['region'], cv2.ROTATE_180)
        Regions_Mid['Player4_Mid']['region'] = cv2.rotate(Regions_Mid['Player4_Mid']['region'], cv2.ROTATE_90_COUNTERCLOCKWISE)

        for key in Regions_Mid:
            Regions_Mid[key]['region'] = self.letterbox(Regions_Mid[key]['region'], size_mid)
            
        Regions_Tiles = {
            1: {
                'player1_hand': {'region': frame[900:1070, 200:1460].copy(), 'description': '1_hand'},
                'player1_discard': {'region': frame[540:770, 750:1150].copy(), 'description': '1_discard'},
                'player1_melds': {
                    #前兩個不動。最一開始四個為一組 x越來越小 y不變 1810 910 1475 1485 1260 
                    'src_points': [(1810, 910), (1840, 1045), (1475, 910), (1485, 1045)],
                    'description': '1_melds'
                },
            },
            2: {
                'player2_discard': {'region': frame[270:550, 1130:1410].copy(), 'description': '2_discard'},
                'player2_melds': {
                    #前兩個不動。最一開始四個為一組 x越來越大 y越來越大
                    'src_points': [(1465, 35), (1570, 35), (1510, 180), (1615, 180)],
                    'description': '2_melds'
                },
            },
            3: {
                'player3_discard': {'region': frame[110:310, 770:1140].copy(), 'description': '3_discard'},
                'player3_melds': {
                    #前兩個不動。最一開始四個為一組 x越來越大 y不變 755 760 140/3 47
                    'src_points': [(395, 30), (375, 110), (620, 30), (615, 110)],
                    'description': '3_melds'
                },
            },
            4: {
                'player4_discard': {'region': frame[270:570, 520:780].copy(), 'description': '4_discard'},
                'player4_melds': {
                    #後兩個不動。最一開始四個為一組 x越來越大 y越來越小
                    'src_points': [(135, 690), (290, 690), (45, 975), (200, 975)],
                    'description': '4_melds'
                },
            }
        }

        for player_key in Regions_Tiles:
            for key in Regions_Tiles[player_key]:
                region_data = Regions_Tiles[player_key][key]
                
                if 'src_points' in region_data:  # 如果是 melds 區域，需要進行透視變換
                    # 取得透視變換需要的 src_points
                    src_points = region_data['src_points']
                    
                    # 透視變換
                    region = self.perspective_crop(frame, src_points)
                    
                    # 進行 letterbox 操作
                    region = self.letterbox(region, size_tiles)
                    
                    # 更新結果
                    region_data['region'] = region
                else:
                    # 其他區域只需要進行 letterbox
                    region_data['region'] = self.letterbox(region_data['region'], size_tiles)

                
        Regions_Tiles_Dora = {
            'dora_indicator': {'region': frame[40:130, 25:310].copy(), 'description': 'dora'}
        }

        Regions_Tiles_Dora['dora_indicator']['region'] = self.letterbox(Regions_Tiles_Dora['dora_indicator']['region'], size_tiles)
        return Regions_Mid, Regions_Tiles, Regions_Tiles_Dora
    
sct = mss.mss()

# 記錄時間
last_capture_time = time.time()

# 初始化 MahjongCropper 類別
cropper = MahjongCropper()

monitor = {"top": 0, "left": 0, "width": 1920, "height": 1080}
# 擷取螢幕畫面
screenshot = np.array(sct.grab(monitor))  # 讀取螢幕畫面
frame = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)  # 轉換顏色格式 (去除透明通道)

# 裁切區域
Regions_Mid, Regions_Tiles, Regions_Tiles_Dora = cropper.crop_regions(frame)

# 存檔
for key, info in Regions_Mid.items():
    filename = os.path.join(cropper.output_folder, f"{key}.png")
    cv2.imwrite(filename, info['region'])
    print(f"已儲存 {filename}")

for player, sections in Regions_Tiles.items():
    for key, info in sections.items():
        filename = os.path.join(cropper.output_folder, f"{key}.png")
        cv2.imwrite(filename, info['region'])
        print(f"已儲存 {filename}")

for key, info in Regions_Tiles_Dora.items():
    filename = os.path.join(cropper.output_folder, f"{key}.png")
    cv2.imwrite(filename, info['region'])
    print(f"已儲存 {filename}")

# 釋放資源
cv2.destroyAllWindows()