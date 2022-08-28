import json
import logging
import sys
import jieba
import os
import customtkinter
import cv2
import tkinter
import numpy as np
from tkinter import Button, filedialog, colorchooser
from wordcloud import WordCloud, ImageColorGenerator
from PIL import Image


def select_file_dir():

    root = tkinter.Tk()
    root.withdraw()

    return filedialog.askopenfilename()


def pop_deleted_and_all_to_str(diary_json):
    # 将所有不为 deleted 的内容并为长字符串
    # 字典列表 -> 字符串
    str = ''
    for i_diary_json in diary_json:
        if(i_diary_json['Content'] != 'deleted'):
            str = str + i_diary_json['Content'] + '\n'

    return str


def jieba_processing_txt(text):
    # 照抄
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


def resize_image(image, height, width):
    top, bottom, left, right = (0, 0, 0, 0)

    # 获取图像尺寸
    h, w, _ = image.shape

    # 对于长宽不相等的图片，找到最长的一边
    longest_edge = max(h, w)

    # 计算短边需要增加多上像素宽度使其与长边等长
    if h < longest_edge:
        dh = longest_edge - h
        top = dh // 2
        bottom = dh - top
    elif w < longest_edge:
        dw = longest_edge - w
        left = dw // 2
        right = dw - left
    else:
        pass

    # RGB颜色
    BLACK = [0, 0, 0]

    # 给图像增加边界，是图片长、宽等长，cv2.BORDER_CONSTANT指定边界颜色由value指定
    constant = cv2.copyMakeBorder(
        image, top, bottom, left, right, cv2.BORDER_CONSTANT, value=BLACK)

    # 调整图像大小并返回
    return cv2.resize(constant, (height, width))


class App(customtkinter.CTk):

    setting_info = ['', '#123456', 2000, 2000]

    def __init__(self):
        super().__init__()
        self.title('配置输出')
        self.minsize(300, 200)

        self.button_select_pic = customtkinter.CTkButton(
            master=self, text='选取地址', command=self.button_select_pic_callback)
        self.button_select_pic.place(relx=0.5, rely=0.1, anchor=tkinter.CENTER)

        self.button_confirm = customtkinter.CTkButton(
            master=self, text='确认', command=self.button_confirm_callback)
        self.button_confirm.place(relx=0.5, rely=0.9, anchor=tkinter.CENTER)

    def button_select_pic_callback(self):
        # 防止为空
        while True:
            self.setting_info[0] = select_file_dir()
            print(self.setting_info[0])
            if(self.setting_info[0] != ''):
                break

    def button_confirm_callback(self):
        if self.setting_info[0] == '':
            self.button_select_pic_callback()
        mask = np.array(
            resize_image(Image.open(self.setting_info[0]), (width, height), background_color))
        print('1')
        background_color = self.setting_info[1]
        print('2')
        width = self.setting_info[2]
        print('3')
        height = self.setting_info[3]
        print('4')
        # 读取所有文本
        diary_json = json.loads(
            open(DIR+'/exportDiary.json', 'r', encoding='utf-8-sig').read())
        text = jieba_processing_txt(pop_deleted_and_all_to_str(diary_json))
        # 使用 WordCloud
        wc = WordCloud(font_path=font_path,
                       background_color=background_color,
                       max_words=2000,
                       mask=mask,
                       max_font_size=100,
                       random_state=40,
                       width=width,
                       height=height,
                       color_func=ImageColorGenerator(mask),
                       margin=2,
                       )

        # 生成并导出
        wc.generate(text)
        wc.to_file(DIR+'/output.png')

        # 结束程序
        quit()


if __name__ == '__main__':
    # 所在地址
    DIR = os.path.dirname(sys.argv[0])

    # 加载讯飞输入法导出的用户词典，并删去其中的单字与部分短句
    jieba.setLogLevel(logging.INFO)
    jieba.load_userdict(DIR + '/user_dict.txt')
    # 搞不懂，内容为空
    stop_words_path = DIR + '/stop_words.txt'
    # 苹方字体
    font_path = DIR + '/Apple.ttc'

    # 使用 tkinter 返回遮罩图片地址、自定义背景色、输出图片大小
    App().mainloop()
