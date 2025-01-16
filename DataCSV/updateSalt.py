import hashlib
from math import floor, ceil
import csv
from datetime import datetime
import os

def encrypt_pass(password, salt):
    saltedPass = salt[0:floor(len(salt)/2)] + password + salt[ceil(len(salt)/2):len(salt)]
    sha256 = hashlib.sha256()
    sha256.update(saltedPass.encode())
    return sha256.hexdigest()

def random_salt():
    import random
    import string
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

PATH = "C:/Users/admin/Desktop/NotSpotify/DataCSV/"

def update_user_csv():

    with open(PATH + 'nsuser.csv', 'r') as file:
        reader = csv.reader(file)
        users = list(reader)
    file.close()

    with open(PATH + 'nsuser.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["user_id", "username", "password", "first_name", "last_name", "email", "last_access_date", "creation_date", "date_of_birth", "salt"])
        for user in users:
            user_id = user[0]
            username = user[1]
            password = user[2]
            first_name = user[3]
            last_name = user[4]
            email = user[5]
            last_access_date = user[6]
            creation_date = user[7]
            date_of_birth = user[8]
            salt = random_salt()

            password = encrypt_pass(password, salt)
            print(f"User: {email}, username: {username} Salt: {salt} Password: {password}")
            writer.writerow([user_id, username, password, first_name, last_name, email, last_access_date, creation_date, date_of_birth, salt])
    file.close()

def update_user_db():

    with open(PATH + 'nsuser.csv', 'r') as file:
        reader = csv.reader(file)
        users = list(reader)
    file.close()
    all_query = ""
    for user in users[1:]:
        print(user)
        user_id = user[0]
        password = user[2]
        salt = user[9]

        all_query += f"UPDATE nsuser SET password = '{password}', salt = '{salt}' WHERE user_id = {user_id};\n"

    with open(PATH + 'update_salt.sql', 'w') as file:
        file.write(all_query)
    file.close()