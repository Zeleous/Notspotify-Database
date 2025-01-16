"""
Script Name: Connection.py
Author: !Spotify
Date: 2024-10-31
Description: This script establishes a connection to the database and runs the NotSpotify application.
Usage: python Connection.py
"""

import psycopg2
from sshtunnel import SSHTunnelForwarder
from application import NotSpotify
from dotenv import load_dotenv
import os

load_dotenv()

username = os.getenv("CS_USERNAME")
password = os.getenv("CS_PASSWORD")
dbName = "p320_15"

try:
    with SSHTunnelForwarder(('starbug.cs.rit.edu', 22),
                            ssh_username=username,
                            ssh_password=password,
                            remote_bind_address=('127.0.0.1', 5432)) as server:
        server.start()
        print("SSH tunnel established")
        params = {
            'database': dbName,
            'user': username,
            'password': password,
            'host': 'localhost',
            'port': server.local_bind_port
        }

        conn = psycopg2.connect(**params)
        curs = conn.cursor()
        print("Database connection established")

        app = NotSpotify(cursor=curs)
        app.main_menu()

        conn.close()
except Exception as e:
    print(e)
    print("Connection failed")