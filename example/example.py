import discord
from redbot.core import (
    commands,  # you cannot import commands from discord.ext for redbots
)
from redbot.core.bot import Red


class ExampleCog(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot

    @commands.command()
    async def example_command(self, ctx: commands.Context) -> None:
        """This is an example."""
        await ctx.send("Hello World!")
