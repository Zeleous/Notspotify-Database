"""
Script Name: application.py
Author: !Spotify
Date: 2024-10-31
Description: 
    This script contains the NotSpotify application, a music CLI application that allows users to create playlists, 
    search for songs, play songs, and follow other users.
Usage: python Connection.py
"""

from user import User
from datetime import date
from datetime import datetime, timedelta
import hashlib
import string
from random import choices
from math import floor, ceil


class NotSpotify:
    def __init__(self, cursor):
        self.cursor = cursor


    '''
        Helper function used by user menu items to check if the user  
        wants to return to the main menu or not.
        Returns True if exit, False if continue
    '''
    def userExitToMenu(self):
        return input("Press any key to continue or press M to return to menu.").lower() == "m"


    '''
        Hashes a given password with a given salt with SHA256
        Returns the hexdigest of the hash
    '''
    def encrypt_pass(self, password, salt):
        saltedPass = salt[0:floor(len(salt)/2)] + password + salt[ceil(len(salt)/2):len(salt)]
        sha256 = hashlib.sha256()
        sha256.update(saltedPass.encode())
        return sha256.hexdigest()


    '''
        Creates an empty playlist tied to the user's ID
    '''
    def create_playlist(self):
        while True:
            playlist_name = input("Please enter the name of the playlist you would like to make:")
            self.cursor.execute(f"INSERT INTO playlist (playlist_id, playlist_name, user_id) VALUES"
                                f"((SELECT COUNT(*) FROM playlist) + 1, '{playlist_name}', '{self.user.user_id}')")
            self.cursor.connection.commit()
            print(f"Playlist '{playlist_name}' created successfully.")
            break


    '''
        Users will be able to get the list of all their playlists by name in descending order.
        Information includes:
        Playlist name
        Returns an array of playlists
    '''
    def get_playlists(self):
        query = f"""
            SELECT p.playlist_id, p.playlist_name, 
            COUNT(ps.song_id) as song_count,
            SUM(
                CAST(SPLIT_PART(s.length, ':', 1) || ' minutes ' ||
                        SPLIT_PART(s.length, ':', 2) || ' seconds' 
                AS INTERVAL)
            ) as total_duration
            FROM playlist as p
            LEFT JOIN playlist_song as ps ON p.playlist_id = ps.playlist_id
            LEFT JOIN song as s ON ps.song_id = s.song_id
            WHERE p.user_id = '{self.user.user_id}'
            GROUP BY p.playlist_id, p.playlist_name
            ORDER BY playlist_name ASC
        """
        self.cursor.execute(query)
        playlists = self.cursor.fetchall()
        if not playlists:
            return None

        return playlists

     
    '''
        Users will be able to get the list of all their playlists by name in ascending order.
        The list must show the following information per playlist:
        Playlist name
        Number of songs in the playlist
        Total duration in minutes
    '''
    def list_playlists(self, playlists):
        if not playlists:
            print("You have no playlists.")
            return
        print("Here are your playlists:")
        print(f"{'Playlist Name':<30} {'Song Count':<15} {'Total Duration':<15}")
        for idx, (playlist_id, playlist_name, song_count, total_duration) in enumerate(playlists, start=1):
            print(f"{idx}. {playlist_name:<30} {song_count:<15} {total_duration}")
        
    '''
    Users will be able to search for songs by name, artist, album, or genre. The resulting
    list of songs must show the songs name, the artists name, the album, the length and
    the listen count. The list must be sorted alphabetically (ascending) by songs name
    and artists name. Users can sort the resulting list by song name, artists name, genre,
    and released year (ascending and descending).
    '''
    def search_songs(self):
        
        print("Search by (1) Song Name, (2) Artist Name, (3) Album Name, (4) Genre:")
        search_criteria = input().strip()
        
        print("Sort by (1) Song Name, (2) Artist Name, (3) Genre, (4) Released Year:")
        sort_by = input().strip()
        
        print("Sort order (1) Ascending, (2) Descending:")
        sort_order = input().strip()

        print("Please enter the search term:")
        search_term = input().strip().title()  
        
        sort_fields = {
            '1': 'song.title',
            '2': 'artist.stage_name',
            '3': 'song.genre',
            '4': 'song.release_date'
        }
        search_fields = {
            '1': 'song.title',
            '2': 'artist.stage_name',
            '3': 'album.name',
            '4': 'genre.name'
        }

        # Default to ascending sort order unless user specifies descending
        order = 'ASC' if sort_order == '1' else 'DESC'

        query = f"""
            SELECT song.title, artist.stage_name, album.name, song.length, 
                COUNT(history.song_id), song.release_date
            FROM song
            JOIN song_album ON song.song_id = song_album.song_id
            JOIN album ON song_album.album_id = album.album_id
            JOIN album_artist ON album.album_id = album_artist.album_id
            JOIN artist ON album_artist.artist_id = artist.artist_id
            JOIN song_genre ON song.song_id = song_genre.song_id
            JOIN genre ON song_genre.genre_id = genre.genre_id
            LEFT JOIN history ON song.song_id = history.song_id
            WHERE {search_fields.get(search_criteria, 'song.title')} LIKE '%{search_term}%'
            GROUP BY song.title, artist.stage_name, album.name, song.length, song.release_date
            ORDER BY {sort_fields.get(sort_by, 'song.title')} {order}, artist.stage_name {order}
        """
        self.cursor.execute(query)
        res = self.cursor.fetchall()
        
        if not res: 
            print("No songs found returning to main menu")
            return
        
        print(f"{'Song Name':<30} {'Artist':<25} {'Album':<25} {'Length':<10} {'Listens':<10} {'Year':<5}")
        for ( title, artist_name, album_name, lenght, listen_count, release_year) in res:
            print(f"{title:<30} {artist_name:<25} {album_name:<25} {lenght:<10} {listen_count:<10} {release_year.year}")
        print("Press enter to return to the main menu.")
        input()
            
        
    '''
        Adds an album or song to the playlist
    '''
    def add_to_playlist(self):
        while True:
            playlists = self.get_playlists()
            if not playlists:
                print("You have no playlists to add to.")
                break
            self.list_playlists(playlists)
            playlist_choice = int(input("Please enter the corresponding number of the playlist you would like to add to: ")) - 1

            type = input("Would you like to add an album or a song? (1) Album (2) Song: ")

            selected_playlist_id = playlists[playlist_choice][0] 

            if type == "1":
                album = input("Please enter the album name you would like to add: ").lower()
                self.cursor.execute(f"""
                    SELECT album.album_id, album.name, album.release_date, artist.stage_name
                    FROM album
                    JOIN album_artist ON album.album_id = album_artist.album_id
                    JOIN artist ON album_artist.artist_id = artist.artist_id
                    WHERE LOWER(album.name) LIKE '%{album}%'
                """)
                albums = self.cursor.fetchall()

                if not albums:
                    print("No matching albums found.")
                    continue

                for idx, (album_id, name, release_date, stage_name) in enumerate(albums, start=1):
                     print(f"{idx}. {name} by {stage_name} - {release_date}")

                print(f"{len(albums) + 1}. Cancel")
                album_choice = int(input("Please enter the corresponding number of the album you would like to add: ")) - 1
                if album_choice == len(albums):
                    continue
                self.cursor.execute(f"SELECT song_id FROM song_album WHERE album_id = '{albums[album_choice][0]}'")
                songs = self.cursor.fetchall()
                inserts = ""
                for song in songs:
                    song_id = song[0]
                    inserts += f"""INSERT INTO playlist_song (playlist_id, song_id, tack_number) VALUES
                                        ({selected_playlist_id}, {song_id}, 
                                        (SELECT COUNT(*) FROM playlist_song WHERE playlist_id = {playlists[playlist_choice][0]}) + 1);
                                        \n
                                        """
                    
                if inserts == "":
                    print("Album has no songs.")
                    continue

                self.cursor.execute(inserts)
                self.cursor.connection.commit()
                print(f"Album '{albums[album_choice][1]}' added to your playlist.")
            elif type == "2":
                song = input("Please enter the song name you would like to add: ").lower()

                self.cursor.execute(f"""
                    SELECT song.song_id, song.title, song.release_date, song.length, artist.stage_name
                    FROM song
                    JOIN song_album ON song.song_id = song_album.song_id
                    JOIN album_artist ON song_album.album_id = album_artist.album_id
                    JOIN artist ON album_artist.artist_id = artist.artist_id
                    WHERE LOWER(song.title) LIKE '%{song}%'
                """)

                songs = self.cursor.fetchall()
                if not songs:
                    print("No matching songs found.")
                    continue

                for idx, (song_id, title, release_date, length, stage_name) in enumerate(songs, start=1):
                    print(f"{idx}. {title} by {stage_name} - {release_date} - {length}")

                print(f"{len(songs) + 1}. Cancel")
                song_choice = int(input("Please enter the corresponding number of the song you would like to add: ")) - 1

                if song_choice == len(songs):
                    continue

                selected_song_id = songs[song_choice][0]
                self.cursor.execute(f"""INSERT INTO playlist_song (playlist_id, song_id, tack_number) VALUES
                                    ({selected_playlist_id}, {selected_song_id}, (SELECT COUNT(*) FROM playlist_song WHERE playlist_id = {playlists[playlist_choice][0]}) + 1)
                                    """)
                self.cursor.connection.commit()
                print(f"Song '{songs[song_choice][1]}' added to your playlist.")

            else:
                print("Invalid input choice, try again?")
                continue

            return

    '''
        Removes an album or song from the playlist
    '''
    def remove_from_playlist(self):
        while True:
            playlists = self.get_playlists()
            if not playlists:
                print("You have no playlists to remove from.")
                break

            self.list_playlists(playlists)
            playlist_choice = int(input("Please enter the corresponding number of the playlist you would like to remove from: ")) - 1

            type = input("Would you like to remove an album or a song? (1) Album (2) Song: ")

            selected_playlist_id = playlists[playlist_choice][0] 

            if type == "1":
                self.cursor.execute(f"""
                    SELECT DISTINCT album.album_id, album.name, album.release_date 
                    FROM album
                    JOIN song_album ON album.album_id = song_album.album_id
                    JOIN playlist_song ON song_album.song_id = playlist_song.song_id
                    WHERE playlist_song.playlist_id = {selected_playlist_id}
                """)
                albums = self.cursor.fetchall()
                
                if not albums:
                    print("No matching albums in playlist.")
                    continue
                
                for idx, (album_id, name, release_date) in enumerate(albums, start=1):
                    print(f"{idx}. {name} - {release_date}")
                print(f"{len(albums) + 1}. Cancel")
                
                album_choice = int(input("Please enter the corresponding number of the album you would like to remove: ")) - 1
                if album_choice == len(albums):
                    continue

                selected_album_id = albums[album_choice][0]
                
                # Delete all songs from the selected album in the playlist
                self.cursor.execute(f"""
                    DELETE FROM playlist_song 
                    WHERE playlist_id = {selected_playlist_id} 
                    AND song_id IN (SELECT song_id FROM song_album WHERE album_id = {selected_album_id})
                """)
                self.cursor.connection.commit()
                print(f"Album '{albums[album_choice][1]}' removed from your playlist.")

            elif type == "2":
                self.cursor.execute(f"SELECT song.song_id, song.title FROM playlist_song as ps JOIN song ON ps.song_id = song.song_id WHERE playlist_id = {playlists[playlist_choice][0]}")
                songs = self.cursor.fetchall()

                if not songs:
                    print("Playlist is empty.")
                    continue

                for idx, (song_id, title) in enumerate(songs, start=1):
                    print(f"{idx}. {title}")

                print(f"{len(songs) + 1}. Cancel")
                song_choice = int(input("Please enter the corresponding number of the song you would like to remove: ")) - 1

                if song_choice == len(songs):
                    continue

                selected_song_id = songs[song_choice][0]
                self.cursor.execute(f"DELETE FROM playlist_song WHERE playlist_id = {selected_playlist_id} AND song_id = {selected_song_id}")
                self.cursor.connection.commit()
                print(f"Song '{songs[song_choice][1]}' removed from your playlist.")

            else:
                print("Invalid input choice, try again?")
                continue

            return


    '''
        Renames a given playlist through user input after printing current user playlists
    '''
    def modify_playlist_name(self):
        playlists = self.get_playlists()
        while True:
            #list_playlists prints from 1, playlists is indexed from 0
            self.list_playlists(playlists)
            oldPlaylistIdx = int(input("Please enter the corresponding number of the playlist you wish to edit:")) - 1

            if (0 <= oldPlaylistIdx <= len(playlists)):
                newName = input("Please enter the new name for your playlist:")
                self.cursor.execute(f"UPDATE playlist SET playlist_name = '{newName}' WHERE playlist_id = '{playlists[oldPlaylistIdx][0]}'")
                self.cursor.connection.commit()
                print("Playlist name updated successfully.")

            else:
                print("Given playlist index is not an option, try again.")

            if self.userExitToMenu():
                break


    '''
        Users can listen to a song individually or it can play an entire collection. You must
        record every time a song is played by a user. You do not need to actually be able to
        play songs, simply mark them as played
    '''
    def play_song(self):
        print("Please enter the song name you would like to play:")
        search_term = input().strip().title()
    
        # Query to search for the song by title
        try:
            self.cursor.execute(f"""
            SELECT song.song_id, song.title, artist.stage_name
            FROM song
            JOIN song_album ON song.song_id = song_album.song_id
            JOIN album_artist ON song_album.album_id = album_artist.album_id
            JOIN artist ON album_artist.artist_id = artist.artist_id
            WHERE song.title LIKE '%{search_term}%'
            """)
            res = self.cursor.fetchall()
            
            if not res:
                print("No matching songs found.")
                return

            # Display the search results
            print(f"Songs matching '{search_term}':")
            for idx, (song_id, title, stage_name) in enumerate(res, start=1):
                print(f"{idx}. {title} by {stage_name}")

            # Let the user select the song to play
            while True:  
                print("Please select the song number to play:")
                user_input = input().strip()

                # Validate input to ensure it is a number
                if user_input.isdigit():  
                    song_choice = int(user_input) - 1  # Convert to zero-based index

                    if 0 <= song_choice < len(res):
                        break  
                    else:
                        print("Invalid selection. Please select a valid song number.")
                else:
                    print("Invalid input. Please enter a number.")
            
            # Get the selected song from the results
            selected_song = res[song_choice]
            print(f"Now playing: '{selected_song[1]}' by {selected_song[2]}")

            listen_date = datetime.now()
            user_id = self.user.user_id
            
            # Insert the song into the history to represent a listen
            self.cursor.execute(f"INSERT INTO history (user_id, song_id, listen_date)"
            f"VALUES ({user_id}, {selected_song[0]}, '{listen_date}')")
            self.cursor.connection.commit() 
            print(f"Song '{selected_song[1]}' added to your history with timestamp {listen_date}.")

            print("press enter to continue to main menu")
            input()
            
        except Exception as e:
            print(f"Error while trying to play song: {e}")
        
    '''
        Plays a given playlist, simulating playing every song in the playlist 
        and updating the user listen history
    '''
    def play_playlist(self):    
        playlists = self.get_playlists()
        while True:
            
            self.list_playlists(playlists)

            print("Please select the playlist number to play:")
            user_input = input().strip()

            if user_input.isdigit(): 
                playlist_choice = int(user_input) - 1  

                if 0 <= playlist_choice < len(playlists):
                    selected_playlist = playlists[playlist_choice]
                    print(f"Now playing playlist: '{selected_playlist[1]}'")
                    self.cursor.execute(f"""
                        SELECT song.song_id, song.title, song.length
                        FROM playlist_song
                        JOIN song ON playlist_song.song_id = song.song_id
                        WHERE playlist_song.playlist_id = {selected_playlist[0]}
                        ORDER BY playlist_song.tack_number ASC
                        """)
                    songs = self.cursor.fetchall()
                    
                    if not songs:
                        print(f"Playlist '{selected_playlist[1]}' has no songs.")
                        return
                    
                    # Initial timestamp 
                    listen_date = datetime.now()
                    user_id = self.user.user_id

                    for song_id, title, length in songs:
                        
                        minutes, seconds = map(int, length.split(":"))
                        song_duration = timedelta(minutes=minutes, seconds=seconds)

                        
                        print(f"Now playing: '{title}' (Duration: {length})")
                        
                        # Insert song into history 
                        self.cursor.execute(f"""INSERT INTO history (user_id, song_id, listen_date)
                                            VALUES ({user_id}, {song_id}, '{listen_date}')
                                            """)
                        self.cursor.connection.commit()

                        print(f"Recorded play of '{title}' in history at {listen_date}.")

                        # Add the song duration to the listen_date for the next song
                        listen_date += song_duration

                    print("Playlist finished playing.")
                    print("Press enter to return to the main menu.")
                    input()
                    break

                else:
                    print("Invalid selection. Please select a valid playlist number.")

            else:
                print("Invalid input. Please enter a number.")
            

    '''
    Users can follow another user. Users can search for new users to follow by email
    '''
    def follow_user(self):
        while True:
            following_username = input("Please enter the username of the user you would like to follow:")

            self.cursor.execute(f"SELECT user_id FROM nsuser WHERE username = '{following_username}'")
            result = self.cursor.fetchall()

            if result:
                following_user_id = result[0]

                self.cursor.execute(f"""
                INSERT INTO user_following (follower, following, follow_date) 
                VALUES ('{self.user.user_id}', '{following_user_id[0]}', '{date.today()}')
                """)
                self.cursor.connection.commit()
                print("User successfully followed.")
                break  

            else:
                print(f"No user found with the username '{following_username}'. Please try again.")
            

    '''
    The application must also allow an user to unfollow a another user
    '''
    # Get the user_id of the user to unfollow, see if there's a match in user_following, delete that entry
    def unfollow_user(self):
        while True:
            unfollow_username = input("Please enter the username of the user you would like to unfollow:")

            self.cursor.execute(f"SELECT user_id FROM nsuser WHERE username = '{unfollow_username}'")
            result = self.cursor.fetchall()

            if result:
                unfollow_user_id = result[0]

                self.cursor.execute(f"""
                DELETE FROM user_following 
                WHERE follower = '{self.user.user_id}' AND following = '{unfollow_user_id[0]}'
                """)
                self.cursor.connection.commit()
                print("User successfully unfollowed.")
                break 

            else:
                print(f"No user found with the username '{unfollow_username}'. Please try again.")

    '''
    The user creates an account and that is placed into the database
    '''
    def create_account(self, email, password, username, first_name, last_name, dob):
        salt = ''.join(choices(string.ascii_letters + string.digits, k=6))
        hashPass = self.encrypt_pass(password, salt)
        self.cursor.execute(f"""INSERT INTO nsuser (user_id, username, password, first_name, last_name, 
                            email, last_access_date, creation_date, date_of_birth, salt) VALUES 
                            ((SELECT COUNT(*) FROM nsuser) + 1, 
                            '{username}', '{hashPass}', '{first_name}', '{last_name}', '{email}',
                            '{date.today()}', '{date.today()}', '{dob}', '{salt}')
                            """)
        self.cursor.connection.commit() 
        return True


    '''
    Users will be able to create new accounts and access via login. The system must record
    the date and time an account is created. It must also stored the date and time an user
    access into the application
    '''
    def login(self, username, password):
        self.cursor.execute(f"SELECT salt FROM nsuser WHERE username = '{username}'")
        raw_salt = self.cursor.fetchall()
        user_salt = raw_salt[0][0] if raw_salt else None
        if not user_salt:
            print("Invalid username or password. Please try again.")
            return False
        
        self.cursor.execute(f"SELECT * FROM nsuser WHERE username = '{username}' AND password = '{self.encrypt_pass(password, user_salt)}'")
        res = self.cursor.fetchall()
        user_data = res[0] if res else None

        if not user_data:
            print("Invalid username or password. Please try again.")
            return False
        
        user = User(*user_data)
        user.last_access_date = date.today()
        self.cursor.execute(f"UPDATE nsuser SET last_access_date = '{user.last_access_date}' WHERE user_id = '{user.user_id}'")
        self.cursor.connection.commit()
        self.user = user
        return True

    """
    • The application provides an user profile functionality that displays the 
        following information:
    The number of collections the user has
    The number of users followed by this user
    The number of users this user is following
    Their top 10 artists (by most plays, additions to collections, or combination)
    """
    def user_profile(self):
        print(f"\nUser Profile for {self.user.username}")

        self.cursor.execute(f"""
            SELECT 
                COUNT(DISTINCT uf.following),
                COUNT(DISTINCT uf.follower),
                COUNT(DISTINCT pl.playlist_id)
            FROM user_following AS uf
            LEFT JOIN playlist AS pl ON uf.follower = pl.user_id 
            WHERE uf.follower = '{self.user.user_id}'
        """)
        counts = self.cursor.fetchall()[0]

        print(f"Following: {counts[0]}, Followed by: {counts[1]}")
        print(f"Number of playlists: {counts[2]}")
        print("Top 10 artists:")
        self.cursor.execute(f"""
            SELECT artist.stage_name, COUNT(history.song_id) as plays
            FROM history
            JOIN song ON history.song_id = song.song_id
            JOIN song_artist ON song.song_id = song_artist.song_id
            JOIN artist ON song_artist.artist_id = artist.artist_id
            WHERE history.user_id = '{self.user.user_id}'
            GROUP BY artist.stage_name
            ORDER BY plays DESC
            LIMIT 10
        """)
        top_artists = self.cursor.fetchall()

        if not top_artists:
            print("No artists found.")
            return
        
        print(f"{'Artist':<30} {'Plays':<15}")
        for idx, (artist, plays) in enumerate(top_artists, start=1):
            print(f"{idx}. {artist:<30} {plays:<15}")

        input("Press enter to return to the main menu.\n")

    """
    • The application must provide a song recommendation system with the 
    following options:
    The top 50 most popular songs in the last 30 days (rolling)
    The top 50 most popular songs among my followerss
    The top 5 most popular genres of the month (calendar month)
    For you: Recommend songs to listen to based on your play history (e.g. genre,
    artist) and the play history of similar users
    """
    def song_recommendations(self):
        while 'm':
            choice = input("""
                        1. Top 50 most popular songs in the last 30 days
                        2. Top 50 most popular songs among my followers
                        3. Top 5 most popular genres of the month
                        4. For you: Recommend songs to listen to based on your play history\n
                        5. Return to main menu
                        Enter your choice: 
                        """)
            match choice:
                case '1':
                    self.top_songs_last_30_days()
                case '2':
                    self.top_songs_followers()
                case '3':
                    self.top_genres_month()
                case '4':
                    self.recommend_songs()
                case '5':
                    return
                case _:
                    print("Invalid choice. Please try again.")
    
    def top_songs_last_30_days(self):
        self.cursor.execute(f"""
            SELECT song.title, artist.stage_name, COUNT(history.song_id) as plays
            FROM history
            JOIN song ON history.song_id = song.song_id
            JOIN song_artist ON song.song_id = song_artist.song_id
            JOIN artist ON song_artist.artist_id = artist.artist_id
            WHERE history.listen_date > (NOW() - INTERVAL '30 days')
            GROUP BY song.title, artist.stage_name
            ORDER BY plays DESC
            LIMIT 50
        """)
        top_songs = self.cursor.fetchall()

        if not top_songs:
            print("No songs found.")
            return
        
        print(f"{'Song':<30} {'Artist':<25} {'Plays':<15}")

        for idx, (title, artist, plays) in enumerate(top_songs, start=1):
            print(f"{idx}. {title:<30} {artist:<25} {plays:<15}")

        input("Press enter to continue.")

    def top_songs_followers(self):
        self.cursor.execute(f"""
            SELECT song.title, artist.stage_name, COUNT(history.song_id) as plays
            FROM history
            JOIN song ON history.song_id = song.song_id
            JOIN song_artist ON song.song_id = song_artist.song_id
            JOIN artist ON song_artist.artist_id = artist.artist_id
            JOIN user_following AS uf ON history.user_id = uf.following
            WHERE uf.follower = '{self.user.user_id}'
            GROUP BY song.title, artist.stage_name
            ORDER BY plays DESC
            LIMIT 50
        """)
        top_songs = self.cursor.fetchall()

        if not top_songs:
            print("No songs found.")
            return
        print(f"{'Song':<30} {'Artist':<25} {'Plays':<15}")

        for idx, (title, artist, plays) in enumerate(top_songs, start=1):
            print(f"{idx}. {title:<30} {artist:<25} {plays:<15}")

        input("Press enter to continue.")

    def top_genres_month(self):
        self.cursor.execute(f"""
            SELECT genre.name, COUNT(history.song_id) as plays
            FROM history
            JOIN song ON history.song_id = song.song_id
            JOIN song_genre ON song.song_id = song_genre.song_id
            JOIN genre ON song_genre.genre_id = genre.genre_id
            WHERE EXTRACT(MONTH FROM history.listen_date) = EXTRACT(MONTH FROM NOW())
            GROUP BY genre.name
            ORDER BY plays DESC
            LIMIT 5
        """)
        top_genres = self.cursor.fetchall()
        
        if not top_genres:
            print("No genres found.")
            return
        
        print(f"{'Genre':<30} {'Plays':<15}")
        for idx, (genre, plays) in enumerate(top_genres, start=1):
            print(f"{idx}. {genre:<30} {plays:<15}")

        input("Press enter to continue.")

    """
        For you: Recommend songs to listen to based on your play history (e.g. genre,
        artist) and the play history of similar users
    """
    def recommend_songs(self):
        self.cursor.execute(f"""
            SELECT song.title, artist.stage_name FROM song
            JOIN song_artist ON song.song_id = song_artist.song_id
            JOIN artist ON song_artist.artist_id = artist.artist_id
            JOIN song_genre ON song.song_id = song_genre.song_id
            JOIN genre ON song_genre.genre_id = genre.genre_id
            WHERE (genre.genre_id IN (SELECT genre_id FROM song_genre WHERE song_id In (SELECT song_id FROM history WHERE user_id = '{self.user.user_id}'))
            OR artist.artist_id IN (SELECT artist_id FROM song_artist WHERE song_id In (SELECT song_id FROM history WHERE user_id = '{self.user.user_id}')))
            AND song.song_id IN (SELECT song_id FROM history WHERE user_id = '{self.user.user_id}')
            GROUP BY song.title, artist.stage_name
            ORDER BY RANDOM() DESC
            LIMIT 25
        """)
        top_songs = self.cursor.fetchall()
        if not top_songs:
            print("No songs found.")
            return
        print(f"{'Song':<30} {'Artist':<25} {'Plays':<15}")
        for idx, (title, artist, plays) in enumerate(top_songs, start=1):
            print(f"{idx}. {title:<30} {artist:<25} {plays:<15}")
        input("Press enter to continue.")

    def logout(self):
        print("Goodbye!")
        return self.main_menu()

    def user_menu(self):
        while True:
            print(f"\t===Welcome {self.user.username}===")
            try:
                print("1. Create Playlist")
                print("2. List Playlists")
                print("3. Search Songs")
                print("4. Add to Playlist")
                print("5. Remove from Playlist")
                print("6. Modify Playlist Name")
                print("7. Play Song")
                print("8. Play Playlist")
                print("9. Follow User")
                print("10. Unfollow User")
                print("11. Song Recommendations")
                print("12. User Profile")
                print("13. Logout")
                choice = input("Enter your choice: ")

                match choice:
                    case '1':
                        self.create_playlist()
                    case '2':
                        self.list_playlists(self.get_playlists())
                        input("Press enter to continue.")
                    case '3':
                        self.search_songs()
                    case '4':
                        self.add_to_playlist()
                    case '5':
                        self.remove_from_playlist()
                    case '6':
                        self.modify_playlist_name()
                    case '7':
                        self.play_song()
                    case '8':
                        self.play_playlist()
                    case '9':
                        self.follow_user()
                    case '10':
                        self.unfollow_user()
                    case '11':
                        self.song_recommendations()
                    case '12':
                        self.user_profile()
                    case '13':
                        self.logout()
                    case _:
                        print("Invalid choice. Please try again.")
            except Exception as e:
                print(e)


    def main_menu(self):
        while True:
            try:
                print("\t===!Spotify===")
                print("1. Create Account")
                print("2. Login")
                print("3. Exit")
                choice = input("Enter your choice: ")

                match choice:
                    case '1':
                        email = input("Enter email: ")
                        password = input("Enter password: ")
                        username = input("Enter username: ")
                        first_name = input("Enter your first name: ")
                        last_name = input("Enter your last name: ")
                        dob = input("Enter your date of birth: ")
                        account = self.create_account(email, password, username, first_name, last_name, dob)
                        if account:
                            print("Account created successfully.")
                        else:
                            print("Account creation failed.")
                    case '2':
                        username = input("Enter username: ")
                        password = input("Enter password: ")
                        if(self.login(username, password)):
                            self.user_menu()
                    case '3':
                        print("Goodbye!")
                        quit()
                    case _:
                        print("Invalid choice. Please try again.")
            except Exception as e:
                print(e)