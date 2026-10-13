CREATE TABLE IF NOT EXISTS chat_sessions (
 session_id TEXT PRIMARY KEY, user_id TEXT, ip_address TEXT, created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS messages (
 id BIGSERIAL PRIMARY KEY, session_id TEXT NOT NULL REFERENCES chat_sessions(session_id),
 role TEXT NOT NULL CHECK(role IN ('user','bot')), content TEXT NOT NULL, sources JSONB,
 confidence DOUBLE PRECISION, created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS feedback (
 id BIGSERIAL PRIMARY KEY, message_id BIGINT NOT NULL REFERENCES messages(id),
 rating INTEGER NOT NULL CHECK(rating IN (1,-1)), comment TEXT, created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at);
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS campus_locations (
 id BIGSERIAL PRIMARY KEY,
 external_id VARCHAR(150) UNIQUE NOT NULL,
 location_name VARCHAR(150) NOT NULL,
 category VARCHAR(50),
 description TEXT,
 address TEXT,
 aliases JSONB NOT NULL DEFAULT '[]'::jsonb,
 source_url TEXT,
 verified BOOLEAN NOT NULL DEFAULT FALSE,
 zoom SMALLINT NOT NULL DEFAULT 16 CHECK (zoom BETWEEN 1 AND 20),
 geom GEOMETRY(Point, 4326) NOT NULL,
 updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_campus_locations_geom ON campus_locations USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_campus_locations_name ON campus_locations (LOWER(location_name));
CREATE TABLE IF NOT EXISTS users (
 id BIGSERIAL PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
 role TEXT NOT NULL CHECK(role IN ('student','faculty','hostel_manager','admin')),
 is_active BOOLEAN NOT NULL DEFAULT TRUE, failed_attempts INTEGER NOT NULL DEFAULT 0,
 locked_until TIMESTAMPTZ, created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS revoked_tokens (jti TEXT PRIMARY KEY, expires_at TIMESTAMPTZ NOT NULL);
CREATE TABLE IF NOT EXISTS security_audit_log (
 id BIGSERIAL PRIMARY KEY, actor_user_id BIGINT, action TEXT NOT NULL,
 target TEXT, details JSONB, created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS learned_question_phrases (
 normalized_question TEXT PRIMARY KEY,
 fact_id TEXT NOT NULL,
 usage_count INTEGER NOT NULL DEFAULT 1,
 created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
 last_seen_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
