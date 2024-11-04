
import discord
from discord.ext.commands import Bot
from discord import app_commands
import os, json
from datetime import datetime
import traceback
import pytz
import requests
import re
tz_NP = pytz.timezone('Asia/Kathmandu')


basepath=os.path.dirname(os.path.abspath(__file__))
from dotenv import load_dotenv
load_dotenv(basepath+'/data/.env')
user_file=basepath+'/data/user.json'
attendance_file=basepath+'/data/attendance.json'

intents = discord.Intents.default()
intents.message_content = True
bot = Bot(command_prefix='/', intents=intents)
bot.remove_command('help')


def read_json(fname):
    with open(basepath+'/data/'+fname+'.json', 'r') as f:
        return json.load(f)


def write_json(fname, data):
    file=basepath+'/data/'+fname+'.json'
    with open(file, 'w') as f:
        json.dump(data, f, indent=4)


@bot.event
async def on_error(event, *args, **kwargs):
    embed = discord.Embed(title=':x: Role.py - Error', colour=0xe74c3c)
    embed.add_field(name='Event', value=event)
    embed.description = '```py\n%s\n```' % traceback.format_exc()
    embed.timestamp = datetime.now()
    bot.AppInfo = await bot.application_info()
    await bot.AppInfo.owner.send(embed=embed)


@app_commands.command(name="enroll", description="Provide your details.")
@app_commands.describe(london_met_id="Your Londeon Met ID", name="Your name")
async def enroll(interaction: discord.Interaction, london_met_id: int, name: str):
    user_data=read_json('user')
    data = {
        "username": interaction.user.name,
        "lid": london_met_id,
        "name": name,
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
    if now.weekday() != 3 or now.hour != 15: 
        await member.move_to(None)
        return
    if after.channel and after.channel.id==1289057002311385118:
        attendance=read_json('attendance')
        date_now=now.strftime('%Y-%m-%d')
        if date_now not in attendance:
            attendance[date_now]=[]
        if not str(member.id) in attendance[date_now]:
            attendance[date_now].append(str(member.id))
            write_json('attendance', attendance)
        await member.move_to(None)

        user_data=read_json('user')
        mem_id=str(member.id)
        if not mem_id in user_data:
            user_data[mem_id]={"username": member.name}
        write_json('user', user_data)


async def check_nos_submission(id):
    reports=requests.get("http://172.104.50.136:8080").json()
    for r in reports:
        if r['id']==int(id): return r['assignments']
    return None


@bot.event
async def on_message(msg):
    if not msg.content.startswith('230'): return
    met_id=msg.content.strip().split()[0]
    if not met_id.isdecimal(): return
    try:
        assignments=await check_nos_submission(met_id)
    except:
        return await msg.channel.send("Something went wrong;/ \nPlease Try Again Later!")
    if not assignments: return await msg.channel.send("Invalid Londot Met ID Provided!")
    to_send=f"__NOS status for **{met_id}**:__\n"
    for a in assignments:
        to_send+=f"{a['name']} --> {a['status']} "
        if a['status']=='Late':
            to_send+=":sob:"
        elif a['status']=='Submitted':
            to_send+=":white_check_mark:"
        elif a['status']=='NotSubmitted':
            to_send+=":x:"
        to_send+="\n"
    await msg.channel.send(to_send)


@bot.event
async def on_ready() -> None:
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="for NOS submissions and HOH attendees"))
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    bot.tree.add_command(enroll)
    await bot.tree.sync()


bot.run(os.getenv("bot_token"))
