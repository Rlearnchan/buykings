CREATE TABLE IF NOT EXISTS wepoll_source_files (
    source_file TEXT PRIMARY KEY,
    sha256 TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    date_min DATE,
    date_max DATE,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
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
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    author_id_masked TEXT,
    views INTEGER,
    comments_count INTEGER,
    likes_count INTEGER,
    has_poll BOOLEAN,
    source_url TEXT,
    source_file TEXT NOT NULL REFERENCES wepoll_source_files(source_file) ON DELETE RESTRICT,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_wepoll_raw_posts_created_at
    ON wepoll_raw_posts (created_at);

CREATE INDEX IF NOT EXISTS idx_wepoll_raw_posts_source_file
    ON wepoll_raw_posts (source_file);

CREATE TABLE IF NOT EXISTS wepoll_daily_features (
    date DATE PRIMARY KEY,
    anchor_label TEXT,
    anchor_bull BOOLEAN,
    anchor_bear BOOLEAN,
    post_count INTEGER,
    fear_weighted_mean DOUBLE PRECISION,
    greed_weighted_mean DOUBLE PRECISION,
    uncertainty_weighted_mean DOUBLE PRECISION,
    fear_dominant_share DOUBLE PRECISION,
    greed_dominant_share DOUBLE PRECISION,
    mixed_share DOUBLE PRECISION,
    uncertain_share DOUBLE PRECISION,
    neutral_share DOUBLE PRECISION,
    fear_high_share DOUBLE PRECISION,
    greed_high_share DOUBLE PRECISION,
    active_emotion_share DOUBLE PRECISION,
    dominant_diff DOUBLE PRECISION,
    dominant_spread DOUBLE PRECISION,
    high_share_diff DOUBLE PRECISION,
    high_share_spread DOUBLE PRECISION,
    avg_engagement_weight DOUBLE PRECISION,
    noise_ratio DOUBLE PRECISION,
    short_ratio DOUBLE PRECISION,
    question_ratio DOUBLE PRECISION,
    meme_ratio DOUBLE PRECISION,
    news_ratio DOUBLE PRECISION,
    stance_calibrated_raw DOUBLE PRECISION,
    stance_calibrated_0_100 DOUBLE PRECISION,
    stance_reliability DOUBLE PRECISION,
    stance_calibrated_shrunk_0_100 DOUBLE PRECISION,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS wepoll_daily_indices (
    date DATE PRIMARY KEY,
    stance_internal_0_100 DOUBLE PRECISION,
    participation_internal_0_100 DOUBLE PRECISION,
    psychology_index_0_100 DOUBLE PRECISION,
    participation_index_0_100 DOUBLE PRECISION,
    state_label_ko TEXT,
    stance_delta DOUBLE PRECISION,
    participation_delta DOUBLE PRECISION,
    prev_state_label_ko TEXT,
    anchor_label TEXT,
    post_count INTEGER,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
