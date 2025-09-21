#!/bin/bash
# SQLite Backup Script for Production

# Configuration
DB_PATH="./data/crm_production.db"
BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/crm_backup_$TIMESTAMP.db"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "🔄 Starting SQLite backup..."

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "❌ Database file not found: $DB_PATH"
    exit 1
fi

# Create backup using SQLite's built-in backup command
sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"

if [ $? -eq 0 ]; then
    echo "✅ Backup completed: $BACKUP_FILE"
    
    # Compress the backup
    gzip "$BACKUP_FILE"
    echo "📦 Backup compressed: $BACKUP_FILE.gz"
    
    # Remove backups older than 30 days
    find "$BACKUP_DIR" -name "crm_backup_*.gz" -mtime +30 -delete
    echo "🧹 Cleaned up old backups (>30 days)"
    
    # Show backup size
    BACKUP_SIZE=$(du -h "$BACKUP_FILE.gz" | cut -f1)
    echo "📊 Backup size: $BACKUP_SIZE"
else
    echo "❌ Backup failed!"
    exit 1
fi

echo "✅ Backup process completed successfully!"