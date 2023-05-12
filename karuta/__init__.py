from .karuta import Karuta


async def setup(bot):
    await bot.add_cog(Karuta(bot))
