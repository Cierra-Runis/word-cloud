'''
WordCloud 生成你的云图
'''

from typing import Iterable
import webbrowser
import json
import logging
import sys
import tkinter
import ctypes
from tkinter import PhotoImage, font, filedialog
import os
import cv2
from wordcloud import WordCloud, ImageColorGenerator
from PIL import Image, ImageTk
import numpy as np
import jieba
import customtkinter


def select_file_dir(
    title: str,
    filetype: Iterable[tuple[str, str | list[str] | tuple[str, ...]]]
    | None = ...
) -> str:
    '''
    选择文件并返回文件地址
    '''
    root = tkinter.Tk()
    root.withdraw()
    return filedialog.askopenfilename(title=title, filetypes=filetype)


def resize(
    img: cv2.Mat,
    target_width: int,
    target_height: int,
    background_color: str,
) -> cv2.Mat:
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
    RGB = Hex_to_BGR(background_color)
    # 定位
    a = (target_width - int(original_width / ratio)) / 2
    b = (target_height - int(original_height / ratio)) / 2
    # 创建边框以达到目标图片大小
    constant = cv2.copyMakeBorder(
        shrink,
        int(b),
        int(b),
        int(a),
        int(a),
        cv2.BORDER_CONSTANT,
        value=RGB,
    )
    constant = cv2.resize(
        constant,
        (target_width, target_height),
        interpolation=cv2.INTER_AREA,
    )

    # 返回
    return constant


def Hex_to_BGR(hex: str) -> list[int]:
    '''
    将 16 进制颜色代码 如 #ff8800 转为 BGR
    '''
    hex = hex[1:]
    r = int(hex[0:2], 16)
    g = int(hex[2:4], 16)
    b = int(hex[4:6], 16)

    return [b, g, r]


def get_image(select_file_dir: str, target_width: int, target_height: int,
              background_color: str, output_filename: str):
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
                    GBR = Hex_to_BGR(background_color)
                    img[xw, yh] = [GBR[0], GBR[1], GBR[2], 255]

    # 将部分透明度不为 0 ~ 255 的图像保险转为 RGB 通道
    img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
    # 将已无透明部分传入的图片居中并不变形缩放至需要的大小，并用边框拓展
    img = resize(img, target_width, target_height, background_color)

    cv2.imwrite(DIR + output_filename, img)


def analyze_json_to_str(diary_json: list[dict], analyze_item: str,
                        exclusion_word: str) -> str:
    '''
    将所有不为 exclusion_word 的 analyze 项的内容并为长字符串
    '''
    str = ''
    for i_diary_json in diary_json:
        if (i_diary_json[analyze_item] != exclusion_word):
            str = str + i_diary_json[analyze_item] + '\n'

    return str


def jieba_processing_text(text: str):
    # 抄自 https://github.com/amueller/word_cloud/blob/master/examples/wordcloud_cn.py
    '''
    使用结巴分词进行分词
    '''

    my_word_list = []
    seg_list = jieba.cut(text, cut_all=False)
    list_str = "/ ".join(seg_list)

    with open(stop_words_path, encoding='utf-8') as f_stop:
        f_stop_text = f_stop.read()
        f_stop_seg_list = f_stop_text.splitlines()

    for my_word in list_str.split('/'):
        if not (my_word.strip()
                in f_stop_seg_list) and len(my_word.strip()) > 1:
            my_word_list.append(my_word)

    return ' '.join(my_word_list)


def txt_to_list(selected_file_dir: str) -> list[dict]:
    list = []
    with open(selected_file_dir, 'r', encoding='utf-8-sig') as f:
        for line in f.readlines():
            list.append({'content': line})
    return list


