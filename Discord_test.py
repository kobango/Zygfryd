import asyncio
import threading
import discord
from discord.ext import commands
#from discord import app_commands
from discord.ext import tasks
import pytube
import os
from pytube import YouTube
from pytube import Playlist
import sqlite3 as sl
import time
import datetime
import music_play
from config_menage import load_config
import database_init
import chanel_inventory
import subprocess
import google.generativeai as genai
from gremlin_chat import gremlin_chat
import global_variables
from enum import Enum

global processed_text 
processed_text = 0

config = load_config()

global con
con = sl.connect('my-test.db')
database_init.init(con)       

intents = discord.Intents.default()
intents.message_content = True


async def send(ctx,str:str):
    with open('send.txt', 'w',encoding="utf-8") as f:
        f.write("\n"+str) 
    file = discord.File('send.txt')
    await ctx.channel.send('See attachment below',file=file)

def log(str:str):
    with open('logs.txt', 'a',encoding="utf-8") as f:
        f.write(str) 


bot = commands.Bot(command_prefix='$', intents=intents)


@bot.command(pass_context=True, description="Return invitation link", help="Use link to invite the bot to other servers" )
async def invite(ctx, arg):
    try:
        await send(ctx,"https://discord.com/api/oauth2/authorize?client_id=478705396962426882&permissions=40662656850752&scope=bot")
    except Exception as e:    
        log(str(e) + str(type(e)) + ' - ' + str(e.args))
        await ctx.channel.send("Błąd :" + str(e) + str(type(e)) + ' - ' + str(e.args))

@bot.command(pass_context=True, description=" Test message, return only one of given arguments", help="Just Test" )
async def test(ctx, arg):
    await ctx.send(arg)

@bot.command(pass_context=True,aliases=['playlista', 'lista_muzyki','poka_playliste','poka_co_je_grane','pokŏż_wykŏz'], description=" Show list of track in playlist WARNING:(if no listname given use main list)", help="Show given playlist")    
async def show_list(ctx,listname:str=''):
    if listname=='':
        listname = global_variables.get_global_variable(ctx,'LAST_AUDIO_LIST','main')
    with con:
        querry = ("SELECT * FROM mlists WHERE server like '"+str(ctx.guild.id)+"' and listname = '"+str(listname)+"'")
        print(querry)
        data = con.execute(querry)
        for row in data:
            await ctx.channel.send(row)

@bot.command(pass_context=True,aliases=['folder', 'lista_plików','poka_foldery','poka_co_byda_grane','pokŏż_wykŏz_z_muzykōm'], description="Show folder linked with server", help="Display folder", )
async def display_music_files(ctx):
    music_path = os.getcwd() + '/Muzyka'+'/'+str(ctx.guild.id)
    dir_inside = os.listdir(music_path)
    list_str = ''
    for f in dir_inside:
        list_str+=(f+'\n')
    await send(ctx,list_str)

@bot.command(pass_context=True,aliases=['usuń_plik','wychrōń_zbiōr'], description="Remove file in folder linked with server", help="remove from folder")
async def remove_music_files(ctx,filename):
    music_path = os.getcwd() + '/Muzyka'+'/'+str(ctx.guild.id)
    dir_inside = os.listdir(music_path)
    try:
        os.remove(music_path+'/'+filename)
    except Exception as e:    
        log(str(e) + str(type(e)) + ' - ' + str(e.args))
        await ctx.channel.send("Błąd zapisu :" + str(e) + str(type(e)) + ' - ' + str(e.args))

@bot.command(pass_context=True,aliases=['zapisz_plik','przipisz_zbiōr'], description="Save attachment to folder", help="Attachment save")
async def save_file(ctx):
    music_path = os.getcwd() + '/Muzyka'+'/'+str(ctx.guild.id)
    dir_inside = os.listdir(music_path)
    for attachment in ctx.message.attachments:
        filename = attachment.filename
        await attachment.save(fp=music_path+'/'+filename)

