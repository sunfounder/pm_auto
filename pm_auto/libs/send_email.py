import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

def send_email(receiver_email, subject, body, attachment_path=None, config=None):
    """
    使用配置字典发送邮件
    
    参数:
    receiver_email: 收件人邮箱地址
    subject: 邮件主题
    body: 邮件正文
    attachment_path: 附件路径(可选)
    config: 邮件配置字典(可选，默认使用全局配置)
    """
    # 使用传入的配置或全局配置
    if config is None:
        config = DEFAULT_CONFIG
    
    # 创建邮件对象
    message = MIMEMultipart()
    message["From"] = config.get("sender_email", "noreply@localhost")
    message["To"] = receiver_email
    message["Subject"] = subject
    
    # 添加邮件正文
    message.attach(MIMEText(body, "plain"))
    
    # 添加附件(如果有)
    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
        
        # 编码附件并添加头信息
        encoders.encode_base64(part)
        filename = os.path.basename(attachment_path)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {filename}",
        )
        message.attach(part)
    
    # 连接到SMTP服务器并发送邮件
    try:
        # 创建SMTP连接
        if config.get("smtp_port") == 465:  # SMTP over SSL (port 465)
            server = smtplib.SMTP_SSL(
                config.get("smtp_server", "localhost"),
                config.get("smtp_port", 25)
            )
        else:
            server = smtplib.SMTP(
                config.get("smtp_server", "localhost"),
                config.get("smtp_port", 25)
            )
            
            # 如果启用TLS，启动TLS加密
            if config.get("use_tls", False):
                server.starttls()
        
        # 如果提供了密码，进行登录认证
        if config.get("sender_password"):
            server.login(
                config.get("sender_email", ""),
                config.get("sender_password", "")
            )
        
        # 发送邮件
        text = message.as_string()
        server.sendmail(message["From"], receiver_email, text)
        server.quit()
        print("邮件发送成功!")
        return True
    except Exception as e:
        print(f"邮件发送失败: {str(e)}")
        return False

# 默认配置字典 - 本地SMTP服务
DEFAULT_CONFIG = {
    "sender_email": "noreply@localhost",
    "sender_password": "",
    "smtp_server": "localhost",
    "smtp_port": 25,
    "use_tls": False
}

# Gmail配置示例
GMAIL_CONFIG = {
    "sender_email": "your_email@gmail.com",
    "sender_password": "your_app_password",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "use_tls": True
}

# QQ邮箱配置示例
QQMAIL_CONFIG = {
    "sender_email": "your_email@qq.com",
    "sender_password": "your_qq_smtp_password",
    "smtp_server": "smtp.qq.com",
    "smtp_port": 465,
    "use_tls": False  # 465端口使用SSL，不需要TLS
}

if __name__ == "__main__":
    # 配置收件人信息
    receiver_email = "recipient_email@example.com"
    
    # 邮件内容
    subject = "来自树莓派的邮件"
    body = "这是一封测试邮件。\n\n祝好,\n树莓派"
    
    # 附件路径(可选)
    attachment_path = None
    
    # 示例1: 使用本地SMTP服务(默认配置)
    send_email(receiver_email, subject, body, attachment_path)
    
    # 示例2: 使用Gmail SMTP服务
    # send_email(
    #     receiver_email=receiver_email,
    #     subject=subject,
    #     body=body,
    #     attachment_path=attachment_path,
    #     config=GMAIL_CONFIG
    # )
    
    # 示例3: 使用QQ邮箱SMTP服务
    # send_email(
    #     receiver_email=receiver_email,
    #     subject=subject,
    #     body=body,
    #     attachment_path=attachment_path,
    #     config=QQMAIL_CONFIG
    # )    