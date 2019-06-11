from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

INIT_SQL = """
       /* accounts */
       CREATE TABLE IF NOT EXISTS accounts (
              id INTEGER PRIMARY KEY,
              name TEXT UNIQUE NOT NULL,
              bank_country TEXT,
              bank_code TEXT,
              bank_branch_id TEXT,
              owner,
              account_number TEXT,
              account_suffix TEXT,
              account_iban TEXT UNIQUE NOT NULL,
              login TEXT NOT NULL,
              pincode TEXT NOT NULL,
              url TEXT NOT NULL);

       /* transactions */
       CREATE TABLE IF NOT EXISTS transactions (
              id INTEGER PRIMARY KEY,
              account_id INTEGER,
              hash TEXT UNIQUE NOT NULL,
              r_country TEXT,
              r_bank_code TEXT,
              r_bank_branch_id TEXT,
              r_account_number TEXT,
              r_account_suffix TEXT,
              r_account_iban TEXT,
              r_name TEXT,
              r_bic TEXT,
              date INTEGER,
              valuta_date INTEGER,
              value FLOAT,
              value_currency TEXT,
              fees FLOAT,
              fees_currency TEXT,
              type_code TEXT,
              purpose TEXT,
              raw TEXT);

       /* account balances */
       CREATE TABLE IF NOT EXISTS balances (
              id INTEGER PRIMARY KEY,
              account_id INTEGER,
              hash TEXT UNIQUE NOT NULL,
              date INTEGER,
              value FLOAT,
              currency TEXT);

       /* additional transaction attributes */
       /* additional attributes for arbitrary records */
       CREATE TABLE IF NOT EXISTS attributes (
              id INTEGER NOT NULL,
              key TEXT NOT NULL,
              value_int INTEGER,
              value_real REAL,
              value_text TEXT,
              PRIMARY KEY (id, key));

       /* date computations */
       CREATE VIEW IF NOT EXISTS transaction_dates AS
              SELECT id AS transaction_id,
              date / 86400.0 + 2440587.5 AS julian_day,
              CAST(strftime('%Y', date / 86400.0 + 2440587.5) AS REAL) AS year,
              CAST(strftime('%m', date / 86400.0 + 2440587.5) AS REAL) AS month,
              CAST(strftime('%d', date / 86400.0 + 2440587.5) AS REAL) AS day
              FROM transactions;

       /* date computations */
       CREATE VIEW IF NOT EXISTS balance_dates AS
              SELECT id AS balance_id,
              date / 86400.0 + 2440587.5 AS julian_day,
              CAST(strftime('%Y', date / 86400.0 + 2440587.5) AS REAL) AS year,
              CAST(strftime('%m', date / 86400.0 + 2440587.5) AS REAL) AS month,
              CAST(strftime('%d', date / 86400.0 + 2440587.5) AS REAL) AS day
              FROM balances;

       /* full text search for transactions */
       CREATE VIRTUAL TABLE IF NOT EXISTS transactions_fts USING fts4(content='transactions', r_name, purpose);
       CREATE VIRTUAL TABLE IF NOT EXISTS transactions_fts_terms USING fts4aux(transactions_fts);
       CREATE VIRTUAL TABLE IF NOT EXISTS tokenizer USING fts3tokenize();
       CREATE VIEW IF NOT EXISTS transaction_text AS SELECT id AS transaction_id, r_name || ' ' || purpose as text FROM transactions;

       /* tags */
       CREATE TABLE IF NOT EXISTS tags (
              id INTEGER PRIMARY KEY,
              name TEXT UNIQUE NOT NULL,
              parent_id INTEGER REFERENCES tags);

       /* linkage between transactions and tags */
       CREATE TABLE IF NOT EXISTS transaction_tags (
              transaction_id INTEGER NOT NULL,
              tag_id INTEGER NOT NULL,
              share FLOAT, /* number [0,1] share of transaction value */
              description TEXT,
              PRIMARY KEY (transaction_id, tag_id));

       /* tokens per tag statistics */
       CREATE TABLE IF NOT EXISTS tag_tokens (
              tag_id INTEGER NOT NULL,
              token TEXT NOT NULL,
              p_count INTEGER NOT NULL,
              n_count INTEGER NOT NULL,
              PRIMARY KEY (tag_id, token));

       /* triggers to keep fts and transaction_tags up to date */
       CREATE TRIGGER IF NOT EXISTS transactions_before_update BEFORE UPDATE ON transactions BEGIN
              DELETE FROM transactions_fts WHERE rowid=old.id;
       END;
       CREATE TRIGGER IF NOT EXISTS transactions_before_delete BEFORE DELETE ON transactions BEGIN
              DELETE FROM transactions_fts WHERE rowid=old.id;
              DELETE FROM transaction_tags WHERE transaction_id = old.id;
       END;
              CREATE TRIGGER IF NOT EXISTS transactions_after_update AFTER UPDATE ON transactions BEGIN
              INSERT INTO transactions_fts(rowid, r_name, purpose) VALUES(new.id, new.r_name, new.purpose);
       END;
       CREATE TRIGGER IF NOT EXISTS transactions_after_insert AFTER INSERT ON transactions BEGIN
              INSERT INTO transactions_fts(rowid, r_name, purpose) VALUES(new.id, new.r_name, new.purpose);
       END;

       /* trigger to keep transaction tags in sync with tags */
       CREATE TRIGGER IF NOT EXISTS tag_after_delete AFTER DELETE ON tags BEGIN
              DELETE FROM transaction_tags WHERE tag_id = old.id;
              DELETE FROM tag_tokens WHERE tag_id = old.id;
       END;

       /* keep tag tokens in sync with transaction tags */
       CREATE TRIGGER IF NOT EXISTS transaction_tags_after_update AFTER UPDATE ON transaction_tags BEGIN
              DELETE FROM tag_tokens WHERE tag_id=new.tag_id;
              INSERT INTO tag_tokens
              SELECT tag_id, token, SUM(c) as p_count, 0 AS n_count
              FROM (
                     SELECT tag_id, token, transaction_id, COUNT(*) AS c
                     FROM tokenizer
                     JOIN transactions AS t ON input=(SELECT t.r_name || ' ' || t.purpose) AND LENGTH(token) > 1
                     JOIN transaction_tags ON t.id=transaction_id AND tag_id=new.tag_id
                     GROUP BY token, transaction_id
              )
              GROUP BY token;
       END;

       CREATE TRIGGER IF NOT EXISTS transaction_tags_after_insert AFTER INSERT ON transaction_tags BEGIN
              DELETE FROM tag_tokens WHERE tag_id=new.tag_id;
              INSERT INTO tag_tokens
              SELECT tag_id, token, SUM(c) as p_count, 0 AS n_count
              FROM (
                     SELECT tag_id, token, transaction_id, COUNT(*) AS c
                     FROM tokenizer
                     JOIN transactions AS t ON input=(SELECT t.r_name || ' ' || t.purpose) AND LENGTH(token) > 1
                     JOIN transaction_tags ON t.id=transaction_id AND tag_id=new.tag_id
                     GROUP BY token, transaction_id
              )
              GROUP BY token;
       END;

       CREATE TRIGGER IF NOT EXISTS transaction_tags_after_delete AFTER DELETE ON transaction_tags BEGIN
              DELETE FROM tag_tokens WHERE tag_id=old.tag_id;
              INSERT INTO tag_tokens
              SELECT tag_id, token, SUM(c) as p_count, 0 AS n_count
              FROM (
                     SELECT tag_id, token, transaction_id, COUNT(*) AS c
                     FROM tokenizer
                     JOIN transactions AS t ON input=(SELECT t.r_name || ' ' || t.purpose) AND LENGTH(token) > 1
                     JOIN transaction_tags ON t.id=transaction_id AND tag_id=old.tag_id
                     GROUP BY token, transaction_id
              )
              GROUP BY token;
       END;
"""
