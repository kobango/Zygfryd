import discord
import os
import sqlite3 as sl
import time
import asyncio
import random
from random import randint

async def send(ctx,str:str):
    with open('send.txt', 'w',encoding="utf-8") as f:
        f.write("\n"+str) 
    file = discord.File('send.txt')
    await ctx.channel.send('See attachment below',file=file)

async def show_inventory(ctx):
    local_con = sl.connect('my-test.db')
    with local_con:
            querry = "Select * from chanel_storage where chanel_id="+str(ctx.channel.id)
            #print(querry)
            data = local_con.execute(querry)
            out_str =''
            l_row = 1
            for row in data:
                out_str+= "\n"+str(l_row)+"  "+str(row[2])+"  "+str(row[3])+"  "+str(row[4])
                l_row+=1
            await send(ctx,out_str)
    pass

async def chanel_deposit(ctx,item:str,quantity:int,descryption:str=""):
    local_con = sl.connect('my-test.db')
    r_querry = local_con.execute("SELECT quantity FROM chanel_storage WHERE chanel_id="+str(ctx.channel.id)+" and object='"+item+"'")
    for row in r_querry:
        new_walue =float(row[0])+quantity
        if new_walue >=0:
            local_con.execute("Update chanel_storage SET quantity ="+str(new_walue)+" WHERE chanel_id="+str(ctx.channel.id)+" and object='"+item+"'")
            local_con.commit()
            await ctx.channel.send('Item deposited succesfully actual quantity: '+str(new_walue))
        else:
            await ctx.channel.send('Deposit fail Invalid quantity')
        break
    else:
        sql = "INSERT INTO chanel_storage (chanel_id, object, quantity, descrypton) values(?, ?, ?, ?)"
        val = (str(ctx.channel.id), str(item), str(quantity),str(descryption))       
        local_con.execute(sql, val)
        local_con.commit()
        await ctx.channel.send('Item deposited succesfully actual quantity: '+str(quantity))
    local_con.close()
    pass

async def chanel_withdraw(ctx,item:str,quantity:int):
    local_con = sl.connect('my-test.db')
    r_querry = local_con.execute("SELECT quantity FROM chanel_storage WHERE chanel_id="+str(ctx.channel.id)+" and object='"+item+"'")
    for row in r_querry:
        new_walue =int(row[0])-quantity
        if new_walue >=0:
            local_con.execute("Update chanel_storage SET quantity ="+str(new_walue)+" WHERE chanel_id="+str(ctx.channel.id)+" and object='"+item+"'")
            local_con.commit()
            await ctx.channel.send('Item withdraw succesfully actual quantity: '+str(new_walue))
        else:
            await ctx.channel.send('Withdraw fail Invalid quantity')
        break
    else:
        await ctx.channel.send('Withdraw fail Invalid quantity')
    local_con.close()
    pass

async def chanel_create_recepture(ctx,name:str,item:str,recepture:str,descryption:str=""):
    try:
        local_con = sl.connect('my-test.db')
        r_querry = local_con.execute("SELECT name FROM chanel_receptures WHERE chanel_id="+str(ctx.channel.id)+" and name='"+name+"'")
        for row in r_querry:
            local_con.execute("Update chanel_receptures SET object ='"+item+"',recepture ='"+recepture+"',descryption ='"+descryption+"' WHERE chanel_id="+str(ctx.channel.id)+" and name='"+name+"'")
            local_con.commit()
            await ctx.channel.send('Item receptures succesfully updated: '+str(recepture))
            break
        else:
            sql = "INSERT INTO chanel_receptures (chanel_id,name, object, recepture, descryption) values(?, ?, ?, ?, ?)"
            val = (str(ctx.channel.id), str(name), str(item), str(recepture),str(descryption))       
            local_con.execute(sql, val)
            local_con.commit()
            await ctx.channel.send('Item: '+str(recepture)+' receptures succesfully added:  '+str(recepture))
        local_con.close()
    except Exception as e:
        await ctx.channel.send(str(e) + str(type(e)) + ' - ' + str(e.args))    
    pass


