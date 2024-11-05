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

bot=Bot(command_prefix='/', intents=intents)
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

@bot.event
async def on_ready() -> None:
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="over ICP-BIT server"))
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    await bot.tree.sync()


@bot.tree.command(name="enroll", description="Hour of Hack Registration")
@app_commands.describe(london_met_id="Your London Met ID", name="Your Name")
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
            try:
                dm_channel = await member.create_dm()
                await dm_channel.send("You are marked as present in today's session.")
            except: pass
        await member.move_to(None)

        user_data=read_json('user')
        mem_id=str(member.id)
        if not mem_id in user_data:
            user_data[mem_id]={"username": member.name}
        write_json('user', user_data)


async def check_nos_submission(id=None):
    reports=requests.get("http://172.104.50.136:8080").json()
    if not id: return reports
    for r in reports:
        if r['id']==int(id): return r['assignments']
    return None

def status_emoji(s):
    if s=='Late':
        return ":sob:"
    elif s=='Submitted':
        return ":white_check_mark:"
    elif s=='NotSubmitted':
        return ":x:"
    else:
        return ":white_small_square:"

@bot.event
async def on_message(msg):
    if not msg.content.startswith('230'): return

    if msg.content=="230":
        reports=await check_nos_submission()
        logs={}
        for r in reports:
            for a in r['assignments']:
                if not a['name'] in logs: logs[a['name']]={}
                if not a['status'] in logs[a['name']]: logs[a['name']][a['status']]=0
                logs[a['name']][a['status']]+=1
        to_send=''
        for l in logs:
            to_send+=f"\n__{l}__:\n"
            i=0
            for s,v in dict(sorted(logs[l].items(), reverse=True)).items():
                to_send+=f"{', ' if i else ''}{status_emoji(s)} ({v})"
                i=1
        await msg.channel.send(to_send)
        return

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
        to_send+=status_emoji(a['status'])
        to_send+="\n"
    await msg.channel.send(to_send)


bot.run(os.getenv("bot_token"))
