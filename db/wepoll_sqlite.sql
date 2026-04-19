CREATE TABLE IF NOT EXISTS wepoll_source_files (
    source_file TEXT PRIMARY KEY,
    sha256 TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    date_min TEXT,
    date_max TEXT,
    ingested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS wepoll_raw_posts (
    post_id TEXT PRIMARY KEY,
    parent_post_id TEXT,
    depth INTEGER,
    reply_code TEXT,
    board_name TEXT,
    content_kind TEXT,
    category TEXT,
    title TEXT,
    body TEXT,
    created_at TEXT,
    updated_at TEXT,
    author_id_masked TEXT,
    views INTEGER,
    comments_count INTEGER,
    likes_count INTEGER,
    has_poll INTEGER,
    source_url TEXT,
    source_file TEXT NOT NULL REFERENCES wepoll_source_files(source_file) ON DELETE RESTRICT,
    ingested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_wepoll_raw_posts_created_at
    ON wepoll_raw_posts (created_at);

CREATE INDEX IF NOT EXISTS idx_wepoll_raw_posts_source_file
    ON wepoll_raw_posts (source_file);

CREATE TABLE IF NOT EXISTS wepoll_daily_features (
    date TEXT PRIMARY KEY,
    anchor_label TEXT,
    anchor_bull INTEGER,
    anchor_bear INTEGER,
    post_count INTEGER,
    fear_weighted_mean REAL,
    greed_weighted_mean REAL,
    uncertainty_weighted_mean REAL,
    fear_dominant_share REAL,
    greed_dominant_share REAL,
    mixed_share REAL,
    uncertain_share REAL,
    neutral_share REAL,
    fear_high_share REAL,
    greed_high_share REAL,
    active_emotion_share REAL,
    dominant_diff REAL,
    dominant_spread REAL,
    high_share_diff REAL,
    high_share_spread REAL,
    avg_engagement_weight REAL,
    noise_ratio REAL,
    short_ratio REAL,
    question_ratio REAL,
    meme_ratio REAL,
    news_ratio REAL,
    stance_calibrated_raw REAL,
    stance_calibrated_0_100 REAL,
    stance_reliability REAL,
    stance_calibrated_shrunk_0_100 REAL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS wepoll_daily_indices (
    date TEXT PRIMARY KEY,
    stance_internal_0_100 REAL,
    participation_internal_0_100 REAL,
    psychology_index_0_100 REAL,
    participation_index_0_100 REAL,
    state_label_ko TEXT,
    stance_delta REAL,
    participation_delta REAL,
    prev_state_label_ko TEXT,
    anchor_label TEXT,
    post_count INTEGER,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
