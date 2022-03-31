import torch
import tkinter as tk
from PIL import Image, ImageTk
import numpy as np
from threading import Timer
from tkinter import ttk
from tkinter import colorchooser
import colorsys
import datetime

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
        self.timer = Timer(0.2, lambda:None)
        self.precision = 50
        self.start_color = (0, 0, 0)
        self.stop_color = (255, 255, 255)

        #window config
        window.title("CUDAbrot")
        try: window.tk.call('wm', 'iconphoto', window._w, tk.PhotoImage(file='icon.png'))
        except: pass


        #main frames
        frm_settings = tk.Frame(master=window, width=200, borderwidth=10)
        frm_settings.pack(fill=tk.Y, side=tk.LEFT)

        frm_image = tk.Frame(master=window, bg="white")
        frm_image.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)

        title = tk.Label(master=frm_settings, text="CUDAbrot v0.1.0")
        title.pack()

        ttk.Separator(master=frm_settings).pack(fill="x")


        #device
        frm_device = tk.Frame(master=frm_settings)
        frm_device.pack()
        str_device = tk.StringVar()
        
        self.device_list = ["CPU"]
        for i in range(torch.cuda.device_count()):
            self.device_list.append(torch.cuda.get_device_name(i))
        
        lbl_device = tk.Label(master=frm_device,
            text="Rendering device:")
        lbl_device.pack()

        menu_device = tk.OptionMenu(frm_device, str_device,
        *self.device_list, command=self.set_device)
        menu_device.pack()
        str_device.set("CPU")

        ttk.Separator(master=frm_settings).pack(fill="x")


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

        lbl_custom_resolution = tk.Label(master=frm_resolution,
            text="Custom resolution:")
        lbl_custom_resolution.pack()
        self.ent_custom_res = tk.Entry(master=frm_resolution, textvariable="kek")
        self.ent_custom_res.pack()
        self.ent_custom_res.insert(-1, "1920x1080")
        res_update = tk.Button(master=frm_resolution, text="Set resolution",
            command=self.set_custom_resolution)
        res_update.pack()

        ttk.Separator(master=frm_settings).pack(fill="x")


        #zoom
        frm_zoom = tk.Frame(master=frm_settings)
        frm_zoom.pack()
        lbl_zoom = tk.Label(master=frm_zoom, text = "Scroll to zoom in/out")
        lbl_zoom.pack()
        zoom_button = tk.Button(master=frm_settings, text="Reset zoom", command=self.zoom_reset)
        zoom_button.pack()

        ttk.Separator(master=frm_settings).pack(fill="x")


        #precision
        frm_precision = tk.Frame(master=frm_settings)
        frm_precision.pack()
        lbl_precision = tk.Label(master=frm_precision, text="Rendering precision (iterations): ")
        lbl_precision.pack()
        scale_precision = tk.Scale(master=frm_precision, from_=30, to=2000,
            orient=tk.HORIZONTAL, command = self.set_precision)
        scale_precision.pack()
        scale_precision.set(self.precision)

        ttk.Separator(master=frm_settings).pack(fill="x")


        #colors
        frm_color = tk.Frame(master=frm_settings)
        frm_color.pack()
        
        self.color_type = tk.StringVar()
        C1 = tk.Radiobutton(master=frm_color, text="RGB",
            variable=self.color_type, 
            value="RGB", command=self.update_image)
        C1.pack()
        C1.select()

        C2 = tk.Radiobutton(master=frm_color, text="HSV",
            variable=self.color_type, 
            value="HSV", command=self.update_image)
        C2.pack()

        frm_color_buttons = tk.Frame(master=frm_color)
        frm_color_buttons.pack(side=tk.LEFT)
        lbl_start_color = tk.Label(master=frm_color_buttons, text="Select start color")
        lbl_start_color.pack()

        lbl_stop_color = tk.Label(master=frm_color_buttons, text="Select stop color")
        lbl_stop_color.pack()

        self.start_color_button = tk.Button(master=frm_color, background=self.color_as_hex("start"),
            command=self.select_start_color)
        self.start_color_button.pack()

        self.stop_color_button = tk.Button(master=frm_color, background=self.color_as_hex("stop"),
            command=self.select_stop_color)
        self.stop_color_button.pack()

        ttk.Separator(master=frm_settings).pack(fill="x")

        #save image
        frm_save = tk.Frame(master=frm_settings)
        frm_save.pack()
        lbl_save = tk.Label(master=frm_save, text="Save rendered image")
        lbl_save.pack()
        save_button = tk.Button(master=frm_save, text="Save", command=self.save_image)
        save_button.pack()


        #image
        self.canvas = tk.Canvas(frm_image, width=self.image_resolution[0],
            height=self.image_resolution[1])
        self.canvas.pack(expand=True, anchor="c")
        self.image_container = self.canvas.create_image(0,0, anchor="nw")

        self.canvas.bind("<Button-4>", self.wait_for_zoom) #zoom in
        self.canvas.bind("<Button-5>", self.wait_for_zoom) #zoom out
        self.canvas.bind("<MouseWheel>", self.wait_for_zoom) #windows zoom

        #run app
        self.set_device("CPU")
        self.update_image()
        window.mainloop()


    def update_image(self):
        #18.3.2022 19:17 byl proveden příspěvek do státního rozpočtu

        #updating area
        width, height = self.image_resolution

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

        #getting color
        start_color = self.start_color
        stop_color = self.stop_color
        if self.color_type.get() == "HSV":
            start_color = self.rgb_to_hsv(start_color)
            stop_color = self.rgb_to_hsv(stop_color)
        a, b, c = start_color
        x, y, z = stop_color

        colors = torch.stack((torch.linspace(a, x, self.precision, device=self.device),
            torch.linspace(b, y, self.precision, device=self.device),
            torch.linspace(c, z, self.precision, device=self.device)), dim=-1)

        #rendering area
        axis_x = torch.linspace(*self.area_x, width, device=self.device)
        axis_y = torch.linspace(*self.area_y, height, device=self.device)
        
        real_part, imag_part = torch.meshgrid(axis_x, axis_y)
        z_1 = (real_part + 1j * imag_part).to(dtype=torch.complex64)
        z_n = z_1.clone()
        image = torch.zeros(3, width, height, device=self.device, dtype=torch.uint8)

        #rendering loop
        for color in colors:
            if self.color_type.get() == "HSV":
                color = self.hsv_to_rgb(color).to(self.device)
            color = color.to(dtype=torch.uint8)
            color = color.unsqueeze(1).unsqueeze(1).repeat(1, width, height)
            z_n = torch.square(z_n) + z_1
            mask = (torch.square(z_n.real) + torch.square(z_n.imag) < 4).repeat(3,1,1)
            image[mask] = color[mask]
            
        image = image.permute(2,1,0).cpu().numpy().astype(np.uint8)
        self.image = ImageTk.PhotoImage(image=Image.fromarray(image))
        self.canvas.itemconfig(self.image_container, image=self.image)


    def set_resolution(self):
        self._set_resolution(self.str_resolution)

    def set_custom_resolution(self):
        self._set_resolution(self.ent_custom_res)

    def _set_resolution(self, resolution):
        width, height = resolution.get().split("x")
        self.canvas.config(width=int(width), height=int(height))
        self.image_resolution = (int(width), int(height))

        #rescale area ratio
        image_ratio = self.image_resolution[1] / self.image_resolution[0]
        dx = self.area_x[1] - self.area_x[0]
        self.area_y = (self.area_y[0],
            self.area_y[0] + dx * image_ratio)
        self.update_image()


    def set_device(self, str_device):
        index = self.device_list.index(str_device)
        if index == 0: self.device = torch.device("cpu") # 0 is cpu
        else: self.device = torch.device(f"cuda:{index-1}")


    def wait_for_zoom(self, event):
        self.timer.cancel()
        self.zoom_ticks += 1
        self.timer = Timer(0.1, self.zoom, (event,))
        self.timer.start()

    def zoom(self, event):
        self.zoom_pos = (event.x, event.y)
        if event.num == 5 or event.delta < 0:
            self.zoom_multiplier = 1.1**self.zoom_ticks
        elif event.num == 4 or event.delta > 0:
            self.zoom_multiplier = 1/1.1**self.zoom_ticks

        self.zoom_ticks = 0
        self.update_image()
        self.zoom_multiplier = 1
        
    def zoom_reset(self):
        self.area_x = (-2.0, 1.0)
        self.area_y = (-1.0, 1.0)
        self.update_image()


    def set_precision(self, value):
        self.precision = int(value)
        self.update_image()

    def select_start_color(self):
        self.start_color = colorchooser.askcolor(title="Select start color")[0]
        self.start_color_button.config(background=self.color_as_hex("start"))
        self.update_image()

    def select_stop_color(self):
        self.stop_color = colorchooser.askcolor(title="Select stop color")[0]
        self.stop_color_button.config(background=self.color_as_hex("stop"))
        self.update_image()

    def color_as_hex(self, color):
        if color == "start": return "#{:02x}{:02x}{:02x}".format(*self.start_color)
        else: return "#{:02x}{:02x}{:02x}".format(*self.stop_color)

    def rgb_to_hsv(self, color):
        r, g, b = color
        return torch.tensor(colorsys.rgb_to_hsv(r/255, g/255, b/255))

    def hsv_to_rgb(self, color):
        h, s, v = color
        return torch.tensor(colorsys.hsv_to_rgb(h, s, v))*255

    def save_image(self):
        image = ImageTk.getimage(self.image)
        filename = datetime.datetime.now().strftime('%H-%M-%S')
        image.save(f"./{filename}.bmp")


if __name__ == "__main__": new=App()

