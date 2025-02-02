import discord
import pytube
import os
from pytube import YouTube
from pytube_fork.pytube.__main__ import YouTube as YouTube2
from pytubefix import YouTube as YouTube3
from pytube import Playlist
import sqlite3 as sl
import time
import asyncio
from moviepy.tools import subprocess_call
import youtube_dl
import uuid
from yt_dlp import YoutubeDL



def ffmpeg_extract_subclip(filename, t1, t2, targetname=None):
    cmd_command = "\""+str(os.getcwd())+'/'+"ffmpeg-master-latest-win64-gpl/bin/ffmpeg.exe"+" \" "+" -ss "+"%0.2f"%t1+ " -t "+"%0.2f"%(t2-t1)+ " -i "+ " \"" + filename + "\" "+"\"" + targetname + "\""
    print(cmd_command)
    log(cmd_command)
    os.popen(cmd_command)


def log(str:str):
    with open('logs.txt', 'a',encoding="utf-8") as f:
        f.write("\n"+str) 

async def play_m(message,file):
    
    try:
        music_path = os.getcwd() + '/Muzyka'
        if not message.author.voice:
            await message.channel.send("{} is not connected to a voice channel".format(message.author.name))
        else:
            channel = message.author.voice.channel
            voice_client = message.guild.voice_client
            if (voice_client is None):
                await channel.connect()
                voice_client = message.guild.voice_client
            else:
                try:
                    await voice_client.disconnect()
                    await channel.connect()
                except:
                    pass    
                
                voice_client = message.guild.voice_client
            #print(file)
            #print(music_path)
        if voice_client and voice_client.is_connected():
            voice_client.play(
                discord.FFmpegPCMAudio(executable="ffmpeg-master-latest-win64-gpl/bin/ffmpeg.exe", source=file))
        else:
            try:
                await voice_client.disconnect()
                await channel.connect()
            except:
                pass    
            
            voice_client.play(
                discord.FFmpegPCMAudio(executable="ffmpeg-master-latest-win64-gpl/bin/ffmpeg.exe", source=file))
            
    except Exception as e:
        log(str(e) + str(type(e)) + ' - ' + str(e.args))
        await message.channel.send("Błąd uruchomienia :" + str(e) + str(type(e)) + ' - ' + str(e.args))
        voice_client = message.guild.voice_client
        if voice_client is not None:
            try:
                await voice_client.disconnect()
            except:
                pass    
        
async def play_url(message,url):
    try:
        file = await downland_m(message,url)
        if file is not None and file != '':
            await play_m(message,file)
             

    except Exception as e: 
        log(str(e) + str(type(e)) + ' - ' + str(e.args))
        await message.channel.send("Błąd zapisu :" + str(e) + str(type(e)) + ' - ' + str(e.args))
        voice_client = message.guild.voice_client
        if voice_client is not None:
            await voice_client.disconnect()
            

def subclip(file,start_time,end_time):
    #print(file)
    try:
        subclipfile = file.replace('.mp4','-cut-'+str(start_time)+'-'+str(end_time)+'.mp4')
        print(file)
        print(subclipfile)
        
        ffmpeg_extract_subclip(file, start_time, end_time, targetname=subclipfile)
        return subclipfile
    except Exception as e:
        log(str(e) + str(type(e)) + ' - ' + str(e.args))

async def copy_existing_musicfile(url):
    local_con = sl.connect('my-test.db')
    r_querry = local_con.execute("Select filename from mlists WHERE url like '"+str(url)+"' ORDER BY id LIMIT 1") 
    filename = ''
    for row in r_querry:
        filename = str(row[0])
    return filename 




async def downland_x(message,url,start_time=-1,end_time=-1):
    try:
        os.mkdir(os.getcwd() + '/Muzyka')
    except:
        pass
    try:
        os.mkdir(os.getcwd() + '/Muzyka'+'/'+str(message.guild.id))
    except:
        pass
    SAVE_PATH = os.getcwd() + '/Muzyka'+'/'+str(message.guild.id)
    try:
        # check that we don't dowland this file before 
        file = await copy_existing_musicfile(url)
        
        # downloading the video
        ''' memento because you tube is a shit 
        if file == '':
            try:
                yt = pytube.YouTube(url)  
                stream = yt.streams.filter(only_audio=True).first()  # first()
                file = stream.download(SAVE_PATH)
            except Exception as e:
                asyncio.create_task(message.channel.send("Error: "+str(e)))
                file =''
        if file == '':
            try:
                yt = YouTube2(url)  
                stream = yt.streams.filter(only_audio=True).first()  # first()
                file = stream.download(SAVE_PATH)
            except Exception as e:
                asyncio.create_task(message.channel.send("Error: "+str(e)))     
                file =''
        '''
        if file == '':
            try:
                yt = YouTube3(url)  
                stream = yt.streams.filter(only_audio=True).first()  # first()
                file = stream.download(SAVE_PATH)
            except Exception as e:
                asyncio.create_task(message.channel.send("Error: "+str(e)))
                file =''        
            
        if start_time>-1:
            if end_time<1:
                end_time = stream._monostate.duration
            file = subclip(file,start_time,end_time)

    except Exception as e: 
        log(str(e) + str(type(e)) + ' - ' + str(e.args))
        print(str(e))
        asyncio.create_task(message.channel.send("Error: "+str(e)))
        file = ""

    return file

