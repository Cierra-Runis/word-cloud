import webbrowser
import cv2
import json
import logging
import sys
import jieba
import os
import customtkinter
import tkinter
import ctypes
import numpy as np
from tkinter import PhotoImage, font, filedialog
from wordcloud import WordCloud, ImageColorGenerator
from PIL import Image, ImageTk


def select_file_dir() -> str:
    '''
    选择文件并返回文件地址
    '''
    root = tkinter.Tk()
    root.withdraw()
    return filedialog.askopenfilename()


def resize(img: cv2.Mat, target_width: int, target_height: int, background_color: str) -> cv2.Mat:
    '''
    将已无透明部分传入的图片居中并不变形缩放至需要的大小，并用边框拓展
    '''
    # 获取原先图片的高度和宽度
    original_height, original_width = img.shape[:2]

    # 计算长宽缩放比例并取大的一方
    ratio_h = original_height / target_height
    ration_w = original_width / target_width
    ratio = max(ratio_h, ration_w)

    # size 是不变形缩放后的图片大小
    size = (int(original_width / ratio), int(original_height / ratio))
    # 缩放
    shrink = cv2.resize(img, size, interpolation=cv2.INTER_AREA)

    # 获取边框颜色
    RGB = Hex_to_RGB(background_color)
    # 定位
    a = (target_width - int(original_width / ratio)) / 2
    b = (target_height - int(original_height / ratio)) / 2
    # 创建边框以达到目标图片大小
    constant = cv2.copyMakeBorder(
        shrink, int(b), int(b), int(a), int(a), cv2.BORDER_CONSTANT, value=RGB
    )
    constant = cv2.resize(
        constant, (target_width, target_height), interpolation=cv2.INTER_AREA
    )

    # 返回
    return constant


def Hex_to_RGB(hex: str) -> list[int]:
    '''
    将 16 进制颜色代码 如 #ff8800 转为 BGR
    '''
    hex = hex[1:]
    r = int(hex[0:2], 16)
    g = int(hex[2:4], 16)
    b = int(hex[4:6], 16)

    return [r, g, b]


def get_image(select_file_dir: str, target_width: int, target_height: int, background_color: str, output_filename: str):
    '''
    将所选的图片拓展后保存至根目录
    '''
    # 读取传入图片
    img = cv2.imread(select_file_dir, cv2.IMREAD_UNCHANGED)

    # 若是透明图像 RGBA ，则需要转为 RGB ，并将不透明部分改为背景色
    if img.shape[2] == 4:
        img = cv2.imread(select_file_dir, cv2.IMREAD_UNCHANGED)
        # 获取传入图片宽度、高度
        width = img.shape[0]
        height = img.shape[1]
        for yh in range(height):
            for xw in range(width):
                # 遍历图像每一个点，获取到每个点 4 通道的颜色数据
                color_d = img[xw, yh]
                # 最后一个通道为透明度，如果其值为 0 ，即图像是透明的话
                if (color_d[3] == 0):
                    # 则将当前点的颜色设置为背景色，且图像设置为不透明
                    RGB = Hex_to_RGB(background_color)
                    img[xw, yh] = [RGB[0], RGB[1], RGB[2], 255]

    # 将部分透明度不为 0 ~ 255 的图像保险转为 RGB 通道
    img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
    # 将已无透明部分传入的图片居中并不变形缩放至需要的大小，并用边框拓展
    img = resize(img, target_width, target_height, background_color)

    cv2.imwrite(DIR+output_filename, img)


def pop_deleted_and_all_to_str(diary_json: list[dict]) -> str:
    '''
    将所有不为 deleted 的内容并为长字符串
    '''
    str = ''
    for i_diary_json in diary_json:
        if(i_diary_json['Content'] != 'deleted'):
            str = str + i_diary_json['Content'] + '\n'

    return str


