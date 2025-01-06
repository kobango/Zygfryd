import sqlite3 as sl
def init(con):
    try:
        with con:
            con.execute("""
                CREATE TABLE logs (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    usser TEXT,
                    tresc TEXT,
                    data datetime
                );
            """)
    except:
        print("table exist")
        
    try:
        with con:
            con.execute("""
                CREATE TABLE mlists (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    server TEXT,
                    url TEXT,
                    filename TEXT,
                    loop INTEGER,
                    listname TEXT,
                    actual INTEGER,
                    data datetime,
                    desc TEXT
                );
            """)
    except:
        print("table exist")

    try:
        with con:
            con.execute("""
                CREATE TABLE reminders (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    chanel_id INTEGER,
                    tresc TEXT,
                    data datetime
                );
            """)
    except:
        print("table exist")

    try:
        with con:
            con.execute("""
                CREATE TABLE chanel_storage (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    chanel_id INTEGER,
                    object TEXT,
                    quantity INTEGER,
                    descrypton TEXT    
                );
            """)
    except:
        print("table exist")

    try:
        with con:
            con.execute("""
                CREATE TABLE chanel_receptures (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    chanel_id INTEGER,
                    name TEXT,
                    object TEXT,    
                    recepture TEXT,
                    descryption TEXT    
                );
            """)
    except:
        print("table exist")    

    try:
        with con:
            con.execute("""
                CREATE TABLE global_variables (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    server_id INTEGER,
                    key TEXT,
                    value TEXT    
                );
            """)
    except:
        print("table exist")       