@bot.command(pass_context=True,aliases=['odpal_liste','sztartnij_wykŏz'], description="Play list, require name of list as optional argument", help="Play list form begining")
async def play_list(ctx,listname:str='main',name:str=''):
    await global_variables.change_global_variable(ctx,'LAST_AUDIO_LIST',listname)
    music_play.reset_list(ctx,listname)
    with con:
        querry = ("SELECT filename FROM mlists WHERE server like '"+str(ctx.guild.id)+"' and listname = '"+str(listname)+"' and actual =1 LIMIT 1")
        print(querry)
        data = con.execute(querry)
        for row in data:
            #await ctx.channel.send(row)
            await music_play.play_from_list(ctx,con,listname,name)
    pass

@bot.command(pass_context=True,aliases=['zmień_liste','zmiyń_wykŏz'], description="Swith actual list without change of actal track", help="Swith actual list")
async def change_list(ctx,listname:str='main',name:str=''):
    await global_variables.change_global_variable(ctx,'LAST_AUDIO_LIST',listname)
    with con:
        querry = ("SELECT filename FROM mlists WHERE  server like '"+str(ctx.guild.id)+"' and listname = '"+str(listname)+"' and actual =1 LIMIT 1")
        #print(querry)
        data = con.execute(querry)
        for row in data:
            #await ctx.channel.send(row)
            await music_play.play_from_list(ctx,con,listname,name)
    pass

@bot.command(pass_context=True,aliases=['pętla','loop','ponawiaj','powtŏrzej'], description="Make actual track to be played in loop (required next_list command to step out of loop)", help="Loop actual track")
async def repeat(ctx,listname:str=''):
    if listname=='':
        listname = global_variables.get_global_variable(ctx,'LAST_AUDIO_LIST','main')
    with con:
        con.execute("Update mlists SET loop = 1 WHERE id in (Select id from mlists WHERE server like '"+str(ctx.guild.id)+"' and listname = '"+str(listname)+"' and actual=1 ORDER BY id LIMIT 1)")
        con.commit()

@bot.command(pass_context=True,aliases=['odpętlić','unloop','nie_ponawiaj','niy_powtŏrzać'], description="Swith off loop", help="Swith off loop")
async def unrepeat(ctx,listname:str=''):
    if listname=='':
        listname = global_variables.get_global_variable(ctx,'LAST_AUDIO_LIST','main')
    with con:
        con.execute("Update mlists SET loop = 0 WHERE id in (Select id from mlists WHERE server like '"+str(ctx.guild.id)+"' and listname = '"+str(listname)+"' and actual=1 ORDER BY id LIMIT 1)")
        con.commit()        

@bot.command(pass_context=True,aliases=['wyczyść','usuń_liste','usuń','wychrōń_liste'], description="Clear list given as argument", help="Clear given list")             
async def clear_list(ctx,listname:str=''):
    if listname=='':
        listname = global_variables.get_global_variable(ctx,'LAST_AUDIO_LIST','main')
    with con:
        querry = ("DELETE FROM mlists WHERE server like '"+str(ctx.guild.id)+"' and listname = '"+str(listname)+"'")
        print(querry)
        con.execute(querry)        

@bot.command(pass_context=True,aliases=['next','następny','dalej','nastympny_z_brify'], description="Swith to next track on list, ( bypass loop)", help="Next track from list")
async def next_list(ctx,listname:str=''):
    if listname=='':
        listname = global_variables.get_global_variable(ctx,'LAST_AUDIO_LIST','main')
    music_play.next_m(ctx,listname)
    music_play.play_actual(ctx,listname)

@bot.command(pass_context=True,aliases=['back','poprzedni','do_tyłu','piyrwyjszy_z_brify'], description="Swith to previous track on list (WARNING: do not step back if track is first on the list)", help="Previous track from list")
async def back_list(ctx,listname:str=''):
    if listname=='':
        listname = global_variables.get_global_variable(ctx,'LAST_AUDIO_LIST','main')
    music_play.back_m(ctx,listname)
    music_play.play_actual(ctx,listname)    

