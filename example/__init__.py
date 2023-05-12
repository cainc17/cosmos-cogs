from redbot.core.bot import Red

from .example import ExampleCog


async def setup(bot: Red) -> None:
    await bot.add_cog(ExampleCog(bot))
