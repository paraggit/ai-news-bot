# Database Migration Fix

## Error: "no such column: topics"

This error occurs when deploying the updated code over an existing database that doesn't have the new columns.

## ✅ Quick Fix (Option 1 - Recommended)

The database now **auto-migrates** when the application starts. Simply restart:

```bash
# Stop the current process
sudo systemctl stop ai-news-bot
# Or if running manually: Ctrl+C

# Start again
sudo systemctl start ai-news-bot
# Or: python -m ai_news_bot.main
```

The application will automatically:
1. Detect missing columns
2. Add them to the database
3. Continue normally

You should see these log messages:
```
Migrating database: adding 'topics' column
Migrating database: adding 'keywords' column
Migrating database: adding 'relevance_score' column
Database schema migration completed
```

## 🔧 Manual Fix (Option 2)

If you prefer to migrate manually before starting:

```bash
# Stop the application first
sudo systemctl stop ai-news-bot

# Run migration script
python migrate_database.py

# Output should show:
# ✅ Migration completed successfully!

# Start the application
sudo systemctl start ai-news-bot
```

## 🗄️ Alternative: Fresh Start (Option 3)

If you want to start fresh (loses existing data):

```bash
# Stop application
sudo systemctl stop ai-news-bot

# Backup old database (optional)
mv data/news_aggregator.db data/news_aggregator.db.backup

# Start application (will create new database)
sudo systemctl start ai-news-bot
```

## ✅ Verify Fix

Check that it's working:

```bash
# Check logs
sudo journalctl -u ai-news-bot -f

# Or check log file
tail -f logs/app.log

# Search database to verify
python -m ai_news_bot.cli_search stats
```

You should see:
- No more "no such column" errors
- Application starting successfully
- Database statistics showing properly

## 📊 What Was Added

The database now has these new columns:
- `topics` - AI topic categories
- `keywords` - Extracted keywords  
- `relevance_score` - AI relevance score (0-100)

Plus:
- Full-text search table (`articles_fts`)
- New indexes for performance
- Triggers for automatic FTS sync

## 🔍 Troubleshooting

### Still Getting the Error?

1. **Check database file permissions:**
   ```bash
   ls -la data/news_aggregator.db
   chmod 644 data/news_aggregator.db
   ```

2. **Verify database isn't locked:**
   ```bash
   lsof | grep news_aggregator.db
   ```

3. **Check SQLite version:**
   ```bash
   sqlite3 --version
   # Should be 3.9.0 or higher for FTS5
   ```

4. **Manual column check:**
   ```bash
   sqlite3 data/news_aggregator.db "PRAGMA table_info(articles);"
   # Should show topics, keywords, relevance_score
   ```

### Migration Script Fails?

Try running with Python directly:
```bash
python3 migrate_database.py data/news_aggregator.db
```

### Can't Stop Service?

```bash
# Force stop
sudo systemctl kill ai-news-bot

# Check status
sudo systemctl status ai-news-bot
```

## 📝 For Systemd Services

If running as a systemd service:

```bash
# Stop service
sudo systemctl stop ai-news-bot

# Optional: Run migration manually
python migrate_database.py

# Start service
sudo systemctl start ai-news-bot

# Check logs
sudo journalctl -u ai-news-bot -f --lines 50
```

Look for:
```
✅ Database schema migration completed
✅ Initialized {source_name} news source
✅ Starting AI News Aggregator...
```

## 🎯 Expected Behavior

**After Fix:**
- Application starts without errors
- Logs show "Database schema migration completed"
- New articles have topics, keywords, and relevance scores
- Old articles work but have NULL for new fields (will be enriched on re-fetch)

## 💡 Tips

1. **Automatic Migration**: The app now migrates automatically, so this should only happen once

2. **Existing Articles**: Old articles won't have topics/keywords until they're encountered again in a fetch

3. **No Data Loss**: Migration preserves all existing articles

4. **Safe to Run Multiple Times**: Migration checks for existing columns before adding

## 📚 Related Files

- `migrate_database.py` - Manual migration script
- `ai_news_bot/database.py` - Auto-migration code
- `RESEARCH_EXPANSION.md` - Details on what was added

## ✅ Success Indicators

After migration, you should see:

```bash
# In logs
Database schema migration completed
Initialization complete

# In CLI
$ python -m ai_news_bot.cli_search stats
Total Articles: 123
Articles Today: 5
...

# In database
$ sqlite3 data/news_aggregator.db "SELECT COUNT(*) FROM articles WHERE topics IS NOT NULL;"
5  # (new articles)
```

---

## 🆘 Still Having Issues?

1. Check the full error in logs:
   ```bash
   sudo journalctl -u ai-news-bot -n 100
   ```

2. Verify Python environment:
   ```bash
   which python
   poetry env info
   ```

3. Test database access:
   ```bash
   sqlite3 data/news_aggregator.db "SELECT COUNT(*) FROM articles;"
   ```

4. If all else fails, start fresh:
   ```bash
   mv data/news_aggregator.db data/backup_$(date +%Y%m%d).db
   sudo systemctl restart ai-news-bot
   ```

The application should now work! 🎉

