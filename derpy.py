#from typing import Optional, Union
from discord import app_commands
from discord.ext import commands
import discord
import asyncio
import os
from dotenv import load_dotenv
import json
import re
import requests
import random
from pytz import timezone
from io import BytesIO
import time
from PIL import Image, ImageDraw, ImageFont
load_dotenv()

# .env file
# discord_token = "TOKEN"
# guild_id = the guild id where the bot should work (guild id for r/place bronies is: 1086048263620276254)


BOT_TOKEN = os.getenv("place")


def is_suspicious_username(username):
    suspicious_patterns = [
        # For Cloud: Add keywords here if you want
        r"\b(?:spam|bot|nudes|18\+|nsfw|admin|dick|tits|dik|hitler|adolf)\b",
    ]

    # random signs check
    random_letters_pattern = r"^(?!.*(.).*\1)[a-z0-9]{4,}$"

    for pattern in suspicious_patterns:
        if re.search(pattern, username, re.IGNORECASE):
            return True

    if re.match(random_letters_pattern, username):
        return True

    return False


class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self.setup_data = {}
        self.mod_role_data = {}
        self.load_data()
        self.load_mod()

    async def on_command_error(self, ctx, error):
        await ctx.reply(error, ephemeral=True)

    def save_data(self):
        with open("setup_data.json", "w") as file:
            json.dump(self.setup_data, file)

    def save_mod(self):
        with open("mod_role_data.json", "w") as file:
            json.dump(self.mod_role_data, file)

    def load_mod(self):
        try:
            with open("mod_role_data.json", "r") as file:
                self.mod_role_data = json.load(file)
        except FileNotFoundError:
            pass

    def load_data(self):
        try:
            with open("setup_data.json", "r") as file:
                self.setup_data = json.load(file)
        except FileNotFoundError:
            pass


bot = Bot()

emote = None
category_name = None


class BanFlags(commands.FlagConverter):
    member: discord.Member
    days: int = 1


class KickFlags(commands.FlagConverter):
    member: discord.Member
    reason: str


class TimeoutFlags(commands.FlagConverter):
    member: discord.member
    reason: str
    duration: int

def load(file):
    try:
        with open(file, "r", encoding="UTF-8") as f:
            config = json.load(f)
            return config
    except Exception as e:
        print(e)
        return None


def save(config, file):
    try:
        with open(file, "w", encoding="UTF-8") as f:
            json.dump(config, f)
            return
    except Exception as e:
        print(e)
        return None
@bot.tree.context_menu(name="ban")
async def ban(
    interaction: discord.Interaction,
    member: discord.User,
):
    try:
        await member.ban(delete_message_days=7)
        await interaction.response.send_message(
            f"{member.mention} got banned!", ephemeral=True
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "I don't have permission to ban members.", ephemeral=True
        )
    except discord.HTTPException:
        await interaction.response.send_message(
            "An error occurred while trying to ban the member. Please try again later.",
            ephemeral=True,
        )


@bot.tree.context_menu(name="kick")
async def ban(interaction: discord.Interaction, member: discord.User):
    try:
        await member.kick()
        await interaction.response.send_message(
            f"{member.mention} has been kicked", ephemeral=True
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "I don't have permission to kick members.", ephemeral=True
        )
    except discord.HTTPException:
        await interaction.response.send_message(
            "An error occurred while trying to kick the member. Please try again later.",
            ephemeral=True,
        )


@bot.tree.context_menu(name="whothis")
async def whothis(interaction: discord.Interaction, member: discord.Member):
    embed = discord.Embed(title=f"{member.name}", description=f" {member.id}")
    embed.add_field(
        name="Joined Discord",
        value=member.created_at.strftime("%d/%m/%Y/%H:%M:%S"),
        inline=False,
    )
    embed.add_field(
        name="Roles",
        value=", ".join([role.mention for role in member.roles]),
        inline=False,
    )
    embed.add_field(
        name="Badges",
        value=", ".join([badge.name for badge in member.public_flags.all()]),
        inline=False,
    )
    embed.add_field(name="Activity", value=member.activity, inline=False)
    embed.set_thumbnail(url=member.avatar.url)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="hug", description="Hug someone :D")
async def hug(interaction: discord.Interaction, user: discord.User):
    search_query = f"https://derpibooru.org/api/v1/json/search/images?q=hug,-explicit,-suggestive,-*fetish&sf=random"
    images = "images"
    username = interaction.user
    incomplete_url = ""
    response = requests.get(search_query)
    if response.status_code == 200:
        data = response.json()
        image = random.choice(data[images])
        image_url = incomplete_url + image["representations"]["full"]
        await interaction.response.send_message(
            f"{username.mention} hugged {user.mention}!\n [Link]({image_url})"
        )


