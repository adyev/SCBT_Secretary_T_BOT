import config
import psycopg2
from psycopg2.extras import DictCursor

def SQL_Select(query, args):
    conn = psycopg2.connect(dbname = config.DB_NAME, user = config.DB_USER, 
                        password = config.DB_PASSWORD, host = config.DB_HOST)
    cursor = conn.cursor(cursor_factory=DictCursor)
    cursor.execute(query, args)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def SQL_Update(query, args):
    conn = psycopg2.connect(dbname = config.DB_NAME, user = config.DB_USER, 
                        password = config.DB_PASSWORD, host = config.DB_HOST)
    cursor = conn.cursor(cursor_factory=DictCursor)
    cursor.execute(query, args)
    conn.commit()
    cursor.close()
    conn.close()