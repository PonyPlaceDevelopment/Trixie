from discord import app_commands
from discord.ext import commands
import discord
import asyncio
import os
from dotenv import load_dotenv
import json
import re
import datetime
load_dotenv()

# .env file
# discord_token = "TOKEN"
# guild_id = the guild id where the bot should work (guild id for r/place bronies is: 1086048263620276254)


BOT_TOKEN = os.getenv("token")
guild_id = os.getenv("authserver")


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


def has_mod_role():  # role check for commands
    async def predicate(ctx):
        with open('setup_data.json', 'r') as file:
            setup_data = json.load(file)

        guild_id = ctx.guild.id
        setup_info = setup_data.get(str(guild_id))

        if setup_info:
            mod_role_id = setup_info.get("mod_role_id")
            if mod_role_id:
                mod_role = discord.utils.get(ctx.guild.roles, id=mod_role_id)
                return mod_role is not None and mod_role in ctx.author.roles
        else:
            await ctx.send("Pls run /setup first!")
        return False

    return commands.check(predicate)


def has_admin_role():  # role check for commands
    async def admin(ctx):
        with open('setup_data.json', 'r') as file:
            setup_data = json.load(file)

        guild_id = ctx.guild.id
        setup_info = setup_data.get(str(guild_id))

        if setup_info:
            admin_role_id = setup_info.get("admin_role_id")
            if admin_role_id:
                admin_role = discord.utils.get(
                    ctx.guild.roles, id=admin_role_id)
                return admin_role is not None and admin_role in ctx.author.roles
        else:
            await ctx.send("Pls run /setup first!")
        return False

    return commands.check(admin)


class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self.setup_data = {}
        self.mod_role_data = {}
        self.load_data()
        self.load_mod()

    async def setup_hook(self):
        await self.tree.sync(guild=discord.Object(id=guild_id))
        print(f"Synced slash commands for {self.user}.")

    async def on_command_error(self, ctx, error):
        await ctx.reply(error, ephemeral=True)

    def save_data(self):
        with open('setup_data.json', 'w') as file:
            json.dump(self.setup_data, file)

    def save_mod(self):
        with open('mod_role_data.json', 'w') as file:
            json.dump(self.mod_role_data, file)

    def load_mod(self):
        try:
            with open('mod_role_data.json', 'r') as file:
                self.mod_role_data = json.load(file)
        except FileNotFoundError:
            pass

    def load_data(self):
        try:
            with open('setup_data.json', 'r') as file:
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