@bot.tree.command(name="kiss", description="Kiss someone :D")
async def kiss(interaction: discord.Interaction, user: discord.User):
    search_query = f"https://derpibooru.org/api/v1/json/search/images?q=kiss,-explicit,-suggestive,-*fetish&sf=random"
    images = "images"
    username = interaction.user
    incomplete_url = ""
    response = requests.get(search_query)
    if response.status_code == 200:
        data = response.json()
        image = random.choice(data[images])
        image_url = incomplete_url + image["representations"]["full"]
        await interaction.response.send_message(
            f"{username.mention} kissed {user.mention}!\n [Link]({image_url})"
        )


@bot.tree.command(name="rps", description="Play Rock, Paper, Scissors against others")
@app_commands.describe(username="@username")
@app_commands.choices(
    user_choice=[
        discord.app_commands.Choice(name="Scissors", value="1"),
        discord.app_commands.Choice(name="Rock", value="2"),
        discord.app_commands.Choice(name="Paper", value="3"),
    ]
)
async def rps_user(
    interaction: discord.Interaction, username: discord.User, user_choice: str
):
    challenger = interaction.user
    opponent = username

    class SSPMultiplayerView(discord.ui.View):
        def __init__(self, challenger, opponent):
            super().__init__()
            self.challenger = challenger
            self.opponent = opponent

        async def interaction_callback(self, interaction: discord.Interaction):
            if self.challenger == self.opponent:
                await interaction.response.send_message(
                    "You can't play against yourself", ephemeral=True
                )
                return
            message_content = f"### {opponent.mention}, yout got challenged by {self.challenger.mention} to play some Rock Paper Scissors"
            print(user_choice)
            message = await interaction.response.send_message(
                message_content, view=self
            )
            return message

        async def disable_buttons(self, interaction):
            for child in self.children:
                child.disabled = True
            await interaction.message.edit(content="Game started", view=self)

        @discord.ui.button(label="Scissors", style=discord.ButtonStyle.grey)
        async def schere_callback(self, interaction, button):
            if (
                self.opponent != interaction.user
            ):  # Only allow the challenged user to click
                await interaction.response.send_message(
                    "Only your opponent can use this!", ephemeral=True
                )
                return

            await interaction.response.send_message(f"Success", ephemeral=True)
            await self.disable_buttons(interaction)
            await game_logic(user_choice, "1")
            print("Schere")

        @discord.ui.button(label="Stone", style=discord.ButtonStyle.grey)
        async def stein_callback(self, interaction, button):
            if (
                self.opponent != interaction.user
            ):  # Only allow the challenged user to click
                await interaction.response.send_message(
                    "Only your opponent can use this!", ephemeral=True
                )
                return

            await interaction.response.send_message(f"Success", ephemeral=True)
            await self.disable_buttons(interaction)
            await game_logic(user_choice, "2")
            print("Stein")

        @discord.ui.button(label="Paper", style=discord.ButtonStyle.grey)
        async def papier_callback(self, interaction, button):
            if (
                self.opponent != interaction.user
            ):  # Only allow the challenged user to click
                await interaction.response.send_message(
                    "Only your opponent can use this!", ephemeral=True
                )
                return

            await interaction.response.send_message(f"Success", ephemeral=True)
            await self.disable_buttons(interaction)
            await game_logic(user_choice, "3")
            print("Papier")

    async def game_logic(view, user_choice):
        win_conditions = {"3": "1", "2": "3", "1": "2"}

        user_options = ["1", "2", "3"]
        bot_choice = random.choice(user_options)

        emojis = {"1": "✂️", "2": "🪨", "3": "📜"}
        await asyncio.sleep(1)
        if user_choice == view:
            before = await interaction.original_response()
            await before.edit(
                content=f"### Tie! {opponent.mention} also choose {emojis[user_choice]}"
            )
        else:
            if win_conditions[user_choice] == view:
                before = await interaction.original_response()
                await before.edit(
                    content=f"### {challenger.mention} won! {emojis[view]} beats {emojis[user_choice]}!"
                )
            else:
                before = await interaction.original_response()
                await before.edit(
                    content=f"### {challenger.mention} lost! {emojis[user_choice]} beats {emojis[view]}!"
                )

    view = SSPMultiplayerView(challenger, opponent)
    message = await view.interaction_callback(interaction)
    return message


