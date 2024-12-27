CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
);
INSERT INTO users (username, password) VALUES ('nikhil', 'password123');

SELECT * FROM USERS;

-- In terminal
-- sqlite3 database.db