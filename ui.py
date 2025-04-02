import tkinter as tk
from tkinter import ttk
import cv2
import json
from FinalDetection import MahjongDetection  
from PIL import Image, ImageTk

def update_frame():
    ret, frame = cap.read()
    if ret:
        detected_frame = MahjongDetection(frame) 
        detected_frame = cv2.cvtColor(detected_frame, cv2.COLOR_BGR2RGB)
        img_detected = ImageTk.PhotoImage(Image.fromarray(detected_frame))
        
        canvas_detected.create_image(0, 0, anchor=tk.NW, image=img_detected)
        canvas_detected.img_tk = img_detected
        
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_original = ImageTk.PhotoImage(Image.fromarray(frame))
        
        canvas_original.create_image(0, 0, anchor=tk.NW, image=img_original)
        canvas_original.img_tk = img_original
    
    update_info()
    root.after(30, update_frame)

def update_info():
    try:
        with open("C:\mahjongproject\game_data.json", "r", encoding="utf-8") as file:
            data = json.load(file)
        
        dealer_label.config(text=f"莊家: 玩家 {data['Banker']}")
        wind_text = "\n".join([f"玩家 {p} 風位: {w}" for p, w in data["players"].items()])
        wind_label.config(text=wind_text)
        dora_label.config(text=f"寶牌: {data['dora']}")
    except Exception as e:
        print("讀取 JSON 失敗:", e)



def start_detection():
    global running
    running = True
    update_frame()

def stop_detection():
    global running
    running = False 

root = tk.Tk()
root.title("日麻小助手")
root.geometry("1300x800")

frame_top = tk.Frame(root)
frame_top.pack(pady=10)

button_start = ttk.Button(frame_top, text="開始辨識", command = start_detection)
button_start.grid(row=0, column=0, padx=10)

button_stop = ttk.Button(frame_top, text="結束辨識", command = stop_detection)
button_stop.grid(row=0, column=1, padx=10)

info_frame = tk.Frame(root)
info_frame.pack(side=tk.LEFT, padx=20)

dealer_label = tk.Label(info_frame, text="莊家: 未知", font=("Arial", 14))
dealer_label.pack(anchor="w")

wind_label = tk.Label(info_frame, text="風位: 未知", font=("Arial", 14))
wind_label.pack(anchor="w")

dora_label = tk.Label(info_frame, text="寶牌: 未知", font=("Arial", 14))
dora_label.pack(anchor="w")

canvas_frame = tk.Frame(root)
canvas_frame.pack()

canvas_original = tk.Canvas(canvas_frame, width=640, height=480)
canvas_original.grid(row=0, column=0, padx=10)
canvas_detected = tk.Canvas(canvas_frame, width=640, height=480)
canvas_detected.grid(row=0, column=1, padx=10)

cap = cv2.VideoCapture(0)
update_frame()

root.mainloop()
cap.release()
cv2.destroyAllWindows()