@bot.command(pass_context=True,aliases=['music_url','dodaj_z_url','z_linka','przidej z powrōz'], description="Add music do list using url", help="Add url do list")
async def to_list_url(ctx,url:str,listname:str='',loop:int=0,name:str = ''):
    if listname=='':
        listname = global_variables.get_global_variable(ctx,'LAST_AUDIO_LIST','main')
    file = await music_play.downland_m(ctx.message,url)
    sql = "INSERT INTO mlists (server, url, filename, loop, listname, actual, data, desc) values(?, ?, ?, ?, ?, 0, datetime('now'),?)"

    val = (str(ctx.guild.id), str(url), str(file),int(loop),str(listname), str(name))
    if (ctx.message.author != 'test_echo#4421'):
        with con:
            con.execute(sql, val)

@bot.command(pass_context=True,aliases=['music_file','dodaj_z_pliku','z_pliku','przidej ze zbioru'], description="Add music do list using given filename ( WARNING: USE WITH DOUBLE QUOTTATION MARK)", help="Add file do list")
async def to_list_file(ctx,listname:str='',loop:int=0,name:str = ''):
    if listname=='':
        listname = global_variables.get_global_variable(ctx,'LAST_AUDIO_LIST','main')
    music_path = os.getcwd() + '/Muzyka'+'/'+str(ctx.guild.id)
    
    for attachment in ctx.message.attachments:
        filename = attachment.filename
        await attachment.save(fp=music_path+'/'+filename)
    file = music_path+'/'+filename
    
    sql = "INSERT INTO mlists (server, url, filename, loop, listname, actual, data, desc) values(?, ?, ?, ?, ?, 0, datetime('now'),?)"

    val = (str(ctx.guild.id), str(''), str(file),int(loop),str(listname), str(name))
    if (ctx.message.author != 'test_echo#4421'):
        with con:
            con.execute(sql, val)            

@bot.command(pass_context=True,aliases=['pobierz','downland','pobieranie','pobier'], description="Downland given track to folder", help="Downland url")
async def downland_url(ctx,url,start = -1, stop = -1):
    try:
        file = await music_play.downland_m(ctx.message,url,start,stop)
        await ctx.channel.send(file)
    except Exception as e:    
        log(str(e) + str(type(e)) + ' - ' + str(e.args))
        await ctx.channel.send("Błąd zapisu :" + str(e) + str(type(e)) + ' - ' + str(e.args))

@bot.command(pass_context=True,aliases=['odtwarzaj z pliku'], description="Play track from file", help="Play file")
async def play_file(ctx, file):
    music_path = os.getcwd() + '/Muzyka'+'/'+str(ctx.guild.id)
    dir_inside = os.listdir(music_path)
    print(music_path+'/'+file)
    await music_play.play_m(ctx.message,music_path+'/'+file)  

@bot.command(pass_context=True,aliases=['odtwarzaj z url'], description="Play using url", help="Play url")
async def play_url(ctx,url):
    print('uruchomiono')

    #asyncio.create_task(music_play.play_url(ctx.message, url))
    await music_play.play_url(ctx.message,url)

@bot.command(pass_context=True, description="Pause voice client", help="Pause")
async def pause(ctx):
    try:
        voice_client = ctx.guild.voice_client
        if voice_client.is_playing():
            voice_client.pause()
    except Exception as e:
        log(str(e) + str(type(e)) + ' - ' + str(e.args))
        await ctx.channel.send("Błąd :" + str(e) + str(type(e)) + ' - ' + str(e.args))


@bot.command(pass_context=True, description="Unpause voice client", help="Unause")
async def unpause(ctx):
    try:
        voice_client = ctx.guild.voice_client
        if voice_client.is_paused():
            voice_client.resume()
    except Exception as e:
        log(str(e) + str(type(e)) + ' - ' + str(e.args))
        await ctx.channel.send("Błąd zapisu :" + str(e) + str(type(e)) + ' - ' + str(e.args))

@bot.command(pass_context=True, description="Disconnect voice client", help="Disconnect")
async def disc(ctx):
    try:
        voice_client = ctx.guild.voice_client
        await voice_client.disconnect()
    except Exception as e:
        log(str(e) + str(type(e)) + ' - ' + str(e.args))
        pass                   

@bot.command(pass_context=True, description="Raw sql Querry", help="Raw Querry", hidden= True)    
async def sql_execute(ctx,querry:str='Select * from mlists'):
    if str(ctx.guild.id) == '888506727140569089':
        with con:
            print(querry)
            data = con.execute(querry)
            out_str =''
            for row in data:
                out_str+= "\n"+str(row)
            await send(ctx,out_str)    


