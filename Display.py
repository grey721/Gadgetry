import tkinter as tk
from tkinter import Menu, messagebox

import os
import json
from platform import system
from PIL import Image


class Pad:
    def __init__(self):
        self.transCol = None
        self.drag_x = None
        self.drag_y = None
        self.picture = None  # gif序列
        self.path = None
        self.config = json.load(open('config.json', 'r', encoding='utf-8'))["settings"]
        self.delay = self.config['delay']  # 毫秒
        assert '.gif' in self.config['picture_name']
        self.x = self.config['x']  # 屏幕左上角为坐标原点
        self.y = self.config['y']
        # =========================窗口设置=================================
        self.root = tk.Tk()  # 窗口主体
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.get_picture()  # 获取gif序列,初始化size
        self.root.attributes('-topmost', self.config["top_status"])  # 置顶信息
        self.root.overrideredirect(True)  # T则不显示UI,拖拽调整大小已关闭
        # ========================设置透明背景==============================
        self.label = tk.Label(self.root, bd=0)  # borderless window
        self.init_transparent()
        self.label.pack()
        # =============================初始参数=======================================
        self.init_drag()  # 设置左键拖动
        self.set_popup()  # 设置右键面板

    def init_transparent(self):
        self.transCol = self.config['transparent_color']
        self.transCol = self.config['color_support'][self.transCol]
        # ================设定透明色，若保留UI则透明色不能为黑色=================
        if system() == 'Windows':
            self.root.wm_attributes('-transparent', self.transCol)
        else:  # platform is Mac/Linux
            # https://stackoverflow.com/questions/19080499/transparent-background-in-a-tkinter-window
            self.root.wm_attributes('-transparent', True)  # do this for mac, but the bg stays black
            self.root.config(bg='systemTransparent')
        self.root.configure(bg=self.transCol)
        self.label.config(bg=self.transCol)
        if system() != 'Windows':
            self.label.config(bg='systemTransparent')

    def init_size(self):
        with Image.open(self.path) as img:  # 获取图片的尺寸（宽度，高度），单位为像素
            width, height = img.size
        assert width, height is not None
        size = f'{width}x{height}'
        if self.x + width > self.screen_width:
            self.x = self.screen_width - width
        if self.y + height > self.screen_height:
            self.y = self.screen_height - height
        self.root.geometry(size)  # 宽×高+x+y
        size = f'+{self.x}+{self.y}'
        self.root.geometry(size)

    def get_picture(self):
        if self.config['picture_name'] in os.listdir(self.config['path']):
            self.path = self.config['path'] + self.config['picture_name']
        else:
            assert self.config['picture_name'] is not None
            for name in os.listdir(self.config['path']):
                if '.gif' in name:
                    self.config['picture_name'] = name
                    self.path = self.config['path'] + name
                    break
            else:
                raise FileNotFoundError
        result = []
        i = 0
        while True:
            try:
                result.append(tk.PhotoImage(file=os.path.abspath(self.path), format='gif -index %i' % i))
                i += 1
            except tk.TclError:
                break
        self.picture = result
        self.init_size()

    def set_popup(self):
        def show_popup(event):
            # 展示右键菜单
            try:
                popup.tk_popup(event.x_root, event.y_root)
            finally:
                # 确保菜单在鼠标离开后能够隐藏
                popup.grab_release()

        def open_settings():
            # =========================创建一个新的Tkinter窗口作为设置面板==================
            settings = tk.Toplevel(self.root)
            settings.title("设置")
            settings.geometry('200x230+650+200')
            settings.resizable(False, False)  # 禁止调整大小
            settings.attributes('-topmost', 1)
            # ====================================设施置顶===========================
            var = tk.IntVar(value=self.config["top_status"])

            def get_top():
                self.config["top_status"] = var.get()
                self.root.attributes('-topmost', self.config["top_status"])

            check1 = tk.Checkbutton(settings, text="置顶", font=('宋体', 15), variable=var, command=get_top)
            check1.pack()
            # ===================================下拉选择图片=============================
            var_pic = tk.StringVar()
            var_pic.set(self.config["picture_name"].split('.')[0])

            def change_pic(event):
                self.config['picture_name'] = var_pic.get() + '.gif'
                self.get_picture()

            name_list = os.listdir(self.config['path'])
            choose = tk.OptionMenu(settings, var_pic, self.config["picture_name".split('.')[0]].split('.')[0],
                                   *[item.split('.')[0] for item in name_list if item != self.config["picture_name"]],
                                   command=change_pic)
            choose.configure(font=('宋体', 15))
            choose.pack()
            # =============================================下拉选择透明色===============================
            var_col = tk.StringVar()
            var_col.set(self.config['transparent_color'])

            def change_col(event):
                self.config['transparent_color'] = var_col.get()
                self.init_transparent()

            color_list = list(self.config['color_support'].keys())
            chose = tk.OptionMenu(settings, var_col, self.config["transparent_color"],
                                  *[item for item in color_list if item != self.config["transparent_color"]],
                                  command=change_col)
            chose.configure(font=('宋体', 15))
            chose.pack()
            # =================================设置速度=================================
            var_speed = tk.IntVar(value=self.delay)
            speed = [('快', 100), ('中', 200), ('慢', 300)]

            def change_speed():
                self.delay = var_speed.get()

            for name, num in speed:
                radio_button = tk.Radiobutton(settings, text=name, variable=var_speed, value=num, command=change_speed)
                radio_button.pack()

            # ==================================恢复默认设置==============================
            def quit_settings():  # 退出保存
                self.save_settings()
                settings.destroy()

            def recover():
                if tk.messagebox.askquestion('确认操作', '确认执行此次操作吗？') == 'yes':
                    self.config = json.load(open('config.json', 'r', encoding='utf-8'))["default"]
                    self.x = self.config['x']
                    self.y = self.config['y']
                    self.init_transparent()
                    self.delay = self.config['delay']
                    self.get_picture()
                    quit_settings()

            # 使用按钮控件调用函数
            b = tk.Button(settings, text="恢复默认", command=recover)
            b.configure(font=('宋体', 15))
            b.pack()
            # ===========================关闭设置时===============================
            settings.protocol("WM_DELETE_WINDOW", quit_settings)

        # ================================= 创建右键菜单=======================
        popup = Menu(self.root, tearoff=0)  # tearoff是否禁止拖动菜单
        popup.add_command(label="设置", command=open_settings)  # 在设置菜单中设置 置顶
        popup.add_separator()
        popup.add_command(label="退出", command=self.quit)
        # 绑定Label的右键点击事件
        self.label.bind("<Button-3>", show_popup)

    def init_drag(self):
        def start_drag(event):
            self.drag_x = event.x
            self.drag_y = event.y

        def do_drag(event):
            delta_x = event.x - self.drag_x
            delta_y = event.y - self.drag_y
            x = self.x + delta_x
            y = self.y + delta_y
            self.root.geometry(f"+{x}+{y}")
            self.x = x
            self.y = y

        self.label.bind("<Button-1>", start_drag)
        self.label.bind("<B1-Motion>", do_drag)

    def update(self, i):
        picture = self.picture
        i += 1
        if i >= len(picture):
            # reached end of this animation, decide on the next animation
            self.label.configure(image=picture[0])
            self.root.after(self.delay, self.update, 0)
        else:
            self.label.configure(image=picture[i])
            self.root.after(self.delay, self.update, i)

    def run(self):
        assert self.picture is not None
        self.root.after(self.delay, self.update, 0)  # 显示的入口
        self.root.mainloop()

    def save_settings(self):
        self.config['x'] = self.x
        self.config['y'] = self.y
        content = json.load(open('config.json', 'r', encoding='utf-8'))
        content["settings"] = self.config
        with open('config.json', 'w') as f:
            json.dump(content, f, indent=4)

    def quit(self):
        self.save_settings()
        self.root.destroy()


if __name__ == '__main__':
    pad = Pad()
    pad.run()
