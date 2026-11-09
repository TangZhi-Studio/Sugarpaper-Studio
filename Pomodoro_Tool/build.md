# 番茄钟工具 EXE打包说明
依赖库：PyQt5

打包命令：
```bash
pyinstaller --clean --hidden-import PyQt5.QtCore --hidden-import PyQt5.QtGui --hidden-import PyQt5.QtWidgets pomodoro.py
⚠️[非常重要]
严禁使用 -F 单文件参数！ PyQt 程序使用单文件模式极易闪退、启动失败。

打包输出目录为 dist/pomodoro，文件夹内所有 .dll、.pyd 文件不可以删除，删除程序无法运行。

对外分发程序：将整个 dist/pomodoro 文件夹压缩为 zip 压缩包。

exe、dll、dist、build 产物不要上传到代码仓库，编译包放到 GitHub Releases 页面发布。

打包前确认已经安装依赖：pip install pyqt5