<div align="center">
  <img id="word-cloud" width="64" alt="word-cloud" src="icon/icon.ico">
  <p>「 WordCloud - 生成你的词云！」</p>
</div>

<br>

[📚 功能](#功能)

[📦 安装](#安装)

[⚠️ 注意事项](#注意事项)

[🧑‍💻 开发者](#开发者)

[🔏 隐私声明](#隐私声明)

# 功能

本软件基于 [词云生成器](https://github.com/amueller/word_cloud) 、 [结巴分词](https://github.com/fxsjy/jieba) 以及 [CustomTkinter UI库](https://github.com/TomSchimansky/CustomTkinter) 读取 txt 文件或解析 json 文件以生成你想要的词云

# 安装

【暂未发布任何版本】

# 注意事项

已知的问题：

- 不能选取中文路径下的图片，请移动文件或修改图片名称以保证不含有中文字符
- txt 解析模式下不能完全读取 txt 文本内容，若需要完全读取请转化为 json 文件（预定解决方案即将 txt 文件以行创建 temp.json 文件再解析 json 文件）
- 部分情况下 WordCloud 库函数会将背景色视作图片本身的颜色，以至于部分文字跑去当背景了
- 在 背景颜色 栏中若使用中文输入法会有很奇怪的 bug （比如文字不显示、删不动等），请在输入前切换至英文输入法以避免该问题

# 开发者

<a href="https://github.com/Cierra-Runis/word-cloud/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=Cierra-Runis/word-cloud" />
</a>

# 隐私声明

本软件无需联网，不会上传任何用户信息
