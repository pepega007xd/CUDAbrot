import torch
import tkinter as tk
from PIL import Image, ImageTk
import numpy as np
from threading import Timer

class App:
    def __init__(self):
        window = tk.Tk()
        self.image_resolution = (640, 480)
        self.zoom_pos = (0, 0)
        self.zoom_multiplier = 1
        self.area_x = (-2.0, 1.0)
        self.area_y = (-1.0, 1.0)
        self.zoom_enabled = True
        self.zoom_ticks = 0
        self.timer = Timer(0.2, lambda:0)


        #main frames
        frm_settings = tk.Frame(master=window, width=200)
        frm_settings.pack(fill=tk.Y, side=tk.LEFT)

        frm_image = tk.Frame(master=window, bg="white")
        frm_image.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)

        title = tk.Label(master=frm_settings, text="CUDAbrot v0.1.0")
        title.pack()


        #device
        str_device = tk.StringVar()
        
        self.device_list = ["CPU"]
        for i in range(torch.cuda.device_count()):
            self.device_list.append(torch.cuda.get_device_name(i))
        
        menu_device = tk.OptionMenu(frm_settings, str_device,
            command=self.set_device, *self.device_list)
        menu_device.pack()
        str_device.set("CPU")


        #resolution
        frm_resolution = tk.Frame(master=frm_settings)
        frm_resolution.pack()
        self.str_resolution = tk.StringVar()

        lbl_resolution = tk.Label(master=frm_resolution,
            text="Choose image resolution:")
        lbl_resolution.pack()

        R1 = tk.Radiobutton(frm_resolution, text="640x480",
            variable=self.str_resolution, 
            value="640x480", command=self.set_resolution)
        R1.pack()
        R1.select()

        R2 = tk.Radiobutton(frm_resolution, text="1280x720", 
            variable=self.str_resolution, 
            value="1280x720", command=self.set_resolution)
        R2.pack()


        #zoom
        frm_zoom = tk.Frame(master=frm_settings)
        frm_zoom.pack()
        lbl_zoom = tk.Label(master=frm_zoom, text = "Scroll to zoom in/out")
        lbl_zoom.pack()
        zoom_button = tk.Button(master=frm_settings, text="Reset zoom", command=self.zoom_reset)
        zoom_button.pack()


        #image
        self.canvas = tk.Canvas(frm_image, width=self.image_resolution[0],
            height=self.image_resolution[1])
        self.canvas.pack(expand=True, anchor="c")
        self.image_container = self.canvas.create_image(0,0, anchor="nw")

        self.canvas.bind("<Button-4>", self.wait_for_zoom) #zoom in
        self.canvas.bind("<Button-5>", self.wait_for_zoom) #zoom out

        #run app
        self.set_device("CPU")
        self.update_image()
        window.mainloop()


    def update_image(self):
        width, height = self.image_resolution

        #18.3.2022 19:17 byl proveden příspěvek do státního rozpočtu

        #updating area
        x0, x1 = self.area_x
        y0, y1 = self.area_y
        px,py = self.zoom_pos
        w, h = self.image_resolution
        m = self.zoom_multiplier

        #don't touch this part
        x = x0 + (x1 - x0) * px / w
        self.area_x = (x - (x - x0) * m, x + (x1 - x) * m)

        y = y0 + (y1 - y0) * py / h
        self.area_y = (y - (y - y0) * m, y + (y1 - y) * m)

        #rendering area
        axis_x = torch.linspace(*self.area_x, width, device=self.device)
        axis_y = torch.linspace(*self.area_y, height, device=self.device)
        
        real_part, imag_part = torch.meshgrid(axis_x, axis_y)
        z_1 = (real_part + 1j * imag_part).to(dtype=torch.complex128)
        z_n = z_1.clone()  
        for i in range(50):
            z_n = z_n ** 2 + z_1

        image = (torch.abs(z_n.T) < 2).cpu().numpy()
        self.image = ImageTk.PhotoImage(image=Image.fromarray(image))
        self.canvas.itemconfig(self.image_container, image=self.image)


    def set_resolution(self):
        width, height = self.str_resolution.get().split("x")
        self.canvas.config(width=int(width), height=int(height))
        self.image_resolution=(int(width), int(height))


    def set_device(self, str_device):
        index=self.device_list.index(str_device)
        if index == 0: self.device = torch.device("cpu") # 0 is cpu
        else: self.device = torch.device(f"cuda:{index-1}")


    def wait_for_zoom(self, event):
        self.timer.cancel()
        self.zoom_ticks += 1
        self.timer = Timer(0.1, self.zoom, (event,))
        self.timer.start()

    def zoom(self, event):
        self.zoom_pos = (event.x, event.y)
        if event.num == 5:
            self.zoom_multiplier = 1.1**self.zoom_ticks
        else:
            self.zoom_multiplier = 1/1.1**self.zoom_ticks
        self.zoom_ticks = 0
        self.update_image()
        self.zoom_multiplier = 1
        
    def zoom_reset(self):
        self.area_x = (-2.0, 1.0)
        self.area_y = (-1.0, 1.0)
        self.update_image()


new=App()

