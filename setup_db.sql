-- Run this once against your PostgreSQL instance to create the database and user.
-- Usage: psql -U postgres -f setup_db.sql

-- Create user
CREATE USER trackweave_user WITH PASSWORD 'trackweave_pass';

-- Create database
CREATE DATABASE trackweave_db OWNER trackweave_user;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE trackweave_db TO trackweave_user;

-- Tables are created automatically by SQLAlchemy on first startup.
-- If you prefer to use Alembic migrations instead, run:
--   alembic init alembic
--   alembic revision --autogenerate -m "initial"
--   alembic upgrade head