@bot.tree.command(name="echo", description="Let the bot say something")
async def echo(
    interaction: discord.Interaction,
    input: str,
    channel: discord.TextChannel = None,
    webhook_name: str = None,
    webhook_image_url: str = None,
):
    if webhook_name and webhook_image_url and channel:
        webhook = await channel.create_webhook(name=webhook_name)
        await webhook.send(content=input, avatar_url=webhook_image_url)
        await webhook.delete()
        await interaction.response.send_message(
            f"Message: {input} was sent in channel: {channel.mention} with webhook: {webhook_name}!",
            ephemeral=True,
        )
    else:
        if webhook_name and webhook_image_url:
            await interaction.response.send_message(
                "You have to define a channel!", ephemeral=True
            )
        else:
            if channel:
                await channel.send(input)
                await interaction.response.send_message(
                    f"Message: {input} was sent in channel: {channel.mention}",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(input)


@bot.tree.context_menu(name="voicekick")
async def kick(interaction: discord.Interaction, member: discord.Member):
    voice_channel = member.voice.channel
    await member.move_to(None)
    await interaction.response.send_message(
        f"{member.mention} got kicked out of {voice_channel.mention}", ephemeral=True
    )


@bot.tree.command(name="purge", description="Delete messages from a channel")
async def delete_messages(
    interaction: discord.Interaction, channel: discord.TextChannel, limit: int
):
    messages = []
    async for message in channel.history(limit=limit):
        messages.append(message)
    await channel.delete_messages(messages)
    await asyncio.sleep(4)
    await interaction.response.send_message(
        f"{limit} messages got deleted in {channel.mention}.", ephemeral=True
    )


@bot.tree.command(name="setup", description="Setup cmd")
@commands.has_permissions(kick_members=True)
async def setup(
    interaction: discord.Interaction,
    mod_role: discord.Role,
    mod_channel: discord.TextChannel,
    log_channel: discord.TextChannel,
    member_role: discord.Role,
):  
    with open("setup_data.json", "r") as file:
        setup_data = json.load(file)
        print(setup_data)
    if setup_data is None:
        setup_data = {}
    if str(interaction.guild_id) not in setup_data:
        setup_data[str(interaction.guild_id)] = {}

    setup_data[str(interaction.guild_id)].update({
        "mod_role_id": mod_role.id,
        "mod_channel_id": mod_channel.id,
        "member_role_id": member_role.id,
        "log_channel_id": log_channel.id,
    })
    save(setup_data, "setup_data.json")

    await interaction.response.send_message(
        "Setup complete! Now the bot is ready to use with the provided configurations."
    )


@bot.tree.command(name="ticket_setup", description="Setup tickets cmd")
@commands.has_permissions(kick_members=True)
async def setup(
    interaction: discord.Interaction,
    create_channels_auto: bool,
    ticket_role: discord.Role = None,
    ticket_category: discord.CategoryChannel = None,
):
    with open("setup_data.json", "r") as file:
        setup_data = json.load(file)
    if not setup_data:
        await interaction.response.send_message("Run /setup first", ephemeral=True)
        return
    if str(interaction.guild_id) not in setup_data:
        await interaction.response.send_message("Run /setup first!", ephemeral=True)
        return
    if create_channels_auto is True and ticket_role is None and ticket_category is None:
        category = discord.utils.get(
            interaction.guild.categories, name="Pending Tickets"
        )
        if category is None:
            category = await interaction.guild.create_category("Pending Tickets")
            cooldown_role = discord.utils.get(
                interaction.guild.roles, name="Ticket Cooldown"
            )
        if cooldown_role is None:
            cooldown_role = await interaction.guild.create_role("Ticket Cooldown")
    else:
        if ticket_role is None or ticket_category is None:
            interaction.response.send_message(
                "Pleaso provide both ticket_role and ticket_category!", ephemeral=True
            )
            return
        category = ticket_category
        cooldown_role = ticket_role
        ticket_data = {"ticket_role": cooldown_role.id, "ticket_category": category.id}

    setup_data[str(interaction.guild_id)].update(ticket_data)
    save(setup_data, "setup_data.json")

    await interaction.response.send_message(
        "Setup complete! Now the bot is ready to use with the provided configurations."
    )


@bot.event
async def on_member_join(member):
    server_id = member.guild.id
    print("New Member!")
    username = member.name
    if is_suspicious_username(username):
        print("Sus name")
    else:
        with open("setup_data.json", "r") as file:
            setup_data = json.load(file)
            if setup_data:
                member_role_id = setup_data.get(str(server_id), {}).get(
                    "member_role_id"
                )
                member_role = discord.utils.get(member.guild.roles, id=member_role_id)

                await member.add_roles(member_role)
                print("[Main INFO]: Member Role given")
            else:
                print(
                    "[Main ERROR]: No Setup Data available! No role was handed out! (Run /setup)"
                )


@bot.event
async def on_message_edit(before, after):
    with open("setup_data.json", "r") as file:
        setup_data = json.load(file)
        server_id = after.author.guild.id
        if before.content == after.content:
            return
        if setup_data:
            channel_id = setup_data.get(str(server_id), {}).get("log_channel_id")
            channel = bot.get_channel(channel_id)
            if after.author.bot:
                return
            embed = discord.Embed(color=discord.Color.blue())
            embed.add_field(
                name=f"Message Edited in {after.channel.mention}",
                value=f"[Jump to Message](https://discordapp.com/channels/{server_id}/{after.channel.id}/{after.id})",
                inline=False,
            )
            embed.add_field(name="User", value=after.author.mention, inline=False)
            embed.set_author(name=before.author.name, icon_url=before.author.avatar.url)
            embed.add_field(name="Before", value=before.content, inline=False)
            embed.add_field(name="After", value=after.content, inline=False)
            embed.set_footer(text=f"User ID: {after.author.id}")
            await channel.send(embed=embed)
        else:
            return


@bot.event
async def on_member_join(member):
    with open("setup_data.json", "r") as file:
        setup_data = json.load(file)
        server_id = member.guild.id
        if setup_data:
            channel_id = setup_data.get(str(server_id), {}).get("log_channel_id")
            mod_channel_id = setup_data.get(str(server_id), {}).get("mod_channel_id")
            mod_channel = bot.get_channel(mod_channel_id)
            channel = bot.get_channel(channel_id)
            if is_suspicious_username(member.name):
                await mod_channel.send(f"{member.mention} got detected by the sus name detection")
            if member.bot:
                return
            embed = discord.Embed(
                description=f"{member.mention} {member.name}",
                color=discord.Color.green(),
            )
            embed.set_author(name="Member Joined", icon_url=member.avatar.url)
            embed.add_field(name="Created at", value=member.created_at, inline=False)
            embed.set_footer(text=f"User ID: {member.id}")
            await channel.send(embed=embed)


@bot.event
async def on_member_remove(member):
    with open("setup_data.json", "r") as file:
        setup_data = json.load(file)
        server_id = member.guild.id
        if setup_data:
            channel_id = setup_data.get(str(server_id), {}).get("log_channel_id")
            channel = bot.get_channel(channel_id)
            if member.bot:
                return
            embed = discord.Embed(
                description=f"{member.mention} {member.name}",
                color=discord.Color.green(),
            )
            embed.set_author(name="Member Left", icon_url=member.avatar.url)
            embed.set_footer(text=f"User ID: {member.id}")
            await channel.send(embed=embed)


# @bot.event
# async def on_member_update(before, after):
# with open('setup_data.json', 'r') as file:
# setup_data = json.load(file)
# server_id = before.guild.id
# setup_data:
# channel_id = setup_data.get(str(server_id), {}).get("log_channel_id")
# channel = bot.get_channel(channel_id)
# if before.bot:
# return
# embed=discord.Embed(description = f"{after.mention} {after.name}", color=discord.Color.orange())
# embed.set_author(name="User updated", icon_url=after.avatar.url)
# embed.add_field(name="Before", value=before.global_name)
# embed.add_field(name="After", value=after.global_name)
# embed.set_footer(text=f"User ID: {after.id}")
# await channel.send(embed=embed)


@bot.event
async def on_message_delete(message):
    with open("setup_data.json", "r") as file:
        setup_data = json.load(file)
        server_id = message.guild.id  # Using message.guild.id directly
        if setup_data:
            channel_id = setup_data.get(str(server_id), {}).get("log_channel_id")
            channel = bot.get_channel(channel_id)
            if message.author.bot:
                return
            if not message.attachments:
                embed = discord.Embed(color=discord.Color.red())
                embed.set_author(
                    name=message.author.name, icon_url=message.author.avatar.url
                )
                embed.add_field(
                    name=f"Message deleted in {message.channel.mention}",
                    value=message.content,
                    inline=False,
                )
                embed.add_field(
                    name="Author", value=message.author.mention, inline=False
                )
                embed.set_footer(text=f"Message ID: {message.id}")

            # Check for attachments (images) in the deleted message
            if message.attachments:
                image_urls = message.attachments[0].url
                print(image_urls)
                embed = discord.Embed(color=discord.Color.red())
                embed.set_author(
                    name=message.author.name, icon_url=message.author.avatar.url
                )
                embed.add_field(
                    name=f"Attachment deleted in {message.channel.mention}",
                    value=message.content,
                    inline=False,
                )
                embed.add_field(
                    name="Author", value=message.author.mention, inline=False
                )
                embed.set_footer(text=f"Message ID: {message.id}")
                if image_urls:
                    embed.set_image(
                        url=image_urls
                    )  # Only adding the first image URL if multiple images are attached

            await channel.send(embed=embed)


async def process_booru_command(
    interaction: discord.Interaction, url, images, incomplete_url
):
    # main body of booru commands in separate func to avoid code repetition
    if url == None:
        await interaction.response.send_message(f"Missing argument search query")
    else:
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            if images in data and len(data[images]) > 0:
                image = random.choice(data[images])
                image_url = incomplete_url + image["representations"]["full"]
                if "uploader" in image:
                    author = image["uploader"]
                else:
                    author = "anonymous"
                embed = discord.Embed(color=discord.Color.pink())
                embed.add_field(name="Author", value=author)
                embed.set_image(url=image_url)
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message("No picture was found")
        else:
            await interaction.response.send_message(
                "Error occured while searching for pictures"
            )


@bot.tree.command(name="manebooru", description="Search for pictures on Manebooru")
async def manebooru(interaction: discord.Interaction, search_query: str = None):
    if search_query != None:
        search_query = f"https://manebooru.art/api/v1/json/search/images?q={search_query},-explicit,-suggestive,-*fetish&sf=random"

    await process_booru_command(interaction, search_query, "images", "")


@bot.tree.command(name="derpibooru", description="Search for pictures on Derpibooru")
async def manebooru(interaction: discord.Interaction, search_query: str = None):
    if search_query != None:
        search_query = f"https://derpibooru.org/api/v1/json/search/images?q={search_query},-explicit,-suggestive,-*fetish&sf=random"

    await process_booru_command(interaction, search_query, "images", "")


async def create_transcript(channel):
    messages = channel.history(limit=None)
    html_content = "<html>\n<body>\n"
    file = "transcript.html"

    async for message in messages:
        html_content += (
            f"<p>{message.author.name} - {message.created_at}: {message.content}</p>\n"
        )
    html_content += "</body>\n</html>"

    with open(file, "w", encoding="UTF-8") as f:
        f.write(html_content)

    try:
        with open(file, "rb") as html:
            msg = await channel.send(
                file=discord.File(html, filename="transcript.html")
            )
    except Exception as e:
        print(f"Error sending file: {e}")
    else:
        # Ensure the file is sent before attempting deletion
        try:
            await msg.publish()
        except Exception as e:
            print(f"Error publishing message: {e}")
        finally:
            os.remove(file)  # Delete the file after it's sent


@bot.tree.command(name="close_request", description="Request to close a ticket")
async def close_request(interaction: discord.Interaction, reason: str):
    text_channel = interaction.channel
    guild_id = interaction.guild_id
    if "ticket" not in text_channel.name:
        await interaction.response.send_message(
            "Current channel is not a ticket channel", ephemeral=True
        )

    class TicketMessageView(discord.ui.View):
        def __init__(self):
            super().__init__()

        @discord.ui.button(label="Delete ticket", style=discord.ButtonStyle.red)
        async def ticket_close_callback(self, interaction, button):
            data = load("setup_data.json")
            if data and str(interaction.guild_id) in data:
                mod_role_id = data.get(str(interaction.guild_id), {}).get("mod_role_id")
                mod_role = discord.utils.get(interaction.guild.roles, id=mod_role_id)
                if mod_role in interaction.user.roles:
                    await interaction.response.send_message(
                        "Closing ticket...", ephemeral=True
                    )
                    await interaction.channel.delete()
                else:
                    await interaction.response.send_message(
                        "You don't have the permission to run this command!",
                        ephemeral=True,
                    )
            else:
                await interaction.response.send_message(
                    "Bot needs some config! Please run /setup first", ephemeral=True
                )

        @discord.ui.button(label="Create transcript", style=discord.ButtonStyle.grey)
        async def transcript_callback(self, interaction, button):
            data = load("setup_data.json")
            if data and str(interaction.guild_id) in data:
                mod_role_id = data.get(str(interaction.guild_id), {}).get("mod_role_id")
                mod_role = discord.utils.get(interaction.guild.roles, id=mod_role_id)
                if mod_role in interaction.user.roles:
                    await interaction.response.send_message("Creating transcript...")
                    await create_transcript(interaction.channel)
                    await interaction.channel.send(
                        f"Ticket transcript created by {interaction.user.mention}."
                    )

                    # Disable button
                    button.disabled = True
                else:
                    await interaction.response.send_message(
                        "You don't have permission to run this command", ephemeral=True
                    )
            else:
                await interaction.response.send_message(
                    "Bot needs some config! Please run /setup first", ephemeral=True
                )

    class close_view(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
            self.textchannel = text_channel
            self.guild_id = guild_id

        async def disable_buttons(self, interaction):
            for child in self.children:
                child.disabled = True

        @discord.ui.button(label="Close", style=discord.ButtonStyle.red)
        async def close_callback(self, interaction, button):
            guild = interaction.guild
            setup_data = load("setup_data.json")
            timeout_role_id = setup_data.get(str(interaction.guild_id), {}).get("ticket_role")
            timeout_role = discord.utils.get(interaction.guild.roles, id=timeout_role_id)
            await interaction.response.send_message(
                "Ticket will be closed in 3 seconds."
            )
            await interaction.channel.edit(name=f"closed-{interaction.channel.name}")
            await interaction.user.remove_roles(timeout_role)
            await interaction.channel.send(
                f"Ticket closed by {interaction.user.mention}. Reason: {reason}"
            )
            await self.disable_buttons(interaction)
            user_id = 1014344645020495942
            await interaction.channel.set_permissions(
                interaction.user, read_messages=False, send_messages=False, view_channel=False
            )
            user = await interaction.guild.fetch_member(user_id)
            await interaction.channel.set_permissions(
                user, read_messages=True, send_messages=True
            )
            data = load("setup_data.json")
            if data and str(interaction.guild_id) in data:
                mod_role_id = data.get(str(interaction.guild_id), {}).get("mod_role_id")
                mod_role = discord.utils.get(interaction.guild.roles, id=mod_role_id)
            await interaction.channel.set_permissions(
                mod_role, read_messages=True, send_messages=True
            
            )
            embed = discord.Embed(
                description=f"Ticket closed by {interaction.user.mention}",
                color=discord.Color.yellow(),
            )
            adminEmbed = discord.Embed(title="```Support team ticket controls```")

            await interaction.channel.send(embed=embed)
            await interaction.channel.send(embed=adminEmbed, view=TicketMessageView())

            await interaction.message.delete(delay=1)

        @discord.ui.button(label="Deny", style=discord.ButtonStyle.gray)
        async def deny_callback(self, interaction, button):
            await interaction.response.send_message(
                "User has declined the close request."
            )
            button.disabled = True
            await self.disable_buttons(interaction)
            await interaction.message.delete(delay=1)

    await interaction.response.send_message(
        f"{interaction.user.mention} requested to close the ticket!", view=close_view()
    )


user_role = None


@bot.tree.command(name="ticket", description="setup ticket system")
@app_commands.choices(
    button_color=[
        discord.app_commands.Choice(name="Blue", value="primary"),
        discord.app_commands.Choice(name="Grey", value="grey"),
        discord.app_commands.Choice(name="Green", value="green"),
        discord.app_commands.Choice(name="Red", value="red"),
    ]
)
async def ticket_system(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    button_message: str,
    ticket_name: str,
    button_color: str
):
    setup_check = load("setup_data.json")
    if setup_check:
        if interaction.guild_id in setup_check:
            ticket_role_id = setup_check.get(
                str(interaction.guild_id), {}.get("ticket_role")
            )
            ticket_category_id = setup_check.get(
                str(interaction.guild_id), {}.get("ticket_category")
            )
            if ticket_category_id is None or ticket_role_id is None:
                interaction.response.send_message(
                    "Please set up ticket roles first! (/ticket_setup)", ephemeral=True
                )
                return
    else:
        interaction.response.send_message(
            "Please set up ticket roles first! (/ticket_setup)", ephemeral=True
        )

    textchannel = channel

    class TicketMessageView(discord.ui.View):
        def __init__(self):
            super().__init__()
            self.text_close_channel = textchannel

        async def interaction_close_callback(
            self, interaction: discord.Interaction, channelus: discord.TextChannel
        ):
            message_content = f"Welcome {interaction.user.mention}! Please stand by until a Moderator has time for your problem"
            message = await channelus.send(message_content)
            return message

        @discord.ui.button(label="Delete ticket", style=discord.ButtonStyle.red)
        async def ticket_close_callback(self, interaction, button):
            data = load("setup_data.json")
            if data and str(interaction.guild_id) in data:
                mod_role_id = data.get(str(interaction.guild_id), {}).get("mod_role_id")
                mod_role = discord.utils.get(interaction.guild.roles, id=mod_role_id)
                if mod_role in interaction.user.roles:
                    await interaction.response.send_message("Deleting ticket...")
                    await interaction.channel.delete()
                else:
                    await interaction.response.send_message(
                        "You dont have permission to do that!", ephemeral=True
                    )

    class TicketView(discord.ui.View):
        def __init__(self):
            super().__init__()
            self.channel = textchannel

        async def interaction_callback(self, interaction: discord.Interaction):
            message_content = f"{button_message}"
            message = await self.channel.send(message_content, view=self)
            await interaction.response.send_message("Ticket button(s) created")

            return message

        button_styless = {
            "primary": discord.ButtonStyle.primary,
            "grey": discord.ButtonStyle.grey,
            "green": discord.ButtonStyle.green,
            "red": discord.ButtonStyle.red,
        }

        @discord.ui.button(
            label=f" Create {ticket_name} ticket", style=button_styless[button_color]
        )
        async def ticket_callback(self, interaction, button):
            guild = interaction.guild
            username = interaction.user.name
            user = interaction.user
            data = load("setup_data.json")
            if data and str(interaction.guild_id) in data:
                ticket_role_id = data.get(str(interaction.guild_id), {}).get("ticket_role")
                ticket_role = discord.utils.get(guild.roles, id=ticket_role_id)
                ticket_category_id = data.get(str(interaction.guild_id), {}).get("ticket_category")

                print(ticket_category_id)
                category = discord.utils.get(guild.categories, id=ticket_category_id)
                print(category)
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(
                    view_channel=False, read_messages=False
                ),
                guild.me: discord.PermissionOverwrite(
                    read_messages=True, send_messages=True
                ),
                user: discord.PermissionOverwrite(
                    read_messages=True, send_messages=True
                ),
            }

            channel = await category.create_text_channel(
                f"{ticket_name}-ticket-{username}", overwrites=overwrites
            )

            await interaction.user.add_roles(ticket_role)
            welcomeView = TicketMessageView()
            message = await welcomeView.interaction_close_callback(interaction, channel)
            await interaction.response.send_message(
                f"Ticket created! {channel.mention}", ephemeral=True
            )
            return message

    view = TicketView()
    message = await view.interaction_callback(interaction)
    return message
@bot.tree.command(name="create_channel", description="Admins are to lazy so this exists")
async def c_channel(interaction: discord.Interaction, channel_name: str, category: discord.CategoryChannel = None, category_name: str = None):
    guild = interaction.guild
    user = interaction.user
    if category is not None:
        overwrites = {
                guild.default_role: discord.PermissionOverwrite(
                    view_channel=False, read_messages=False
                ),
                guild.me: discord.PermissionOverwrite(
                    read_messages=True, send_messages=True
                ),
                user: discord.PermissionOverwrite(
                    read_messages=True, send_messages=True
                )
            }
        await category.create_text_channel(
            f"{channel_name}",
            overwrites = overwrites
        )
        await interaction.response.send_message("Channel created", ephemeral=True)
    else:
        if category_name is not None:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(
                    view_channel=False, read_messages=False
                ),
                guild.me: discord.PermissionOverwrite(
                    read_messages=True, send_messages=True
                ),
                user: discord.PermissionOverwrite(
                    read_messages=True, send_messages=True
                )
            }
        categoryname = await interaction.guild.create_category(name=category_name)
        await categoryname.create_text_channel(
            f"{channel_name}",
            overwrites = overwrites
        )
        await interaction.response.send_message("Channel created", ephemeral=True)


