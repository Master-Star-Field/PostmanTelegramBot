CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE,
    username TEXT,
    full_name TEXT,
    total_letters INTEGER DEFAULT 0,
    category_a_count INTEGER DEFAULT 0,
    category_b_count INTEGER DEFAULT 0,
    category_c_count INTEGER DEFAULT 0,
    role_in_chat TEXT DEFAULT '📬 Почемар',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS meeting_time_ranges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE,
    start_time TIME,
    end_time TIME,
    window_duration_min INTEGER DEFAULT 10,
    max_meetings_per_window INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS meeting_windows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    range_id INTEGER,
    start_time TIME,
    end_time TIME,
    current_bookings INTEGER DEFAULT 0,
    is_available BOOLEAN DEFAULT 1,
    assigned_user_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (range_id) REFERENCES meeting_time_ranges (id),
    FOREIGN KEY (assigned_user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    address TEXT,
    is_custom BOOLEAN DEFAULT 0,
    created_by_admin BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    meeting_window_id INTEGER,
    custom_location TEXT,
    location_id INTEGER,
    is_anonymous BOOLEAN,
    delivery_delay_days INTEGER,
    target_delivery_date DATE,
    status TEXT DEFAULT 'pending',
    card_type_1_count INTEGER DEFAULT 0,
    card_type_2_count INTEGER DEFAULT 0,
    card_type_3_count INTEGER DEFAULT 0,
    card_type_1_desc TEXT,
    card_type_2_desc TEXT,
    card_type_3_desc TEXT,
    recipient_name TEXT,
    delivery_address TEXT,
    client_name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    cancelled_reason TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (meeting_window_id) REFERENCES meeting_windows (id),
    FOREIGN KEY (location_id) REFERENCES locations (id)
);

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    rating INTEGER,
    comment TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders (id)
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    message TEXT,
    is_read BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);