# sender.py
import os

flag_file = "notify.flag"

# 创建/更新文件（表示数据变更）
with open(flag_file, "w") as f:
    f.write("1")  # 内容不重要，文件变化即可
print("程序A：已发送通知")