# How the shared application stored lectures

The original Flask service used MySQL. Each saved lecture linked a student account to a title, source URL and summary. A separate generation ledger recorded when a summary was created so the dashboard and extension could display recent usage. SQLite in the portfolio edition uses a smaller schema for its browser-scoped library.

The following excerpts come from the shared database layer. They contain table definitions and parameterized query text only. The local demonstration never executes them.

## Library and usage schema


```sql
CREATE TABLE IF NOT EXISTS UserLectures(
    ID INT AUTO_INCREMENT PRIMARY KEY,
    Username VARCHAR(50) NOT NULL,
    Lecture_ID VARCHAR(50) NOT NULL,
    Title VARCHAR(255) NOT NULL,
    URL VARCHAR(2048),
    Summary TEXT,
    Timestamp DATETIME,
    FOREIGN KEY (Username) REFERENCES Users(Username) ON DELETE CASCADE,
    UNIQUE(Username, URL(255))
);
```

```sql
CREATE TABLE IF NOT EXISTS SummaryGenerations(
    ID INT AUTO_INCREMENT PRIMARY KEY,
    Username VARCHAR(255) NOT NULL,
    Lecture_ID VARCHAR(255) NOT NULL,
    Timestamp DATETIME NOT NULL
);
```

The composite unique key used the account name and a prefix of the source URL to deduplicate imports. The separate generation table counted repeat generations even when the saved item was replaced. A URL-prefix collision and concurrent writes were limitations of this design. The portfolio stores each user-confirmed import as its own item.

## Reading data for the signed-in student


```sql
SELECT Lecture_ID, URL, Summary, Timestamp, Title 
FROM UserLectures 
WHERE Username = %s 
ORDER BY Timestamp DESC
```

```sql
SELECT Lecture_ID, URL, Summary, Timestamp, Title, Username
FROM UserLectures 
WHERE Lecture_ID = %s AND Username = %s
```

```sql
SELECT COUNT(*) as count FROM SummaryGenerations
WHERE Username = %s AND DATE(Timestamp) = %s
```

These queries illustrate the shared project's owner-scoped read and usage-count paths. In the portfolio, the web handler checks the browser-session owner on every lecture read, edit, export view and removal. The synthetic library has no paid tier.
