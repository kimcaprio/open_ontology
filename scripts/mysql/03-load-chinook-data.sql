-- Load Chinook CSV data into MySQL tables
-- Note: This assumes CSV files are accessible to MySQL server

-- Disable foreign key checks for data loading
SET FOREIGN_KEY_CHECKS = 0;

-- Load Artist data
LOAD DATA LOCAL INFILE '/docker-entrypoint-initdb.d/Artist.csv'
INTO TABLE Artist
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(ArtistId, @Name)
SET Name = NULLIF(@Name, '');

-- Load Genre data
LOAD DATA LOCAL INFILE '/docker-entrypoint-initdb.d/Genre.csv'
INTO TABLE Genre
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(GenreId, @Name)
SET Name = NULLIF(@Name, '');

-- Load MediaType data
LOAD DATA LOCAL INFILE '/docker-entrypoint-initdb.d/MediaType.csv'
INTO TABLE MediaType
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(MediaTypeId, @Name)
SET Name = NULLIF(@Name, '');

-- Load Album data
LOAD DATA LOCAL INFILE '/docker-entrypoint-initdb.d/Album.csv'
INTO TABLE Album
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(AlbumId, @Title, ArtistId)
SET Title = NULLIF(@Title, '');

-- Load Employee data
LOAD DATA LOCAL INFILE '/docker-entrypoint-initdb.d/Employee.csv'
INTO TABLE Employee
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(EmployeeId, @LastName, @FirstName, @Title, @ReportsTo, @BirthDate, @HireDate, @Address, @City, @State, @Country, @PostalCode, @Phone, @Fax, @Email)
SET 
    LastName = NULLIF(@LastName, ''),
    FirstName = NULLIF(@FirstName, ''),
    Title = NULLIF(@Title, ''),
    ReportsTo = NULLIF(@ReportsTo, ''),
    BirthDate = STR_TO_DATE(NULLIF(@BirthDate, ''), '%Y-%m-%d %H:%i:%s'),
    HireDate = STR_TO_DATE(NULLIF(@HireDate, ''), '%Y-%m-%d %H:%i:%s'),
    Address = NULLIF(@Address, ''),
    City = NULLIF(@City, ''),
    State = NULLIF(@State, ''),
    Country = NULLIF(@Country, ''),
    PostalCode = NULLIF(@PostalCode, ''),
    Phone = NULLIF(@Phone, ''),
    Fax = NULLIF(@Fax, ''),
    Email = NULLIF(@Email, '');

-- Load Customer data
LOAD DATA LOCAL INFILE '/docker-entrypoint-initdb.d/Customer.csv'
INTO TABLE Customer
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(CustomerId, @FirstName, @LastName, @Company, @Address, @City, @State, @Country, @PostalCode, @Phone, @Fax, @Email, @SupportRepId)
SET 
    FirstName = NULLIF(@FirstName, ''),
    LastName = NULLIF(@LastName, ''),
    Company = NULLIF(@Company, ''),
    Address = NULLIF(@Address, ''),
    City = NULLIF(@City, ''),
    State = NULLIF(@State, ''),
    Country = NULLIF(@Country, ''),
    PostalCode = NULLIF(@PostalCode, ''),
    Phone = NULLIF(@Phone, ''),
    Fax = NULLIF(@Fax, ''),
    Email = NULLIF(@Email, ''),
    SupportRepId = NULLIF(@SupportRepId, '');

-- Load Invoice data
LOAD DATA LOCAL INFILE '/docker-entrypoint-initdb.d/Invoice.csv'
INTO TABLE Invoice
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(InvoiceId, CustomerId, @InvoiceDate, @BillingAddress, @BillingCity, @BillingState, @BillingCountry, @BillingPostalCode, Total)
SET 
    InvoiceDate = STR_TO_DATE(@InvoiceDate, '%Y-%m-%d %H:%i:%s'),
    BillingAddress = NULLIF(@BillingAddress, ''),
    BillingCity = NULLIF(@BillingCity, ''),
    BillingState = NULLIF(@BillingState, ''),
    BillingCountry = NULLIF(@BillingCountry, ''),
    BillingPostalCode = NULLIF(@BillingPostalCode, '');

-- Load Track data
LOAD DATA LOCAL INFILE '/docker-entrypoint-initdb.d/Track.csv'
INTO TABLE Track
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(TrackId, @Name, @AlbumId, MediaTypeId, @GenreId, @Composer, @Milliseconds, @Bytes, UnitPrice)
SET 
    Name = NULLIF(@Name, ''),
    AlbumId = NULLIF(@AlbumId, ''),
    GenreId = NULLIF(@GenreId, ''),
    Composer = NULLIF(@Composer, ''),
    Milliseconds = NULLIF(@Milliseconds, ''),
    Bytes = NULLIF(@Bytes, '');

-- Load Playlist data
LOAD DATA LOCAL INFILE '/docker-entrypoint-initdb.d/Playlist.csv'
INTO TABLE Playlist
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(PlaylistId, @Name)
SET Name = NULLIF(@Name, '');

-- Load InvoiceLine data
LOAD DATA LOCAL INFILE '/docker-entrypoint-initdb.d/InvoiceLine.csv'
INTO TABLE InvoiceLine
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(InvoiceLineId, InvoiceId, TrackId, UnitPrice, Quantity);

-- Load PlaylistTrack data
LOAD DATA LOCAL INFILE '/docker-entrypoint-initdb.d/PlaylistTrack.csv'
INTO TABLE PlaylistTrack
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(PlaylistId, TrackId);

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- Display data loading results
SELECT 'Artist' as TableName, COUNT(*) as RecordCount FROM Artist
UNION ALL
SELECT 'Genre', COUNT(*) FROM Genre
UNION ALL
SELECT 'MediaType', COUNT(*) FROM MediaType
UNION ALL
SELECT 'Album', COUNT(*) FROM Album
UNION ALL
SELECT 'Employee', COUNT(*) FROM Employee
UNION ALL
SELECT 'Customer', COUNT(*) FROM Customer
UNION ALL
SELECT 'Invoice', COUNT(*) FROM Invoice
UNION ALL
SELECT 'Track', COUNT(*) FROM Track
UNION ALL
SELECT 'Playlist', COUNT(*) FROM Playlist
UNION ALL
SELECT 'InvoiceLine', COUNT(*) FROM InvoiceLine
UNION ALL
SELECT 'PlaylistTrack', COUNT(*) FROM PlaylistTrack; 