@bot.tree.context_menu(name="ban", guild=discord.Object(id=guild_id))
async def ban(interaction: discord.Interaction, member: discord.User, ):
    try:
        await member.ban(delete_message_days=7)
        await interaction.response.send_message(f"{member.mention} got banned!", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to ban members.", ephemeral=True)
    except discord.HTTPException:
        await interaction.response.send_message("An error occurred while trying to ban the member. Please try again later.", ephemeral=True)


@bot.tree.context_menu(name="kick", guild=discord.Object(id=guild_id))
async def ban(interaction: discord.Interaction, member: discord.User):
    try:
        await member.kick()
        await interaction.response.send_message(f"{member.mention} has been kicked", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to kick members.", ephemeral=True)
    except discord.HTTPException:
        await interaction.response.send_message("An error occurred while trying to kick the member. Please try again later.", ephemeral=True)


@bot.tree.command(name="echo", description="Let the bot say something", guild=discord.Object(id=guild_id))
async def echo(interaction: discord.Interaction, input: str, channel: discord.TextChannel = None, webhook_name: str = None, webhook_image_url: str = None):
    if webhook_name and webhook_image_url and channel:
        webhook = await channel.create_webhook(name=webhook_name)
        await webhook.send(content=input, avatar_url=webhook_image_url)
        await webhook.delete()
        await interaction.response.send_message(f"Message: {input} was sent in channel: {channel.mention} with webhook: {webhook_name}!")
    else:
        if webhook_name and webhook_image_url:
            await interaction.response.send_message("You have to define a channel!")
        else:
            if channel:
                await channel.send(input)
                await interaction.response.send_message(f"Message: {input} was sent in channel: {channel.mention}")
            else:
                await interaction.response.send_message(input)


@bot.tree.context_menu(name="voicekick", guild=discord.Object(id=guild_id))
async def kick(interaction: discord.Interaction, member: discord.Member):
    voice_channel = member.voice.channel
    await member.move_to(None)
    await interaction.response.send_message(f"{member.mention} got kicked out of {voice_channel.mention}")


@bot.hybrid_command(name="purge", with_app_command=True, description="Delete messages from a channel")
@app_commands.guilds(discord.Object(id=guild_id))
@has_mod_role()
async def delete_messages(ctx, channel: discord.TextChannel, limit: int):
    messages = []
    async for message in channel.history(limit=limit):
        messages.append(message)
    await channel.delete_messages(messages)
    await ctx.send(f"{limit} messages got deleted in {channel.mention}.")


@bot.tree.command(name="setup", description="Setup cmd")
@app_commands.guilds(discord.Object(id=guild_id))
@commands.has_permissions(kick_members=True)
async def setup(interaction: discord.Interaction, mod_role: discord.Role, mod_channel: discord.TextChannel, log_channel: discord.TextChannel, member_role: discord.Role):
    setup_data = {}

    def save_data():
        with open('setup_data.json', 'w') as file:
            json.dump(setup_data, file)
    guild_id = interaction.guild.id
    if guild_id in bot.setup_data:
        await interaction.response.send_message("Setup data already exists for this server.")
        return

    setup_data[guild_id] = {
        "mod_role_id": mod_role.id,
        "mod_channel_id": mod_channel.id,
        "member_role_id": member_role.id,
        "log_channel_id": log_channel.id
    }

    save_data()
    await interaction.response.send_message("Setup complete! Now the bot is ready to use with the provided configurations.")


@bot.hybrid_command(name="admin_add_role", with_app_command=True, description="Adds Roles to the list of roles that mods can add with the /addrole command")
@app_commands.guilds(discord.Object(id=guild_id))
@has_admin_role()
async def add_entry(ctx, rolename: str, role: discord.Role):
    guild_id = str(ctx.guild.id)

    try:
        with open('mod_role_data.json', 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {}

    if guild_id not in data:
        data[guild_id] = {}

        with open('mod_role_data.json', 'w') as file:
            json.dump(data, file, indent=4)

    data[guild_id][rolename] = role.id

    with open('mod_role_data.json', 'w') as file:
        json.dump(data, file, indent=4)

    await ctx.send(f'Role "{rolename}" with value "{role.mention}" added for this guild.')


@bot.hybrid_command(name="add_role", with_app_command=True, description="Add a role to a user")
@app_commands.guilds(discord.Object(id=guild_id))
@has_mod_role()
async def add_role(ctx, member: discord.Member, role: discord.Role):
    guild_id = str(ctx.guild.id)

    try:
        with open('mod_role_data.json', 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {}

    if guild_id not in data or role.id not in data[guild_id].values():
        await ctx.send("You don't have the permission to add this role.")
        return

    if role not in member.roles:
        try:
            await member.add_roles(role)
            await ctx.send(f'Role "{role.name}" added to {member.mention}.')
        except discord.Forbidden:
            await ctx.send("I don't have the necessary permissions to add this role.")
    else:
        await ctx.send(f'{member.mention} already has the role "{role.name}".')


@bot.hybrid_command(name="testname", with_app_command=True, description="Setup cmd")
@app_commands.guilds(discord.Object(id=guild_id))
@has_mod_role()
async def membertest(ctx, testname: str):
    if is_suspicious_username(testname):
        await ctx.send("SUS")
    else:
        await ctx.send("NOT SUS YAY")


@bot.event
async def on_member_join(member):

    server_id = member.guild.id
    print("New Member!")
    username = member.name
    if is_suspicious_username(username):
        timeout_role = discord.utils.get(member.guild.roles, name="Jail")
        await member.add_roles(timeout_role, reason="suspicious name")
        print("Sus name")
    else:

        with open('setup_data.json', 'r') as file:
            setup_data = json.load(file)
            if setup_data:
                member_role_id = setup_data.get(
                    str(server_id), {}).get("member_role_id")
                member_role = discord.utils.get(
                    member.guild.roles, id=member_role_id)

                await member.add_roles(member_role)
                print("[Main INFO]: Member Role given")
            else:
                print(
                    "[Main ERROR]: No Setup Data available! No role was handed out! (Run /setup)")


bot.run(BOT_TOKEN)