async def downland_m(message, url, start_time=-1, end_time=-1):
    try:
        os.makedirs(os.path.join(os.getcwd(), 'Muzyka', str(message.guild.id)), exist_ok=True)
        SAVE_PATH = os.path.join(os.getcwd(), 'Muzyka', str(message.guild.id))

        # Sprawdzenie, czy plik został już pobrany
        file = await copy_existing_musicfile(url)

        if file == '':
            try:
                await message.channel.send(f"Download start")
                unique_code = str(uuid.uuid4())  # Generowanie unikalnego identyfikatora
                options = {
                    "format": "worstaudio",  # Pobieranie najgorszej dostępnej jakości audio
                    "outtmpl": os.path.join(SAVE_PATH, f"{unique_code}.%(ext)s"),  # Ustawienie nazwy pliku na unikalny kod
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",  # Konwersja do MP3
                            "preferredquality": "128",  # Najniższa jakość
                        }
                    ],
                }

                with YoutubeDL(options) as ydl:
                    info = ydl.extract_info(url, download=True)
                    await message.channel.send(f"MP3 conversion start: {str(info.get("title", "Unknown"))}")
                    file = os.path.join(SAVE_PATH, f"{unique_code}.mp3")

                # Dodanie rekordu do bazy danych
                local_con = sl.connect('my-test.db')
                sql = """
                    INSERT INTO mlists (server, url, filename, loop, listname, actual, data, desc)
                    VALUES (?, ?, ?, ?, ?, 0, datetime('now'), ?)
                """
                loop = 0
                listname = 'play_url'
                val = (str(message.guild.id), str(url), str(file), int(loop), str(listname), str(info.get("title", "Unknown")))
                with local_con:
                    local_con.execute(sql, val)
                await message.channel.send(f"Added to database as name: {str(info.get("title", "Unknown"))}")    
            except Exception as e:
                await message.channel.send(f"Error during download: {str(e)}")
                file = ''

        # Jeśli zdefiniowano `start_time`, wycinanie fragmentu audio
        if file and start_time > -1:
            try:
                if end_time < 1:
                    # Pobierz czas trwania z metadanych
                    with YoutubeDL() as ydl:
                        info = ydl.extract_info(url, download=False)
                        end_time = info.get("duration", 0)

                file = subclip(file, start_time, end_time)

            except Exception as e:
                await message.channel.send(f"Error during clipping: {str(e)}")
                file = ''

    except Exception as e:
        log(f"{str(e)} {type(e)} - {str(e.args)}")
        await message.channel.send(f"Error downland: {str(e)}")
        file = ""

    return file


async def play_from_list(ctx,con,listname:str='main',name:str=''):
    try:
        if name == '':
            querry = ("SELECT filename, id FROM mlists WHERE server like '"+str(ctx.guild.id)+"' and listname = '"+str(listname)+"' and actual =1 LIMIT 1")
        else:
            querry = ("SELECT filename, id FROM mlists WHERE server like '"+str(ctx.guild.id)+"' and listname = '"+str(listname)+"' and desc ='"+str(name)+"' LIMIT 1")
        #print(querry)
        data = con.execute(querry)
        
        SAVE_PATH = os.getcwd() + '/Muzyka'+'/'+str(ctx.guild.id)
        for row in data:
            await ctx.channel.send(row)
            channel = ctx.author.voice.channel
            voice_client = channel.guild.voice_client
            if (voice_client is None):
                await channel.connect()
                voice_client = channel.guild.voice_client
            else:
                await voice_client.disconnect()
                await channel.connect()
                voice_client = channel.guild.voice_client
            #print(row)
            voice_client.play(discord.FFmpegPCMAudio(executable="ffmpeg-master-latest-win64-gpl/bin/ffmpeg.exe",source=row[0]), after=lambda e: play_next(ctx,listname))
            await ctx.send("Now playing list "+listname+" ...")
            con.execute("Update mlists SET actual = 0 WHERE server like '"+str(ctx.guild.id)+"' and listname = '"+str(listname)+"'") 
            con.commit()
            con.execute("Update mlists SET actual = 1 WHERE id ="+str(row[1]))
            con.commit()
            

    except Exception as e:
        log(str(e) + str(type(e)) + ' - ' + str(e.args))
        await ctx.channel.send("Błąd listy :" + str(e) + str(type(e)) + ' - ' + str(e.args))
        voice_client = ctx.guild.voice_client
        if voice_client is not None:
            await voice_client.disconnect()

