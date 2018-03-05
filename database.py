import sqlite3

class Database(object):
    def __init__(self, filename="cursedboard.db"):
        self.dbfilename = filename
        self.db = sqlite3.connect(self.dbfilename)
        c = self.db.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS boards (bid INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, description TEXT, country_balls INT)")
        self.db.commit()
        c.close()


    def _create_board_tables(self, boardid):
        c = self.db.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS posts_%s (pid INTEGER PRIMARY KEY AUTOINCREMENT, \
                        tid INTEGER, \
                        title TEXT, \
                        name TEXT, \
                        content TEXT, \
                        created DATETIME DEFAULT CURRENT_TIMESTAMP, country TEXT)" % boardid)

        self.db.commit()
        c.close()

    def get_boards(self):
        c = self.db.cursor()
        c.execute('SELECT bid, name, description FROM boards')
        records = c.fetchall()
        for key, row in enumerate(records):
            c.execute("SELECT datetime(created,'localtime') as created FROM posts_%s ORDER BY created DESC LIMIT 1" % (records[key][0],))
            record = c.fetchall()
            if len(record) == 0:
                records[key] = row + ("",)
            else:
                records[key] = row + record[0]

        c.close()
        return records

    def board_has_country_balls(self, boardid):
        c = self.db.cursor()
        c.execute("SELECT country_balls FROM boards WHERE bid = ? ", (boardid,))
        records = c.fetchone()
        c.close()
        
        return int(records[0]) == 1

    def get_board(self, boardid):
        c = self.db.cursor()
        c.execute("SELECT name, description FROM boards WHERE bid = ? ", (boardid,))
        records = c.fetchone()
        c.close()
        return records

    def name_to_bid(self, name):
        c = self.db.cursor()
        c.execute("SELECT bid FROM boards WHERE name = ? ", (name,))
        records = c.fetchone()
        c.close()
        return records


    def create_board(self, name, description, country_balls):
        c = self.db.cursor()
        c.execute("INSERT INTO boards (name, description, country_balls) VALUES(?, ?, ?)", (name, description, country_balls))
        self.db.commit()
        self._create_board_tables(c.lastrowid)
        c.close()

    def get_threads(self, boardid):
        c = self.db.cursor()
        c.row_factory = sqlite3.Row
        c.execute("SELECT tid, COUNT(tid) as posts FROM posts_%s GROUP BY tid ORDER BY created DESC" % (boardid,))
        threads = c.fetchall()

        result = []
        for t in threads:
            record = {'posts':t['posts']}
            c.execute("SELECT pid, tid, title, name, content, datetime(created,'localtime') as created, country FROM posts_%s WHERE tid = ? ORDER BY created ASC LIMIT 1" % (boardid,), (t['tid'],))
            record['first'] = c.fetchone()
            c.execute("SELECT pid, tid, title, name, content, datetime(created,'localtime') as created, country FROM posts_%s WHERE tid = ? ORDER BY created DESC LIMIT 1" % (boardid,), (t['tid'],))
            record['last'] = c.fetchone()
            result.append(record)

        return result

    def get_thread(self, boardid, threadid):
        c = self.db.cursor()
        c.row_factory = sqlite3.Row
        c.execute("SELECT pid, tid, name, title, content, datetime(created,'localtime') as created, country FROM posts_%s WHERE tid = ? ORDER BY created ASC" % (boardid,), (threadid,))
        records = c.fetchall()
        c.close()
        return records

    def post(self, boardid, thread, name, title, content, country):
        c = self.db.cursor()
        c.execute("INSERT INTO posts_%s (name, title, content, country) VALUES (?,?,?,?)" %(boardid), (name, title, content, country))
        self.db.commit()

        if thread == 0:
            thread = c.lastrowid

        pid = c.lastrowid
        c.execute("UPDATE posts_%s SET tid = ? WHERE pid = ?" % boardid, (thread, pid))
        self.db.commit()
        return thread

    def delete_post(self, boardid, postid):
        c = self.db.cursor()
        c.execute("DELETE FROM posts_%s WHERE pid = ?" % boardid, (postid,))
        self.db.commit()
        c.close()

    def nuke_board(self, boardid):
        c = self.db.cursor()
        c.execute("DROP TABLE IF EXISTS posts_%s"%(boardid,))
        c.execute("DELETE FROM boards WHERE bid = ?", (boardid,))
        self.db.commit()
        c.close()

