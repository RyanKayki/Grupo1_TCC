CREATE TABLE IF NOT EXISTS chamados (
    id_chamado INTEGER PRIMARY KEY,
    titulo TEXT NOT NULL,
    descricao TEXT NOT NULL,
    sala TEXT NOT NULL,
    status TEXT NOT NULL,
    prioridade TEXT NOT NULL,
    data_abertura DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_conclusao DATETIME,
    img_chamado TEXT
);
