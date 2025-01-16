"""
Script Name: convert.py
Author: Adrian Marcellus
Date: 2024-10-19
Description: 
    Convert JSON data for tables Artist, Album, Song, Genre, Album_Artist, Song_Album, Album_Genre, Song_Genre, and Song_Artist to CSV files.
    Certain file structure in needed in base directory to run this script.
Usage: python convert.py
"""

import csv
import json
import os

PATH = "C:/Users/admin/Desktop/NotSpotify/DataCSV/"
# function to read JSON data from file
def read_json_file(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return json.load(file)

# function to write data to CSV
def write_to_csv(filename, data, fieldnames):
    filepath = PATH + "outputConvert/" + filename
    file_exists = os.path.isfile(filepath)
    with open(filepath, 'a+', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for row in data:
            writer.writerow(row)

# write all csv files
def process_data(json_filename):
    # Load the JSON data
    json_filepath = "C:/Users/admin/Desktop/NotSpotify/DataCSV/JSONData/" + json_filename
    data = read_json_file(json_filepath)

    # Write main entities to CSV
    write_to_csv('artist.csv', data['Artist'], ['artist_id', 'stage_name'])
    write_to_csv('album.csv', data['Album'], ['album_id', 'name', 'release_date'])
    write_to_csv('song.csv', data['Song'], ['song_id', 'title', 'release_date', 'length'])
    #write_to_csv('genre.csv', data['Genre'], ['genre_id', 'name'])

    # Write relationships to CSV
    write_to_csv('album_artist.csv', data['Album_Artist'], ['album_id', 'artist_id'])
    write_to_csv('song_album.csv', data['Song_Album'], ['song_id', 'album_id', 'track_number'])
    write_to_csv('album_genre.csv', data['Album_Genre'], ['album_id', 'genre_id'])
    write_to_csv('song_genre.csv', data['Song_Genre'], ['song_id', 'genre_id'])
    write_to_csv('song_artist.csv', data['Song_Artist'], ['song_id', 'artist_id'])

    print("Data for " + json_filename + " has been written to CSV files.")

# Main
if __name__ == "__main__":
     # get folder names list
    list = os.listdir(PATH + "/JSONData")
    sorted_list = sorted(list, key=lambda x: int(x.split('-')[0]))
    for i in range(len(sorted_list)):
        process_data(sorted_list[i])