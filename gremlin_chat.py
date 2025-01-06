import sqlite3
import discord
import ast
import io
import sys
import gremlin_functions
from config_menage import load_config
import google.generativeai as genai

async def send(ctx,str:str):
    with open('send.txt', 'w',encoding="utf-8") as f:
        f.write("\n"+str) 
    file = discord.File('send.txt')
    await ctx.channel.send('See attachment below',file=file)

def podziel_tekst(tekst, max_dlugosc):
    akapity = tekst.split('\n\n')
    fragmenty = []
    biezacy_fragment = ""
    for akapit in akapity:
        if len(biezacy_fragment) + len(akapit) <= max_dlugosc:
            biezacy_fragment += akapit + '\n\n'
        else:
            fragmenty.append(biezacy_fragment.strip())
            biezacy_fragment = akapit + '\n\n'
    fragmenty.append(biezacy_fragment.strip())
    return fragmenty

async def send_message(ctx, bot_response):
    """Wysyła odpowiedź na Discord, dzieląc ją na mniejsze części, jeśli jest za długa."""
    if len(bot_response) <= 1800:
        await ctx.channel.send(bot_response)
    else:
        parts = podziel_tekst(bot_response,1800)
        for part in parts:
            await ctx.channel.send(part)    

async def execute_code(ctx, message,conn):
    """Bezpiecznie wykonuje kod Python zawarty między znacznikami <python_run> i </python_run>."""

    start_index = message.find("<python_run>")
    if start_index == -1:
        return  # Znacznik nie znaleziony

    end_index = message.find("</python_run>", start_index + len("<python_run>"))
    if end_index == -1:
        return  # Zamykający znacznik nie znaleziony

    code_snippet = message[start_index + len("<python_run>"):end_index].strip()
    #print(str(code_snippet))
    code_snippet = code_snippet.strip()
    code_snippet = code_snippet.replace("```","")
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
        exec(compiled_code)
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

async def inner_message_datagen(ctx, input_text:str):
    autor = ctx.message.author

    cursor.execute("SELECT input_code, output_code FROM code_history ORDER BY timestamp DESC LIMIT 4")
    previous_returns = cursor.fetchall()
    conn.commit()
    # Tworzenie kontekstu kodu
    code_context = "\n".join(
        [f"Kod wejścia: {chat[0]} | Zwrócił: {chat[1]}" for chat in reversed(previous_returns)]
    )

    cursor.execute("SELECT user_input, bot_response FROM chat_history ORDER BY timestamp DESC LIMIT 10")
    previous_chats = cursor.fetchall()
    conn.commit()
    # Tworzenie kontekstu rozmowy
    conversation_context = "\n".join(
        [f"Użytkownik: {chat[0]} | Bot: {chat[1]}" for chat in reversed(previous_chats)]
    )

    cursor.execute("SELECT note, timestamp FROM bot_notes ORDER BY timestamp DESC LIMIT 10")
    notes = cursor.fetchall()
    conn.commit()
    # Tworzenie kontekstu rozmowy
    notes_contex = "\n".join(
        [f" treść notki: {chat[0]} | czas notki: {chat[1]}" for chat in reversed(notes)]
    )

    nazwy_funkcji = gremlin_functions.extract_def_lines("gremlin_functions.py")
    
    print(str(nazwy_funkcji))
    text_with_context = (
        f"Masz przyjąć że posiadasz historię kodu. Oto historia kodu:\n{code_context}\n"
        f"Masz przyjąć że posiadasz historię. Oto historia rozmowy:\n{conversation_context}\n"
        f"Masz przyjąć że posiadasz notki. Oto zapisane przez ciebie notki:\n{notes_contex}\n"
        f"Istnieje klauzura <repeat> używana na końcu, powoduje ona że raz jeszcze wszystko za nią wysyłąsz do generowania ale z odpowiedzią na zewnątrz, brak klauzury to koniec generowania"
        f"Istnieje klauzura <inner> używana na początku, dodana do odpowiedzi przekazuje do ciebie wewnętrznie wszystko, nic nie zostanie wypisane, klauzura ta ma wyższy priorytet niż repeat ale staraj się nie powielać."
        f"Dostępne są podane funkcje wraz z opisami, sugeruje sie użycie kolejnego <inner> lub funkcji <repeat> by wyświetlić dane."
        f"Dostępne Funkcje które będą możliwe do wykonana jeśli użyto inner: {str(nazwy_funkcji)}"
        f"Użyj repeat i uzyskane dane postaraj się zademonstrować jako że nikt nie widzi wyniku kodu, to wyjątek od reguły minimalizmu"
        f"Kontynuujesz wątek z klauzurli <inner> staraj się tego używać tylko do podglądu funkcji, nikt nie widzi tego co tu piszesz, nawet ja \n"
        f"Wysłałeś do siebie następujące informacje używając <inner> \n {input_text}"
        
    )
    return text_with_context


