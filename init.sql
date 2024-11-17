-- init.sql
-- Grant the necessary permissions to the airflow user on the public schema
GRANT CREATE, USAGE ON SCHEMA public TO airflow;
-- Grant insert privileges on all tables in the public schema
GRANT INSERT ON ALL TABLES IN SCHEMA public TO airflow;

-- init.sql for initializing Postgres database with seeclickfix_source table
CREATE TABLE IF NOT EXISTS seeclickfix_source (
    id SERIAL PRIMARY KEY,
    obj JSONB NOT NULL,  -- Store JSON objects
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP  -- Automatically set current timestamp when a row is created
);

-- Optionally, you can add an index to speed up searches on the `updated_at` column
CREATE INDEX IF NOT EXISTS idx_seeclickfix_source_updated_at ON seeclickfix_source(updated_at);
