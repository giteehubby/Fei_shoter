import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 飞书相关配置
    FEISHU_EMAIL = os.getenv('FEISHU_EMAIL', '')
    FEISHU_PASSWORD = os.getenv('FEISHU_PASSWORD', '')
    
    # 小红书相关配置
    XIAOHONGSHU_USERNAME = os.getenv('XIAOHONGSHU_USERNAME', '')
    XIAOHONGSHU_PASSWORD = os.getenv('XIAOHONGSHU_PASSWORD', '')
    
    # 大模型API配置
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    
    # 截图配置
    SCREENSHOT_WIDTH = 1080  # 截图宽度
    SCREENSHOT_HEIGHT = 1920  # 截图高度（小红书推荐比例）
    SCROLL_OVERLAP = 0.2  # 滚动重叠比例
    
    # 浏览器配置
    BROWSER_HEADLESS = False  # 是否无头模式
    BROWSER_TIMEOUT = 30  # 浏览器超时时间
    
    # 文件路径配置
    SCREENSHOT_DIR = 'screenshots'
    OUTPUT_DIR = 'output'
    
    # 小红书文案配置
    MAX_TITLE_LENGTH = 50  # 标题最大长度
    MAX_CONTENT_LENGTH = 1000  # 内容最大长度 