@bot.command(pass_context=True, description=" Show list of playlists WARNING", help="Show all playlist")    
async def show_all_playlist(ctx,listname:str='main'):
    with con:
        querry = ("SELECT listname, count(*) FROM mlists WHERE server like '"+str(ctx.guild.id)+"' GROUP BY listname")
        print(querry)
        data = con.execute(querry)
        for row in data:
            await ctx.channel.send(row)

@bot.command(pass_context=True, description=" DO NOT USE TEST COMMAND", help="DO NOT", hidden= True)      
async def cmd_execute(ctx,command):
    if str(ctx.guild.id) == '888506727140569089':
        output = subprocess.check_output(command, shell=True)
        await send(ctx,str(output.decode("utf-8",errors="ignore")))

@bot.command(pass_context=True, description=" DO NOT USE TEST COMMAND", help="DO NOT", hidden= True)      
async def shuttdown(ctx):
    await ctx.channel.send("Starting shutdownn comand...")
    time.sleep(2)
    os.system("shutdown /r /t 1")    


@bot.command(pass_context=True, description=" DO NOT USE TEST COMMAND DROP TABLE IN DATABASE", help="DO NOT", hidden= True)             
async def drop_list(ctx):
    with con:
        querry = ("DROP TABLE mlists")
        print(querry)
        con.execute(querry)

@bot.command(pass_context=True, description=" hello ", help="Just hello")
async def hello(ctx):
    await ctx.channel.send('Hello!')


@bot.command(pass_context=True, description="Echo but entire message", help="Just echo")
async def echo(ctx):
    await ctx.channel.send(ctx.message.content[6:])

@bot.command(pass_context=True, description="Chat with AI basend on Gemini", help="GEMINI API")
async def chat(ctx):
    global processed_text 
    try:
        if processed_text <2:
            if ctx.message.content[:4] == '$chat':
                input_text = ctx.message.content[4:]
            else:
                input_text = ctx.message.content
            processed_text+=1
            await gremlin_chat(ctx,input_text)
            processed_text-=1
        else:
            await ctx.channel.send("Zajęte, proszę pisać później")
    except Exception as e:    
        log(str(e) + str(type(e)) + ' - ' + str(e.args))
        await ctx.channel.send("Błąd :" + str(e) + str(type(e)) + ' - ' + str(e.args))



@bot.command(pass_context=True, description="Add item to chanel deposit", help="Deposit item in chanel")
async def deposit(ctx,item:str,quantity:float=1,descryption:str=""):
    item = item.strip()
    item = item.lower()
    await chanel_inventory.chanel_deposit(ctx,item,quantity,descryption)

@bot.command(pass_context=True, description="Add item to chanel deposit", help="Deposit item in chanel")
async def withdraw(ctx,item:str,quantity:float=1):
    await chanel_inventory.chanel_withdraw(ctx,item,quantity)

@bot.command(pass_context=True, description="Show chanel deposit", help="Show chanel item deposit")
async def inventory(ctx):
    await chanel_inventory.show_inventory(ctx)

@bot.command(pass_context=True, description="Add recepture to chanel deposit", help="Deposit recepture in chanel")
async def make_recepture(ctx,name:str,item:str,recepture:str,descryption:str=""):
    try:
        await chanel_inventory.chanel_create_recepture(ctx,name,item,recepture,descryption)
    except Exception as e:
        await ctx.channel.send(str(e) + str(type(e)) + ' - ' + str(e.args)) 

@bot.command(pass_context=True, description="Show reciepes", help="Show reciepes")
async def show_receptures(ctx):
    await chanel_inventory.show_receptures(ctx)

@bot.command(pass_context=True, description="Execute recepture formula", help="Execute recepture formula")
async def execute_recepture(ctx,name:str):
    await chanel_inventory.chanel_execute_recepture(ctx,name)

@bot.command(pass_context=True,aliases=["turn"], description="Execute all recepture formula", help="Execute all recepture formula")
async def execute_all_recepture(ctx):
    await chanel_inventory.chanel_execute_all_receptures(ctx)    

