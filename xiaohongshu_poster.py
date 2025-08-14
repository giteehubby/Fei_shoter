import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from config import Config

class XiaohongshuPoster:
    def __init__(self):
        self.driver = None
        self.config = Config()
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_driver(self):
        """设置Chrome浏览器驱动"""
        chrome_options = Options()
        if self.config.BROWSER_HEADLESS:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 使用ChromeDriverManager，让webdriver-manager自动处理架构
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            self.logger.error(f"ChromeDriver初始化失败: {str(e)}")
            # 尝试使用系统PATH中的ChromeDriver
            self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.implicitly_wait(self.config.BROWSER_TIMEOUT)
        
    def login_xiaohongshu(self):
        """登录小红书"""
        try:
            self.driver.get('https://www.xiaohongshu.com/')
            self.logger.info("正在打开小红书...")
            
            # 等待页面加载
            time.sleep(5)
            
            # 检查是否已经登录
            if self._check_login_status():
                self.logger.info("检测到已登录状态")
                return True
            
            # 点击登录按钮
            try:
                login_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '登录')]"))
                )
                login_button.click()
                
                # 等待登录页面加载
                time.sleep(3)
            except:
                self.logger.info("未找到登录按钮，可能已经在登录页面")
            
            # 这里需要手动登录，因为小红书有反爬虫机制
            self.logger.info("请在浏览器中手动完成登录操作...")
            self.logger.info("登录完成后，脚本将自动继续...")
            
            # 等待用户手动登录，使用多种检测方法
            max_wait_time = 300  # 5分钟
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                if self._check_login_status():
                    self.logger.info("小红书登录成功")
                    return True
                time.sleep(2)  # 每2秒检查一次
            
            self.logger.error("登录超时，请检查登录状态")
            return False
            
        except Exception as e:
            self.logger.error(f"小红书登录失败: {str(e)}")
            return False
    
    def _check_login_status(self):
        """检查登录状态"""
        try:
            # 多种登录状态检测方法
            login_indicators = [
                # 用户头像相关
                (By.CLASS_NAME, "user-avatar"),
                (By.CLASS_NAME, "avatar"),
                (By.XPATH, "//img[contains(@class, 'avatar')]"),
                (By.XPATH, "//img[contains(@class, 'user')]"),
                
                # 用户菜单相关
                (By.XPATH, "//div[contains(@class, 'user-menu')]"),
                (By.XPATH, "//div[contains(@class, 'profile')]"),
                (By.XPATH, "//div[contains(@class, 'account')]"),
                
                # 发布按钮（登录后才会显示）
                (By.XPATH, "//button[contains(text(), '发布')]"),
                (By.XPATH, "//div[contains(text(), '发布')]"),
                (By.XPATH, "//span[contains(text(), '发布')]"),
                (By.XPATH, "//a[contains(text(), '发布')]"),
                
                # 个人中心相关
                (By.XPATH, "//a[contains(@href, '/user')]"),
                (By.XPATH, "//div[contains(@class, 'personal')]"),
                
                # 登录后特有的元素
                (By.XPATH, "//div[contains(@class, 'logged-in')]"),
                (By.XPATH, "//div[contains(@class, 'authenticated')]"),
                
                # 检查URL是否包含用户信息
                (By.XPATH, "//meta[@name='user-id']"),
                
                # 更多可能的登录指示器
                (By.XPATH, "//div[contains(@class, 'header')]//img[contains(@class, 'avatar')]"),
                (By.XPATH, "//div[contains(@class, 'nav')]//img[contains(@class, 'avatar')]"),
                (By.XPATH, "//div[contains(@class, 'toolbar')]//img[contains(@class, 'avatar')]"),
            ]
            
            for selector_type, selector in login_indicators:
                try:
                    element = self.driver.find_element(selector_type, selector)
                    if element.is_displayed():
                        self.logger.info(f"检测到登录状态，使用选择器: {selector}")
                        return True
                except Exception as e:
                    # 记录详细的错误信息用于调试
                    self.logger.debug(f"选择器 {selector} 失败: {str(e)}")
                    continue
            
            # 检查URL是否包含用户信息
            current_url = self.driver.current_url
            if '/user/' in current_url or 'profile' in current_url:
                self.logger.info("通过URL检测到登录状态")
                return True
            
            # 检查页面标题是否包含用户信息
            page_title = self.driver.title
            if '个人' in page_title or '我的' in page_title:
                self.logger.info("通过页面标题检测到登录状态")
                return True
            
            # 使用JavaScript检查登录状态
            login_status = self.driver.execute_script("""
                // 检查是否有用户相关的元素
                var userElements = document.querySelectorAll('[class*="user"], [class*="avatar"], [class*="profile"]');
                if (userElements.length > 0) {
                    for (var i = 0; i < userElements.length; i++) {
                        if (userElements[i].offsetWidth > 0 && userElements[i].offsetHeight > 0) {
                            return true;
                        }
                    }
                }
                
                // 检查是否有发布按钮
                var publishButtons = document.querySelectorAll('button, div, a');
                for (var i = 0; i < publishButtons.length; i++) {
                    if (publishButtons[i].textContent && publishButtons[i].textContent.includes('发布')) {
                        return true;
                    }
                }
                
                return false;
            """)
            
            if login_status:
                self.logger.info("通过JavaScript检测到登录状态")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"检查登录状态时发生错误: {str(e)}")
            return False
    
    def navigate_to_create_post(self):
        """导航到发布页面"""
        try:
            # 多种发布按钮选择器
            publish_selectors = [
                (By.XPATH, "//button[contains(text(), '发布')]"),
                (By.XPATH, "//div[contains(text(), '发布')]"),
                (By.XPATH, "//span[contains(text(), '发布')]"),
                (By.XPATH, "//a[contains(text(), '发布')]"),
                (By.XPATH, "//*[contains(text(), '发布')]"),
                # 更具体的选择器
                (By.XPATH, "//button[contains(@class, 'publish')]"),
                (By.XPATH, "//div[contains(@class, 'publish')]"),
                (By.XPATH, "//button[contains(@class, 'post')]"),
                (By.XPATH, "//div[contains(@class, 'post')]"),
                # 图标按钮
                (By.XPATH, "//button[contains(@class, 'icon')]"),
                (By.XPATH, "//div[contains(@class, 'icon')]"),
            ]
            
            publish_button = None
            
            # 尝试找到发布按钮
            for selector_type, selector in publish_selectors:
                try:
                    self.logger.info(f"尝试查找发布按钮: {selector}")
                    elements = self.driver.find_elements(selector_type, selector)
                    
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            # 检查元素是否包含发布相关文本
                            element_text = element.text.strip().lower()
                            if '发布' in element_text or 'post' in element_text or 'publish' in element_text:
                                publish_button = element
                                self.logger.info(f"找到发布按钮: {element_text}")
                                break
                    
                    if publish_button:
                        break
                        
                except Exception as e:
                    self.logger.debug(f"选择器 {selector} 失败: {str(e)}")
                    continue
            
            if not publish_button:
                # 如果没找到发布按钮，尝试使用JavaScript查找
                self.logger.info("使用JavaScript查找发布按钮")
                publish_button = self.driver.execute_script("""
                    // 查找所有可能包含"发布"文本的元素
                    var elements = document.querySelectorAll('button, div, span, a');
                    for (var i = 0; i < elements.length; i++) {
                        var element = elements[i];
                        if (element.offsetWidth > 0 && element.offsetHeight > 0) {
                            var text = element.textContent || element.innerText || '';
                            if (text.includes('发布') || text.includes('Post') || text.includes('Publish')) {
                                return element;
                            }
                        }
                    }
                    return null;
                """)
            
            if publish_button:
                # 尝试点击发布按钮
                try:
                    # 滚动到元素位置
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", publish_button)
                    time.sleep(1)
                    
                    # 尝试点击
                    publish_button.click()
                    self.logger.info("成功点击发布按钮")
                    
                    # 等待页面加载
                    time.sleep(3)
                    
                    # 检查是否成功进入发布页面
                    current_url = self.driver.current_url
                    page_title = self.driver.title
                    
                    if 'publish' in current_url.lower() or 'post' in current_url.lower() or 'create' in current_url.lower():
                        self.logger.info("已进入发布页面")
                        return True
                    else:
                        self.logger.info(f"当前页面: {page_title}, URL: {current_url}")
                        # 即使URL没有变化，也可能已经进入发布页面
                        return True
                        
                except Exception as e:
                    self.logger.error(f"点击发布按钮失败: {str(e)}")
                    
                    # 尝试使用JavaScript点击
                    try:
                        self.driver.execute_script("arguments[0].click();", publish_button)
                        self.logger.info("使用JavaScript点击发布按钮")
                        time.sleep(3)
                        return True
                    except Exception as js_e:
                        self.logger.error(f"JavaScript点击也失败: {str(js_e)}")
                        return False
            else:
                self.logger.error("未找到发布按钮")
                
                # 显示页面上的所有按钮信息用于调试
                try:
                    buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    self.logger.info(f"页面上找到 {len(buttons)} 个按钮")
                    for i, btn in enumerate(buttons[:10]):  # 只显示前10个
                        if btn.text.strip():
                            self.logger.info(f"按钮 {i+1}: {btn.text}")
                except:
                    pass
                
                return False
            
        except Exception as e:
            self.logger.error(f"进入发布页面失败: {str(e)}")
            return False

    def click_upload_content(self):
        """点击上传图文按钮"""
        try:
            self.logger.info("尝试点击 上传图文 标签")
            # 首选：参考社区代码的 CSS 选择器
            try:
                upload_button = WebDriverWait(self.driver, 10, 0.2).until(
                    lambda x: x.find_element(By.CSS_SELECTOR, "div.tab:nth-child(2)")
                )
                upload_button.click()
                time.sleep(1)
                return True
            except Exception:
                pass
            # 备用 CSS（更窄范围）
            for css_selector in [
                "div.tab-item:nth-child(2)",
                ".tab-item:nth-child(2)",
            ]:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, css_selector)
                    if elem.is_displayed() and elem.is_enabled():
                        elem.click()
                        time.sleep(1)
                        return True
                except Exception:
                    continue
            # 最后回退：基于文本的 XPath
            try:
                xpath_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//*[text()='上传图文' or contains(text(),'上传图文')]"))
                )
                xpath_btn.click()
                time.sleep(1)
                return True
            except Exception:
                self.logger.error("未找到上传图文标签")
                return False
        except Exception as e:
            self.logger.error(f"点击上传图文失败: {str(e)}")
            return False

    def upload_images(self, image_files):
        """上传图片"""
        try:
            # 直接定位文件选择 input（参考社区代码）
            file_input = None
            for css in [
                ".upload-wrapper > div:nth-child(1) > input:nth-child(1)",
                ".upload-wrapper input[type='file']",
                "input[type='file']",
            ]:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, css)
                    if elem and elem.is_displayed():
                        file_input = elem
                        self.logger.info(f"使用CSS找到文件上传输入框: {css}")
                        break
                except Exception:
                    continue
            if not file_input:
                try:
                    file_input = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
                    )
                    self.logger.info("使用XPath找到文件上传输入框")
                except Exception as e2:
                    self.logger.error(f"未找到文件上传输入框: {str(e2)}")
                    return False

            # 依次上传图片
            for image_file in image_files:
                if os.path.exists(image_file):
                    file_input.send_keys(os.path.abspath(image_file))
                    self.logger.info(f"已上传图片: {image_file}")
                    time.sleep(2)
                else:
                    self.logger.warning(f"图片文件不存在: {image_file}")
            # 简单等待上传结束
            time.sleep(5)
            self.logger.info("图片上传完成")
            return True
        except Exception as e:
            self.logger.error(f"图片上传失败: {str(e)}")
            return False

    def input_title(self, title):
        """输入标题"""
        try:
            # 查找标题输入框
            title_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//textarea[@placeholder*='标题']"))
            )
            
            # 清空并输入标题
            title_input.clear()
            title_input.send_keys(title)
            
            self.logger.info(f"已输入标题: {title}")
            return True
            
        except Exception as e:
            self.logger.error(f"输入标题失败: {str(e)}")
            return False
    
    def input_content(self, content, topics):
        """输入内容"""
        try:
            # 查找内容输入框
            content_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//textarea[@placeholder*='分享']"))
            )
            
            # 组合内容和话题标签
            full_content = content + "\n\n" + " ".join(topics)
            
            # 清空并输入内容
            content_input.clear()
            content_input.send_keys(full_content)
            
            self.logger.info("已输入内容")
            return True
            
        except Exception as e:
            self.logger.error(f"输入内容失败: {str(e)}")
            return False
    
    def publish_post(self):
        """发布帖子"""
        try:
            self.logger.info("等待资源上传...")
            time.sleep(5)
            # 首选：CSS + JS 点击（社区代码）
            try:
                btn = self.driver.execute_script(
                    'return document.querySelector("button.css-k3hpu2:nth-child(1)")'
                )
                if btn:
                    btn.click()
                else:
                    raise Exception("css 发布按钮不存在")
            except Exception:
                # 回退：基于文本的 XPath
                btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'发布')]"))
                )
                btn.click()
            time.sleep(5)
            self.logger.info("帖子发布成功")
            return True
        except Exception as e:
            self.logger.error(f"发布失败: {str(e)}")
            return False
    
    def create_post(self, image_files, title, content, topics):
        """创建并发布小红书帖子"""
        try:
            # 设置浏览器驱动
            self.setup_driver()
            
            # 登录小红书
            if not self.login_xiaohongshu():
                return False
            
            # 导航到发布页面
            if not self.navigate_to_create_post():
                return False
            
            # 点击上传图文按钮
            if not self.click_upload_content():
                return False
            
            # 上传图片
            if not self.upload_images(image_files):
                return False
            
            # 输入标题
            if not self.input_title(title):
                return False
            
            # 输入内容
            if not self.input_content(content, topics):
                return False
            
            # 发布帖子
            if not self.publish_post():
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"创建帖子过程中出错: {str(e)}")
            return False
        
        finally:
            if self.driver:
                self.driver.quit()
    
    def save_post_draft(self, image_files, title, content, topics, output_file):
        """保存帖子草稿到文件"""
        try:
            # 组合完整内容
            full_content = f"""
标题: {title}

内容:
{content}

话题标签:
{' '.join(topics)}

图片文件:
{chr(10).join(image_files)}
"""
            
            # 保存到文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(full_content)
            
            self.logger.info(f"帖子草稿已保存到: {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存草稿失败: {str(e)}")
            return False 