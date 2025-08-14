#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书笔记转小红书图文工具
功能：
1. 自动截图飞书笔记
2. 生成小红书文案
3. 发布到小红书平台
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from feishu_screenshot import FeishuScreenshot
from ai_summary import AISummary
from xiaohongshu_poster import XiaohongshuPoster
from config import Config

class FeishuToXiaohongshu:
    def __init__(self):
        self.config = Config()
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志"""
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"feishu_to_xiaohongshu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def validate_config(self):
        """验证配置"""
        required_configs = [
            ('FEISHU_EMAIL', self.config.FEISHU_EMAIL),
            ('FEISHU_PASSWORD', self.config.FEISHU_PASSWORD),
        ]
        
        missing_configs = []
        for name, value in required_configs:
            if not value:
                missing_configs.append(name)
        
        if missing_configs:
            self.logger.error(f"缺少必要的配置: {', '.join(missing_configs)}")
            self.logger.error("请在 .env 文件中设置这些配置项")
            return False
            
        return True
    
    def process_note(self, note_url, auto_publish=False, use_ai=True):
        """处理单个飞书笔记"""
        try:
            self.logger.info(f"开始处理飞书笔记: {note_url}")
            
            # 1. 截图飞书笔记
            self.logger.info("步骤1: 开始截图飞书笔记...")
            feishu_screenshot = FeishuScreenshot()
            screenshot_files, title = feishu_screenshot.take_full_screenshot(note_url)
            
            if not screenshot_files:
                self.logger.error("截图失败")
                return False
            
            self.logger.info(f"截图完成，共 {len(screenshot_files)} 张图片")
            

            
            # 2. 生成小红书文案
            self.logger.info("步骤2: 生成小红书文案...")
            ai_summary = AISummary()
            
            if use_ai and self.config.OPENAI_API_KEY:
                # 获取笔记内容用于AI生成
                content = feishu_screenshot.get_note_content()
                self.logger.info(f'笔记长度：{len(content)}， 内容: {content}')
                summary_result = ai_summary.generate_summary(content)
                
                post_title = summary_result['title']
                post_content = summary_result['content']
                post_topics = summary_result['topics']
                
                # 可选：进一步优化内容
                post_content = ai_summary.enhance_content(post_content)
                
            else:
                # 使用简单处理
                post_title = title[:self.config.MAX_TITLE_LENGTH] if len(title) > self.config.MAX_TITLE_LENGTH else title
                post_content = "分享一篇有用的飞书笔记内容"
                post_topics = ["#飞书笔记", "#知识分享", "#学习笔记"]
            
            self.logger.info(f"文案生成完成")
            self.logger.info(f"标题: {post_title}")
            self.logger.info(f"话题: {', '.join(post_topics)}")
            
            # 3. 保存草稿
            draft_file = os.path.join(self.config.OUTPUT_DIR, f"draft_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            poster = XiaohongshuPoster()
            poster.save_post_draft(screenshot_files, post_title, post_content, post_topics, draft_file)
            
            # 5. 发布到小红书（可选）
            if auto_publish:
                self.logger.info("步骤4: 发布到小红书...")
                success = poster.create_post(screenshot_files, post_title, post_content, post_topics)
                
                if success:
                    self.logger.info("发布成功！")
                else:
                    self.logger.error("发布失败")
                    return False
            else:
                self.logger.info("跳过自动发布，草稿已保存")
            
            self.logger.info("处理完成！")
            return True
            
        except Exception as e:
            self.logger.error(f"处理过程中出错: {str(e)}")
            return False
    
    def batch_process(self, note_urls, auto_publish=False, use_ai=True):
        """批量处理多个飞书笔记"""
        self.logger.info(f"开始批量处理 {len(note_urls)} 个笔记")
        
        success_count = 0
        for i, url in enumerate(note_urls, 1):
            self.logger.info(f"处理第 {i}/{len(note_urls)} 个笔记")
            
            if self.process_note(url, auto_publish, use_ai):
                success_count += 1
            else:
                self.logger.warning(f"第 {i} 个笔记处理失败")
            
            # 添加间隔，避免过于频繁的请求
            if i < len(note_urls):
                self.logger.info("等待 30 秒后处理下一个笔记...")
                import time
                time.sleep(30)
        
        self.logger.info(f"批量处理完成，成功 {success_count}/{len(note_urls)} 个")
        return success_count == len(note_urls)

def main():
    parser = argparse.ArgumentParser(description='飞书笔记转小红书图文工具')
    parser.add_argument('note_url', nargs='?', help='飞书笔记URL')
    parser.add_argument('--batch', '-b', help='批量处理文件，每行一个URL')
    parser.add_argument('--publish', '-p', action='store_true', help='自动发布到小红书（默认只生成草稿）')
    parser.add_argument('--no-ai', action='store_true', help='不使用AI生成文案')
    parser.add_argument('--config', '-c', help='配置文件路径')
    
    args = parser.parse_args()
    
    # 初始化工具
    tool = FeishuToXiaohongshu()
    
    # 验证配置
    if not tool.validate_config():
        sys.exit(1)
    
    # 处理单个笔记
    if args.note_url:
        success = tool.process_note(
            args.note_url, 
            auto_publish=args.publish, 
            use_ai=not args.no_ai
        )
        sys.exit(0 if success else 1)
    
    # 批量处理
    elif args.batch:
        if not os.path.exists(args.batch):
            tool.logger.error(f"批量处理文件不存在: {args.batch}")
            sys.exit(1)
        
        with open(args.batch, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        success = tool.batch_process(
            urls, 
            auto_publish=args.publish, 
            use_ai=not args.no_ai
        )
        sys.exit(0 if success else 1)
    
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main() 