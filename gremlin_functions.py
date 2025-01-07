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