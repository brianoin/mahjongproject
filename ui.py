import tkinter as tk
from tkinter import ttk
import subprocess
from detection import MahjongDetection
from analysis import MahjongAnalyzer

class MahjongAnalyzerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("麻將分析系統")
        self.root.geometry("1200x800")
        self.root.configure(bg="#2c3e50")
        
        self.detection_process = None  # 用來存 `detection.py` 的執行狀態

        self.setup_styles()
        self.create_widgets()

    def setup_styles(self):
        """設定 UI 樣式"""
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", font=("Arial", 12), padding=10, background="#3498db")
        style.configure("TLabel", font=("Arial", 12), padding=5, background="#2c3e50", foreground="white")
        style.configure("TFrame", background="#2c3e50")

    def create_widgets(self):
        """建立 UI 元件"""
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        # 開始即時辨識按鈕
        self.start_detection_btn = ttk.Button(control_frame, text="開始即時辨識", command=self.start_real_time_detection)
        self.start_detection_btn.grid(row=0, column=0, padx=10, pady=10)

        # 停止即時辨識按鈕
        self.stop_detection_btn = ttk.Button(control_frame, text="停止辨識", command=self.stop_real_time_detection, state=tk.DISABLED)
        self.stop_detection_btn.grid(row=0, column=1, padx=10, pady=10)

        # 狀態欄
        self.status_var = tk.StringVar(value="就緒")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def start_real_time_detection(self):
        """啟動即時辨識 (執行 detection.py)"""
        if self.detection_process is None:
            self.detection_process = subprocess.Popen(["python", "detection.py"])  # 啟動辨識程式
            self.status_var.set("即時辨識運行中...")
            self.start_detection_btn.config(state=tk.DISABLED)
            self.stop_detection_btn.config(state=tk.NORMAL)

    def stop_real_time_detection(self):
        """停止即時辨識"""
        if self.detection_process is not None:
            self.detection_process.terminate()  # 終止辨識程式
            self.detection_process = None
            self.status_var.set("即時辨識已停止")
            self.start_detection_btn.config(state=tk.NORMAL)
            self.stop_detection_btn.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = MahjongAnalyzerUI(root)
    root.mainloop()
