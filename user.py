class User:

    def __init__(self, user_id, username, password, first_name, last_name, email, last_access_date, creation_date, date_of_birth, salt):
        self.user_id = user_id
        self.username = username
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.last_access_date = last_access_date
        self.creation_date = creation_date
        self.date_of_birth = date_of_birth
        self.salt = salt

    def __str__(self):
        return f"User: {self.email}"