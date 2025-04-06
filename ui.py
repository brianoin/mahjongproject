import tkinter as tk
from tkinter import ttk, PhotoImage
import json
import subprocess
from PIL import Image,ImageTk
from FinalDetection import MahjongDetection

running = False
process = None

def update_info():
    """定時讀取 JSON 檔案，更新 UI 上的資訊"""
    try:
        with open(r"C:/mahjongproject/game_data.json", "r", encoding="utf-8") as file:
            data = json.load(file)
        
        dealer_label.config(text=f"莊家: 玩家 {data['Banker']}")
        wind_text = "\n".join([f"玩家 {p} 風位: {w}" for p, w in data["field_wind"].items()])
        wind_label.config(text=wind_text)
        dora_label.config(text=f"寶牌: {data['dora']}")
    
    except Exception as e:
        print("讀取 JSON 失敗:", e)

    if running:
        root.after(500, update_info)  # 每 1 秒讀取一次 JSON

def start_detection():
    global running, process
    running = True
    update_info()  # 開始讀取 JSON
    
    # **執行辨識程式（確保路徑正確）**
    if process is None:
        process = subprocess.Popen(["python", r"C:/mahjongproject/FinalDetection.py"])

def stop_detection():
    global running, process
    running = False  

    # **關閉辨識程式**
    if process:
        process.terminate()  # 終止辨識程式
        process = None

# UI 介面設定
root = tk.Tk()
root.title("日麻小助手")
root.geometry("1280x720")

image = Image.open(r"C:\Users\1\OneDrive\桌面\mahjongproject\maxresdefault.jpg")
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


dealer_label = tk.Label(info_frame, text="莊家: 未知", font=("Arial", 14))
dealer_label.pack(anchor="w")

wind_label = tk.Label(info_frame, text="場風: 未知", font=("Arial", 14))
wind_label.pack(anchor="w")

dora_label = tk.Label(info_frame, text="寶牌: 未知", font=("Arial", 14))
dora_label.pack(anchor="w")

columns = ("筒","條","萬","字")
tree = ttk.Treeview(root, columns=columns, show="headings")

for col in columns:
    tree.heading(col, text=col)

data = [(info_frame),(info_frame),(info_frame),(info_frame)]  

for item in data :
    tree.insert("", tk.END, values=item)

tree.pack()


root.mainloop()
