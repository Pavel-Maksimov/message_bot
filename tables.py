TABLES = [
    (
        'CREATE TABLE users ('
        '    id BIGINT NOT NULL PRIMARY KEY,'
        '    first_addressing DATETIME NOT NULL,'
        '    last_message_id BIGINT UNSIGNED NULL'
        ');'
    ),
    (
        'CREATE TABLE messages ('
        '    id BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,'
        '    date DATETIME NOT NULL,'
        '    text TEXT NOT NULL,'
        '    user_id BIGINT NOT NULL,'
	    '    FOREIGN KEY (user_id)'
        '    REFERENCES users(id)'
        '    ON DELETE CASCADE'
        ');'
    ),
    (
        'ALTER TABLE users '
        'ADD FOREIGN KEY (last_message_id) REFERENCES messages(id)'
        'ON DELETE SET NULL;'
    ),
    (
        'CREATE TABLE tags ('
        '    id INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,'
        '    name VARCHAR(50) NOT NULL,'
        '    definition TEXT NOT NULL'
        ');'
    ),
    (
        'CREATE TABLE messages_tags ('
        '    message_id BIGINT UNSIGNED NOT NULL,'
        '    tag_id INT UNSIGNED NOT NULL,'
        '    FOREIGN KEY (message_id)'
                'REFERENCES messages(id)'
                'ON DELETE CASCADE,'
        '    FOREIGN KEY (tag_id)'
                'REFERENCES tags(id)'
                'ON DELETE CASCADE,' 
        '    UNIQUE KEY message_tag (message_id, tag_id)'
        ');'
    )
]