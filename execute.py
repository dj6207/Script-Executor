import json
import pyautogui as pya
import tkinter as tk
import pygetwindow as gw
import time
import os
from queue import Queue
from tkinter import filedialog, messagebox

def get_file_path() -> str:
    return filedialog.askopenfilename()   

class Execute(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Execute")

        self.input_number = tk.Label(self, text="Input:").pack()
        self.input_number_entry = tk.Entry(self)
        self.input_number_entry.pack()
        self.start_button = tk.Button(self, text="Start", command=self.main).pack()

    def parse_json(self, json_path:str) -> dict:
        with open(json_path, 'r') as file:
            commands_list:dict = json.load(file)
        return commands_list

    def initalize_queue(self, commands_list:dict) -> None:
        self.commands_queue = Queue()
        for command in commands_list.get("commands"):
            self.commands_queue.put(command)
    
    def execute_commands(self, command:dict) -> bool:
        command_name: str = command.get("command")

        delay: int = command.get("delay")
        if delay: time.sleep(delay)

        # Pauses the command execution and displays a message box
        if command.get("pause"):
            self.deiconify()
            messagebox.showinfo("Information", command.get("command"))
            self.iconify()
        
        mouse_scroll: int = command.get("scroll")
        if mouse_scroll: pya.scroll(mouse_scroll)

        if command.get("screenshot"):
            screenshot_folder = "./screenshot"
            if not os.path.exists(screenshot_folder):
                os.makedirs(screenshot_folder)
            image = pya.screenshot()
            image.save(os.path.join(screenshot_folder, f"{command_name}.png"))
        
        # Press the keys typed into the input box
        key_list:list[str] = command.get("keys")
        if command.get("input"):
            key_list = list(self.input_number_entry.get()) + key_list

        for key in key_list:
            try:
                pya.press(key, presses=command.get("clicks"))
            except Exception as e:
                self.deiconify()
                messagebox.showerror("Key not found", f"{key} key not found")
                self.iconify()

        item_list:list[str] = command.get("find")
        if not len(item_list):
            for _ in range(command.get("clicks")):
                pya.click()
        
        found = False
        for item in item_list:
            try:
                search_time: int = command.get("search")
                # Type in a search time if the image you are looking for might take some time to appear
                coordinates = pya.locateCenterOnScreen(f"./assets/{item}", confidence=0.9, minSearchTime=search_time) if search_time else pya.locateCenterOnScreen(f"./assets/{item}", confidence=0.9)
                if coordinates:
                    found = True
                    for _ in range(command.get("clicks")):
                        pya.click(coordinates)
                    break
            except Exception as e:
                continue
        if not found and len(item_list):
            # Execute a fix if any if the image is not found
            fix_commands: list = command.get("fix")                
            if fix_commands and self.fix(fix_commands): return True
            self.deiconify()
            error = command.get("error")
            messagebox.showerror(f"{command_name} not found", error if error else f"{command_name} not found")
            self.iconify()
            return False
        return True

    def fix(self, fix_commands:list) -> bool:
        for command in fix_commands:
            if not self.execute_commands(command): return False
        return True

    def expand_window(self, window_name:str) -> bool:
        try:
            window:gw.Win32Window = gw.getWindowsWithTitle(window_name)[0]
            window.activate()
            window.maximize()
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Please open {window_name} before starting. {e}")
            return False
        
    def main(self) -> None:
        self.iconify()
        self.initalize_queue(
            commands_list=self.parse_json(
                json_path=get_file_path()
            )
        )

        if self.expand_window():
            while not self.commands_queue.empty():
                command:dict = self.commands_queue.get()
                if not self.execute_commands(command): break
            self.deiconify()
            messagebox.showinfo("Finished", "Script finished execution")

if __name__ == "__main__":
    execute = Execute()
    execute.mainloop()