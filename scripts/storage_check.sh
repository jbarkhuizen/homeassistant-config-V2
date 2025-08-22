#!/bin/bash

# Home Assistant Storage Cleanup Script
# Run this script to identify large files and clean up storage

echo "=== Home Assistant Storage Analysis ==="
echo "Current date: $(date)"
echo

# Get the Home Assistant config directory
# Adjust this path if your HA is installed differently
HA_CONFIG="/config"  # For HA OS/Supervised
# HA_CONFIG="/home/homeassistant/.homeassistant"  # For HA Core

if [ ! -d "$HA_CONFIG" ]; then
    echo "Home Assistant config directory not found at $HA_CONFIG"
    echo "Please adjust the HA_CONFIG variable in this script"
    exit 1
fi

cd "$HA_CONFIG" || exit 1

echo "Home Assistant directory: $HA_CONFIG"
echo

# 1. Overall disk usage
echo "=== OVERALL DISK USAGE ==="
df -h .
echo

# 2. Directory sizes
echo "=== DIRECTORY SIZES (Top 20) ==="
du -sh * .* 2>/dev/null | sort -hr | head -20
echo

# 3. Find largest files
echo "=== LARGEST FILES (Top 30) ==="
find . -type f -exec du -h {} + 2>/dev/null | sort -hr | head -30
echo

# 4. Database files specifically
echo "=== DATABASE FILES ==="
echo "Home Assistant database files:"
ls -lh *.db* 2>/dev/null || echo "No .db files found in root"
echo
find . -name "*.db*" -type f -exec ls -lh {} \; 2>/dev/null
echo

# 5. Log files
echo "=== LOG FILES ==="
echo "Current log files:"
find . -name "*.log*" -type f -exec ls -lh {} \; 2>/dev/null
echo

# 6. InfluxDB data (if exists)
echo "=== INFLUXDB DATA ==="
if [ -d "influxdb" ]; then
    echo "InfluxDB directory size:"
    du -sh influxdb/
    echo "InfluxDB subdirectories:"
    du -sh influxdb/*/ 2>/dev/null
else
    echo "No local InfluxDB directory found"
fi
echo

# 7. Backup files
echo "=== BACKUP FILES ==="
echo "Backup directory:"
if [ -d "backup" ] || [ -d "backups" ]; then
    du -sh backup* 2>/dev/null
    ls -lh backup*/*.tar* 2>/dev/null | head -10
else
    echo "No backup directory found"
fi
echo

# 8. Media files
echo "=== MEDIA FILES ==="
if [ -d "www" ]; then
    echo "www directory size:"
    du -sh www/
    find www/ -name "*.mp3" -o -name "*.mp4" -o -name "*.wav" -o -name "*.jpg" -o -name "*.png" 2>/dev/null | head -10
fi
echo

# 9. Custom components cache
echo "=== CUSTOM COMPONENTS ==="
if [ -d "custom_components" ]; then
    echo "Custom components directory size:"
    du -sh custom_components/
    echo "Largest custom component directories:"
    du -sh custom_components/*/ 2>/dev/null | sort -hr | head -10
fi
echo

# 10. HACS cache
echo "=== HACS DATA ==="
if [ -d "custom_components/hacs" ]; then
    echo "HACS directory size:"
    du -sh custom_components/hacs/
fi
if [ -d "www/community" ]; then
    echo "HACS frontend components size:"
    du -sh www/community/
fi
echo

# 11. TTS cache
echo "=== TTS CACHE ==="
if [ -d "tts" ]; then
    echo "TTS cache size:"
    du -sh tts/
    echo "Number of TTS files:"
    find tts/ -name "*.mp3" 2>/dev/null | wc -l
fi
echo

# 12. Dependencies
echo "=== DEPENDENCIES ==="
if [ -d "deps" ]; then
    echo "Dependencies directory size:"
    du -sh deps/
fi
echo

# 13. Home Assistant specific storage files
echo "=== HOME ASSISTANT STORAGE ==="
if [ -d ".storage" ]; then
    echo ".storage directory size:"
    du -sh .storage/
    echo "Largest .storage files:"
    find .storage/ -type f -exec du -h {} \; 2>/dev/null | sort -hr | head -10
fi
echo

# 14. Recorder database analysis
echo "=== RECORDER DATABASE ANALYSIS ==="
if command -v sqlite3 >/dev/null 2>&1; then
    for db in home-assistant_v2.db *.db; do
        if [ -f "$db" ]; then
            echo "Database: $db"
            echo "  Size: $(du -h "$db" | cut -f1)"
            echo "  Tables with most records:"
            sqlite3 "$db" "SELECT name, COUNT(*) as count FROM sqlite_master m LEFT JOIN pragma_table_info(m.name) p GROUP BY m.name ORDER BY count DESC LIMIT 5;" 2>/dev/null
            echo "  States table record count:"
            sqlite3 "$db" "SELECT COUNT(*) FROM states;" 2>/dev/null
            echo "  Events table record count:"
            sqlite3 "$db" "SELECT COUNT(*) FROM events;" 2>/dev/null
            echo
        fi
    done
else
    echo "sqlite3 not available for database analysis"
fi

echo "=== CLEANUP RECOMMENDATIONS ==="
echo
echo "Based on the analysis above, consider the following cleanup actions:"
echo
echo "1. RECORDER DATABASE:"
echo "   - Your current purge_keep_days is set to 7 days"
echo "   - Consider reducing to 3-5 days if database is large"
echo "   - Run: 'recorder.purge' service manually"
echo
echo "2. LOG FILES:"
echo "   - Delete old *.log files"
echo "   - Command: find . -name '*.log.*' -mtime +7 -delete"
echo
echo "3. BACKUPS:"
echo "   - Keep only recent backups (last 5-10)"
echo "   - Move old backups to external storage"
echo
echo "4. TTS CACHE:"
echo "   - Clear TTS cache if large"
echo "   - Command: rm -rf tts/*"
echo
echo "5. INFLUXDB:"
echo "   - Check InfluxDB retention policies"
echo "   - Consider reducing data retention period"
echo
echo "6. MEDIA FILES:"
echo "   - Review www/ directory for large media files"
echo "   - Move large files to external storage"
echo

echo "=== IMMEDIATE CLEANUP COMMANDS ==="
echo "Run these commands carefully (backup first!):"
echo
echo "# Clean old log files (older than 7 days)"
echo "find $HA_CONFIG -name '*.log.*' -mtime +7 -delete"
echo
echo "# Clean TTS cache"
echo "rm -rf $HA_CONFIG/tts/*"
echo
echo "# Manual recorder purge (run in HA)"
echo "# Go to Developer Tools > Services > recorder.purge"
echo "# Set keep_days: 3 and repack: true"
echo
echo "# Clean old database WAL files"
echo "find $HA_CONFIG -name '*.db-wal' -mtime +1 -delete"
echo "find $HA_CONFIG -name '*.db-shm' -mtime +1 -delete"

echo
echo "=== SCRIPT COMPLETED ==="