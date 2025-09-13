import sqlite3 as sl

def init(con):
    tables = {
        "logs": """
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usser TEXT,
                tresc TEXT,
                data DATETIME
            );
        """,
        "mlists": """
            CREATE TABLE IF NOT EXISTS mlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server TEXT,
                url TEXT,
                filename TEXT,
                loop INTEGER,
                listname TEXT,
                actual INTEGER,
                data DATETIME,
                desc TEXT
            );
        """,
        "reminders": """
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chanel_id INTEGER,
                tresc TEXT,
                data DATETIME
            );
        """,
        "chanel_storage": """
            CREATE TABLE IF NOT EXISTS chanel_storage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chanel_id INTEGER,
                object TEXT,
                quantity INTEGER,
                descrypton TEXT    
            );
        """,
        "chanel_receptures": """
            CREATE TABLE IF NOT EXISTS chanel_receptures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chanel_id INTEGER,
                name TEXT,
                object TEXT,    
                recepture TEXT,
                descryption TEXT    
            );
        """,
        "global_variables": """
            CREATE TABLE IF NOT EXISTS global_variables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_id INTEGER,
                key TEXT,
                value TEXT    
            );
        """
    }

    with con:
        for name, ddl in tables.items():
            con.execute(ddl)
            print(f"Table '{name}' checked/created.")


def init_old(con):
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
