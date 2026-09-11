-- Runs once on first container start (docker-entrypoint-initdb.d), as superuser
-- against POSTGRES_DB=cpoai.

-- pgvector (I05) on the application database.
CREATE EXTENSION IF NOT EXISTS vector;

-- Separate databases for Temporal dev (I04). auto-setup provisions the schema.
CREATE DATABASE temporal;
CREATE DATABASE temporal_visibility;
