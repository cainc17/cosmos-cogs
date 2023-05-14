from example_slash import ExampleSlash

from redbot.core.bot import Red

async def setup(bot: Red) -> None:
    await bot.add_cog(ExampleSlash(bot))