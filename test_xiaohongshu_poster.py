#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书发布功能测试脚本
用于测试 XiaohongshuPoster 类的各项功能
"""

import os
import sys
import time
import logging
from xiaohongshu_poster import XiaohongshuPoster

class XiaohongshuPosterTester:
    def __init__(self):
        self.poster = XiaohongshuPoster()
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('test_poster.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def create_test_images(self):
        """创建测试图片（如果不存在）"""
        test_images = []
        
        # 创建screenshots目录（如果不存在）
        if not os.path.exists('screenshots'):
            os.makedirs('screenshots')
            
        # 测试图片路径
        test_image_paths = [
            'screenshots/screenshot_000.png',
            'screenshots/screenshot_001.png'
        ]
        
        for i, image_path in enumerate(test_image_paths, 1):
            if not os.path.exists(image_path):
                # 创建一个简单的测试图片（使用PIL）
                try:
                    from PIL import Image, ImageDraw, ImageFont
                    
                    # 创建一个简单的测试图片
                    img = Image.new('RGB', (800, 600), color='white')
                    draw = ImageDraw.Draw(img)
                    
                    # 添加文字
                    try:
                        # 尝试使用系统字体
                        font = ImageFont.truetype("arial.ttf", 40)
                    except:
                        # 使用默认字体
                        font = ImageFont.load_default()
                    
                    text = f"测试图片 {i}\n小红书发布测试"
                    draw.text((50, 50), text, fill='black', font=font)
                    
                    # 保存图片
                    img.save(image_path)
                    self.logger.info(f"创建测试图片: {image_path}")
                    
                except ImportError:
                    self.logger.warning("PIL未安装，无法创建测试图片")
                    # 创建一个空文件作为占位符
                    with open(image_path, 'w') as f:
                        f.write("测试图片占位符")
                    self.logger.info(f"创建图片占位符: {image_path}")
            
            test_images.append(image_path)
        
        return test_images
    
    def get_test_content(self):
        """获取测试内容"""
        test_title = "🌟 小红书发布功能测试 🌟"
        
        test_content = """
今天来测试一下小红书自动发布功能！

✨ 功能特点：
• 自动登录小红书
• 自动上传图片
• 自动填写标题和内容
• 自动发布帖子

🎯 测试目的：
验证自动化发布流程是否正常工作

💡 使用体验：
整个过程非常流畅，大大提高了发布效率！

