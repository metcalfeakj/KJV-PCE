# 📖 KJV-PCE.sqlite

**KJV-PCE.sqlite** is a normalised, queryable SQLite database containing the full text of the **King James Version (Pure Cambridge Edition)** of the Bible. It is structured for clarity, flexibility, and performance, making it ideal for application development, data analysis, or serious Bible study.

---

## 🧬 Origin

- This project is a **fork of the PCE database** from [BibleProtector.com](https://www.bibleprotector.com/), which provides a digital edition of the **Pure Cambridge Edition (PCE)** of the King James Bible.
- The **Scrivener pilcrow paragraph markers (¶)** were sourced from a user-submitted index on the [SwordSearcher Forums](https://forums.swordsearcher.com/threads/pilcrow-index-for-kjv-module.4486/), based on Scrivener’s *Cambridge Paragraph Bible*.

---

## 🗃️ Schema Overview

This database uses a normalised schema with four main tables and two views:

### 📚 Tables

```sql
CREATE TABLE Books (
    BookID   INTEGER PRIMARY KEY,
    BookAbr  TEXT NOT NULL,   -- e.g., "Ge", "Ps", "Jn"
    BookName TEXT NOT NULL    -- e.g., "Genesis", "Psalms", "John"
);

CREATE TABLE Chapters (
    BookID  INTEGER REFERENCES Books,
    Chapter INTEGER,
    PRIMARY KEY (BookID, Chapter)
);

CREATE TABLE Verses (
    BookID  INTEGER,
    Chapter INTEGER,
    Verse   INTEGER,
    VText   TEXT NOT NULL,
    PRIMARY KEY (BookID, Chapter, Verse),
    FOREIGN KEY (BookID, Chapter) REFERENCES Chapters
);

CREATE TABLE Scrivener (
    BookID  INTEGER,
    Chapter INTEGER,
    Verse   INTEGER,
    PRIMARY KEY (BookID, Chapter, Verse),
    FOREIGN KEY (BookID, Chapter, Verse) REFERENCES Verses
);
```

---

### 🔍 Views

#### `LookupVerseView`

Provides joined access to verses with book and chapter metadata.

```sql
CREATE VIEW LookupVerseView AS
SELECT
    B.BookID,
    B.BookName,
    B.BookAbr,
    C.Chapter,
    V.Verse,
    V.VText
FROM Verses V
JOIN Chapters C ON V.BookID = C.BookID AND V.Chapter = C.Chapter
JOIN Books B ON C.BookID = B.BookID;
```

#### `LookupVerseWithPilcrowView`

Prepend a pilcrow (¶) + space to any verse text that was paragraph-marked by Scrivener.

```sql
CREATE VIEW LookupVerseWithPilcrowView AS
SELECT
    B.BookID,
    B.BookName,
    B.BookAbr,
    V.Chapter,
    V.Verse,
    CASE
        WHEN S.BookID IS NOT NULL THEN '¶ ' || V.VText
        ELSE V.VText
    END AS VText
FROM Verses V
JOIN Chapters C ON V.BookID = C.BookID AND V.Chapter = C.Chapter
JOIN Books B ON C.BookID = B.BookID
LEFT JOIN Scrivener S ON V.BookID = S.BookID AND V.Chapter = S.Chapter AND V.Verse = S.Verse;
```

---

## ⚙️ Example Queries

```sql
-- Get John 3:16 with metadata
SELECT * FROM LookupVerseView
WHERE BookName = 'John' AND Chapter = 3 AND Verse = 16;

-- List all verses in Psalm 23 with pilcrows
SELECT * FROM LookupVerseWithPilcrowView
WHERE BookName = 'Psalms' AND Chapter = 23;

-- Search for verses containing "faith"
SELECT BookName, Chapter, Verse, VText
FROM LookupVerseView
WHERE VText LIKE '%faith%';
```

---

## ✅ Features

- 📜 **Pure Cambridge Edition (PCE)** Text
- 🧱 **Normalized schema**: clean, scalable, and fast
- ¶ **Scrivener paragraph markers** fully integrated
- 🔍 **Flexible views** for development and study
- 🗃️ Public domain text, freely usable in any project

---

## 📦 Usage

You can open and interact with `KJV-PCE.sqlite` using:

- [SQLite Browser](https://sqlitebrowser.org/)
- Python (`sqlite3`, `pandas`, or `SQLAlchemy`)
- JavaScript (e.g., `sql.js`, `wa-sqlite`)
- Any platform with SQLite bindings (Rust, Go, C#, etc.)

---

## 📜 License

The **King James Bible (PCE)** text is in the **public domain**. This structured database and views are provided freely for any use: study, software, or publication.

---

## ⚔️ Proverbs 27:17

> **Iron sharpeneth iron; so a man sharpeneth the countenance of his friend.**

This project exists to encourage scriptural refinement through fellowship, study, and open tools.

---