async def show_receptures(ctx):
    local_con = sl.connect('my-test.db')
    with local_con:
            querry = "Select * from chanel_receptures where chanel_id="+str(ctx.channel.id)
            #print(querry)
            data = local_con.execute(querry)
            out_str =''
            l_row = 1
            for row in data:
                out_str+= "\n"+str(l_row)+"  "+str(row[2])+"  "+str(row[3])+"  "+str(row[4])+"  "+str(row[5])
                l_row+=1
            await send(ctx,out_str)
    pass


async def chanel_execute_recepture(ctx,name:str):
    try:
        local_con = sl.connect('my-test.db')
        r_querry = local_con.execute("SELECT object,recepture FROM chanel_receptures WHERE chanel_id="+str(ctx.channel.id)+" and name='"+name+"'")
        for row in r_querry:
            initial_recepture =str(row[1])
            await ctx.channel.send(initial_recepture) 
            globals_querry = local_con.execute("SELECT key,value FROM global_variables WHERE server_id="+str(ctx.guild.id))
            for gobal_row in globals_querry:
                initial_recepture = initial_recepture.replace("["+str(gobal_row[0])+"]",str(gobal_row[1]))
            items_querry = local_con.execute("SELECT object,quantity FROM chanel_storage WHERE chanel_id="+str(ctx.channel.id))
            for item_row in items_querry:
                initial_recepture = initial_recepture.replace("["+str(item_row[0])+"]",str(item_row[1]))
            for dice in range(2,1000):
                initial_recepture = initial_recepture.replace("[d"+str(dice)+"]","(randint(1, "+str(dice)+"))")
            #initial_recepture.replace("[bydło]",'22')
            await ctx.channel.send(initial_recepture)  
            output_value = eval(initial_recepture)
            await ctx.channel.send(str(output_value))
            await chanel_deposit(ctx,row[0],output_value)
            break
        else:
            await ctx.channel.send('Name not found')
        local_con.close()
    except Exception as e:
        await ctx.channel.send(str(e) + str(type(e)) + ' - ' + str(e.args))    
    pass

async def chanel_execute_all_receptures(ctx):
    try:
        r_con = sl.connect('my-test.db')
        r_querry = r_con.execute("SELECT object,recepture FROM chanel_receptures WHERE chanel_id="+str(ctx.channel.id))
        table = r_querry.fetchall()
        r_con.close()
        print(table)
        for row in table:
            initial_recepture =str(row[1])
            initial_recepture = initial_recepture.replace('*',' * ')
            await ctx.channel.send('Recepture: '+row[0]+' : '+initial_recepture)
            l_con = sl.connect('my-test.db')
            globals_querry = l_con.execute("SELECT key,value FROM global_variables WHERE server_id="+str(ctx.guild.id))
            for gobal_row in globals_querry:
                initial_recepture = initial_recepture.replace("["+str(gobal_row[0])+"]",str(gobal_row[1]))
            items_querry = l_con.execute("SELECT object,quantity FROM chanel_storage WHERE chanel_id="+str(ctx.channel.id))
            for item_row in items_querry:
                initial_recepture = initial_recepture.replace("["+str(item_row[0])+"]",str(item_row[1]))
            for dice in range(2,1000):
                initial_recepture = initial_recepture.replace("[d"+str(dice)+"]","(randint(1, "+str(dice)+"))")
            #initial_recepture.replace("[bydło]",'22')
            await ctx.channel.send(initial_recepture)    
            l_con.close()  
            output_value = eval(initial_recepture)
            await ctx.channel.send(str(output_value))
            await chanel_deposit(ctx,row[0],output_value)
        
        if table == []:
            await ctx.channel.send('Name not found')
        
    except Exception as e:
        await ctx.channel.send(str(e) + str(type(e)) + ' - ' + str(e.args))    
    pass

async def chanel_delete_recepture(ctx,name:str):
    local_con = sl.connect('my-test.db')
    local_con.execute("DELETE FROM chanel_receptures WHERE chanel_id="+str(ctx.channel.id)+" and name='"+name+"'")
    local_con.commit()
    await ctx.channel.send("Recepture deleted") 
    local_con.close()   