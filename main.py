from pkg.plugin.context import register, handler, BasePlugin, APIHost, EventContext
from pkg.plugin.events import *
from pkg.platform.types import *
import requests
import asyncio

@register(name="MCWiki", description="Minecraft Wiki查询插件", version="1.0", author="YourName")
class MCWikiPlugin(BasePlugin):
    
    def __init__(self, host: APIHost):
        super().__init__(host)  # 必须调用父类初始化方法
        self.ap = host  # 根据LangBot约定，保存APIHost实例为 self.ap
    
    async def initialize(self):
        # 使用 self.ap.logger 前确认其存在
        if hasattr(self.ap, 'logger'):
            self.ap.logger.info("MCWiki插件已加载！")
        else:
            print("警告：APIHost未提供logger属性，请检查框架版本！")

    @handler(PersonNormalMessageReceived)
    async def handle_person_message(self, ctx: EventContext):
        await self._process_wiki_query(ctx, is_group=False)

    @handler(GroupNormalMessageReceived)
    async def handle_group_message(self, ctx: EventContext):
        await self._process_wiki_query(ctx, is_group=True)

    async def _process_wiki_query(self, ctx: EventContext, is_group: bool):
        msg = ctx.event.text_message.strip()
        
        # 使用 print 替代 self.ap.logger 确保日志输出
        print(f"[MCWiki] 收到消息: {msg}")  # 调试日志
        
        if not msg.startswith("wiki "):
            return
        
        keyword = msg[len("wiki "):].strip()
        if not keyword:
            reply = "请输入查询内容，例如：wiki 草方块"
            ctx.add_return("reply", [reply])
            ctx.prevent_default()
            return
        
        print(f"[MCWiki] 处理查询: {keyword}")
        
        try:
            await asyncio.sleep(1)  # 降低风控
            result = self._search_wiki(keyword)
            reply = result if result else "未找到相关条目。"
        except Exception as e:
            reply = "查询时发生错误，请稍后再试。"
            print(f"[MCWiki] 错误: {str(e)}")
        
        ctx.add_return("reply", [reply])
        ctx.prevent_default()

    def _search_wiki(self, keyword: str) -> str:
        url = "https://minecraft.fandom.com/zh/api.php"
    
    # 第一步：搜索关键词获取准确页面标题
        search_params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": keyword
        }
    
        try:
            # 1. 搜索关键词获取准确页面标题
            search_response = requests.get(url, params=search_params, timeout=10)
            search_data = search_response.json()
            search_results = search_data.get("query", {}).get("search", [])
        
            if not search_results:
                return "未找到相关条目。"
        
            # 取第一个匹配结果的标题
            page_title = search_results[0]["title"]
        
            # 2. 获取页面摘要
            content_params = {
                "action": "query",
                "format": "json",
                "prop": "extracts",
                "exintro": True,    # 仅获取摘要
                "explaintext": True, # 纯文本格式
                "titles": page_title
            }
        
            content_response = requests.get(url, params=content_params, timeout=10)
            content_data = content_response.json()
        
            # 提取页面内容
            pages = content_data.get("query", {}).get("pages", {})
            page_id = next(iter(pages))  # 获取第一个页面的ID
            page_info = pages.get(page_id, {})
        
            if "extract" not in page_info:
                return f"找到条目：{page_title}\n（暂无摘要）\n链接：https://minecraft.fandom.com/zh/wiki/{page_title.replace(' ', '_')}"
        
            summary = page_info["extract"]
            # 清理换行符并截断
            summary = summary.replace('\n', ' ')[:250] + "..." if len(summary) > 250 else summary
            link = f"https://minecraft.fandom.com/zh/wiki/{page_title.replace(' ', '_')}"
        
            return f"【{page_title}】\n{summary}\n🔗 详细内容：{link}"
        
        except requests.exceptions.Timeout:
            return "请求超时，请重试。"
        except Exception as e:
            return f"获取信息失败：{str(e)}"
    def __del__(self):
        if hasattr(self.ap, 'logger'):
            self.ap.logger.info("MCWiki插件已卸载")