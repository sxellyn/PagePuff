USE pagepuff;

-- Inserir usuário de teste com senha '123456' (hasheada com bcrypt)
INSERT INTO users (username, email, password) 
VALUES ('teste', 'teste@pagepuff.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.s5uO8i');

-- Ou usar o usuário 'alice' com senha '123456'
-- UPDATE users SET password = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.s5uO8i' WHERE username = 'alice';
