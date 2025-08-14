from openai import OpenAI
import logging
from config import Config

class AISummary:
    def __init__(self, api_key: str = None, base_url: str = None):
        self.client = None
        self.config = Config()
        self.api_key_override = api_key
        self.base_url_override = base_url
        self.setup_logging()
        self.setup_openai()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_openai(self):
        """设置OpenAI客户端"""
        api_key = self.api_key_override or self.config.OPENAI_API_KEY
        base_url = self.base_url_override or (self.config.OPENAI_BASE_URL if self.config.OPENAI_BASE_URL else None)
        if api_key:
            self.client = OpenAI(
                api_key=api_key,
                base_url=base_url
            )
        else:
            self.logger.warning("未配置OpenAI API Key，AI摘要功能将不可用")
            self.client = None
    
    def generate_summary(self, content):
        """根据笔记内容生成小红书文案摘要"""
        if not self.client:
            self.logger.warning("未配置OpenAI API Key，跳过AI摘要生成")
            return self._generate_fallback_summary("", content)
        
        try:
            prompt = f"""
请根据以下飞书笔记内容，生成一篇适合小红书的图文文案。
笔记内容：
{content}
要求：
1. 标题要吸引人，长度不超过{self.config.MAX_TITLE_LENGTH}字
2. 内容要简洁明了，突出重点，适合小红书平台风格
3. 内容长度不超过{self.config.MAX_CONTENT_LENGTH}字
4. 可以添加相关的话题标签（用#包围）
5. 语言要活泼、亲切，符合小红书用户习惯
6. 如果有实用价值，要突出实用性

请按以下格式返回：
标题：[生成的标题]
内容：[生成的文案内容]
话题：[相关话题标签，用#包围]
"""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个专业的小红书文案创作助手，擅长将各种内容转化为吸引人的小红书图文。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            result = response.choices[0].message.content.strip()
            self.logger.info("AI摘要生成成功")
            
            # 解析返回结果
            return self._parse_ai_response(result)
            
        except Exception as e:
            self.logger.error(f"AI摘要生成失败: {str(e)}")
            return self._generate_fallback_summary("", content)
    
    def _parse_ai_response(self, response):
        """解析AI返回的结果"""
        try:
            lines = response.split('\n')
            title = ""
            content = ""
            topics = []
            
            current_section = None
            content_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('标题：'):
                    title = line.replace('标题：', '').strip()
                    current_section = 'title'
                elif line.startswith('内容：'):
                    current_section = 'content'
                    # 获取内容的第一行
                    content_line = line.replace('内容：', '').strip()
                    if content_line:
                        content_lines.append(content_line)
                elif line.startswith('话题：'):
                    current_section = 'topics'
                    topics_text = line.replace('话题：', '').strip()
                    # 提取话题标签 - 支持多种格式
                    import re
                    # 匹配 #话题# 格式
                    topics = re.findall(r'#([^#]+)#', topics_text)
                    # 如果没有找到，尝试匹配单个#的格式
                    if not topics:
                        topics = re.findall(r'#([^\s#]+)', topics_text)
                    # 如果还是没有，尝试匹配任何包含#的文本
                    if not topics:
                        topics = re.findall(r'#([^#\s]+)', topics_text)
                elif current_section == 'content':
                    # 继续收集内容行
                    content_lines.append(line)
                elif current_section == 'topics' and line:
                    # 继续收集话题行
                    import re
                    additional_topics = re.findall(r'#([^#\s]+)', line)
                    topics.extend(additional_topics)
            
            # 合并内容行
            content = '\n'.join(content_lines).strip()
            
            # 验证解析结果
            if not title and not content:
                self.logger.warning("AI响应格式不符合预期，尝试备用解析方法")
                return self._parse_ai_response_fallback(response)
            
            return {
                'title': title or "飞书笔记分享",
                'content': content or "分享一篇有用的笔记内容",
                'topics': ["# " + t for t in topics] or ["#飞书笔记", "#知识分享"]
            }
            
        except Exception as e:
            self.logger.error(f"解析AI响应失败: {str(e)}")
            return self._generate_fallback_summary("", "")
    
    def _parse_ai_response_fallback(self, response):
        """备用解析方法，处理格式不标准的AI响应"""
        try:
            import re
            
            # 尝试提取标题（通常在开头）
            title_match = re.search(r'标题[：:]\s*(.+)', response)
            title = title_match.group(1).strip() if title_match else ""
            
            # 尝试提取内容（通常在中间部分）
            content_match = re.search(r'内容[：:]\s*(.+)', response, re.DOTALL)
            content = content_match.group(1).strip() if content_match else ""
            
            # 如果没有找到标准格式，尝试提取整个响应作为内容
            if not content:
                # 移除可能的标题部分
                content = re.sub(r'标题[：:].*?\n', '', response, flags=re.DOTALL)
                content = content.strip()
            
            # 提取话题标签
            topics = re.findall(r'#([^#\s]+)', response)
            
            return {
                'title': title or "飞书笔记分享",
                'content': content or "分享一篇有用的笔记内容",
                'topics': topics or ["#飞书笔记", "#知识分享"]
            }
            
        except Exception as e:
            self.logger.error(f"备用解析方法也失败: {str(e)}")
            return self._generate_fallback_summary("", "")
    
    def _generate_fallback_summary(self, title, content):
        """生成备用摘要（当AI不可用时）"""
        # 截取标题
        if title and len(title) > self.config.MAX_TITLE_LENGTH:
            title = title[:self.config.MAX_TITLE_LENGTH-3] + "..."
        
        # 截取内容
        if content and len(content) > self.config.MAX_CONTENT_LENGTH:
            content = content[:self.config.MAX_CONTENT_LENGTH-3] + "..."
        
        # 添加一些常用的话题标签
        topics = ["#飞书笔记", "#知识分享", "#学习笔记"]
        
        return {
            'title': title or "飞书笔记分享",
            'content': content or "分享一篇有用的笔记内容",
            'topics': topics
        }
    
    def enhance_content(self, original_content):
        """增强内容，添加更多吸引人的元素"""
        if not self.client:
            return original_content
        
        try:
            prompt = f"""
请对以下小红书文案进行优化，让它更加吸引人：

{original_content}

要求：
1. 保持原有核心信息不变
2. 增加一些吸引人的表达方式
3. 可以添加emoji表情
4. 让语言更加活泼有趣
5. 突出实用价值
6. 适合小红书平台风格

请直接返回优化后的文案内容。
"""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个专业的小红书文案优化助手。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.8
            )
            
            enhanced_content = response.choices[0].message.content.strip()
            self.logger.info("内容优化成功")
            return enhanced_content
            
        except Exception as e:
            self.logger.error(f"内容优化失败: {str(e)}")
            return original_content 