#!/usr/bin/env python3
"""
Load Chinook CSV data into MySQL database
"""

import pandas as pd
import pymysql
import os
import sys
from datetime import datetime

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'ontology_user',
    'password': 'ontology_password',
    'database': 'ontology_dev',
    'charset': 'utf8mb4'
}

# CSV file mapping to table names
CSV_FILES = [
    ('data/Artist.csv', 'Artist'),
    ('data/Genre.csv', 'Genre'),
    ('data/MediaType.csv', 'MediaType'),
    ('data/Album.csv', 'Album'),
    ('data/Employee.csv', 'Employee'),
    ('data/Customer.csv', 'Customer'),
    ('data/Invoice.csv', 'Invoice'),
    ('data/Track.csv', 'Track'),
    ('data/Playlist.csv', 'Playlist'),
    ('data/InvoiceLine.csv', 'InvoiceLine'),
    ('data/PlaylistTrack.csv', 'PlaylistTrack'),
]

def clean_data(df, table_name):
    """Clean and prepare DataFrame for database insertion"""
    
    # Handle datetime columns
    if table_name == 'Employee':
        if 'BirthDate' in df.columns:
            df['BirthDate'] = pd.to_datetime(df['BirthDate'], errors='coerce')
        if 'HireDate' in df.columns:
            df['HireDate'] = pd.to_datetime(df['HireDate'], errors='coerce')
    
    elif table_name == 'Invoice':
        if 'InvoiceDate' in df.columns:
            df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], errors='coerce')
    
    # Replace empty strings with None
    df = df.replace('', None)
    
    # Handle NULL values for foreign keys
    foreign_key_columns = {
        'Album': ['ArtistId'],
        'Customer': ['SupportRepId'],
        'Employee': ['ReportsTo'],
        'Track': ['AlbumId', 'GenreId'],
        'Invoice': ['CustomerId'],
        'InvoiceLine': ['InvoiceId', 'TrackId'],
        'PlaylistTrack': ['PlaylistId', 'TrackId']
    }
    
    if table_name in foreign_key_columns:
        for col in foreign_key_columns[table_name]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def load_data():
    """Load all CSV files into MySQL database"""
    
    try:
        # Connect to database
        connection = pymysql.connect(**DB_CONFIG)
        print(f"✅ Connected to MySQL database: {DB_CONFIG['database']}")
        
        # Disable foreign key checks
        with connection.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            print("🔓 Disabled foreign key checks")
        
        total_records = 0
        
        # Load each CSV file
        for csv_file, table_name in CSV_FILES:
            if not os.path.exists(csv_file):
                print(f"❌ File not found: {csv_file}")
                continue
            
            print(f"\n📁 Loading {csv_file} into {table_name} table...")
            
            # Read CSV file
            df = pd.read_csv(csv_file)
            print(f"   📊 Found {len(df)} records")
            
            # Clean data
            df = clean_data(df, table_name)
            
            # Insert data using pandas to_sql method
            from sqlalchemy import create_engine
            
            # Create SQLAlchemy engine
            engine_url = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
            engine = create_engine(engine_url)
            
            # Insert data
            df.to_sql(table_name, engine, if_exists='append', index=False, method='multi', chunksize=1000)
            
            print(f"   ✅ Successfully loaded {len(df)} records into {table_name}")
            total_records += len(df)
        
        # Re-enable foreign key checks
        with connection.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            print("\n🔒 Re-enabled foreign key checks")
        
        # Display summary
        print(f"\n🎉 Data loading completed!")
        print(f"📈 Total records loaded: {total_records}")
        
        # Show table counts
        print("\n📊 Table Record Counts:")
        with connection.cursor() as cursor:
            for _, table_name in CSV_FILES:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"   {table_name}: {count:,} records")
        
        connection.close()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

def test_data():
    """Test the loaded data with sample queries"""
    
    try:
        connection = pymysql.connect(**DB_CONFIG)
        print("\n🧪 Testing loaded data...")
        
        with connection.cursor() as cursor:
            # Test query 1: Top 5 artists by album count
            cursor.execute("""
                SELECT a.Name as Artist, COUNT(al.AlbumId) as AlbumCount
                FROM Artist a
                LEFT JOIN Album al ON a.ArtistId = al.ArtistId
                GROUP BY a.ArtistId, a.Name
                ORDER BY AlbumCount DESC
                LIMIT 5
            """)
            
            print("\n🎵 Top 5 Artists by Album Count:")
            for row in cursor.fetchall():
                print(f"   {row[0]}: {row[1]} albums")
            
            # Test query 2: Sales by country
            cursor.execute("""
                SELECT BillingCountry, COUNT(*) as InvoiceCount, SUM(Total) as TotalSales
                FROM Invoice
                GROUP BY BillingCountry
                ORDER BY TotalSales DESC
                LIMIT 5
            """)
            
            print("\n💰 Top 5 Countries by Sales:")
            for row in cursor.fetchall():
                print(f"   {row[0]}: ${row[2]:,.2f} ({row[1]} invoices)")
        
        connection.close()
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting Chinook data loading process...")
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    load_data()
    test_data()
    
    print(f"\n🏁 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}") 