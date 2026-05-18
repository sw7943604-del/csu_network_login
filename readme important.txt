使用方法:
  1. 进入代码修改python的 USERNAME 和 PASSWORD
  
2. python campus_network_login.py或者直接配置开机自启动按 Win + R 键，输入 shell:startup 回车。

把保存好的 run_wifi.vbs 文件或者快捷方式放进弹出的「启动」文件夹里。

现在你可以双击运行一下这个 .vbs 文件。因为加了 vbhide，双击后屏幕上什么都不会弹出来，但你可以断开一下网页认证，或者直接打开任务管理器（Ctrl + Shift + Esc），看看进程里有没有

个 Python 正在后台默默守护你的网络了。
  
3. 保持窗口运行即可 (Ctrl+C 退出)

""" 1. 如果你用的是 校园电信：

USERNAME = "12345678@dx"
PASSWORD = "你的密码"
2. 如果你用的是 校园联通：

USERNAME = "12345678@lt"
PASSWORD = "你的密码"
3. 如果你用的是 校园移动：
通常是加 @cmccn（或者是根据你学校网页上选择“校园移动”后，输入框里自动帮你补全的后缀为准）：

USERNAME = "12345678@cmccn"
PASSWORD = "你的密码"
4. 如果你用的是 纯校园网用户（不走运营商，只上内网或学校免流）：
那就不需要加任何后缀，只填学号：

Python
USERNAME = "12345678"
PASSWORD = "你的密码"
"""