import sqlite3
import discord
import ast
import io
import os
import sys
import gremlin_functions
from config_menage import load_config
#import google.generativeai as genai
import google.generativeai as genai
import mimetypes
import re
import random
import string

#from google.generativeai.tools import Tool, GoogleSearch
#from google.generativeai.types import GenerateContentConfig
config = load_config()
genai.configure(api_key= config["GEMINI_API_KEY"])
model = genai.GenerativeModel(
                model_name="gemini-2.0-flash-exp",
                tools=[gremlin_functions.przetworz_link]
            )
chat = model.start_chat(enable_automatic_function_calling=True)

def generate_random_uid(length=5):
    # Zbiór znaków (małe litery, duże litery i cyfry)
    characters = string.ascii_lowercase + string.ascii_uppercase + string.digits
    # Generowanie losowego ciągu
    random_uid = ''.join(random.choice(characters) for _ in range(length))
    return random_uid

def sanitize_filename(filename):
    # Usuń niedozwolone znaki i upewnij się, że nazwa pliku nie zaczyna ani kończy się myślnikiem
    sanitized = re.sub(r'[^a-z0-9-"]', '', filename.lower())  # Tylko małe litery, cyfry i myślniki
    if sanitized.startswith('-'):
        sanitized = sanitized[1:]  # Usuń myślnik na początku
    if sanitized.endswith('-'):
        sanitized = sanitized[:-1]  # Usuń myślnik na końcu
    return sanitized

async def send(ctx,str:str):
    with open('send.txt', 'w',encoding="utf-8") as f:
        f.write("\n"+str) 
    file = discord.File('send.txt')
    await ctx.channel.send('See attachment below',file=file)

def podziel_tekst_rekurencyjnie(tekst, max_dlugosc, znaki_podzialu=None):
    if znaki_podzialu is None:
        znaki_podzialu = ['\n\n', '\n', ' ']  # Kolejność podziałów
    
    # Jeśli tekst mieści się w limicie, zwracamy go jako jeden fragment
    if len(tekst) <= max_dlugosc:
        return [tekst.strip()]

    # Próbujemy podzielić tekst używając aktualnego znaku podziału
    if znaki_podzialu:
        znak = znaki_podzialu[0]
        fragmenty = tekst.split(znak)
        aktualny_fragment = ""
        wynik = []

        for fragment in fragmenty:
            if len(aktualny_fragment) + len(fragment) + len(znak) <= max_dlugosc:
                aktualny_fragment += fragment + znak
            else:
                if aktualny_fragment:
                    wynik.append(aktualny_fragment.strip())
                aktualny_fragment = fragment + znak

        if aktualny_fragment.strip():
            wynik.append(aktualny_fragment.strip())

        # Jeśli fragmenty nadal są zbyt długie, dzielimy je rekurencyjnie
        ostateczny_wynik = []
        for czesc in wynik:
            if len(czesc) > max_dlugosc:
                ostateczny_wynik.extend(
                    podziel_tekst_rekurencyjnie(czesc, max_dlugosc, znaki_podzialu[1:])
                )
            else:
                ostateczny_wynik.append(czesc)
        
        return ostateczny_wynik

    # Jeśli brak znaków podziału, dzielimy na kawałki o maksymalnej długości
    return [tekst[i:i + max_dlugosc] for i in range(0, len(tekst), max_dlugosc)]



async def send_message(ctx, bot_response):
    """Wysyła odpowiedź na Discord, dzieląc ją na mniejsze części, jeśli jest za długa."""
    if len(bot_response) <= 1800:
        await ctx.channel.send(bot_response)
    else:
        parts = podziel_tekst_rekurencyjnie(bot_response,1800)
        for part in parts:
            await ctx.channel.send(part)    

