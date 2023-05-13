import asyncio
import datetime
import re
from typing import Dict, Optional

import discord
from discord.ext import tasks
from redbot.core import Config, commands
from redbot.core.bot import Red

# Constants

KARUTA_ID = 646937666251915264
DROP_REGEX = re.compile(r"<@!?([0-9]+)> is dropping ([3-4]) cards!")
AUTO_DROP_REGEX = re.compile(
    r"I'm dropping (\d+) cards since this server is currently active!"
)
MIN_DROPS = 3
DROP_ROLE_ID = 1106603803983220758
CHECK_EMOJI = discord.PartialEmoji(name="TC_checkmark", id=1081578785075384370)
ELEGANT_GUILD = 961115362051620884
DROP_LOGS = 1106602811493462057

WHITELISTED_CHANNELS = [1051328495571181588, 1106602671416299540, 1062345872647659620]

emoji = [
    "\N{FIRST PLACE MEDAL}",
    "\N{SECOND PLACE MEDAL}",
    "\N{THIRD PLACE MEDAL}",
    "\N{BLACK SMALL SQUARE}",
    "\N{BLACK SMALL SQUARE}",
    "\N{BLACK SMALL SQUARE}",
    "\N{BLACK SMALL SQUARE}",
    "\N{BLACK SMALL SQUARE}",
    "\N{BLACK SMALL SQUARE}",
    "\N{BLACK SMALL SQUARE}",
]


