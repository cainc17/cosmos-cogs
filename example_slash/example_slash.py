import discord
from redbot.core import commands, app_commands # instead of `from discord.ext import commands, app_commands`

from redbot.core.bot import Red

class ExampleSlash(commands.Cog):

    def __init__(self, bot: Red):
        self.bot = bot

    @app_commands.command()
    async def hello(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message("Hello!")
        
         @app_commands.command()
    async def event(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message("<@&!")

        # if your command takes more than 3s to process, you must defer
        # 
        # import asyncio
        # 
        # await interaction.response.defer()
        # await asyncio.sleep(3)
        # await interaction.followup.send("Hello after 3 seconds")

        # if you want to respond ephemerally
        # await interaction.response.send_message("Only you can see this message", ephemeral=True)
