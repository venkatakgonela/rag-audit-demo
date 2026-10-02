CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS demo_users (
    subject text PRIMARY KEY,
    role text NOT NULL CHECK (role IN ('customer','broker','underwriter','admin')),
    teams text[] NOT NULL,
    CHECK (role NOT IN ('customer','broker') OR cardinality(teams) = 0)
);
CREATE TABLE IF NOT EXISTS demo_brokers (
    broker text REFERENCES demo_users(subject),
    customer text REFERENCES demo_users(subject),
    PRIMARY KEY (broker, customer)
);
CREATE TABLE IF NOT EXISTS demo_documents (
    id text PRIMARY KEY,
    source text NOT NULL,
    kind text NOT NULL,
    tier text NOT NULL CHECK (tier IN ('public','broker','internal','restricted')),
    team text NOT NULL CHECK (team <> ''),
    owner text REFERENCES demo_users(subject),
    CHECK ((kind = 'claim' AND tier = 'restricted' AND owner IS NOT NULL)
        OR (kind <> 'claim' AND owner IS NULL)),
    UNIQUE (id,tier,team)
);
CREATE TABLE IF NOT EXISTS demo_chunks (
    id text PRIMARY KEY,
    document_id text NOT NULL REFERENCES demo_documents(id) ON DELETE CASCADE,
    text text NOT NULL,
    section text NOT NULL,
    ordinal integer NOT NULL,
    start_offset integer NOT NULL CHECK (start_offset >= 0),
    end_offset integer NOT NULL CHECK (end_offset > start_offset),
    tier text NOT NULL,
    team text NOT NULL,
    owner text REFERENCES demo_users(subject),
    embedding vector(384) NOT NULL,
    search tsvector NOT NULL,
    corpus_version text NOT NULL,
    model_identity text NOT NULL,
    FOREIGN KEY (document_id,tier,team) REFERENCES demo_documents(id,tier,team),
    UNIQUE (document_id,ordinal)
);
CREATE TABLE IF NOT EXISTS demo_configuration (
    singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
    model_identity text NOT NULL,
    corpus_version text NOT NULL
);
