class SqliteReviewHintStore:
    def __init__(self, connection):
        self.db = connection
        self.db.execute('PRAGMA cache_size=-2048')
        self.db.execute('CREATE TABLE hints(block_id TEXT PRIMARY KEY, group_id TEXT, title TEXT)')

    def put(self, block_id, group_id, title):
        self.db.execute('INSERT INTO hints VALUES (?,?,?)', (block_id, group_id, title))

    def get(self, block_id):
        return self.db.execute('SELECT group_id,title FROM hints WHERE block_id=?', (block_id,)).fetchone()

    def finish(self):
        self.db.commit()