class Karuta(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot

        # Timezone
        self.tz = datetime.timezone.utc
        default_time = datetime.datetime(2023, 3, 19, tzinfo=self.tz)

        # Drops
        self.config = Config.get_conf(self, identifier=54564545137)
        default_global = {
            "last_daily_reset": default_time.timestamp(),
            "last_weekly_reset": default_time.timestamp(),
        }  # Random numbers

        default_guild = {"daily_drops": {}, "weekly_drops": {}}
        self.config.register_global(**default_global)
        self.config.register_guild(**default_guild)

        # Cached Data
        self.settings = (
            default_time,
            default_time,
        )  # Assiging default values just in case something gets fucked up.

        asyncio.create_task(self.initialize())  # Initialize the cog.

    async def initialize(self) -> None:
        await self.cache_configs()

        if not self.auto_reset_task.is_running():
            self.auto_reset_task.start()

    def cog_unload(self) -> None:
        self.auto_reset_task.stop()

    async def cache_configs(self) -> None:
        last_daily_reset_timestamp = await self.config.last_daily_reset()
        last_daily_reset = datetime.datetime.fromtimestamp(
            last_daily_reset_timestamp
        ).astimezone(tz=self.tz)

        last_weekly_reset_timestamp = await self.config.last_weekly_reset()
        last_weekly_reset = datetime.datetime.fromtimestamp(
            last_weekly_reset_timestamp
        ).astimezone(tz=self.tz)

        self.settings = (
            last_daily_reset,
            last_weekly_reset,
        )

    @tasks.loop(minutes=1)
    async def auto_reset_task(self) -> None:
        now = datetime.datetime.now(tz=datetime.timezone.utc)

        target_time = datetime.time(hour=6, minute=30)

        if now.time() > target_time and now.date() > self.settings[0].date():
            await self.reset_daily_drops()
            if (
                now.weekday() == 0
                and now.isocalendar().week > self.settings[1].isocalendar().week
            ):
                await self.reset_weekly_drops()

            await self.cache_configs()
        else:
            pass

    @auto_reset_task.before_loop
    async def wait_until_ready(self) -> None:
        await self.bot.wait_until_ready()

    async def reset_daily_drops(self) -> None:
        guild = self.bot.get_guild(ELEGANT_GUILD)
        if not guild:
            return

        drops_dict = await self.get_all_drops(guild, "daily")

        await self.config.guild(guild).daily_drops.set({})

        today = datetime.datetime.now(tz=self.tz)

        await self.config.last_daily_reset.set(today.timestamp())

        channel = guild.get_channel(DROP_LOGS)
        if not channel:
            return
        assert isinstance(channel, discord.TextChannel)

        embed_1 = discord.Embed(
            description="Daily karuta drops have been reset!", color=0x2B2D31
        )

        description = ""
        i = 0
        for member_id, drops in drops_dict.items():
            member = await self.bot.get_or_fetch_user(member_id)
            description += f"{emoji[i]} {member} - ` {drops} `\n"
            i += 1

        embed_2 = discord.Embed(
            title=f"Daily Drops Leaderboard",
            description=description,
            color=0x2B2D31,
        )

        for embed in (embed_1, embed_2):
            await channel.send(embed=embed)

        role = guild.get_role(DROP_ROLE_ID)
        if not role:
            return
        for member in role.members:
            try:
                await member.remove_roles(role)
            except:
                continue

    async def reset_weekly_drops(self) -> None:
        guild = self.bot.get_guild(ELEGANT_GUILD)
        if not guild:
            return

        drops_dict = await self.get_all_drops(guild, "weekly")

        await self.config.guild(guild).weekly_drops.set({})

        today = datetime.datetime.now(tz=self.tz)

        await self.config.last_weekly_reset.set(today.timestamp())

        channel = guild.get_channel(DROP_LOGS)
        if not channel:
            return
        assert isinstance(channel, discord.TextChannel)

        embed_1 = discord.Embed(
            description="Weekly karuta drops have been reset!", color=0x2B2D31
        )

        description = ""
        i = 0
        for member_id, drops in drops_dict.items():
            member = await self.bot.get_or_fetch_user(member_id)
            description += f"{emoji[i]} {member} - ` {drops} `\n"
            i += 1

        embed_2 = discord.Embed(
            title=f"Weekly Drops Leaderboard",
            description=description,
            color=0x2B2D31,
        )

        for embed in (embed_1, embed_2):
            await channel.send(embed=embed)

    @commands.Cog.listener("on_message")
    async def drop_counter(self, message: discord.Message) -> None:
        if not message.guild:
            return
        if message.author.id != KARUTA_ID:
            return
        if message.guild.id != ELEGANT_GUILD:
            return
        if message.channel.id not in WHITELISTED_CHANNELS:
            return

        matches = re.findall(DROP_REGEX, str(message.content))
        if not matches:
            return

        match = matches[0]
        user_id = int(match[0])

        member = await self.bot.get_or_fetch_member(message.guild, user_id)

        if member is None:
            return

        daily_drops = await self.config.guild(message.guild).daily_drops()
        weekly_drops = await self.config.guild(message.guild).weekly_drops()

        daily_drops[str(member.id)] = daily_drops.get(str(member.id), 0) + 1
        weekly_drops[str(member.id)] = weekly_drops.get(str(member.id), 0) + 1

        await self.config.guild(message.guild).daily_drops.set(daily_drops)
        await self.config.guild(message.guild).weekly_drops.set(weekly_drops)

        if daily_drops[str(member.id)] >= MIN_DROPS:
            role = message.guild.get_role(DROP_ROLE_ID)
            if role and not role in member.roles:
                await asyncio.sleep(60)
                await member.add_roles(role)

        await message.add_reaction(CHECK_EMOJI)

    async def get_drops(self, member: discord.Member, type: str) -> None:
        drops = await getattr(self.config.guild(member.guild), f"{type}_drops")()
        return drops.get(str(member.id), 0)

    async def get_all_drops(self, guild: discord.Guild, type: str) -> Dict[int, int]:
        drops = await getattr(self.config.guild(guild), f"{type}_drops")()
        sorted_drops = dict(sorted(drops.items(), key=lambda x: x[1], reverse=True))
        return dict(list(sorted_drops.items())[:10])

    @commands.command()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def drops(
        self,
        ctx: commands.Context,
        member: Optional[discord.Member] = None,
        type: str = "daily",
    ) -> None:
        """View your or someone's drops."""
        if not ctx.guild:
            return
        if not ctx.guild.id == ELEGANT_GUILD:
            return

        if not member:
            assert isinstance(ctx.author, discord.Member)
            member = ctx.author

        if not type.lower() in ["daily", "weekly"]:
            await ctx.send("Valid types are: `daily`, `weekly`.")

        drops = await self.get_drops(member, type)

        embed = discord.Embed(
            title=f"{member}'s {type} drops!",
            description=f"They have dropped `{drops}` times {'today' if type == 'daily' else 'this week'}.",
            color=discord.Colour.green(),
        )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="karutaleaderboard", aliases=["klb", "karutalb"])
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def karutaleaderboard(
        self,
        ctx: commands.Context,
        type: str = "daily",
    ) -> None:
        """View the karuta drops leaderboard"""
        if not ctx.guild:
            return
        if not ctx.guild.id == ELEGANT_GUILD:
            return

        if not type.lower() in ["daily", "weekly"]:
            await ctx.send("Valid types are: `daily`, `weekly`.")

        drops_dict = await self.get_all_drops(ctx.guild, type)
        description = ""
        i = 0
        for member_id, drops in drops_dict.items():
            member = await self.bot.get_or_fetch_user(member_id)
            description += f"{emoji[i]} {member} - ` {drops} `\n"
            i += 1

        embed = discord.Embed(
            title=f"{type.capitalize()} Drops Leaderboard",
            description=description,
            color=0x2B2D31,
        )

        await ctx.reply(embed=embed, mention_author=False)
