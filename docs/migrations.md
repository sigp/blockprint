# Database Migrations

When the database schema changes, manual intervention is required to update existing databases.

You should apply each of the migrations in `blockprint/migrations` in order, like so:

```
sqlite3 block_db.sqlite ".read migrations/00_pr_grandine.sql"
```