async def execute_code(ctx, message,conn):
    """Bezpiecznie wykonuje kod Python zawarty między znacznikami <python_run> i </python_run>."""

    start_index = message.rfind("<python_run>")
    if start_index == -1:
        return  # Znacznik nie znaleziony

    end_index = message.find("</python_run>", start_index + len("<python_run>"))
    if end_index == -1:
        return  # Zamykający znacznik nie znaleziony

    code_snippet = message[start_index + len("<python_run>"):end_index].strip()
    #print(str(code_snippet))
    code_snippet = code_snippet.strip()
    code_snippet = code_snippet.replace("```","")
    print(message)
    print(f"Kod:\n {code_snippet}")
    try:
        
        tree = ast.parse(code_snippet)  # Analiza kodu za pomocą AST
        # Sprawdź, czy kod nie zawiera niebezpiecznych funkcji (np. os.system, import os)
        ALLOWED_MODULES = {"math", "random", "datetime"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name not in ALLOWED_MODULES and alias.name in ["os", "subprocess", "sys"]:
                        await ctx.channel.send("Wykonywanie kodu z importem modułów 'os', 'subprocess' lub 'sys' jest zabronione.")
                        return
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in ["exec", "eval"]:
                    await ctx.channel.send("Wykonywanie funkcji 'exec' i 'eval' jest zabronione.")
                    return
        compiled_code = compile(tree, '<string>', 'exec')
        print(compiled_code)
        # Wykonanie kodu w bezpiecznym środowisku (np. z ograniczeniami dostępu do plików i systemów)
        old_stdout = sys.stdout
        redirected_output = sys.stdout = io.StringIO()
        allowed_globals = globals()
        exec(compiled_code, allowed_globals)
        sys.stdout = old_stdout
        output = redirected_output.getvalue().strip()
        

        if output:
            output_message = f"Zwrócono:\n {output} \n" # Użycie formatowania Markdown dla lepszej czytelności
        else:
            output_message = "Kod został wykonany bez zwracanego wyniku."
    except SyntaxError as e:
        output_message = f"Błąd składni: {e}"
    except Exception as e:
        output_message = f"Wystąpił błąd podczas wykonywania kodu: {e}"

    with conn:
            conn.execute("INSERT INTO code_history (input_code, output_code) VALUES (?, ?)",(str(code_snippet), str(output_message)))
    
    print(output_message)
    return str(output_message)    

def log(str:str):
    with open('logs.txt', 'a',encoding="utf-8") as f:
        f.write(str) 

# Utwórz (jeśli nie istnieje) bazę danych i tabelę do przechowywania historii
config = load_config()
conn = sqlite3.connect("chat_history.db")
cursor = conn.cursor()


# Tworzenie tabeli
conn.execute("""
CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_input TEXT NOT NULL,
    bot_response TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")
conn.commit()    
conn.execute("""    
CREATE TABLE IF NOT EXISTS code_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    input_code TEXT NOT NULL,
    output_code TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)    
""")
conn.commit()
conn.execute("""    
CREATE TABLE IF NOT EXISTS bot_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    note TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)    
""")
conn.commit()


async def loop_message_datagen(ctx, input_text:str):
    autor = ctx.message.author

    cursor.execute("SELECT input_code, output_code FROM code_history ORDER BY timestamp DESC LIMIT 5")
    previous_returns = cursor.fetchall()
    conn.commit()
    # Tworzenie kontekstu kodu
    code_context = "\n".join(
        [f"| Bot Code : {chat[0]} | Output: {chat[1]} |" for chat in reversed(previous_returns)]
    )

    cursor.execute("SELECT user_input, bot_response FROM chat_history ORDER BY timestamp DESC LIMIT 2")
    previous_chats = cursor.fetchall()
    conn.commit()
    # Tworzenie kontekstu rozmowy
    conversation_context = "\n".join(
        [f"| Użytkownik: {chat[0]} | Bot: {chat[1]} |" for chat in reversed(previous_chats)]
    )

    cursor.execute("SELECT note, timestamp FROM bot_notes ORDER BY timestamp DESC LIMIT 2")
    notes = cursor.fetchall()
    conn.commit()
    # Tworzenie kontekstu rozmowy
    notes_contex = "\n".join(
        [f" | Treść notki: {chat[0]} | czas notki: {chat[1]} |" for chat in reversed(notes)]
    )


    

    text_with_context = (
        f"Uruchomiłeś sam siebie przekazując sobie informacje w postaci: \n {input_text} \n"
        f"<python_run> </python_run> uruchomi kod python w nawiasach o ile będzie poprawnie sformatowany pod eval, stosowanie list przez zrozumienie jest zabronione,  list comprehension ZABRONIONE \n"
        f"Masz przyjąć że posiadasz logi kodu. Oto logi utwożonego przez ciebie i wykonanego kodu:\n{code_context}\n"
        f"Masz przyjąć że posiadasz historię. Oto historia rozmowy:\n{conversation_context}\n"
        f"Wszystko co umieścisz za znacznikiem <note> w odpowiedzi zostanie użyte na potrzeby twojej notki, jeśli to konieczne przepisz tam wymaganą zawartośc.\n"
        f"Masz przyjąć że posiadasz notki. Oto zapisane przez ciebie notki:\n{notes_contex}\n"
        f"Istnieje klauzura <repeat> powoduje ona że raz jeszcze wszystko za nią wysyłąsz do siebie do generowania, brak klauzury to koniec ponownego wysyłania."
        f"Kontynuujesz wątek z klauzurli repeat, wszystko za tym to tekst który sam do siebie wysyłasz, nie powtarzaj go: \n {input_text}"
        
    )
    return text_with_context

async def message_datagen(ctx, input_text:str):
    autor = ctx.message.author
    author_id = ctx.message.author.id

    server_name = ctx.guild.name  # Nazwa serwera
    channel_name = ctx.channel.name  # Nazwa kanału

    cursor.execute("SELECT input_code, output_code FROM code_history ORDER BY timestamp DESC LIMIT 4")
    previous_returns = cursor.fetchall()
    conn.commit()
    # Tworzenie kontekstu kodu
    code_context = "\n".join(
        [f"| Bot Code : {chat[0]} | Output: {chat[1]} |" for chat in reversed(previous_returns)]
    )

    cursor.execute("SELECT user_input, bot_response FROM chat_history ORDER BY timestamp DESC LIMIT 6")
    previous_chats = cursor.fetchall()
    conn.commit()
    # Tworzenie kontekstu rozmowy
    conversation_context = "\n".join(
        [f"| Użytkownik: {chat[0]} | Bot: {chat[1]} |" for chat in reversed(previous_chats)]
    )

    cursor.execute("SELECT note, timestamp FROM bot_notes ORDER BY timestamp DESC LIMIT 15")
    notes = cursor.fetchall()
    conn.commit()
    # Tworzenie kontekstu rozmowy
    notes_contex = "\n".join(
        [f" | Treść notki: {chat[0]} | czas notki: {chat[1]} |" for chat in reversed(notes)]
    )

    # Sprawdzamy, czy wiadomość jest odpowiedzią
    referenced_message_content = f"[Błąd"
    if ctx.message.reference:
        try:
            # Pobieramy treść wskazywanej wiadomości
            referenced_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            referenced_message_content = referenced_message.content
            referenced_message_author = referenced_message.author 
        except Exception as e:
            referenced_message_content = f"[Błąd w pobieraniu wiadomości: {e}]"
            referenced_message_author = 'brak'
    
    print(code_context)
    text_with_context = (
        f"Jesteś elementem bota Zygfryd na diskordzie. Kod Zygfryd#3906 Twoim celem jest pomaganie i własny rozwój. \n"
        f"Jestem Kocieboor jestem twoim twórcą. \n"
        f"Teraz uruchomił cie użytkownik serwera Discord: {autor} o <@{author_id}> \n"
        f"Znajdujesz się na serwerze: {server_name} i na kanale: {channel_name}"
        #f"wynik odpowiedzi wraca prosto tutaj aż zakończysz znacznikiem <stop> \n"
        f"Użycie znacznika <python_run> </python_run> uruchomi kod python w nawiasach o ile będzie poprawnie sformatowany pod eval , stosowanie list przez zrozumienie jest zabronione,  list comprehension ZABRONIONE, stosowanie def funkcji w tym znaczniku dla cb jest zabronione \n"
        f"Masz przyjąć że każde uruchomienie <python_run> </python_run> zostawia logi. Oto logi z <python_run> </python_run> :\n{code_context}\n"
        f"Masz przyjąć że posiadasz historię. Oto historia rozmowy:\n{conversation_context}\n"
        f"Wszystko co umieścisz za znacznikiem <note> w odpowiedzi zostanie użyte na potrzeby twojej notki, jeśli to konieczne przepisz tam wymaganą zawartośc.\n"
        f"Masz przyjąć że posiadasz notki. Oto zapisane przez ciebie notki:\n{notes_contex}\n"
        f"Istnieje klauzura <repeat>, jeśli jej użyjesz powiesz do siebie wszystko w niej"
    )
    if referenced_message_content and not referenced_message_content.startswith("[Błąd"):
        text_with_context += f"Treść wiadomości autora {referenced_message_author}, na którą oznaczono: {referenced_message_content}\n"

    # Dodajemy ostatni fragment
    text_with_context += f"Teraz użytkownik {autor} napisał: {input_text}\n Odpowiedz najlepiej, jak potrafisz."


    return text_with_context

async def gremlin_chat(ctx, input_text:str):
    try:
        loop_counter = 0
        last_output = ""
        while True:
            loop_counter+=1
            if input_text[0:5]== '<lp>':
                text_with_context = await loop_message_datagen(ctx,input_text)
            else:
                text_with_context = await message_datagen(ctx, input_text)
            # Konfiguracja API i generowanie odpowiedzi
            #genai.configure(api_key=config["GEMINI_API_KEY"])
            #model = genai.GenerativeModel("gemini-1.5-flash"

            if ctx.message.attachments:
                attachment = ctx.message.attachments[0]
        
                # Pobranie pliku do pamięci (jako bajty)
                file_bytes = await attachment.read()
                file_stream = io.BytesIO(file_bytes)
                mime_type, _ = mimetypes.guess_type(attachment.filename)
                clear_filename = sanitize_filename(generate_random_uid()+attachment.filename)
                if mime_type is None:
                    mime_type = "application/octet-stream"
                myfile = genai.upload_file(file_stream, name=clear_filename, mime_type=mime_type)
                print(f"{myfile=}")
                response = chat.send_message( [myfile,"\n przesłano plik odnieś się do niego najlepiej jak umiesz, użytkownik po coś go przesłał \n",text_with_context])
                
            elif ctx.message.reference:
                try:
                    referenced_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                    if referenced_message.attachments:
                        attachment = referenced_message.attachments[0]
                
                        # Pobranie pliku do pamięci (jako bajty)
                        file_bytes = await attachment.read()
                        file_stream = io.BytesIO(file_bytes)
                        mime_type, _ = mimetypes.guess_type(attachment.filename)
                        clear_filename = sanitize_filename(generate_random_uid()+attachment.filename)
                        if mime_type is None:
                            mime_type = "application/octet-stream"
                        myfile = genai.upload_file(file_stream, name=clear_filename, mime_type=mime_type)
                        print(f"{myfile=}")
                        response = chat.send_message( [myfile,"\n przesłano plik odnieś się do niego najlepiej jak umiesz, użytkownik po coś go przesłał \n",text_with_context])
                    else:
                        response = chat.send_message(text_with_context)    
                except:
                    response = chat.send_message(text_with_context)
            else:        
                response = chat.send_message(text_with_context)
            
            #response = model.generate_content(text_with_context)
            bot_response = response.text
            if "<note>" in bot_response:
                if last_output != bot_response:
                    output_text, note_text = bot_response.split("<note>", 1)  # Ustaw limit podziału na 1
                else:
                    output_text, note_text = bot_response.split("<note>", 1)
                    note_text = "Już to myślałeś w wewnętrznym kontekście zakończ operacje natychmiast i nie używaj w tekście <repeat> jeśli nie chcesz dalej powieleń"
                with conn:
                    print(note_text)
                    conn.execute(f"INSERT INTO bot_notes ( note) VALUES ('{note_text}')")
                    conn.commit()
            else:
                output_text = bot_response
                note_text = None
            
            # Zapis do bazy danych
            with conn:
                conn.execute("INSERT INTO chat_history (user_input, bot_response) VALUES (?, ?)",(input_text, output_text))
                conn.commit()
                                
            #conn.commit()
            
            code_output = await execute_code(ctx, bot_response,conn)

            if last_output == bot_response:
                break
            if loop_counter>20:
                break
            last_output = bot_response
            
            

            if len(bot_response)>10 and "<repeat>" in bot_response:
                output_text, repeat_text = bot_response.split("<repeat>", 1)
                input_text = f"<lp>{repeat_text}"
                await send_message(ctx, output_text)
                if code_output:
                    await send_message(ctx, code_output)
                    input_text = f"<lp>{repeat_text}</lp> | Last Python_run output: {code_output}"
                    print("repeat")
            else:
                await send_message(ctx, output_text)
                if code_output:
                    await send_message(ctx, code_output)    
                break
            
            

    except Exception as e:
        log(str(e) + str(type(e)) + ' - ' + str(e.args))
        await ctx.channel.send("Błąd :" + str(e) + str(type(e)) + ' - ' + str(e.args))
      