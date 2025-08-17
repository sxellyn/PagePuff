CREATE DATABASE IF NOT EXISTS pagepuff;
USE pagepuff;

CREATE TABLE mangas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    rating DECIMAL(3,2),
    year INT,
    tags TEXT,
    cover VARCHAR(512)
);