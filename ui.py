import tkinter as tk
from tkinter import ttk, PhotoImage
import json
import subprocess
from PIL import Image,ImageTk
from FinalDetection import MahjongDetection

# UI 介面設定
root = tk.Tk()
root.title("日麻小助手")
root.geometry("1280x720")

running = False
process = None
process1 = None

banker_var = tk.StringVar()
dora_var = tk.StringVar()
field_wind_var = tk.StringVar()

info_frame = ttk.LabelFrame(root , text="遊戲資訊", padding=10)
info_frame.pack(padx=10, pady=10, fill="both", expand= True)

#顯示資訊的label
for var in [banker_var, field_wind_var, dora_var]:
    ttk.Label(info_frame, textvariable=var, font=("Arial", 12), wraplength=500, anchor="w", justify="left").pack(anchor="w")

tenpai_p2_var = tk.StringVar()
tenpai_p3_var = tk.StringVar()
tenpai_p4_var = tk.StringVar()

for var in [tenpai_p2_var, tenpai_p3_var, tenpai_p4_var]:
    ttk.Label(info_frame, textvariable=var, font=("Arial", 12), wraplength=500, anchor="w", justify="left").pack(anchor="w")
def update_info():
    try:
        with open(r"D:/mahjongproject/game_data.json", "r", encoding="utf-8")as  file:
            data = json.load(file)

        banker_id = str(data["Banker"])
        player = data["players"].get(banker_id, {})

        banker_var.set(f"莊家: 玩家 {banker_id}")
        dora_var.set(f"寶牌: {'、'.join(data['dora'])}")
        field_wind_var.set(f"場風: {player.get('field_wind', '未知')}")

    except Exception as e:
        print("讀取json失敗:", e)

    # 加入顯示對手聽牌機率
    try:
        chances = data["analysis"]["opponent_tenpai_chance"]
        tenpai_p2_var.set(f"下家(p2)聽牌機率: {chances.get('p2', 0)}%")
        tenpai_p3_var.set(f"對家(p3)聽牌機率: {chances.get('p3', 0)}%")
        tenpai_p4_var.set(f"上家(p4)聽牌機率: {chances.get('p4', 0)}%")
    except:
        tenpai_p2_var.set("下家(p2)聽牌機率: 無資料")
        tenpai_p3_var.set("對家(p3)聽牌機率: 無資料")
        tenpai_p4_var.set("上家(p4)聽牌機率: 無資料")
        
    if running:
        root.after(1000, update_info)

def start_detection():
    global running, process,process1
    running = True
    update_info()  # 開始讀取 JSON
    
    # **執行辨識程式（確保路徑正確）**
    if process is None:
        process = subprocess.Popen(["python", r"D:/mahjongproject/FinalDetection.py"])
    if process1 is None:
        process1 = subprocess.Popen(["python", r"D:/mahjongproject/analysis.py"])

def stop_detection():
    global running, process,process1
    running = False  

    # **關閉辨識程式**
    if process:
        process.terminate() # 終止辨識程式
        process = None
    if process1:
        process1.terminate() # 終止辨識程式
        process1 = None

"這裡要修改不然圖片會擋住"
image = Image.open(r"D:/mahjongproject/321.PNG")
bg_image = ImageTk.PhotoImage(image)

bg_label = tk.Label(root, image=bg_image)
bg_label.place(relwidth=1, relheight=1)

frame_top = tk.Frame(root)
frame_top.pack(pady=10)

button_start = ttk.Button(frame_top, text="開始讀取", command=start_detection)
button_start.grid(row=0, column=0, padx=10)

button_stop = ttk.Button(frame_top, text="停止讀取", command=stop_detection)
button_stop.grid(row=0, column=1, padx=10)

info_frame = tk.Frame(root)
info_frame.pack(pady=20)

root.mainloop()