@bot.command(pass_context=True, description="Delete recepture formula", help="Delete recepture formula")
async def delete_recepture(ctx,name:str):
    await chanel_inventory.chanel_delete_recepture(ctx,name)             

@bot.command(pass_context=True, description="Add music do list using url", help="Add url do list")
async def remind(ctx,date:str=''):
    mesage = ctx.message.content[7:]
    sql = "INSERT INTO reminders (chanel_id, tresc, data) values(?, ?,datetime(?))"
    val = (str(ctx.channel.id), str(mesage), str(date))
    if (ctx.message.author != 'test_echo#4421'):
        with con:
            con.execute(sql, val)
            await ctx.channel.send("Reminder at "+date+" ADDED")           
#TO
@bot.command()
async def start_record(ctx):
    voice_client = ctx.channel.guild.voice_client
    if (voice_client is None):
        await ctx.author.voice.channel.connect() # Connect to the voice channel of the author
    ctx.voice_client.start_recording(discord.sinks.MP3Sink(), finished_callback, ctx) # Start the recording
    await ctx.channel.send("Recording...") 

async def finished_callback(sink, ctx):
    # Here you can access the recorded files:
    recorded_users = [
        f"<@{user_id}>"
        for user_id, audio in sink.audio_data.items()
    ]
    files = [discord.File(audio.file, f"{user_id}.{sink.encoding}") for user_id, audio in sink.audio_data.items()]
    await ctx.channel.send(f"Finished! Recorded audio for {', '.join(recorded_users)}.", files=files) 

@bot.command()
async def stop_recording(ctx):
    ctx.voice_client.stop_recording() # Stop the recording, finished_callback will shortly after be called
    await ctx.channel.send("Stopped!")


#DO
@tasks.loop(minutes=1)
async def reminder_agent(bot):
    local_con = sl.connect('my-test.db')
    r_querry = local_con.execute("SELECT * FROM reminders WHERE data < datetime('now', 'localtime')")
    for row in r_querry:
        mlistid = row[0]
        chanel = bot.get_channel(row[1])
        await chanel.send(str(row[2]))
        local_con.execute("DELETE FROM reminders  WHERE id ="+str(mlistid)+"")
        local_con.commit()
    pass

@tasks.loop(minutes=10)
async def voice_evaluator(bot):
    processed_text = 0

    bot_voice_chanels = bot.voice_clients
    if len(bot_voice_chanels) > 0:
            for vc in bot_voice_chanels:    
                element_chanel = vc.channel
                member_list = [member for member in element_chanel.members]
                if bot.user.id in [m.id for m in member_list] and [m.id for m in member_list if m.id != bot.user.id] == []:
                    try:
                        await vc.disconnect()
                    except Exception as e:
                        log(str(e) + str(type(e)) + ' - ' + str(e.args))
                        pass    
                    print(member_list)
    

@bot.event
async def on_message(message):
    try:
        sql = "INSERT INTO logs (usser, tresc, data) values(?, ?, datetime('now'))"
        val = (str(message.author), str(message.content))
        if str(message.author) not in ('Zygfryd#3906','slonzak (Ślonzak)','oskar__2137 (Oskar)'):
        #if str(message.author) not in ('Zygfryd#3906'):
            with con:
                con.execute(sql, val)
                con.commit()
            if bot.user in message.mentions:
                ctx = await bot.get_context(message)
                # Wywołanie komendy greet za pomocą invoke
                await ctx.invoke(chat)

            await bot.process_commands(message)
    except Exception as e:    
        log(str(e) + str(type(e)) + ' - ' + str(e.args))
        await message.channel.send("Błąd :" + str(e) + str(type(e)) + ' - ' + str(e.args))
          
    

@bot.event
async def on_ready():
    if not reminder_agent.is_running():
        reminder_agent.start(bot)
    if not voice_evaluator.is_running():
        voice_evaluator.start(bot) 

@bot.event
async def on_member_join(member):
    if member.created_at() >  (datetime.datetime.now() - datetime.timedelta(days=7)).date():
        await member.ban(reason = " IP Ban Multi")



bot.run(config["DISCORD_TOKEN"])
