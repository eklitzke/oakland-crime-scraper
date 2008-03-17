CREATE TABLE IF NOT EXISTS atom_feed (
	id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	cs_guid TEXT,
	cs_category TEXT,
	cs_title TEXT,
	cs_url TEXT,
	time_fetched INTEGER,
	time_updated INTEGER,
	latitude REAL,
	longitude REAL,
	UNIQUE (cs_guid),
	UNIQUE (cs_url)
);

CREATE TABLE IF NOT EXISTS category (
	id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	cs_name TEXT,
	display_name TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS cs_guid_idx ON atom_feed (cs_guid);
