import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import logging
from config import Config

class FeishuScreenshot:
    def __init__(self, aspect_ratio: float = None, screenshot_width: int = None, screenshot_height: int = None):
        self.driver = None
        self.config = Config()
        self.aspect_ratio = float(aspect_ratio) if aspect_ratio else None  # r = 宽/高
        # 保持向后兼容：若传入明确宽高则沿用
        if screenshot_width:
            self.config.SCREENSHOT_WIDTH = int(screenshot_width)
        if screenshot_height:
            self.config.SCREENSHOT_HEIGHT = int(screenshot_height)
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
        
        # 仅当显式给出宽高时才固定窗口尺寸；否则采用浏览器默认宽度
        if hasattr(self, 'config') and self.config.SCREENSHOT_WIDTH and self.config.SCREENSHOT_HEIGHT and not self.aspect_ratio:
            chrome_options.add_argument(f'--window-size={self.config.SCREENSHOT_WIDTH},{self.config.SCREENSHOT_HEIGHT}')
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            self.logger.error(f"ChromeDriver初始化失败: {str(e)}")
            # 尝试使用系统PATH中的ChromeDriver
            self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(self.config.BROWSER_TIMEOUT)
        
        # 按照宽高比设置窗口高度（宽保持为默认浏览器宽度）
        try:
            if self.aspect_ratio:
                # 宽采用当前窗口的可见宽度
                width = int(self.driver.execute_script("return window.innerWidth;") or 0)
                if width <= 0:
                    width = int(self.driver.get_window_size().get('width', 1080))
                # r = 宽/高 => 高 = 宽 / r
                target_height = max(360, int(width / self.aspect_ratio))
                self.driver.set_window_size(width, target_height)
                # 同步更新配置，供下游日志/计算参考
                self.config.SCREENSHOT_WIDTH = width
                self.config.SCREENSHOT_HEIGHT = target_height
        except Exception:
            pass

    
    def navigate_to_note(self, note_url):
        """导航到指定的飞书笔记（优化等待策略，启动更快）"""
        try:
            self.driver.get(note_url)
            self.logger.info(f"正在打开笔记: {note_url}")
            
            # 等待页面就绪（readyState 完成）
            try:
                WebDriverWait(self.driver, 10, 0.5).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
            except Exception:
                pass
            
            # 暂时关闭隐式等待，避免与显式等待叠加导致的放大延迟
            _original_implicit = self.config.BROWSER_TIMEOUT
            try:
                self.driver.implicitly_wait(0)
                # 同时等待多个可能的内容容器，整体超时更短
                content_locators = [
                    (By.CLASS_NAME, "note-content"),
                    (By.CLASS_NAME, "wiki-content"),
                    (By.CLASS_NAME, "document-content"),
                    (By.XPATH, "//div[contains(@class, 'content')]") ,
                    (By.XPATH, "//div[contains(@class, 'wiki')]") ,
                    (By.XPATH, "//div[contains(@class, 'document')]") ,
                    (By.XPATH, "//main"),
                    (By.XPATH, "//article")
                ]
                # Selenium 4: EC.any_of
                try:
                    WebDriverWait(self.driver, 8, 0.5).until(
                        EC.any_of(*[EC.presence_of_element_located(loc) for loc in content_locators])
                    )
                    self.logger.info("检测到笔记内容容器")
                except Exception:
                    self.logger.warning("未找到标准内容容器，将继续尝试截图")
            finally:
                # 恢复隐式等待
                self.driver.implicitly_wait(_original_implicit)
            
            # 给予极短时间让首屏内容稳定
            time.sleep(1)
            return True
        
        except Exception as e:
            self.logger.error(f"打开笔记失败: {str(e)}")
            return False
    
    def get_note_title(self):
        """获取笔记标题"""
        try:
            # 尝试多种标题选择器
            title_selectors = [
                (By.CLASS_NAME, "note-title"),
                (By.CLASS_NAME, "wiki-title"),
                (By.CLASS_NAME, "document-title"),
                (By.XPATH, "//h1"),
                (By.XPATH, "//h2"),
                (By.XPATH, "//div[contains(@class, 'title')]"),
                (By.XPATH, "//span[contains(@class, 'title')]"),
                (By.XPATH, "//title")
            ]
            
            for selector_type, selector in title_selectors:
                try:
                    title_element = self.driver.find_element(selector_type, selector)
                    title = title_element.text.strip()
                    if title:
                        # 清理不可见字符
                        import re
                        title = re.sub(r'[\u200B-\u200D\uFEFF]', '', title)  # 移除零宽字符
                        title = re.sub(r'\s+', ' ', title)  # 合并多个空格
                        title = title.strip()
                        if title:
                            return title
                except:
                    continue
            
            # 如果都没找到，尝试从页面标题获取
            try:
                page_title = self.driver.title
                if page_title and page_title != "飞书":
                    # 清理页面标题
                    import re
                    page_title = re.sub(r'[\u200B-\u200D\uFEFF]', '', page_title)
                    page_title = re.sub(r'\s+', ' ', page_title)
                    page_title = page_title.strip()
                    if page_title and page_title != "飞书":
                        return page_title
            except:
                pass
            
            return "飞书笔记"
        except:
            return "飞书笔记"
    
    def get_note_content(self):
        """获取笔记内容"""
        try:
            # 确保页面已加载
            try:
                WebDriverWait(self.driver, 6, 0.5).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
            except Exception:
                pass

            # 尝试找到主要滚动容器，并滚动至底部以触发懒加载
            find_container_js = """
            const selectors = [
                'div[class*="content"]','div[class*="wiki"]','div[class*="document"]',
                'div[class*="editor"]','div[class*="note"]','main','article','div[role="main"]'
            ];
            for (const s of selectors) {
                const el = document.querySelector(s);
                if (el) return s;
            }
            return null;
            """
            container_selector = self.driver.execute_script(find_container_js)

            def scroll_to_bottom():
                try:
                    if container_selector:
                        # 容器滚动
                        view = int(self.driver.execute_script("return document.querySelector(arguments[0]).clientHeight;", container_selector) or 0)
                        total = int(self.driver.execute_script("return document.querySelector(arguments[0]).scrollHeight;", container_selector) or 0)
                        pos = int(self.driver.execute_script("return document.querySelector(arguments[0]).scrollTop;", container_selector) or 0)
                        step = max(200, view - 150) if view else 400
                        loops = 0
                        while pos + view + 5 < total and loops < 50:
                            self.driver.execute_script("document.querySelector(arguments[0]).scrollTop = arguments[1];", container_selector, pos + step)
                            time.sleep(0.25)
                            pos = int(self.driver.execute_script("return document.querySelector(arguments[0]).scrollTop;", container_selector) or 0)
                            total = int(self.driver.execute_script("return document.querySelector(arguments[0]).scrollHeight;", container_selector) or 0)
                            loops += 1
                    else:
                        # 页面滚动
                        view = int(self.driver.execute_script("return window.innerHeight;") or 0)
                        total = int(self.driver.execute_script("return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);") or 0)
                        pos = int(self.driver.execute_script("return window.pageYOffset;") or 0)
                        step = max(200, view - 150) if view else 400
                        loops = 0
                        while pos + view + 5 < total and loops < 50:
                            self.driver.execute_script("window.scrollTo(0, arguments[0]);", pos + step)
                            time.sleep(0.25)
                            pos = int(self.driver.execute_script("return window.pageYOffset;") or 0)
                            total = int(self.driver.execute_script("return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);") or 0)
                            loops += 1
                except Exception:
                    pass

            scroll_to_bottom()

            # 首选：从主要内容容器中读取 innerText（更完整，保留换行）
            content_selectors = [
                (By.CLASS_NAME, "note-content"),
                (By.CLASS_NAME, "wiki-content"),
                (By.CLASS_NAME, "document-content"),
                (By.CLASS_NAME, "editor-content"),
                (By.XPATH, "//div[contains(@class, 'content')]"),
                (By.XPATH, "//div[contains(@class, 'wiki')]"),
                (By.XPATH, "//div[contains(@class, 'document')]"),
                (By.XPATH, "//div[contains(@class, 'editor')]"),
                (By.XPATH, "//main"),
                (By.XPATH, "//article"),
                (By.XPATH, "//div[@role='main']"),
                (By.XPATH, "//div[contains(@class, 'rich-text')]"),
                (By.XPATH, "//div[contains(@class, 'text')]"),
                # 更通用的选择器
                (By.XPATH, "//div[contains(@class, 'body')]"),
                (By.XPATH, "//div[contains(@class, 'main')]"),
                (By.XPATH, "//div[contains(@class, 'container')]")
            ]

            import re
            content_chunks = []
            for selector_type, selector in content_selectors:
                try:
                    el = WebDriverWait(self.driver, 2).until(
                        EC.presence_of_element_located((selector_type, selector))
                    )
                    inner_text = ""
                    try:
                        inner_text = (self.driver.execute_script("return arguments[0].innerText;", el) or "").strip()
                    except Exception:
                        inner_text = ""
                    text = inner_text or (el.text or "").strip()
                    if text:
                        # 规范化换行与空白
                        text = re.sub(r"[\u200B-\u200D\uFEFF]", "", text)
                        text = re.sub(r"\s+\n", "\n", text)
                        content_chunks.append(text)
                except Exception:
                    continue

            if content_chunks:
                merged = "\n".join(content_chunks).strip()
                # 合并多余空行
                merged = re.sub(r"\n{3,}", "\n\n", merged)
                if len(merged) > 10:
                    return merged

            # 回退方案：移除明显的导航/工具区域后，读取 body.innerText
            try:
                fallback_js = """
                var exclude = ['nav','header','footer','button','input','select','textarea','.nav','.header','.footer','.button','.input','.select','.menu','.toolbar','.sidebar'];
                var removed = [];
                for (var i=0;i<exclude.length;i++){
                    var nodes = document.querySelectorAll(exclude[i]);
                    for (var j=0;j<nodes.length;j++){
                        var n = nodes[j];
                        removed.push({n:n, display:n.style.display});
                        n.style.display='none';
                    }
                }
                var text = document.body.innerText || '';
                for (var k=0;k<removed.length;k++){ removed[k].n.style.display = removed[k].display; }
                return text.trim();
                """
                body_text = self.driver.execute_script(fallback_js)
                if body_text and len(body_text) > 10:
                    return body_text
            except Exception:
                pass

            self.logger.warning("无法获取笔记内容")
            return ""
        
        except Exception as e:
            self.logger.error(f"获取笔记内容时发生错误: {str(e)}")
            return ""
        finally:
            if self.driver:
                self.driver.quit()
    
    def take_full_screenshot(self, note_url, output_dir=None):
        """对飞书笔记进行完整截图"""
        if output_dir is None:
            output_dir = self.config.SCREENSHOT_DIR

        os.makedirs(output_dir, exist_ok=True)

        try:
            # 设置浏览器驱动
            self.setup_driver()

            # 直接导航到笔记页面
            self.logger.info("导航到笔记页面...")
            if not self.navigate_to_note(note_url):
                return None, None

            # 获取笔记信息
            title = self.get_note_title()
            self.logger.info(f"笔记标题: {title}")

            # 确保从顶部开始
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)

            # 获取页面信息
            viewport_height = self.driver.execute_script("return window.innerHeight;")
            
            # 使用更可靠的方法检测页面高度
            # 先滚动到底部，然后获取实际高度
            self.logger.info("检测页面实际高度...")
            
            # 滚动到底部触发内容加载
            self.driver.execute_script("window.scrollTo(0, 999999);")
            time.sleep(3)

            # 尝试获取主要内容区域的高度
            total_height = self.driver.execute_script("""
                // 尝试多种方法获取页面高度
                var height = 0;
                
                // 方法1: 获取文档高度
                height = Math.max(height, document.documentElement.scrollHeight);
                height = Math.max(height, document.body.scrollHeight);
                
                // 方法2: 获取内容元素高度
                var contentElements = document.querySelectorAll('div[class*="content"], div[class*="wiki"], div[class*="document"], main, article, div[class*="note"], div[class*="editor"]');
                for (var i = 0; i < contentElements.length; i++) {
                    var elementHeight = contentElements[i].scrollHeight || contentElements[i].offsetHeight;
                    if (elementHeight > height) {
                        height = elementHeight;
                    }
                }
                
                // 方法3: 获取所有可见元素的最大底部位置
                var allElements = document.querySelectorAll('*');
                for (var i = 0; i < allElements.length; i++) {
                    var rect = allElements[i].getBoundingClientRect();
                    var bottom = rect.bottom + window.pageYOffset;
                    if (bottom > height) {
                        height = bottom;
                    }
                }
                
                return height;
            """)
            self.logger.info(f"通过多种方法检测到高度: {total_height}")

            
            self.logger.info(f"页面总高度: {total_height}, 视口高度: {viewport_height}")
            
            # 如果页面内容确实很短，只截一张图
            if total_height <= viewport_height:
                self.logger.info("页面内容较短，只截取一张图片")
                screenshot_path = os.path.join(output_dir, f"screenshot_000.png")
                self.driver.save_screenshot(screenshot_path)
                screenshot_files = [screenshot_path]
                self.logger.info("截图完成，共 1 张")
                return screenshot_files, title

            # 滚动截图
            screenshot_files = []
            current_position = 0
            overlap = 200  # 截图重叠部分
            scroll_step = viewport_height - overlap
            
            screenshot_count = 0
            max_screenshots = 50  # 防止无限循环
            
            # 尝试找到正确的滚动容器
            scroll_container = self.driver.execute_script("""
                // 查找飞书的主要滚动容器
                var selectors = [
                    'div[class*="content"]',
                    'div[class*="wiki"]', 
                    'div[class*="document"]',
                    'div[class*="note"]',
                    'div[class*="editor"]',
                    'main',
                    'article',
                    'div[style*="overflow"]',
                    'div[style*="scroll"]'
                ];
                
                for (var i = 0; i < selectors.length; i++) {
                    var elements = document.querySelectorAll(selectors[i]);
                    for (var j = 0; j < elements.length; j++) {
                        var element = elements[j];
                        if (element.scrollHeight > element.clientHeight && element.scrollHeight > 1000) {
                            return {
                                element: element,
                                selector: selectors[i],
                                scrollHeight: element.scrollHeight,
                                clientHeight: element.clientHeight
                            };
                        }
                    }
                }
                return null;
            """)
            
            if scroll_container:
                self.logger.info(f"找到滚动容器: {scroll_container['selector']}")
                self.logger.info(f"容器高度: {scroll_container['scrollHeight']}px, 可视高度: {scroll_container['clientHeight']}px")
                # 使用容器高度而不是文档高度
                total_height = scroll_container['scrollHeight']
            else:
                self.logger.warning("未找到专门的滚动容器，使用文档高度")

            while current_position < total_height and screenshot_count < max_screenshots:
                # 根据是否找到滚动容器选择滚动方法
                if scroll_container:
                    # 使用找到的滚动容器
                    self.driver.execute_script("""
                        var selectors = arguments[0];
                        var targetPosition = arguments[1];
                        
                        for (var i = 0; i < selectors.length; i++) {
                            var elements = document.querySelectorAll(selectors[i]);
                            for (var j = 0; j < elements.length; j++) {
                                var element = elements[j];
                                if (element.scrollHeight > element.clientHeight && element.scrollHeight > 1000) {
                                    element.scrollTop = targetPosition;
                                    return element.scrollTop;
                                }
                            }
                        }
                        return -1;
                    """, ['div[class*="content"]', 'div[class*="wiki"]', 'div[class*="document"]', 'div[class*="note"]', 'div[class*="editor"]', 'main', 'article'], current_position)
                    time.sleep(2)
                else:
                    # 使用传统的页面滚动方法
                    self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                    time.sleep(1)
                    
                    # 如果window滚动失败，尝试其他方法
                    current_scroll = self.driver.execute_script("return window.pageYOffset;")
                    if abs(current_scroll - current_position) > 50:
                        self.driver.execute_script(f"document.body.scrollTop = {current_position};")
                        time.sleep(1)
                    
                    current_scroll = self.driver.execute_script("return window.pageYOffset;")
                    if abs(current_scroll - current_position) > 50:
                        self.driver.execute_script(f"document.documentElement.scrollTop = {current_position};")
                        time.sleep(1)
                
                # 等待页面稳定和内容加载
                time.sleep(2)
                
                # 等待页面完全加载
                try:
                    WebDriverWait(self.driver, 10).until(
                        lambda driver: driver.execute_script("return document.readyState") == "complete"
                    )
                except:
                    pass
                
                # 再次检查页面高度，因为可能有新内容加载
                current_total_height = self.driver.execute_script("""
                    // 尝试多种方法获取页面高度
                    var height = 0;
                    
                    // 方法1: 获取文档高度
                    height = Math.max(height, document.documentElement.scrollHeight);
                    height = Math.max(height, document.body.scrollHeight);
                    
                    // 方法2: 获取内容元素高度
                    var contentElements = document.querySelectorAll('div[class*="content"], div[class*="wiki"], div[class*="document"], main, article, div[class*="note"], div[class*="editor"]');
                    for (var i = 0; i < contentElements.length; i++) {
                        var elementHeight = contentElements[i].scrollHeight || contentElements[i].offsetHeight;
                        if (elementHeight > height) {
                            height = elementHeight;
                        }
                    }
                    
                    return height;
                """)
                
                # 如果检测到新的高度，更新总高度
                if current_total_height > total_height:
                    total_height = current_total_height
                    self.logger.info(f"检测到新内容，更新总高度为: {total_height}")
                
                # 截图
                screenshot_path = os.path.join(output_dir, f"screenshot_{screenshot_count:03d}.png")
                self.driver.save_screenshot(screenshot_path)
                screenshot_files.append(screenshot_path)
                
                # 获取当前滚动位置进行验证
                if scroll_container:
                    # 检查容器滚动位置
                    current_scroll_position = self.driver.execute_script("""
                        var selectors = arguments[0];
                        for (var i = 0; i < selectors.length; i++) {
                            var elements = document.querySelectorAll(selectors[i]);
                            for (var j = 0; j < elements.length; j++) {
                                var element = elements[j];
                                if (element.scrollHeight > element.clientHeight && element.scrollHeight > 1000) {
                                    return element.scrollTop;
                                }
                            }
                        }
                        return 0;
                    """, ['div[class*="content"]', 'div[class*="wiki"]', 'div[class*="document"]', 'div[class*="note"]', 'div[class*="editor"]', 'main', 'article'])
                else:
                    # 检查页面滚动位置
                    current_scroll_position = self.driver.execute_script("return window.pageYOffset;")
                
                # 获取详细的滚动信息用于调试
                scroll_info = self.driver.execute_script("""
                    var info = {
                        windowScroll: window.pageYOffset,
                        bodyScroll: document.body.scrollTop,
                        documentElementScroll: document.documentElement.scrollTop,
                        containers: []
                    };
                    
                    var containers = document.querySelectorAll('div[class*="content"], div[class*="wiki"], div[class*="document"], main, article, div[class*="note"], div[class*="editor"], div[style*="overflow"], div[style*="scroll"]');
                    for (var i = 0; i < containers.length; i++) {
                        if (containers[i].scrollHeight > containers[i].clientHeight) {
                            info.containers.push({
                                className: containers[i].className,
                                scrollTop: containers[i].scrollTop,
                                scrollHeight: containers[i].scrollHeight,
                                clientHeight: containers[i].clientHeight
                            });
                        }
                    }
                    return info;
                """)
                
                self.logger.info(f"已截图 {screenshot_count + 1} 张，目标位置: {current_position}, 实际位置: {current_scroll_position}")
                self.logger.info(f"滚动信息 - window: {scroll_info['windowScroll']}, body: {scroll_info['bodyScroll']}, documentElement: {scroll_info['documentElementScroll']}")
                
                if scroll_info['containers']:
                    for i, container in enumerate(scroll_info['containers']):
                        self.logger.info(f"容器 {i+1}: {container['className']} - scrollTop: {container['scrollTop']}, scrollHeight: {container['scrollHeight']}")
                
                # 如果滚动位置没有变化，可能是页面结构问题
                if screenshot_count > 0 and abs(current_scroll_position - current_position) > 50:
                    self.logger.warning(f"滚动位置不匹配！目标: {current_position}, 实际: {current_scroll_position}")
                    
                    # 尝试强制滚动
                    if screenshot_count == 1:  # 只在第一次失败时尝试
                        self.logger.info("尝试强制滚动...")
                        if scroll_container:
                            # 强制滚动容器
                            self.driver.execute_script("""
                                var selectors = arguments[0];
                                var targetPosition = arguments[1];
                                for (var i = 0; i < selectors.length; i++) {
                                    var elements = document.querySelectorAll(selectors[i]);
                                    for (var j = 0; j < elements.length; j++) {
                                        var element = elements[j];
                                        if (element.scrollHeight > element.clientHeight && element.scrollHeight > 1000) {
                                            element.scrollTop = targetPosition;
                                        }
                                    }
                                }
                            """, ['div[class*="content"]', 'div[class*="wiki"]', 'div[class*="document"]', 'div[class*="note"]', 'div[class*="editor"]', 'main', 'article'], current_position)
                        else:
                            # 强制滚动页面
                            self.driver.execute_script("""
                                window.scrollTo(0, arguments[0]);
                                document.body.scrollTop = arguments[0];
                                document.documentElement.scrollTop = arguments[0];
                            """, current_position)
                        time.sleep(3)

                # 移动到下一个位置
                current_position += scroll_step
                screenshot_count += 1

            self.logger.info(f"截图完成，共 {len(screenshot_files)} 张")
            return screenshot_files, title

        except Exception as e:
            self.logger.error(f"截图过程中出错: {str(e)}")
            return None, None