// Initialize MongoDB with admin user
db.createUser({
  user: "admin",
  pwd: "admin123",
  roles: [
    { role: "readWrite", db: "telegram_target_bot" },
    { role: "dbAdmin", db: "telegram_target_bot" }
  ]
});

// Create database
db = db.getSiblingDB('telegram_target_bot');

// Create indexes
db.targets.createIndex({ user_id: 1, date: 1 }, { unique: true });
db.users.createIndex({ user_id: 1 }, { unique: true });
db.group_settings.createIndex({ group_id: 1 }, { unique: true });

print("✅ MongoDB initialized successfully!");