async def loop_message_datagen(ctx, input_text:str):
    autor = ctx.message.author

    cursor.execute("SELECT input_code, output_code FROM code_history ORDER BY timestamp DESC LIMIT 4")
    previous_returns = cursor.fetchall()
    conn.commit()
    # Tworzenie kontekstu kodu
    code_context = "\n".join(
        [f"Kod wejścia: {chat[0]} | Zwrócił: {chat[1]}" for chat in reversed(previous_returns)]
    )

    cursor.execute("SELECT user_input, bot_response FROM chat_history ORDER BY timestamp DESC LIMIT 10")
    previous_chats = cursor.fetchall()
    conn.commit()
    # Tworzenie kontekstu rozmowy
    conversation_context = "\n".join(
        [f"Użytkownik: {chat[0]} | Bot: {chat[1]}" for chat in reversed(previous_chats)]
    )

    cursor.execute("SELECT note, timestamp FROM bot_notes ORDER BY timestamp DESC LIMIT 10")
    notes = cursor.fetchall()
    conn.commit()
    # Tworzenie kontekstu rozmowy
    notes_contex = "\n".join(
        [f" treść notki: {chat[0]} | czas notki: {chat[1]}" for chat in reversed(notes)]
    )


    

    text_with_context = (
        f"Istnieje limit 1800 znaków, jeśli go przekroczono doklej przerwy tak by podzielić odpowiednio znaczniki kodu.\n"
        f"<python_run> </python_run> uruchomi kod python w nawiasach o ile będzie poprawnie sformatowany pod eval, stosowanie list przez zrozumienie jest zabronione,  list comprehension ZABRONIONE \n"
        f"Masz przyjąć że posiadasz historię kodu. Oto historia kodu:\n{code_context}\n"
        f"Masz przyjąć że posiadasz historię. Oto historia rozmowy:\n{conversation_context}\n"
        f"Wszystko co umieścisz za znacznikiem <note> w odpowiedzi zostanie użyte na potrzeby twojej notki, jeśli to konieczne przepisz tam wymaganą zawartośc.\n"
        f"Masz przyjąć że posiadasz notki. Oto zapisane przez ciebie notki:\n{notes_contex}\n"
        f"Istnieje klauzura <repeat> powoduje ona że raz jeszcze wszystko za nią wysyłąsz do siebie do generowania, brak klauzury to koniec ponownego wysyłania."
        f"Kontynuujesz wątek z klauzurli repeat, wszystko za tym to tekst który sam do siebie wysyłasz, nie powtarzaj go: \n {input_text}"
        
    )
    return text_with_context

async def message_datagen(ctx, input_text:str):
    autor = ctx.message.author

    cursor.execute("SELECT input_code, output_code FROM code_history ORDER BY timestamp DESC LIMIT 4")
    previous_returns = cursor.fetchall()
    conn.commit()
    # Tworzenie kontekstu kodu
    code_context = "\n".join(
        [f"Kod wejściowy : {chat[0]} | Output twojego kodu: {chat[1]}" for chat in reversed(previous_returns)]
    )

    cursor.execute("SELECT user_input, bot_response FROM chat_history ORDER BY timestamp DESC LIMIT 10")
    previous_chats = cursor.fetchall()
    conn.commit()
    # Tworzenie kontekstu rozmowy
    conversation_context = "\n".join(
        [f"Użytkownik: {chat[0]} | Bot: {chat[1]}" for chat in reversed(previous_chats)]
    )

    cursor.execute("SELECT note, timestamp FROM bot_notes ORDER BY timestamp DESC LIMIT 10")
    notes = cursor.fetchall()
    conn.commit()
    # Tworzenie kontekstu rozmowy
    notes_contex = "\n".join(
        [f" treść notki: {chat[0]} | czas notki: {chat[1]}" for chat in reversed(notes)]
    )


    
    print(code_context)
    text_with_context = (
        f"Jesteś elementem bota Zygfryd na diskordzie. Kod Zygfryd#3906 Twoim celem jest pomaganie i własny rozwój. \n"
        f"Jestem Kocieboor jestem twoim twórcą. \n"
        f"Istnieje limit 1800 znaków, jeśli go przekroczono doklej przerwy tak by podzielić odpowiednio znaczniki kodu.\n"
        f"Uważaj by nie wpaść w pętle. \n "
        #f"wynik odpowiedzi wraca prosto tutaj aż zakończysz znacznikiem <stop> \n"
        f"<python_run> </python_run> uruchomi kod python w nawiasach o ile będzie poprawnie sformatowany pod eval , stosowanie list przez zrozumienie jest zabronione,  list comprehension ZABRONIONE, stosowanie def funkcji w tym znaczniku dla cb jest zabronione \n"
        f"Masz przyjąć że każde uruchomienie <python_run> </python_run> zostawia historię. Oto historia kodu z <python_run> </python_run> :\n{code_context}\n"
        f"Masz przyjąć że posiadasz historię. Oto historia rozmowy:\n{conversation_context}\n"
        f"Wszystko co umieścisz za znacznikiem <note> w odpowiedzi zostanie użyte na potrzeby twojej notki, jeśli to konieczne przepisz tam wymaganą zawartośc.\n"
        f"Masz przyjąć że posiadasz notki. Oto zapisane przez ciebie notki:\n{notes_contex}\n"
        f"Istnieje klauzura <repeat>, powoduje ona że raz jeszcze wszystkoi w niej wszystko za nią wysyłąsz do modelu do generowania, brak klauzury to koniec generowania"
        f"Teraz użytkownik {autor} napisał: {input_text}\n Odpowiedz najlepiej jak potrafisz."
    )
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
            genai.configure(api_key=config["GEMINI_API_KEY"])
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(text_with_context)
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
                    input_text = f"<lp>{repeat_text} | Last Python_run output: {code_output}"
                    print("repeat")
            else:
                await send_message(ctx, output_text)
                if code_output:
                    await send_message(ctx, code_output)    
                break
            
            

    except Exception as e:
        log(str(e) + str(type(e)) + ' - ' + str(e.args))
        await ctx.channel.send("Błąd :" + str(e) + str(type(e)) + ' - ' + str(e.args))
      