@bot.tree.command(name="unsync", description="Unsync unused commands")
async def test(interaction: discord.Interaction):
    guild = interaction.guild_id
    await interaction.response.send_message("Unsynced Commands")
    await bot.tree.sync(guild=discord.Object(id=guild))
# level system
@bot.tree.command(name="rank", description="Display your current chat level")
async def levelcard(interaction: discord.Interaction,
                    user: discord.User = None):
  if user is None:
    user = interaction.user

  guild_id = str(interaction.guild_id)
  user_id = str(user.id)

  levels = load("levels.json")

  if levels is not None and guild_id in levels and user_id in levels[guild_id]:
    username = user.name
    level = levels.get(str(interaction.guild_id), {}).get(str(user_id), {}).get("level")
    current_xp = levels.get(str(interaction.guild_id), {}).get(str(user_id), {}).get("xp")
    next_level = 5*level**2 + 50*level + 100

    card_width = 380
    card_height = 110
    progress_bar_radius = 50  # Adjust the radius for the circular progress bar
    image = Image.new("RGB", (card_width, card_height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    large_font = ImageFont.load_default()
    draw.text((20, 20),
              f"{username}'s Card",
              fill=(0, 0, 0),
              font=large_font)
    draw.text((20, 40), f"Level: {level}", fill=(0, 0, 0), font=large_font)
    draw.text((20, 60), f"{current_xp}/{next_level} XP", fill=(0, 0, 0), font=large_font)


    # Circular progress bar creation
    progress_bar_position = (200, 55)  # Adjust the position of the circular progress bar
    end_angle = int(360 * (current_xp / next_level))
    draw.arc([(progress_bar_position[0] - progress_bar_radius, progress_bar_position[1] - progress_bar_radius),
              (progress_bar_position[0] + progress_bar_radius, progress_bar_position[1] + progress_bar_radius)],
             start=0,
             end=360,
             fill=(200, 200, 200),
             width=20)  # Draw background circle

    draw.arc([(progress_bar_position[0] - progress_bar_radius, progress_bar_position[1] - progress_bar_radius),
              (progress_bar_position[0] + progress_bar_radius, progress_bar_position[1] + progress_bar_radius)],
             start=0,
             end=end_angle,
             fill=(0, 128, 128),
             width=20)  # Draw progress arc

    # Draw the level number in the center of the circular progress bar
    level_text = f"{level}"
    text_position = (progress_bar_position[0] - len(level_text) * 5, progress_bar_position[1] - 7)
    draw.text(text_position, level_text, fill=(0, 0, 0), font=font)

    # Avatar handling
    avatar_response = requests.get(user.avatar.url)
    if avatar_response.status_code == 200:
        avatar_image = Image.open(BytesIO(avatar_response.content))
        avatar_image = avatar_image.resize((80, 80))  # Resize the avatar image if needed
        image.paste(avatar_image, (290, 10))
    else:
        print(f"Failed to fetch the image. Status code: {avatar_response.status_code}")

    image.save("level_card.png")

    # Send the level card
    await interaction.response.send_message(file=discord.File("level_card.png")
                                            )
    os.remove("level_card.png")
  else:
    await interaction.response.send_message(
        "You don't have a level yet. Start chatting to earn XP!", ephemeral=True)


# commands

xp_cooldown = {}


@bot.event
async def on_message(message):
    if message.author.bot or message.guild is None:
        return

    # Check if user has a cooldown
    if str(message.author.id) in xp_cooldown and time.time() - xp_cooldown[message.author.id] < 60:
        print("Test")
        return

    try:
        levels = load("levels.json")
    except Exception as e:
        print(e)
        levels = None

    if levels is None:
        levels = {}
    if str(message.guild.id) not in levels:
        levels[str(message.guild.id)] = {}
    if str(message.author.id) not in levels[str(message.guild.id)]:
        levels[str(message.guild.id)][str(message.author.id)] = {}

        # Initialize new guild and user entry
        add_xp = random.randint(15, 25)
        current_xp = 0
        xp = current_xp + add_xp
        lvl = 0
        next_level = 5*lvl**2 + 50*lvl + 100

        if xp >= next_level:
            xp = xp - next_level
            lvl = lvl + 1

        levels[str(message.guild.id)][str(message.author.id)].update({
            "level": lvl,
            "xp": xp 
        })
        
        save(levels, "levels.json")
    else:

        if levels is None:
            levels = {}
        if str(message.guild.id) not in levels:
            levels[str(message.guild.id)] = {}
        if str(message.author.id) not in levels[str(message.guild.id)]:
            levels[str(message.guild.id)][str(message.author.id)] = {}
        # Initialize new user entry
            add_xp = random.randint(15, 25)
            current_xp = 0
            xp = current_xp + add_xp
            lvl = 0
            next_level = 5*lvl**2 + 50*lvl + 100

            if xp >= next_level:
                xp = xp - next_level
                lvl = lvl + 1
                print(xp, lvl)

            levels[str(message.guild.id)][str(message.author.id)].update({
                "level": lvl,
                "xp": xp 
            })
            save(levels, "levels.json")
        else:
        # Existing user, update their data
            # user_levels = levels[str(guild_id)][str(user_id)]
            lvl = levels.get(str(message.guild.id), {}).get(str(message.author.id), {}).get("level")
            current_xp = levels.get(str(message.guild.id), {}).get(str(message.author.id), {}).get("xp")
            add_xp = random.randint(15, 25)
            xp = current_xp + add_xp
            print(xp)
            next_level = 5*lvl**2 + 50*lvl + 100

            if xp >= next_level:
                xp = xp - next_level
                lvl = lvl + 1
                print(xp, lvl)

            levels[str(message.guild.id)][str(message.author.id)].update({
                "level": lvl,
                "xp": xp 
            })
            print(levels)
            save(levels, "levels.json")

  # After XP is earned, update the cooldown
    xp_cooldown[message.author.id] = time.time()

@bot.event
async def on_ready():
    global guild
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching, name="A Heartswarming Tail"
        )
    )
    print("logged in")
    await bot.tree.sync(guild=discord.Object(id=1086048263620276254)) # place
    #await bot.tree.sync(guild=discord.Object(id=1183697496342536252)) # test
    try:
        synced = await bot.tree.sync()
        print(f"Synced{len(synced)} command(s)")
    except Exception as e:
        pass


bot.run(BOT_TOKEN)