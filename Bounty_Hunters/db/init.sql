-- Schema and seed data for the Space Bounty Hunters API.
-- Docker runs this automatically on the first start (empty volume).
-- Manual import: psql -U bounty_user -d bounty_db -f db/init.sql

CREATE TABLE IF NOT EXISTS wanted_criminals (
    id             SERIAL PRIMARY KEY,
    name           VARCHAR(100),                       -- real name, NULL if unknown
    nickname       VARCHAR(100) NOT NULL,
    reward         INTEGER      NOT NULL CHECK (reward >= 0),
    latitude       DOUBLE PRECISION CHECK (latitude BETWEEN -90 AND 90),
    longitude      DOUBLE PRECISION CHECK (longitude BETWEEN -180 AND 180),
    location_note  TEXT,                               -- used when exact coordinates are unknown
    difficulty     INTEGER      NOT NULL CHECK (difficulty BETWEEN 1 AND 10),
    armed          BOOLEAN      NOT NULL DEFAULT FALSE,
    has_crew       BOOLEAN      NOT NULL DEFAULT FALSE,
    escape_master  BOOLEAN      NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS hunt_logs (
    id           SERIAL PRIMARY KEY,
    criminal_id  INTEGER     NOT NULL REFERENCES wanted_criminals(id) ON DELETE CASCADE,
    success      BOOLEAN     NOT NULL,
    notes        TEXT        NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_hunt_logs_criminal_id ON hunt_logs (criminal_id);

INSERT INTO wanted_criminals (name, nickname, reward, latitude, longitude, location_note, difficulty, armed, has_crew, escape_master) VALUES
    ('Drax Morrow',  'The Comet',     15000, 43.2389,  76.8897, NULL,                                      7, TRUE,  TRUE,  FALSE),
    (NULL,           'Ghost of Orion', 50000, NULL,     NULL,    'Last seen near the Orion Nebula trade lanes', 10, TRUE,  FALSE, TRUE),
    ('Lira Voss',    'Silver Fang',    8000,  51.1694,  71.4491, NULL,                                      5, FALSE, TRUE,  TRUE),
    ('Kaal Brenn',   'Iron Jaw',       3000,  -33.8688, 151.2093, NULL,                                     3, TRUE,  FALSE, FALSE),
    (NULL,           'Nebula Rat',     1200,  NULL,     NULL,    'Hiding in the asteroid belt of Kepler-22', 2, FALSE, FALSE, TRUE),
    ('Zed Okonkwo',  'Black Hole',     27000, 35.6762,  139.6503, NULL,                                     8, TRUE,  TRUE,  TRUE);

INSERT INTO hunt_logs (criminal_id, success, notes, created_at) VALUES
    (1, FALSE, 'Target escaped through an asteroid field.',               NOW() - INTERVAL '20 days'),
    (1, FALSE, 'Ambushed by his crew at the space station dock.',         NOW() - INTERVAL '15 days'),
    (2, FALSE, 'Tracking beacon went silent near the nebula.',            NOW() - INTERVAL '14 days'),
    (3, FALSE, 'She vanished in a smoke cloud at the cantina.',           NOW() - INTERVAL '12 days'),
    (4, TRUE,  'Captured after a short fight on a mining planet.',        NOW() - INTERVAL '10 days'),
    (5, FALSE, 'Lost the signal inside the asteroid belt.',               NOW() - INTERVAL '8 days'),
    (5, TRUE,  'Caught while refueling at Kepler-22 outpost.',            NOW() - INTERVAL '6 days'),
    (6, FALSE, 'His ship jumped to hyperspace before boarding.',          NOW() - INTERVAL '5 days'),
    (3, TRUE,  'Finally cornered on the frozen moon of Glacia-9.',          NOW() - INTERVAL '3 days'),
    (2, FALSE, 'Intel was fake, the Ghost was never there.',              NOW() - INTERVAL '1 day');