def next_m(ctx,listname):
    local_con = sl.connect('my-test.db')
    r_querry = local_con.execute("SELECT id FROM mlists WHERE server like '"+str(ctx.guild.id)+"' and listname = '"+str(listname)+"' and actual =1 LIMIT 1")
    for row in r_querry:
        mlistid = row[0]
    #print(mlistid)
    r_querry = local_con.execute("Select id from mlists WHERE server like '"+str(ctx.guild.id)+"' and listname = '"+str(listname)+"' and id > "+str(mlistid)+" ORDER BY id LIMIT 1") 
    
    for row in r_querry:    
        local_con.execute("Update mlists SET actual = 1 WHERE id ="+str(row[0]))
        local_con.commit()
        local_con.execute("Update mlists SET actual = 0 WHERE id ="+str(mlistid)+" ")    
        local_con.commit()
        local_con.close()
        break
    else:
        reset_list(ctx,listname)    
    local_con.close()
    

def back_m(ctx,listname):
    local_con = sl.connect('my-test.db')
    r_querry = local_con.execute("SELECT id FROM mlists WHERE server like '"+str(ctx.guild.id)+"' and listname = '"+str(listname)+"' and actual =1 LIMIT 1")
    for row in r_querry:
        mlistid = row[0]
    #print(mlistid)
    r_querry = local_con.execute("Select id from mlists WHERE server like '"+str(ctx.guild.id)+"' and listname = '"+str(listname)+"' and id < "+str(mlistid)+" ORDER BY id DESC LIMIT 1") 
    for row in r_querry:
        local_con.execute("Update mlists SET actual = 1 WHERE id ="+str(row[0]))
        local_con.commit()
        local_con.execute("Update mlists SET actual = 0 WHERE id ="+str(mlistid)+" ")    
        local_con.commit()
    local_con.close()

def reset_list(ctx,listname):
    local_con = sl.connect('my-test.db')
    local_con.execute("Update mlists SET actual = 0 WHERE server like '"+str(ctx.guild.id)+"' and listname = '"+str(listname)+"'")
    local_con.commit()
    local_con.execute("Update mlists SET actual = 1 WHERE id in (Select id from mlists WHERE server like '"+str(ctx.guild.id)+"' and listname = '"+str(listname)+"' ORDER BY id LIMIT 1)")
    local_con.commit()
    local_con.close()            

def play_actual(ctx,listname):

    local_con = sl.connect('my-test.db')
            
    querry = (f"""SELECT filename,
              (SELECT position FROM (
                SELECT 
                    filename,
                    ROW_NUMBER() OVER (PARTITION BY server, listname ORDER BY ID) AS position
                FROM 
                    mlists
                 WHERE 
                    server = '{ctx.guild.id}' AND 
                    listname = '{listname}'
                ) AS subquery
              WHERE subquery.filename = m.filename) AS position,
              (Select Count(1) FROM mlists 
              WHERE server like '{str(ctx.guild.id)}' and listname = '{listname}' ) AS max,
              loop
              FROM mlists m
              WHERE server like '{str(ctx.guild.id)}' and listname = '{listname}' and actual =1 LIMIT 1""")
    #print(querry)
    data = local_con.execute(querry)
    SAVE_PATH = os.getcwd() + '/Muzyka'+'/'+str(ctx.guild.id)
    
    for row in data:
        #print(row)
        if row[0] != "":
            path = row[0]
            filename = os.path.basename(path)
            odpowiedzi = ['No','Yes']

            try:
                loop = asyncio.get_event_loop()
                tasks = list()
                tasks.append(asyncio.create_task(ctx.channel.send(f"Now playing list: {listname}, part: {filename}  {row[1]}/{row[2]} loop: {odpowiedzi[row[3]]} ..."),name='Chanel Counter'))
                loop.run_until_complete(tasks)
                loop.close()
            except Exception as e:
                #print(e)
                pass
            voice_client = ctx.guild.voice_client
            if voice_client:
                voice_client.pause()
            else:
                channel = ctx.message.author.voice.channel
                channel.connect()
                voice_client = ctx.message.guild.voice_client
            voice_client.play(discord.FFmpegPCMAudio(executable="ffmpeg-master-latest-win64-gpl/bin/ffmpeg.exe", source=row[0]), after=lambda e: play_next(ctx,listname))
            

def play_next(ctx, listname):
    #print("inside")
    local_con = sl.connect('my-test.db')
    r_querry = local_con.execute("SELECT loop FROM mlists WHERE server like '"+str(ctx.guild.id)+"' and listname = '"+str(listname)+"' and actual =1 LIMIT 1")
    loop=0
    for row in r_querry:
        loop = row[0]
    r_querry.close()
    voice_client = ctx.guild.voice_client
    if voice_client:
        voice_client.stop()
    if loop<1:
        next_m(ctx,listname)   
    
    play_actual(ctx,listname)
    
               