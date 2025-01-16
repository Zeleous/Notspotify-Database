"""
Script Name: createRandom.py
Author: Adrian Marcellus
Date: 2024-10-19
Description: 
    This script generates random data for the User_Following, Playlist, Playlist_Song, History, and Rating tables and saves the data to CSV files.
    Certain file structure in needed in base directory to run this script.
Usage: python createRandom.py
"""

import random
import csv
from datetime import datetime, timedelta

# Define ranges of primary keys for random data generation
USER = 200
SONG = 438
PLAYLIST = 200
TRACK = 15
STAR = 5

PATH = "C:/Users/admin/Desktop/NotSpotify/DataCSV/"

# Generate random date within the last year
def random_date():
    end = datetime.now()
    start = end - timedelta(days=365)
    return start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

# Generate data for User_Following table
def generate_user_following(num):
    data = []
    for _ in range(num + 1):
        follower = random.randint(1, USER)
        following = random.randint(1, USER)
        while following == follower:
            following = random.randint(1, USER)
        follow_date = random_date()
        data.append({
            'follower': follower,
            'following': following,
            'follow_date': follow_date.strftime('%Y-%m-%d')
        })
    return data

# Generate data for Playlist table
def generate_playlist():
    data = []
    for i in range(1, PLAYLIST + 1):
        name = f"Playlist_{i}"
        user_id = random.randint(1, USER)
        data.append({
            'playlist_id': i,
            'name': name,
            'user_id': user_id
        })
    return data

# Generate data for Playlist_Song table
def generate_playlist_song():
    data = []
    for playlist_id in range(1, PLAYLIST + 1):
        for track_id in range(1, random.randint(1, TRACK)):
            song_id = random.randint(1, SONG)
            data.append({
                'playlist_id': playlist_id,
                'song_id': song_id,
                'track_number': track_id
            })
    return data

# Generate data for History table
def generate_history(num):
    data = []
    for _ in range(num + 1):
        user_id = random.randint(1, USER)
        song_id = random.randint(1, SONG)
        listen_date = random_date()
        data.append({
            'user_id': user_id,
            'song_id': song_id,
            'listen_date': listen_date.strftime('%Y-%m-%d %H:%M:%S')
        })
    return data

# Generate data for Rating table
def generate_rating(num):
    data = []
    for _ in range(num + 1):
        user_id = random.randint(1, USER)
        song_id = random.randint(1, SONG)
        star_rating = random.randint(1, STAR)
        data.append({
            'user_id': user_id,
            'song_id': song_id,
            'star_rating': star_rating
        })
    return data

# Function to write data to CSV
def write_to_csv(filename, data):
    with open(PATH + "outputRandom/" + filename, 'w', newline='', encoding='utf-8') as csvfile:
        if data:
            writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    print("Data written to outputRandom/" + filename)

# Main function to generate all data and save to CSV
def generate_and_save_all_data():
    tables = {
        'User_Following': generate_user_following(450),
        'Playlist': generate_playlist(),
        'Playlist_Song': generate_playlist_song(),
        'History': generate_history(450),
        'Rating': generate_rating(450)
    }

    for table_name, data in tables.items():
        write_to_csv(f"{table_name}.csv", data)

# Generate and save data
if __name__ == "__main__":
    generate_and_save_all_data()