#自动化测试 #小红书发布 #效率提升
        """.strip()
        
        test_topics = [
            "#自动化测试",
            "#小红书发布", 
            "#效率提升",
            "#技术分享",
            "#测试笔记"
        ]
        
        return test_title, test_content, test_topics
    
    def test_poster_initialization(self):
        """测试海报类初始化"""
        self.logger.info("=" * 50)
        self.logger.info("测试1: 海报类初始化")
        self.logger.info("=" * 50)
        
        try:
            poster = XiaohongshuPoster()
            self.logger.info("✅ 海报类初始化成功")
            return True
        except Exception as e:
            self.logger.error(f"❌ 海报类初始化失败: {str(e)}")
            return False
    
    def test_driver_setup(self):
        """测试浏览器驱动设置"""
        self.logger.info("=" * 50)
        self.logger.info("测试2: 浏览器驱动设置")
        self.logger.info("=" * 50)
        
        try:
            self.poster.setup_driver()
            self.logger.info("✅ 浏览器驱动设置成功")
            
            # 测试访问小红书首页
            self.poster.driver.get('https://www.xiaohongshu.com/')
            time.sleep(3)
            
            page_title = self.poster.driver.title
            self.logger.info(f"✅ 成功访问小红书首页，页面标题: {page_title}")
            
            # 关闭浏览器
            self.poster.driver.quit()
            self.poster.driver = None
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 浏览器驱动设置失败: {str(e)}")
            if self.poster.driver:
                self.poster.driver.quit()
                self.poster.driver = None
            return False
    
    def test_login_detection(self):
        """测试登录状态检测"""
        self.logger.info("=" * 50)
        self.logger.info("测试3: 登录状态检测")
        self.logger.info("=" * 50)
        
        try:
            self.poster.setup_driver()
            self.poster.driver.get('https://www.xiaohongshu.com/')
            time.sleep(3)
            
            login_status = self.poster._check_login_status()
            if login_status:
                self.logger.info("✅ 检测到已登录状态")
            else:
                self.logger.info("ℹ️ 未检测到登录状态（需要手动登录）")
            
            self.poster.driver.quit()
            self.poster.driver = None
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 登录状态检测失败: {str(e)}")
            if self.poster.driver:
                self.poster.driver.quit()
                self.poster.driver = None
            return False
    
    def test_full_publish_flow(self):
        """测试完整发布流程"""
        self.logger.info("=" * 50)
        self.logger.info("测试4: 完整发布流程")
        self.logger.info("=" * 50)
        
        # 准备测试数据
        test_images = self.create_test_images()
        test_title, test_content, test_topics = self.get_test_content()
        
        self.logger.info(f"测试图片: {test_images}")
        self.logger.info(f"测试标题: {test_title}")
        self.logger.info(f"测试话题: {test_topics}")
        
        try:
            # 执行完整发布流程
            success = self.poster.create_post(
                image_files=test_images,
                title=test_title,
                content=test_content,
                topics=test_topics
            )
            
            if success:
                self.logger.info("✅ 完整发布流程测试成功")
                return True
            else:
                self.logger.error("❌ 完整发布流程测试失败")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 完整发布流程测试异常: {str(e)}")
            return False
    
    def test_draft_save(self):
        """测试草稿保存功能"""
        self.logger.info("=" * 50)
        self.logger.info("测试5: 草稿保存功能")
        self.logger.info("=" * 50)
        
        # 准备测试数据
        test_images = self.create_test_images()
        test_title, test_content, test_topics = self.get_test_content()
        
        try:
            # 保存草稿
            output_file = "test_output/test_draft.txt"
            
            # 确保输出目录存在
            os.makedirs("test_output", exist_ok=True)
            
            success = self.poster.save_post_draft(
                image_files=test_images,
                title=test_title,
                content=test_content,
                topics=test_topics,
                output_file=output_file
            )
            
            if success and os.path.exists(output_file):
                self.logger.info(f"✅ 草稿保存成功: {output_file}")
                
                # 读取并显示保存的内容
                with open(output_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.logger.info("保存的草稿内容:")
                    self.logger.info("-" * 30)
                    self.logger.info(content)
                    self.logger.info("-" * 30)
                
                return True
            else:
                self.logger.error("❌ 草稿保存失败")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 草稿保存测试异常: {str(e)}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        self.logger.info("🚀 开始运行小红书发布功能测试")
        self.logger.info("=" * 60)
        
        test_results = []
        
        # 运行各项测试
        tests = [
            ("完整发布流程", self.test_full_publish_flow),
        ]
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                test_results.append((test_name, result))
            except Exception as e:
                self.logger.error(f"测试 {test_name} 发生异常: {str(e)}")
                test_results.append((test_name, False))
        
        # 输出测试结果汇总
        self.logger.info("=" * 60)
        self.logger.info("📊 测试结果汇总")
        self.logger.info("=" * 60)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ 通过" if result else "❌ 失败"
            self.logger.info(f"{test_name}: {status}")
            if result:
                passed += 1
        
        self.logger.info("-" * 60)
        self.logger.info(f"总计: {passed}/{total} 项测试通过")
        
        if passed == total:
            self.logger.info("🎉 所有测试都通过了！")
        else:
            self.logger.warning(f"⚠️ 有 {total - passed} 项测试失败，请检查相关功能")
        
        return passed == total

def main():
    """主函数"""
    print("小红书发布功能测试脚本")
    print("=" * 40)
    
    # 检查依赖
    try:
        import selenium
        print("✅ Selenium 已安装")
    except ImportError:
        print("❌ Selenium 未安装，请运行: pip install selenium")
        return
    
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        print("✅ webdriver-manager 已安装")
    except ImportError:
        print("❌ webdriver-manager 未安装，请运行: pip install webdriver-manager")
        return
    
    # 创建测试器并运行测试
    tester = XiaohongshuPosterTester()
    
    # 询问用户是否要运行完整发布流程测试
    print("\n注意：完整发布流程测试会实际发布帖子到小红书")
    print("如果只想测试其他功能，可以跳过完整发布流程测试")
    
   
    # 运行所有测试
    success = tester.run_all_tests()

    
    print(f"\n测试完成！详细日志请查看: test_poster.log")
    return success

if __name__ == "__main__":
    main() 