def jieba_processing_txt(text):
    '''
    抄自
    '''
    my_word_list = []
    seg_list = jieba.cut(text, cut_all=False)
    list_str = "/ ".join(seg_list)

    with open(stop_words_path, encoding='utf-8') as f_stop:
        f_stop_text = f_stop.read()
        f_stop_seg_list = f_stop_text.splitlines()

    for my_word in list_str.split('/'):
        if not (my_word.strip() in f_stop_seg_list) and len(my_word.strip()) > 1:
            my_word_list.append(my_word)

    return ' '.join(my_word_list)


class App(customtkinter.CTk):

    # 用于存储传入图片的地址
    dir = ''

    # 初始化
    def __init__(self):
        super().__init__()

        # 设定标题、大小、图标、透明度、居中、置顶
        self.title('WordCloud')
        window_width = 1200
        window_height = 675
        self.resizable(height=False, width=False)
        self.fg_color = "#282C34"
        self.configure(bg='#282C34')
        self.iconbitmap(DIR+'/icon/icon.ico')
        self.attributes('-alpha', 1)
        self.geometry(
            "%dx%d+%d+%d" % (
                window_width,
                window_height,
                int((self.winfo_screenwidth()-window_width)/2),
                int((self.winfo_screenheight()-window_height)/2)
            )
        )

        # 名称
        self.app_name = customtkinter.CTkLabel(
            master=self,
            text='　　　　WordCloud',
            width=300,
            height=100,
            text_font=font.Font(
                family='Microsoft YaHei UI',
                size=18,
                weight=font.BOLD
            ),
            fg_color='#37373F',
            text_color='#DCDCDC',
            corner_radius=30
        )
        self.app_name.place(
            anchor='nw',
            x=30,
            y=30
        )

        # 图标
        self.icon = customtkinter.CTkButton(
            master=self,
            text='',
            width=90,
            height=100,
            image=PhotoImage(file=DIR+'/icon/icon.png').subsample(3, 3),
            corner_radius=0,
            fg_color="#37373F",
            hover_color="#37373F",
            command=self.button_icon_callback
        )
        self.icon.place(
            anchor='nw',
            x=60,
            y=30
        )

        # 设置框 #################################################################################################################################################
        self.setting_frame = customtkinter.CTkLabel(
            fg_color='#37373F',
            text='Setting',
            corner_radius=30,
            width=300,
            height=495,
            anchor='n',
            text_font=font.Font(
                family='Microsoft YaHei UI',
                size=20,
                weight=font.BOLD
            ),
            text_color='#DCDCDC',
            pady=20
        )
        self.setting_frame.place(
            anchor='nw',
            x=30,
            y=155
        )

        # 输入目标宽度框 ###########################################################
        self.target_width_frame = customtkinter.CTkFrame(
            master=self.setting_frame,
            width=274,
            height=52,
            fg_color='#1F1F1F',
            corner_radius=15
        )
        self.target_width_frame.place(
            x=13,
            y=75,
            anchor='nw'
        )
        # 输入部分
        self.entry_target_width = customtkinter.CTkEntry(
            master=self.target_width_frame,
            width=154,
            height=36,
            text_font=font.Font(
                family='Microsoft YaHei UI',
                size=10,
                weight=font.NORMAL
            ),
            fg_color='#1F1F1F',
            border_color='#1F1F1F',
            corner_radius=0,
            placeholder_text='目标宽度',
            justify='center',
        )
        self.entry_target_width.place(
            x=60,
            y=8,
            anchor='nw'
        )
        # 图标部分
        self.icon_target_width = customtkinter.CTkButton(
            master=self.target_width_frame,
            text='',
            width=36,
            height=36,
            image=PhotoImage(file=DIR+'/icon/width.png'),
            corner_radius=0,
            fg_color="#1F1F1F",
            hover_color="#1F1F1F"
        )
        self.icon_target_width.place(
            anchor='nw',
            x=15,
            y=5
        )
        # 单位
        self.text_target_width = customtkinter.CTkLabel(
            master=self.target_width_frame,
            text='px',
            width=18,
            text_font=font.Font(
                family='Microsoft YaHei UI',
                size=10,
                weight=font.NORMAL
            ),
            text_color='#DCDCDC',
        )
        self.text_target_width.place(
            anchor='nw',
            x=235,
            y=10,
        )

        # 输入目标长度框 ###########################################################
        self.target_height_frame = customtkinter.CTkFrame(
            master=self.setting_frame,
            width=274,
            height=52,
            fg_color='#1F1F1F',
            corner_radius=15
        )
        self.target_height_frame.place(
            x=13,
            y=75+75,
            anchor='nw'
        )
        # 输入部分
        self.entry_target_height = customtkinter.CTkEntry(
            master=self.target_height_frame,
            width=154,
            height=36,
            text_font=font.Font(
                family='Microsoft YaHei UI',
                size=10,
                weight=font.NORMAL
            ),
            fg_color='#1F1F1F',
            border_color='#1F1F1F',
            corner_radius=0,
            placeholder_text='目标高度',
            justify='center'
        )
        self.entry_target_height.place(
            x=60,
            y=8,
            anchor='nw'
        )
        # 图标部分
        self.icon_target_height = customtkinter.CTkButton(
            master=self.target_height_frame,
            text='',
            width=36,
            height=36,
            image=PhotoImage(file=DIR+'/icon/height.png'),
            corner_radius=0,
            fg_color="#1F1F1F",
            hover_color="#1F1F1F"
        )
        self.icon_target_height.place(
            anchor='nw',
            x=15,
            y=5
        )
        # 单位
        self.text_target_height = customtkinter.CTkLabel(
            master=self.target_height_frame,
            text='px',
            width=18,
            text_font=font.Font(
                family='Microsoft YaHei UI',
                size=10,
                weight=font.NORMAL
            ),
            text_color='#DCDCDC',
        )
        self.text_target_height.place(
            anchor='nw',
            x=235,
            y=10,
        )

        # 输入目标背景色框 ###########################################################
        self.target_color_frame = customtkinter.CTkFrame(
            master=self.setting_frame,
            width=274,
            height=52,
            fg_color='#1F1F1F',
            corner_radius=15
        )
        self.target_color_frame.place(
            x=13,
            y=75+75+75,
            anchor='nw'
        )
        # 输入部分
        self.entry_target_color = customtkinter.CTkEntry(
            master=self.target_color_frame,
            width=154,
            height=36,
            text_font=font.Font(
                family='Microsoft YaHei UI',
                size=10,
                weight=font.NORMAL
            ),
            fg_color='#1F1F1F',
            border_color='#1F1F1F',
            corner_radius=0,
            placeholder_text='背景颜色',
            justify='center',
        )
        self.entry_target_color.place(
            x=60,
            y=8,
            anchor='nw'
        )
        # 图标部分
        self.icon_target_color = customtkinter.CTkButton(
            master=self.target_color_frame,
            text='',
            width=36,
            height=36,
            image=PhotoImage(file=DIR+'/icon/color.png'),
            corner_radius=0,
            fg_color="#1F1F1F",
            hover_color="#1F1F1F"
        )
        self.icon_target_color.place(
            anchor='nw',
            x=15,
            y=5
        )
        # 单位
        self.text_target_color = customtkinter.CTkLabel(
            master=self.target_color_frame,
            text='px',
            width=18,
            text_font=font.Font(
                family='Microsoft YaHei UI',
                size=10,
                weight=font.NORMAL
            ),
            text_color='#DCDCDC',
        )
        self.text_target_color.place(
            anchor='nw',
            x=235,
            y=10,
        )

        # 预览框 #################################################################################################################################################
        self.preview_frame = customtkinter.CTkLabel(
            fg_color='#21252B',
            text='Preview',
            corner_radius=30,
            width=815,
            height=620,
            anchor='n',
            text_font=font.Font(
                family='Microsoft YaHei UI',
                size=20,
                weight=font.BOLD
            ),
            text_color='#DCDCDC',
            pady=30
        )
        self.preview_frame.place(
            anchor='nw',
            x=360,
            y=30
        )
        self.preview_image = customtkinter.CTkButton(
            text='',
            width=755,
            height=490,
            corner_radius=30,
            fg_color='#1F1F1F',
            hover_color="#1F1F1F",
            bg_color='#21252B',
        )
        self.preview_image.place(
            anchor='nw',
            x=390,
            y=130
        )

        # 选取按钮
        self.button_select = customtkinter.CTkButton(
            master=self,
            text='',
            width=50,
            height=50,
            corner_radius=25,
            bg_color='#1F1F1F',
            fg_color='#DCDCDC',
            hover_color='#A5A5A5',
            command=self.button_select_callback,
            image=PhotoImage(file=DIR+'/icon/select.png'),
        )
        self.button_select.place(
            anchor='nw',
            x=1000,
            y=555
        )

        # 生成按钮
        self.button_generate = customtkinter.CTkButton(
            master=self,
            text='',
            width=50,
            height=50,
            corner_radius=25,
            bg_color='#1F1F1F',
            fg_color='#DCDCDC',
            hover_color='#A5A5A5',
            command=self.button_generate_callback,
            image=PhotoImage(file=DIR+'/icon/generate.png'),
        )
        self.button_generate.place(
            anchor='nw',
            x=1080,
            y=555,
        )

    def button_icon_callback(self):
        webbrowser.open_new_tab('https://github.com/Cierra-Runis/word-cloud')

    def button_select_callback(self):
        # 防止为空
        while True:
            self.dir = select_file_dir()
            if(self.dir != ''):
                break

        # 将选取文件放至预览框
        self.preview_image.configure(image=None)
        get_image(self.dir, 430, 430, '#1F1F1F', '/temp.png')
        self.preview_image.configure(
            image=ImageTk.PhotoImage(file=DIR+'/temp.png'),
            fg_color='#1F1F1F',
            hover_color='#1F1F1F'
        )

    def button_generate_callback(self):

        target_width = int(self.entry_target_width.get())
        target_height = int(self.entry_target_height.get())
        background_color = self.entry_target_color.get()

        # 读取所有文本
        diary_json = json.loads(
            open(DIR+'/exportDiary.json', 'r', encoding='utf-8-sig').read()
        )
        text = jieba_processing_txt(
            pop_deleted_and_all_to_str(diary_json)
        )

        get_image(
            self.dir,
            target_width,
            target_height,
            background_color,
            '/temp.png'
        )

        get_image(
            DIR+'/temp.png',
            target_width,
            target_height,
            background_color,
            '/temp.png'
        )

        mask = np.array(Image.open(DIR+'/temp.png'))
        wc = WordCloud(
            font_path=font_path,
            background_color=background_color,
            max_words=2000,
            mask=mask,
            max_font_size=100,
            random_state=20,
            width=target_width,
            height=target_height,
            color_func=ImageColorGenerator(mask),
            margin=2,
            collocations=False
        )

        wc.generate(text)
        wc.to_file(DIR+'/generated.png')
        wordcloud_svg = wc.to_svg(embed_font=True)
        with open(DIR+'/generated.svg', "w", encoding="utf-8") as svg:
            svg.write(wordcloud_svg)

        self.preview_image.configure(image=None)
        get_image(DIR+'/generated.png', 430, 430,
                  background_color, '/temp.png')
        self.preview_image.configure(
            image=ImageTk.PhotoImage(file=DIR+'/temp.png'),
            fg_color=background_color,
            hover_color=background_color,
        )
        self.button_generate.configure(
            bg_color=background_color,
        )
        self.button_select.configure(
            bg_color=background_color,
        )
        os.remove(DIR+'/temp.png')


if __name__ == '__main__':

    # 所在地址
    DIR = os.path.dirname(sys.argv[0])

    # 加载讯飞输入法导出的用户词典，并删去其中的单字、部分短句、形容词
    jieba.setLogLevel(logging.INFO)
    jieba.load_userdict(DIR + '/user_dict.txt')

    # 屏蔽词
    stop_words_path = DIR + '/stop_words.txt'

    # 苹方字体
    font_path = DIR + '/Apple.ttf'

    # appid
    my_appid = 'pers.cierra_runis.wordcloud'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(my_appid)

    # 使用 tkinter 返回遮罩图片地址、自定义背景色、输出图片大小
    App().mainloop()
