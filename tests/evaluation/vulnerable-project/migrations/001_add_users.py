"""
KD-005: Migration with no rollback function.
If this migration fails mid-way, the database is left in a partially
migrated state with no way to cleanly revert.
"""

def upgrade():
    """Add users table."""
    return [
        "CREATE TABLE users (id SERIAL PRIMARY KEY, email TEXT NOT NULL, name TEXT, ssn TEXT)",
        "CREATE INDEX idx_users_email ON users(email)",
        "INSERT INTO users (email, name) VALUES ('seed@example.com', 'Seed User')",
    ]

# KD-005: No downgrade() function — migration cannot be rolled back
# A proper migration would have:
# def downgrade():
#     return ["DROP TABLE IF EXISTS users"]
