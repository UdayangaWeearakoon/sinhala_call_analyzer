CREATE TABLE transcripts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    content_hash CHAR(64) NOT NULL,
    status ENUM('pending','processing','completed','failed','dead_letter') NOT NULL DEFAULT 'pending',
    category VARCHAR(100),
    confidence DECIMAL(5,2),
    retry_count INT DEFAULT 0,
    last_error TEXT,
    prompt_tokens INT,
    completion_tokens INT,
    claimed_by VARCHAR(100),
    claimed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_hash (content_hash),
    INDEX idx_status (status)
);


