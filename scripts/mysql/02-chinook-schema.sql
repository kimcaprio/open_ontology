-- Chinook Database Schema for MySQL
-- Drop existing tables if they exist (in reverse dependency order)
DROP TABLE IF EXISTS PlaylistTrack;
DROP TABLE IF EXISTS InvoiceLine;
DROP TABLE IF EXISTS Track;
DROP TABLE IF EXISTS Invoice;
DROP TABLE IF EXISTS Playlist;
DROP TABLE IF EXISTS Album;
DROP TABLE IF EXISTS Customer;
DROP TABLE IF EXISTS Employee;
DROP TABLE IF EXISTS Artist;
DROP TABLE IF EXISTS Genre;
DROP TABLE IF EXISTS MediaType;

-- Create Artist table
CREATE TABLE Artist (
    ArtistId INT PRIMARY KEY,
    Name VARCHAR(120)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create Genre table
CREATE TABLE Genre (
    GenreId INT PRIMARY KEY,
    Name VARCHAR(120)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create MediaType table
CREATE TABLE MediaType (
    MediaTypeId INT PRIMARY KEY,
    Name VARCHAR(120)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create Album table
CREATE TABLE Album (
    AlbumId INT PRIMARY KEY,
    Title VARCHAR(160) NOT NULL,
    ArtistId INT NOT NULL,
    FOREIGN KEY (ArtistId) REFERENCES Artist(ArtistId)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create Employee table
CREATE TABLE Employee (
    EmployeeId INT PRIMARY KEY,
    LastName VARCHAR(20) NOT NULL,
    FirstName VARCHAR(20) NOT NULL,
    Title VARCHAR(30),
    ReportsTo INT,
    BirthDate DATETIME,
    HireDate DATETIME,
    Address VARCHAR(70),
    City VARCHAR(40),
    State VARCHAR(40),
    Country VARCHAR(40),
    PostalCode VARCHAR(10),
    Phone VARCHAR(24),
    Fax VARCHAR(24),
    Email VARCHAR(60),
    FOREIGN KEY (ReportsTo) REFERENCES Employee(EmployeeId)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create Customer table
CREATE TABLE Customer (
    CustomerId INT PRIMARY KEY,
    FirstName VARCHAR(40) NOT NULL,
    LastName VARCHAR(20) NOT NULL,
    Company VARCHAR(80),
    Address VARCHAR(70),
    City VARCHAR(40),
    State VARCHAR(40),
    Country VARCHAR(40),
    PostalCode VARCHAR(10),
    Phone VARCHAR(24),
    Fax VARCHAR(24),
    Email VARCHAR(60) NOT NULL,
    SupportRepId INT,
    FOREIGN KEY (SupportRepId) REFERENCES Employee(EmployeeId)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create Invoice table
CREATE TABLE Invoice (
    InvoiceId INT PRIMARY KEY,
    CustomerId INT NOT NULL,
    InvoiceDate DATETIME NOT NULL,
    BillingAddress VARCHAR(70),
    BillingCity VARCHAR(40),
    BillingState VARCHAR(40),
    BillingCountry VARCHAR(40),
    BillingPostalCode VARCHAR(10),
    Total DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (CustomerId) REFERENCES Customer(CustomerId)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create Track table
CREATE TABLE Track (
    TrackId INT PRIMARY KEY,
    Name VARCHAR(200) NOT NULL,
    AlbumId INT,
    MediaTypeId INT NOT NULL,
    GenreId INT,
    Composer VARCHAR(220),
    Milliseconds INT,
    Bytes INT,
    UnitPrice DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (AlbumId) REFERENCES Album(AlbumId),
    FOREIGN KEY (MediaTypeId) REFERENCES MediaType(MediaTypeId),
    FOREIGN KEY (GenreId) REFERENCES Genre(GenreId)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create Playlist table
CREATE TABLE Playlist (
    PlaylistId INT PRIMARY KEY,
    Name VARCHAR(120)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create InvoiceLine table
CREATE TABLE InvoiceLine (
    InvoiceLineId INT PRIMARY KEY,
    InvoiceId INT NOT NULL,
    TrackId INT NOT NULL,
    UnitPrice DECIMAL(10,2) NOT NULL,
    Quantity INT NOT NULL,
    FOREIGN KEY (InvoiceId) REFERENCES Invoice(InvoiceId),
    FOREIGN KEY (TrackId) REFERENCES Track(TrackId)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create PlaylistTrack table (many-to-many relationship)
CREATE TABLE PlaylistTrack (
    PlaylistId INT NOT NULL,
    TrackId INT NOT NULL,
    PRIMARY KEY (PlaylistId, TrackId),
    FOREIGN KEY (PlaylistId) REFERENCES Playlist(PlaylistId),
    FOREIGN KEY (TrackId) REFERENCES Track(TrackId)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create indexes for better performance
CREATE INDEX idx_album_artist ON Album(ArtistId);
CREATE INDEX idx_track_album ON Track(AlbumId);
CREATE INDEX idx_track_mediatype ON Track(MediaTypeId);
CREATE INDEX idx_track_genre ON Track(GenreId);
CREATE INDEX idx_customer_support ON Customer(SupportRepId);
CREATE INDEX idx_invoice_customer ON Invoice(CustomerId);
CREATE INDEX idx_invoiceline_invoice ON InvoiceLine(InvoiceId);
CREATE INDEX idx_invoiceline_track ON InvoiceLine(TrackId);
CREATE INDEX idx_employee_reports ON Employee(ReportsTo); 