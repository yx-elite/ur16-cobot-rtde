import tkinter as tk
import logging
import rtde.rtde as rtde
import rtde.rtde_config as rtde_config
import sys
from tkinter import ttk, messagebox
from config import ROBOT_HOST, ROBOT_PORT, config_filename

class Ur16GUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("UR16 Joint Coordinate Extractor")
        self.geometry("480x600")
        self.config(bg = "#f0f0f0")

        style = ttk.Style()
        style.theme_use("winnative")
        style.configure(".", background="#f0f0f0", foreground="#000")

        self.create_instruction()
        self.create_widgets()

        self.positions = []
        # self.button_clicked_flags = [False] * 6

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.ur_init()

    def ur_init(self):
        logging.getLogger().setLevel(logging.INFO)

        conf = rtde_config.ConfigFile(config_filename)
        state_names, state_types = conf.get_recipe('state')
        setp_names, setp_types = conf.get_recipe('setp') 
        watchdog_names, watchdog_types = conf.get_recipe('watchdog')

        self.con = rtde.RTDE(ROBOT_HOST, ROBOT_PORT)
        self.con.connect()

        ver = self.con.get_controller_version()

        self.con.send_output_setup(state_names, state_types)
        self.setp = self.con.send_input_setup(setp_names, setp_types)
        self.watchdog = self.con.send_input_setup(watchdog_names, watchdog_types)

        if not self.con.send_start():
            print('Failed to start data synchronization')
            sys.exit()

        for i in range(6):
            self.setp.__setattr__(f'input_double_register_{i}', 0)

    def create_instruction(self):
        label = ttk.Label(self, text="UR16 Joint Coordinate Extractor", font=('Arial', 18))
        label.pack(padx=20, pady=(20, 0))

    def create_widgets(self):
        button_frame = ttk.Frame(self)
        button_frame.pack(side="top", fill="both", expand=True, padx=20, pady=10)

        self.textboxes = []
        self.buttons = []
        for i in range(6):
            position_frame = ttk.Frame(button_frame)
            position_frame.pack(pady=10)

            button = ttk.Button(position_frame, text=f"RecordPosition {i+1}", command=lambda j=i: self.button_clicked(j))
            button.pack(side="left", padx=10)
            self.buttons.append(button)

            reset_button = ttk.Button(position_frame, text="Reset", command=lambda j=i: self.reset_textbox(j))
            reset_button.pack(side="left", padx=10)

            textbox = tk.Text(button_frame, height=2, width=10, wrap="word")
            textbox.pack(fill="x", pady=5)
            self.textboxes.append(textbox)

    def button_clicked(self, i):
        for _ in range(200):
            state = self.con.receive()
        current_position = state.actual_TCP_pose
        print(current_position)
        
        self.positions.append(current_position)
        text = current_position
        self.textboxes[i].delete("1.0", tk.END)
        self.textboxes[i].insert("1.0", text)
    
    def reset_textbox(self, index):
        self.textboxes[index].delete("1.0", "end")

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            try:
                self.con.send_pause()
                self.con.disconnect()
                self.destroy()
            except Exception as e:
                print(e)

if __name__ == "__main__":
    app = Ur16GUI()
    app.mainloop()
