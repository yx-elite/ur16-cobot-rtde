# Beta testing

import sys
import logging
import csv
import tkinter as tk
import rtde.rtde as rtde
import rtde.rtde_config as rtde_config
import matplotlib.pyplot as plt
from tkinter import ttk, messagebox
from time import time, sleep


class Ur16GUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("UR16 Cobot Universal Controller v1.0")
        self.geometry("600x730")
        self.config(bg = "#f0f0f0")

        style = ttk.Style()
        style.theme_use("winnative")
        style.configure(".", background="#f0f0f0", foreground="#000")

        self.create_instruction()
        self.create_widgets()

        # Display connection status on bottom left of main window
        status_label = ttk.Label(self, text="Status:", font=('Arial', 8))
        status_label.pack(side="left", padx=(10, 0), pady=(0, 5))
        self.connection_status = tk.StringVar()
        self.connection_status.set("Inactive")
        self.status_text_label = ttk.Label(self, textvariable=self.connection_status, font=('Arial', 8))
        self.status_text_label.pack(side="left", pady=(0, 5), anchor="w")

        self.positions = []
        # self.button_clicked_flags = [False] * 6

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # self.ur_init()

    def ur_init(self):
        try:
            # Extract the user input from user entries
            ROBOT_HOST = str(self.entries[0].get())
            ROBOT_PORT = int(self.entries[1].get())
            config_filename = str(self.entries[2].get())
            
            logging.getLogger().setLevel(logging.INFO)

            conf = rtde_config.ConfigFile(config_filename)
            state_names, state_types = conf.get_recipe('state')
            setp_names, setp_types = conf.get_recipe('setp') 
            watchdog_names, watchdog_types = conf.get_recipe('watchdog')

            self.con = rtde.RTDE(ROBOT_HOST, ROBOT_PORT)
            self.con.connect()

            self.con.get_controller_version()

            self.con.send_output_setup(state_names, state_types)
            self.setp = self.con.send_input_setup(setp_names, setp_types)
            self.watchdog = self.con.send_input_setup(watchdog_names, watchdog_types)

            if not self.con.send_start():
                print('Failed to start data synchronization')
                sys.exit()

            for i in range(6):
                self.setp.__setattr__(f'input_double_register_{i}', 0)
            
            # Update connected status to the label
            self.connection_status.set("Connected")
            self.status_text_label.config(foreground="green")
            messagebox.showinfo("Connection", "Connected to robot successfully!")
            
        except Exception as e:
            # Update inactive status to the label
            self.connection_status.set("Connection Error")
            self.status_text_label.config(foreground="red")
            messagebox.showerror("Connection Error", "Failed to start data synchronization")

    def create_instruction(self):
        label = ttk.Label(self, text="UR16 Collaborative Robot Universal Controller", font=('Arial', 18))
        label.pack(padx=20, pady=(20, 0))

    def create_widgets(self):
        ## Create a general large frame
        input_frame = ttk.Frame(self)
        input_frame.pack(side="top", fill="both", expand=True, padx=20, pady=10)
        
        ## Create a frame for config settings
        connection_frame = ttk.Frame(input_frame)
        connection_frame.pack(pady=10)
        
        # Create config input setup
        self.fields = ["Robot Host", "Robot Port", "Config File"]
        self.entries = []
        default_texts = ['192.168.189.129', 30004, 'test/data-logging-config.xml']

        for row, field in enumerate(self.fields):
            connection_label = ttk.Label(connection_frame, text=f"{field}\t:", font=('Arial', 10))
            connection_label.grid(row=row, column=0, padx=10, pady=5)

            entry = ttk.Entry(connection_frame, width=40)
            entry.grid(row=row, column=1, padx=10, pady=5)
            self.entries.append(entry)
            
            # Add default text to the entry
            default_text = default_texts[row]
            entry.insert(0, default_text)
        
        connect_button = ttk.Button(connection_frame, text="Connect", command=self.ur_init)
        connect_button.grid(row=len(self.fields), columnspan=2, pady=5)
        #connect_button.pack(pady=10)
        
        ## Create a frame for users' control
        control_frame = ttk.Frame(input_frame)
        control_frame.pack(pady=10)
        
        # Create repetition count and control setup
        rep_label = ttk.Label(control_frame, text="Repetition Count :", font=('Arial', 10))
        rep_label.pack(side="left", padx=10, pady=0)
        
        self.rep_entry = ttk.Entry(control_frame, width=5)
        self.rep_entry.pack(side="left", padx=(0, 100))
        
        run_button = ttk.Button(control_frame, text="Run", command=self.run_robot)
        run_button.pack(side="right", padx=5)
        # log_button = ttk.Button(control_frame, text="Log Data")
        # log_button.pack(side="right", padx=5)
        # csv_button = ttk.Button(control_frame, text="Export CSV")
        # csv_button.pack(side="right", padx=5)

        self.textboxes = []
        self.buttons = []
        for i in range(5):
            position_frame = ttk.Frame(input_frame)
            position_frame.pack(pady=10)

            button = ttk.Button(position_frame, text=f"Record Position {i+1}", command=lambda j=i: self.button_clicked(j))
            button.pack(side="left", padx=10)
            self.buttons.append(button)

            reset_button = ttk.Button(position_frame, text="Reset", command=lambda j=i: self.reset_textbox(j))
            reset_button.pack(side="left", padx=10)

            textbox = tk.Text(input_frame, height=2, width=10, wrap="word")
            textbox.pack(fill="x", pady=(0,10))
            self.textboxes.append(textbox)
    
    def button_clicked(self, i):
        for _ in range(200):
            state = self.con.receive()
        current_position = state.actual_TCP_pose
        
        self.positions.append(current_position)
        text = current_position
        self.textboxes[i].delete("1.0", tk.END)
        self.textboxes[i].insert("1.0", text)
    
    def reset_textbox(self, index):
        self.textboxes[index].delete("1.0", "end")
    
    def run_robot(self):
        #Initialise plotting parameters
        op_time = 0
        plot_time = []
        x, y, z, rx, ry, rz = [], [], [], [], [], []
        fx, fy, fz, frx, fry, frz = [], [], [], [], [], []
        
        try:
            # Strip to remove all empty spaces from entries & spilt using comma into list
            setp1 = [float(value) for value in self.textboxes[0].get("1.0", tk.END).strip().split()]
            setp2 = [float(value) for value in self.textboxes[1].get("1.0", tk.END).strip().split()]
            #setp1 = list(map(float, self.textboxes[0].get("1.0", tk.END).strip().split()))
            #setp2 = list(map(float, self.textboxes[1].get("1.0", tk.END).strip().split()))

            self.setp.input_double_register_0 = 0
            self.setp.input_double_register_1 = 0
            self.setp.input_double_register_2 = 0
            self.setp.input_double_register_3 = 0
            self.setp.input_double_register_4 = 0
            self.setp.input_double_register_5 = 0

            self.watchdog.input_int_register_0 = 0
            
            def setp_to_list(sp):
                sp_list = []
                for i in range(0, 6):
                    sp_list.append(sp.__dict__["input_double_register_%i" % i])
                return sp_list
            
            def list_to_setp(sp, list):
                for i in range(0, 6):
                    sp.__dict__["input_double_register_%i" % i] = list[i]
                return sp

            # Start data synchronization
            if not self.con.send_start():
                sys.exit()

            # Initialise looping parameters
            rt_init = time()
            repetition_counter = 0
            repetition = int(self.rep_entry.get())
            move_completed = True

            # Robot main control loop
            while repetition_counter < repetition:
                state = self.con.receive()

                if state is None:
                    break

                if move_completed and state.output_int_register_0 == 1:
                    move_completed = False
                    new_setp = setp1 if setp_to_list(self.setp) == setp2 else setp2
                    list_to_setp(self.setp, new_setp)
                    print("New pose = " + str(new_setp))
                    # Send new setpoint
                    self.con.send(self.setp)
                    self.watchdog.input_int_register_0 = 1

                elif not move_completed and state.output_int_register_0 == 0:
                    print("Move to confirmed pose = " + str(state.target_q))
                    move_completed = True
                    self.watchdog.input_int_register_0 = 0

                    # Data returned from cobot
                    tcp_pose = state.actual_TCP_pose
                    tcp_force = state.actual_TCP_force
                    self.process_data(rt_init, tcp_pose, tcp_force)
                    #print(f"Current pose = {tcp_pose}")
                    #print(f"Current force = {tcp_force}")


                    # Two motions in one repetition
                    repetition_counter += 0.5
                    print(repetition_counter)
                    # Handle movement delay
                    sleep(1)

                self.con.send(self.watchdog)

            print('---------------------------------------------')
            print(f'{repetition} repetitions are completed successfully!')
            
            self.log_data(plot_time, x, y, z, rx, ry, rz, fx, fy, fz, frx, fry, frz)
            self.plot_data(plot_time, x, y, z, rx, ry, rz, fx, fy, fz, frx, fry, frz)

        except Exception as e:
            print(f"Error in run_robot: {e}")
        finally:
            print(f'Runtime completed in {op_time:.4f} seconds.')
    
    
    def process_data(rt_init, tcp_pose, tcp_force, 
                    plot_time, 
                    x, y, z, rx, ry, rz, fx, fy, fz, frx, fry, frz):
        # Input to list for graph plotting
        rt_refresh = time()
        op_time = rt_refresh - rt_init
        print(f'Operation Time: {op_time:.4f} seconds')
        plot_time.append(op_time)

        x.append(tcp_pose[0])
        y.append(tcp_pose[1])
        z.append(tcp_pose[2])
        rx.append(tcp_pose[3])
        ry.append(tcp_pose[4])
        rz.append(tcp_pose[5])

        fx.append(tcp_force[0])
        fy.append(tcp_force[1])
        fz.append(tcp_force[2])
        frx.append(tcp_force[3])
        fry.append(tcp_force[4])
        frz.append(tcp_force[5])


    def log_data(self, plot_time, x, y, z, rx, ry, rz, fx, fy, fz, frx, fry, frz):
        try:
            filename = 'robot_data_log.csv'
            with open(filename, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['Timestamp', 'x', 'y', 'z', 'rx', 'ry', 'rz', 'Fx', 'Fy', 'Fz', 'Frx', 'Fry', 'Frz'])
                for i in range(len(plot_time)):
                    writer.writerow([plot_time[i], x[i], y[i], z[i], rx[i], ry[i], rz[i], fx[i], fy[i], fz[i], frx[i], fry[i], frz[i]])
            print(f"Data logged successfully to {filename}!")

        except Exception as e:
            print(f"Error in log_data: {e}")


    def plot_data(self, plot_time, x, y, z, rx, ry, rz, fx, fy, fz, frx, fry, frz):
        try:
            # Initialize graph plotting
            fig1, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8))
            ax1.plot(plot_time, x, label='x')
            ax1.plot(plot_time, y, label='y')
            ax1.plot(plot_time, z, label='z')
            ax1.set_xlabel('Operation Time (s)')
            ax1.set_ylabel('Real Time Position Coordinate')
            ax1.legend()

            ax2.plot(plot_time, rx, label='rx')
            ax2.plot(plot_time, ry, label='ry')
            ax2.plot(plot_time, rz, label='rz')
            ax2.set_xlabel('Operation Time (s)')
            ax2.set_ylabel('Real Time Angular Coordinate')
            ax2.legend()

            fig2, (ax3, ax4) = plt.subplots(2, 1, figsize=(8, 8))
            ax3.plot(plot_time, fx, label='Fx')
            ax3.plot(plot_time, fy, label='Fy')
            ax3.plot(plot_time, fz, label='Fz')
            ax3.set_xlabel('Operation Time (s)')
            ax3.set_ylabel('Real Time Joint Force')
            ax3.legend()

            ax4.plot(plot_time, frx, label='Frx')
            ax4.plot(plot_time, fry, label='Fry')
            ax4.plot(plot_time, frz, label='Frz')
            ax4.set_xlabel('Operation Time (s)')
            ax4.set_ylabel('Real Time Joint Torque')
            ax4.legend()
            plt.show()
        
        except Exception as e:
            print(f"Error in plot_data: {e}")

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            try:
                if hasattr(self, 'con') and self.con:
                    # If con exists, then only proceed
                    self.con.send_pause()
                    self.con.disconnect()
                
                # If con does not exist, close window directly    
                self.destroy()
            
            except Exception as e:
                print(e)


if __name__ == "__main__":
    app = Ur16GUI()
    app.mainloop()