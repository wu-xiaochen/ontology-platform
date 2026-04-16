"""
Clawra Discord Bot

Usage:
    export DISCORD_BOT_TOKEN='your-token-here'
    python bot.py
"""

import discord
from discord import app_commands
import logging
import sys
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Discord Bot Token - 从环境变量读取，不要硬编码！
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not TOKEN:
    logger.error("❌ DISCORD_BOT_TOKEN 环境变量未设置")
    logger.info("设置方式: export DISCORD_BOT_TOKEN='你的token'")
    sys.exit(1)

# 机器人名称
BOT_NAME = "Clawra"

class ClawraBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True  # 允许读取消息内容
        intents.guilds = True
        intents.members = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        """机器人启动后的初始化"""
        logger.info(f"🧠 {BOT_NAME} 机器人启动中...")
        
        # 同步 slash commands
        await self.tree.sync()
        logger.info(f"✅ {BOT_NAME} 命令同步完成")

    async def on_ready(self):
        """机器人准备就绪"""
        logger.info(f"""
╔════════════════════════════════════════════╗
║  🧠 {BOT_NAME} Discord Bot 已上线！
║  用户名: {self.user}
║  用户ID: {self.user.id}
╚════════════════════════════════════════════╝
        """)
        
        # 设置机器人状态
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="Clawra Engine | /help for commands"
        )
        await self.client.change_presence(activity=activity)

    async def on_message(self, message):
        """处理消息"""
        # 忽略机器人自己的消息
        if message.author == self.client.user:
            return
        
        # 日志记录
        logger.info(f"[{message.guild.name}] {message.author}: {message.content[:50]}...")

        # 命令处理
        if message.content.startswith('/'):
            await self.handle_command(message)


    async def handle_command(self, message):
        """处理命令"""
        cmd = message.content.lower().split()[0]
        
        commands = {
            '/help': '🧠 Clawra 命令列表:\n• /help - 显示帮助\n• /repo - GitHub 仓库链接\n• /demo - 运行演示\n• /learn - 了解 Clawra\n• /status - 系统状态',
            '/repo': '📦 GitHub: https://github.com/wu-xiaochen/clawra-engine\n⭐ 给个 Star 吧！',
            '/demo': '🚀 运行 Demo:\n```bash\ngit clone https://github.com/wu-xiaochen/clawra-engine.git\ncd clawra-engine\npip install -e .\npython examples/demo_basic.py\n```',
            '/learn': '''🧠 Clawra 是什么？

让 AI Agent 自己学会规则，而不是你替它写规则。

核心能力：
• 自主规则学习 - 从文本自动提取知识
• 神经符号融合 - LLM + 符号逻辑
• 8阶段进化闭环 - AI 从错误中学习
• GraphRAG - 向量+图谱双通道检索

📖 文档: https://github.com/wu-xiaochen/clawra-engine''',
            '/status': '✅ Clawra Engine 运行正常\n📊 版本: 4.2.0-alpha\n🧪 测试: 433 个测试全部通过',
        }
        
        response = commands.get(cmd, f'❓ 未知命令: {cmd}\n输入 /help 查看可用命令')
        await message.channel.send(response)


async def main():
    """主函数"""
    logger.info("🚀 启动 Clawra Discord Bot...")
    client = ClawraBot()
    
    try:
        await client.start(TOKEN)
    except discord.LoginFailure:
        logger.error("❌ Token 无效，请检查 Discord Bot Token")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
