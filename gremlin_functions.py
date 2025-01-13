import sqlite3
import discord
import ast
import io
import sys
import gremlin_functions
from config_menage import load_config
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup # Wymagana biblioteka do parsowania HTML
import re

def extract_def_lines(filepath):
    """
    Odczytuje plik i zwraca listę linii zawierających słowo "def".

    Args:
        filepath: Ścieżka do pliku.

    Returns:
        Listę linii zawierających "def" lub None w przypadku błędu.
    """
    try:
        with open(filepath, 'r') as file:
            lines = file.readlines()
    except FileNotFoundError:
        print(f"Błąd: Plik '{filepath}' nie został znaleziony.")
        return None
    except Exception as e:
        print(f"Błąd podczas otwierania pliku: {e}")
        return None

    def_lines = [line.strip() for line in lines if "def " in line]  # Użycie list comprehension dla lepszej czytelności
    return def_lines



def przetworz_link(url:str):
  """
  Pobiera zawartość strony internetowej z podanego adresu URL i zwraca przetworzone dane.

  Args:
    url: Adres URL strony internetowej.

  Returns:
    Słownik zawierający przetworzone dane lub None w przypadku błędu.
  """
  try:
    response = requests.get(url) # Pobieranie strony
    response.raise_for_status() # Sprawdzanie błędów HTTP (np. 404)
    soup = BeautifulSoup(response.content, "html.parser") # Parsowanie HTML

    #  ---  Tutaj należy dodać logikę przetwarzania danych ---
    #  Przykład:  wyodrębnienie tytułu strony
    tytul = soup.title.string if soup.title else "Tytuł niedostępny"

    # ... Dodaj więcej logiki ekstrakcji danych (np. tekst, metadane) ...

    return {"url": url, "tytul": tytul, "treść": soup.get_text()}   # ...inne dane...}


  except requests.exceptions.RequestException as e:
    print(f"Błąd podczas pobierania strony: {e}")
    return None
  except Exception as e:
    print(f"Błąd podczas przetwarzania danych: {e}")
    return None
  

def extract_python_code(text):
  """
  Extracts Python code enclosed in <python_run></python_run> and ```python ``` blocks.

  Args:
      text (str): Input text to search for Python code.

  Returns:
      list: List of extracted Python code snippets.
  """
  # Regular expressions to match the desired patterns
  pattern_python_run = r"<python_run>(.*?)</python_run>"
  pattern_triple_backticks = r"```python\n(.*?)```"

  # Extract content between <python_run>...</python_run>
  python_run_matches = re.findall(pattern_python_run, text, re.DOTALL)

  # Extract content between ```python ... ```
  triple_backticks_matches = re.findall(pattern_triple_backticks, text, re.DOTALL)

  # Combine all matches into a single list
  extracted_code = python_run_matches + triple_backticks_matches

  return extracted_code



async def execute_snippet(snippet, ctx, conn):
    try:
        tree = ast.parse(snippet)  # Analyze code with AST
        # Check for dangerous functions (e.g., os.system, import os)
        ALLOWED_MODULES = {"math", "random", "datetime"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name not in ALLOWED_MODULES and alias.name in ["os", "subprocess", "sys"]:
                        await ctx.channel.send("Wykonywanie kodu z importem modułów 'os', 'subprocess' lub 'sys' jest zabronione.")
                        return ""
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in ["exec", "eval"]:
                    await ctx.channel.send("Wykonywanie funkcji 'exec' i 'eval' jest zabronione.")
                    return ""
        compiled_code = compile(tree, '<string>', 'exec')

        # Execute code in a safe environment (e.g., with restricted access to files and systems)
        old_stdout = sys.stdout
        redirected_output = sys.stdout = io.StringIO()
        allowed_globals = globals()
        allowed_globals['ctx'] = ctx
        exec(compiled_code, allowed_globals)
        sys.stdout = old_stdout
        output_message = redirected_output.getvalue().strip()

    except SyntaxError as e:
        output_message = f"Błąd składni: {e}"
    except Exception as e:
        output_message = f"Wystąpił błąd podczas wykonywania kodu: {e}"

    # Save to database
    with conn:
        conn.execute("INSERT INTO code_history (input_code, output_code, server) VALUES (?, ?, ?)",
                      (snippet, output_message, str(ctx.guild.id)))

    return output_message
