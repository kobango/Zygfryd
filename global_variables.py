import discord
import os
import sqlite3 as sl
import time
import asyncio

async def send(ctx,str:str):
    with open('send.txt', 'w',encoding="utf-8") as f:
        f.write("\n"+str) 
    file = discord.File('send.txt')
    await ctx.channel.send('See attachment below',file=file)

async def show_global_variables(ctx):
    local_con = sl.connect('my-test.db')
    with local_con:
            querry = "Select * from global_variables where server_id="+str(ctx.guild.id)
            print(querry)
            data = local_con.execute(querry)
            out_str =''
            l_row = 1
            for row in data:
                out_str+= "\n"+str(l_row)+"  "+str(row[2])+"  "+str(row[3])+"  "+str(row[4])
                l_row+=1
            await send(ctx,out_str)
    pass

async def change_global_variable(ctx,key:str,value:str):
    local_con = sl.connect('my-test.db')
    r_querry = local_con.execute("SELECT value FROM global_variables WHERE server_id="+str(ctx.guild.id)+" and key='"+key+"'")
    for row in r_querry:
        local_con.execute("Update global_variables SET value ='"+str(value)+"' WHERE server_id="+str(ctx.guild.id)+" and key='"+key+"'")
        local_con.commit()
        await ctx.channel.send('Global Variable '+key+' succesfully  updated: '+str(value))
        break
    else:
        sql = "INSERT INTO global_variables (server_id, key, value) values(?, ?, ?)"
        val = (str(ctx.guild.id), str(key), str(value))       
        local_con.execute(sql, val)
        local_con.commit()
        #await ctx.channel.send('Global Variable '+key+' succesfully added: '+str(value))
    local_con.close()
    pass

def change_global_variable_silence(ctx,key:str,value:str):
    local_con = sl.connect('my-test.db')
    r_querry = local_con.execute("SELECT value FROM global_variables WHERE server_id="+str(ctx.guild.id)+" and key='"+key+"'")
    for row in r_querry:
        local_con.execute("Update global_variables SET value ='"+str(value)+"' WHERE server_id="+str(ctx.guild.id)+" and key='"+key+"'")
        local_con.commit()
        break
    else:
        sql = "INSERT INTO global_variables (server_id, key, value) values(?, ?, ?)"
        val = (str(ctx.guild.id), str(key), str(value))       
        local_con.execute(sql, val)
        local_con.commit()
    local_con.close()
    pass

def get_global_variable(ctx,key,deflaut_value=''):
    local_con = sl.connect('my-test.db')
    r_querry = local_con.execute("SELECT value FROM global_variables WHERE server_id="+str(ctx.guild.id)+" and key='"+key+"' LIMIT 1")
    for row in r_querry:
        return row[0]
    else:
        if(deflaut_value!=''):
            change_global_variable_silence(ctx,key,deflaut_value)
            return deflaut_value
        else:
            return deflaut_value
    