class App(customtkinter.CTk):

    # 用于存储传入图片的地址
    selected_img_dir = ''
    # 用于生成词云的 txt 或 json 文件的地址
    selected_file_dir = ''

    # 初始化

    def __init__(self):
        super().__init__()

        # 设定标题、大小、图标、透明度、居中、置顶
        self.title(APP_NAME)
        window_width = 1200
        window_height = 675
        self.resizable(height=False, width=False)
        self.fg_color = BG_COLOR
        self.configure(bg=BG_COLOR)
        self.iconbitmap(DIR + '/icon/icon.ico')
        self.attributes('-alpha', 1)
        self.geometry("%dx%d+%d+%d" % (
            window_width,
            window_height,
            int((self.winfo_screenwidth() - window_width) / 2),
            int((self.winfo_screenheight() - window_height) / 2),
        ))

        # 名称
        self.app_name = customtkinter.CTkLabel(
            master=self,
            text='　　　　' + APP_NAME,
            width=300,
            height=100,
            text_font=font.Font(family='Microsoft YaHei UI',
                                size=18,
                                weight=font.BOLD),
            fg_color=BLOCK_COLOR,
            text_color=LIGHT_GRAY_COLOR,
            corner_radius=30,
        )
        self.app_name.place(anchor='nw', x=30, y=30)

        # 图标
        self.icon = customtkinter.CTkButton(
            master=self,
            text='',
            width=90,
            height=100,
            image=PhotoImage(file=DIR + '/icon/icon.png').subsample(3, 3),
            corner_radius=0,
            fg_color=BLOCK_COLOR,
            hover_color=BLOCK_COLOR,
            command=self.button_icon_callback)
        self.icon.place(anchor='nw', x=60, y=30)

        # 设置框 #################################################################################################################################################
        self.setting_frame = customtkinter.CTkLabel(
            fg_color=BLOCK_COLOR,
            text='Setting',
            corner_radius=30,
            width=300,
            height=495,
            anchor='n',
            text_font=font.Font(
                family='Microsoft YaHei UI',
                size=20,
                weight=font.BOLD,
            ),
            text_color=LIGHT_GRAY_COLOR,
            pady=20)
        self.setting_frame.place(anchor='nw', x=30, y=155)

        # 输入目标宽度框 ###########################################################
        self.target_width_frame = customtkinter.CTkFrame(
            master=self.setting_frame,
            width=274,
            height=52,
            fg_color=DARK_BLACK_COLOR,
            corner_radius=15,
        )
        self.target_width_frame.place(x=13, y=75, anchor='nw')
        # 输入部分
        self.entry_target_width = customtkinter.CTkEntry(
            master=self.target_width_frame,
            width=154,
            height=36,
            text_font=font.Font(family='Microsoft YaHei UI',
                                size=10,
                                weight=font.NORMAL),
            fg_color=DARK_BLACK_COLOR,
            border_color=DARK_BLACK_COLOR,
            corner_radius=0,
            placeholder_text='目标宽度',
            justify='center',
        )
        self.entry_target_width.place(x=60, y=8, anchor='nw')
        # 图标部分
        self.icon_target_width = customtkinter.CTkButton(
            master=self.target_width_frame,
            text='',
            width=36,
            height=36,
            image=PhotoImage(file=DIR + '/icon/width.png'),
            corner_radius=0,
            fg_color=DARK_BLACK_COLOR,
            hover_color=DARK_BLACK_COLOR,
        )
        self.icon_target_width.place(anchor='nw', x=15, y=5)
        # 单位
        self.text_target_width = customtkinter.CTkLabel(
            master=self.target_width_frame,
            text='px',
            width=18,
            text_font=font.Font(family='Microsoft YaHei UI',
                                size=10,
                                weight=font.NORMAL),
            text_color=LIGHT_GRAY_COLOR,
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
            fg_color=DARK_BLACK_COLOR,
            corner_radius=15)
        self.target_height_frame.place(x=13, y=75 + 75, anchor='nw')
        # 输入部分
        self.entry_target_height = customtkinter.CTkEntry(
            master=self.target_height_frame,
            width=154,
            height=36,
            text_font=font.Font(family='Microsoft YaHei UI',
                                size=10,
                                weight=font.NORMAL),
            fg_color=DARK_BLACK_COLOR,
            border_color=DARK_BLACK_COLOR,
            corner_radius=0,
            placeholder_text='目标高度',
            justify='center')
        self.entry_target_height.place(x=60, y=8, anchor='nw')
        # 图标部分
        self.icon_target_height = customtkinter.CTkButton(
            master=self.target_height_frame,
            text='',
            width=36,
            height=36,
            image=PhotoImage(file=DIR + '/icon/height.png'),
            corner_radius=0,
            fg_color=DARK_BLACK_COLOR,
            hover_color=DARK_BLACK_COLOR)
        self.icon_target_height.place(anchor='nw', x=15, y=5)
        # 单位
        self.text_target_height = customtkinter.CTkLabel(
            master=self.target_height_frame,
            text='px',
            width=18,
            text_font=font.Font(family='Microsoft YaHei UI',
                                size=10,
                                weight=font.NORMAL),
            text_color=LIGHT_GRAY_COLOR,
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
            fg_color=DARK_BLACK_COLOR,
            corner_radius=15)
        self.target_color_frame.place(x=13, y=75 + 75 + 75, anchor='nw')
        # 输入部分
        self.entry_target_color = customtkinter.CTkEntry(
            master=self.target_color_frame,
            width=154,
            height=36,
            text_font=font.Font(family='Microsoft YaHei UI',
                                size=10,
                                weight=font.NORMAL),
            fg_color=DARK_BLACK_COLOR,
            border_color=DARK_BLACK_COLOR,
            corner_radius=0,
            placeholder_text='背景颜色',
            justify='center',
        )
        self.entry_target_color.place(x=60, y=8, anchor='nw')
        # 图标部分
        self.icon_target_color = customtkinter.CTkButton(
            master=self.target_color_frame,
            text='',
            width=36,
            height=36,
            image=PhotoImage(file=DIR + '/icon/color.png'),
            corner_radius=0,
            fg_color=DARK_BLACK_COLOR,
            hover_color=DARK_BLACK_COLOR)
        self.icon_target_color.place(anchor='nw', x=15, y=5)
        # 单位
        self.text_target_color = customtkinter.CTkLabel(
            master=self.target_color_frame,
            text='px',
            width=18,
            text_font=font.Font(family='Microsoft YaHei UI',
                                size=10,
                                weight=font.NORMAL),
            text_color=LIGHT_GRAY_COLOR,
        )
        self.text_target_color.place(
            anchor='nw',
            x=235,
            y=10,
        )

        # 解析模式选择框 ###########################################################
        radio_var = tkinter.IntVar(value=0)

        def radiobutton_event():
            self.entry_json_keyword.entry_focus_out()
            self.entry_json_keyword.configure(
                state=((radio_var.get() == 2) and 'normal' or 'disabled'))
            while True:
                self.selected_file_dir = ''
                self.selected_file_dir = select_file_dir(
                    title=((radio_var.get() == 2) and '请选取 json 文件'
                           or '请选取 txt 文件'),
                    filetype=((radio_var.get() == 2) and
                              (('json files', '*.json'), )
                              or (('txt files', '*.txt'), )))
                if (self.selected_file_dir != ''):
                    break
            if ((radio_var.get() == 2)
                    and (self.entry_json_keyword.get() == '解析项')):
                self.entry_json_keyword.delete(0, 3)
                self.entry_json_keyword.insert(0, '')

        self.target_mode_frame = customtkinter.CTkFrame(
            master=self.setting_frame,
            width=274,
            height=52,
            fg_color=DARK_BLACK_COLOR,
            corner_radius=15)
        self.target_mode_frame.place(x=13, y=75 + 75 + 75 + 75, anchor='nw')
        # 图标部分
        self.icon_target_mode = customtkinter.CTkButton(
            master=self.target_mode_frame,
            text='',
            width=36,
            height=36,
            image=PhotoImage(file=DIR + '/icon/mode.png'),
            corner_radius=0,
            fg_color=DARK_BLACK_COLOR,
            hover_color=DARK_BLACK_COLOR)
        self.icon_target_mode.place(anchor='nw', x=15, y=5)
        # txt 模式按钮
        self.button_txt_mode = customtkinter.CTkRadioButton(
            master=self.target_mode_frame,
            text='txt',
            command=radiobutton_event,
            variable=radio_var,
            value=1)
        self.button_txt_mode.place(anchor='nw', x=75, y=15)
        # json 模式按钮
        self.button_json_mode = customtkinter.CTkRadioButton(
            master=self.target_mode_frame,
            text='json',
            command=radiobutton_event,
            variable=radio_var,
            value=2)
        self.button_json_mode.place(anchor='nw', x=135, y=15)
        # 解析项输入框
        self.entry_json_keyword = customtkinter.CTkEntry(
            master=self.target_mode_frame,
            width=80,
            height=36,
            text_font=font.Font(family='Microsoft YaHei UI',
                                size=10,
                                weight=font.NORMAL),
            fg_color=DARK_BLACK_COLOR,
            border_color=DARK_BLACK_COLOR,
            corner_radius=0,
            placeholder_text='解析项',
            justify='center')
        self.entry_json_keyword.configure(state='disabled')
        self.entry_json_keyword.place(x=190, y=8, anchor='nw')

        # 预览框 #################################################################################################################################################
        self.preview_frame = customtkinter.CTkLabel(
            fg_color=BLOCK_COLOR,
            text='Preview',
            corner_radius=30,
            width=815,
            height=620,
            anchor='n',
            text_font=font.Font(family='Microsoft YaHei UI',
                                size=20,
                                weight=font.BOLD),
            text_color=LIGHT_GRAY_COLOR,
            pady=30)
        self.preview_frame.place(anchor='nw', x=360, y=30)
        self.preview_image = customtkinter.CTkButton(
            text='',
            width=755,
            height=490,
            corner_radius=30,
            fg_color=DARK_BLACK_COLOR,
            hover_color=DARK_BLACK_COLOR,
            bg_color=BLOCK_COLOR,
        )
        self.preview_image.place(anchor='nw', x=390, y=130)

        # 选取按钮
        self.button_select = customtkinter.CTkButton(
            master=self,
            text='',
            width=50,
            height=50,
            corner_radius=25,
            bg_color=DARK_BLACK_COLOR,
            fg_color=LIGHT_GRAY_COLOR,
            hover_color=DARK_GRAY_COLOR,
            command=self.button_select_callback,
            image=PhotoImage(file=DIR + '/icon/select.png'),
        )
        self.button_select.place(anchor='nw', x=1000, y=555)

        # 生成按钮
        self.button_generate = customtkinter.CTkButton(
            master=self,
            text='',
            width=50,
            height=50,
            corner_radius=25,
            bg_color=DARK_BLACK_COLOR,
            fg_color=LIGHT_GRAY_COLOR,
            hover_color=DARK_GRAY_COLOR,
            command=self.button_generate_callback,
            image=PhotoImage(file=DIR + '/icon/generate.png'),
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
            self.selected_img_dir = select_file_dir(
                title='请选取图片',
                filetype=(('jpg files', '*.jpg'), ('png files', '*.png')),
            )
            if (self.selected_img_dir != ''):
                break

        try:
            # 将选取文件放至预览框
            self.preview_image.configure(image=None)
            get_image(self.selected_img_dir, 430, 430, DARK_BLACK_COLOR,
                      '/temp.png')
            self.preview_image.configure(image=ImageTk.PhotoImage(file=DIR +
                                                                  '/temp.png'),
                                         fg_color=DARK_BLACK_COLOR,
                                         hover_color=DARK_BLACK_COLOR)
            self.button_generate.configure(bg_color=DARK_BLACK_COLOR, )
            self.button_select.configure(bg_color=DARK_BLACK_COLOR, )
        except AttributeError:
            self.button_select_callback()

    def button_generate_callback(self):

        # 防止未选择图片
        if (self.selected_img_dir == ''):
            self.button_select_callback()

        # 防止未选择解析文件
        if (self.selected_file_dir == ''):
            self.button_txt_mode.invoke()

        # 获取目标宽度、高度、背景颜色
        target_width = int(self.entry_target_width.get())
        target_height = int(self.entry_target_height.get())
        background_color = self.entry_target_color.get()

        # 读取所有文本
        if (self.button_json_mode.check_state):
            # 当是 json 解析模式时
            selected_json = json.loads(
                open(self.selected_file_dir, 'r', encoding='utf-8-sig').read())
            text = jieba_processing_text(
                analyze_json_to_str(selected_json,
                                    self.entry_json_keyword.get(), 'deleted'))
        else:
            # 当是 txt 解析模式时
            with open('temp.json', 'w', encoding='utf-8-sig') as f:
                f.write(
                    json.dumps(txt_to_list(self.selected_file_dir),
                               ensure_ascii=False))
            selected_json = json.loads(
                open('temp.json', 'r', encoding='utf-8-sig').read())
            text = jieba_processing_text(
                analyze_json_to_str(selected_json, 'content', 'deleted'))
            os.remove(DIR + '/temp.json')

        get_image(self.selected_img_dir, target_width, target_height,
                  background_color, '/temp.png')

        get_image(DIR + '/temp.png', target_width, target_height,
                  background_color, '/temp.png')

        mask = np.array(Image.open(DIR + '/temp.png'))
        wc = WordCloud(font_path=font_path,
                       background_color=background_color,
                       max_words=2000,
                       mask=mask,
                       max_font_size=100,
                       min_font_size=12,
                       random_state=20,
                       width=target_width,
                       height=target_height,
                       color_func=ImageColorGenerator(mask),
                       margin=2,
                       collocations=False)

        wc.generate(text)
        wc.to_file(DIR + '/generated.png')
        wordcloud_svg = wc.to_svg(embed_font=True)
        with open(DIR + '/generated.svg', "w", encoding="utf-8") as svg:
            svg.write(wordcloud_svg)

        self.preview_image.configure(image=None)
        get_image(DIR + '/generated.png', 430, 430, background_color,
                  '/temp.png')
        self.preview_image.configure(
            image=ImageTk.PhotoImage(file=DIR + '/temp.png'),
            fg_color=background_color,
            hover_color=background_color,
        )
        self.button_generate.configure(bg_color=background_color, )
        self.button_select.configure(bg_color=background_color, )
        os.remove(DIR + '/temp.png')


if __name__ == '__main__':

    # 所在地址
    DIR = os.path.dirname(sys.argv[0])

    # 常量
    APP_NAME = 'WordCloud'
    BG_COLOR = '#282C34'
    BLOCK_COLOR = '#37373F'
    LIGHT_GRAY_COLOR = '#DCDCDC'
    DARK_GRAY_COLOR = '#A5A5A5'
    DARK_BLACK_COLOR = '#1F1F1F'
    PLACEHOLDER_GRAY_COLOR = '#9E9E9E'

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
