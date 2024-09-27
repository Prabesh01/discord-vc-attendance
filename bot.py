
import discord
from discord.ext import tasks
from discord.ext.commands import Bot
from discord import app_commands
import os, json
from datetime import datetime
import traceback
import pytz
tz_NP = pytz.timezone('Asia/Kathmandu')


basepath=os.path.dirname(os.path.abspath(__file__))
from dotenv import load_dotenv
load_dotenv(basepath+'/data/.env')
user_file=basepath+'/data/user.json'
attendance_file=basepath+'/data/attendance.json'

intents = discord.Intents.default()
bot = Bot(command_prefix='/', intents=intents)
bot.remove_command('help')


def read_json(fname):
    with open(basepath+'/data/'+fname+'.json', 'r') as f:
        return json.load(f)


def write_json(fname, data):
    with open(basepath+'/data/'+fname+'.json', 'w') as f:
        json.dump(data, f, indent=4)


@bot.event
async def on_error(event, *args, **kwargs):
    embed = discord.Embed(title=':x: Role.py - Error', colour=0xe74c3c)
    embed.add_field(name='Event', value=event)
    embed.description = '```py\n%s\n```' % traceback.format_exc()
    embed.timestamp = datetime.datetime.utcnow()
    bot.AppInfo = await bot.application_info()
    await bot.AppInfo.owner.send(embed=embed)


@app_commands.command(name="enroll", description="Provude your details.")
@app_commands.describe(id="Your Londeon Met ID", name="Your name", section="Your Section")
@app_commands.choices(years=[
    app_commands.Choice(name="Year 1 Autumn", value="1 - Autumn"),
    app_commands.Choice(name="Year 1 Spring", value="1 - Spring"),
    app_commands.Choice(name="Year 2", value="2"),
    app_commands.Choice(name="Year 3", value="3"),
    ])
async def enroll(interaction: discord.Interaction, id: str, name: str=None, years: app_commands.Choice[str]= None, section: int= None):
    user_data=read_json('user')
    data = {
        "username": interaction.user.name,
        "lid": id,
        "name": name,
        "year": years.value if years else None,
        "section": section
    }
    if str(interaction.user.id) in user_data:
        txt="Enrollment Updated Sucessfully!"
    else:
        txt="Enrolled Sucessfully!"
    user_data[str(interaction.user.id)]=data
    write_json('user', user_data)
    await interaction.response.send_message(txt, ephemeral=True)


@bot.event
async def on_voice_state_update(member, before, after):
    now=datetime.now(tz_NP)
    if now.weekday() != 3 or now.hour != 15: return
    if after.channel and after.channel.id==1289057002311385118:
        attendance=read_json('attendance')
        date_now=now.strftime('%Y-%m-%d')
        if date_now not in attendance:
            attendance[date_now]=[]
        if not member.id in attendance[date_now]:
            attendance[date_now].append(member.id)
            write_json('attendance', attendance)
        await member.move_to(None)


@bot.event
async def on_ready() -> None:
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="for attendees"))
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    bot.tree.add_command(enroll)
    await bot.tree.sync()


bot.run(os.getenv("bot_token"))
