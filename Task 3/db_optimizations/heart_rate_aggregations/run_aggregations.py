#!/usr/bin/env python3
# filepath: /home/shadab/Desktop/Github Repos/wearipedia-project-assesment/Task 3/db_optimizations/run_aggregations.py

import argparse
import datetime
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import os
# from dotenv import load_dotenv

# Load environment variables from .env file
# load_dotenv()

def get_db_connection():
    """Create a connection to the TimescaleDB database"""
    try:

        conn = psycopg2.connect(
            host="localhost", 
            port="5432",
            dbname="fitbit_data",
            user="postgres",
            password="password" 
        )
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        sys.exit(1)

def setup_aggregations(conn):
    """Create the aggregation views and policies"""
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT create_heart_rate_aggregations()")
            print("Heart rate aggregation views and policies created successfully")
    except Exception as e:
        print(f"Error setting up aggregations: {e}")
        sys.exit(1)

def refresh_aggregation(conn, level, start_date=None, end_date=None):
    """Get instructions for refreshing a specific aggregation level"""
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT refresh_heart_rate_aggregation(%s, %s, %s)",
                (level, start_date, end_date)
            )
            result = cursor.fetchone()[0]
            print(result)
    except Exception as e:
        print(f"Error getting refresh instructions: {e}")
        sys.exit(1)

def execute_refresh(conn, level, start_date=None, end_date=None):
    """Execute the actual refresh for an aggregation level"""
    try:
        with conn.cursor() as cursor:
            # Get the refresh instructions first
            cursor.execute(
                "SELECT refresh_heart_rate_aggregation(%s, %s, %s)",
                (level, start_date, end_date)
            )
            instructions = cursor.fetchone()[0]
            
            # Parse the instructions to get the actual refresh commands
            commands = [line.strip() for line in instructions.split('\n') if line.strip().startswith('CALL')]
            
            # Execute each refresh command in order
            for cmd in commands:
                print(f"Executing: {cmd}")
                cursor.execute(cmd)
                print(f"✓ Command completed successfully")
            
            print(f"\nSuccessfully refreshed heart_rate_{level} aggregation")
    except Exception as e:
        print(f"Error during refresh execution: {e}")
        sys.exit(1)

def get_stats(conn):
    """Get statistics about the heart rate aggregations"""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM get_heart_rate_aggregation_stats()")
            stats = cursor.fetchall()
            
            if not stats:
                print("No aggregation statistics available")
                return
                
            print("\nHeart Rate Aggregation Statistics:")
            print("-" * 80)
            print(f"{'Level':<6} {'Last Refresh':<25} {'Total Rows':<15} {'Size':<15} {'Compression':<10}")
            print("-" * 80)
            
            for row in stats:
                size_mb = row['size_bytes'] / (1024 * 1024) if row['size_bytes'] else 0
                print(f"{row['level']:<6} {str(row['last_refresh'] or 'Never'):<25} "
                      f"{row['total_rows'] or 0:<15} {f'{size_mb:.2f} MB':<15} "
                      f"{row['compression_ratio'] or '-':<10.2f}")
    except Exception as e:
        print(f"Error getting aggregation statistics: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Manage TimescaleDB heart rate aggregations')
    
    # Command subparsers
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Create aggregation views and policies')
    
    # Refresh command
    refresh_parser = subparsers.add_parser('refresh', help='Refresh aggregation for a specific level')
    refresh_parser.add_argument('level', choices=['1m', '1h', '1d', '1w', '1mo'], help='Aggregation level')
    refresh_parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD)')
    refresh_parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD)')
    refresh_parser.add_argument('--execute', action='store_true', help='Execute the refresh commands')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Get aggregation statistics')
    
    args = parser.parse_args()
    
    # Establish database connection
    conn = get_db_connection()
    
    try:
        if args.command == 'setup':
            setup_aggregations(conn)
        elif args.command == 'refresh':
            start_date = None
            end_date = None
            
            if args.start:
                try:
                    start_date = datetime.datetime.strptime(args.start, '%Y-%m-%d')
                except ValueError:
                    print("Error: Start date must be in format YYYY-MM-DD")
                    sys.exit(1)
            
            if args.end:
                try:
                    end_date = datetime.datetime.strptime(args.end, '%Y-%m-%d')
                except ValueError:
                    print("Error: End date must be in format YYYY-MM-DD")
                    sys.exit(1)
            
            if args.execute:
                execute_refresh(conn, args.level, start_date, end_date)
            else:
                refresh_aggregation(conn, args.level, start_date, end_date)
        elif args.command == 'stats':
            get_stats(conn)
        else:
            parser.print_help()
    finally:
        conn.close()

if __name__ == "__main__":
    main()