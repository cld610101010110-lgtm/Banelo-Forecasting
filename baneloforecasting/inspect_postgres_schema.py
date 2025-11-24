#!/usr/bin/env python
"""
PostgreSQL Schema Inspector
Run this script to see the exact table structure from your mobile app's database.
This will help match Django models to the existing PostgreSQL tables.

Usage:
    python inspect_postgres_schema.py
"""

import os
import sys

# Add Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baneloforecasting.settings')

import django
django.setup()

from django.db import connection

def inspect_schema():
    print("=" * 70)
    print("PostgreSQL Schema Inspector for Banelo Database")
    print("=" * 70)

    try:
        with connection.cursor() as cursor:
            # Test connection
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"\n✅ Connected to PostgreSQL!")
            print(f"   Version: {version[0][:50]}...")

            # Get all tables
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()

            print(f"\n📋 Found {len(tables)} tables in 'banelo_db':\n")

            for (table_name,) in tables:
                print(f"\n{'─' * 60}")
                print(f"📦 TABLE: {table_name}")
                print(f"{'─' * 60}")

                # Get columns for each table
                cursor.execute("""
                    SELECT
                        column_name,
                        data_type,
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    AND table_name = %s
                    ORDER BY ordinal_position;
                """, [table_name])

                columns = cursor.fetchall()

                print(f"{'Column Name':<30} {'Type':<20} {'Nullable':<10} {'Default'}")
                print("-" * 80)

                for col_name, data_type, nullable, default in columns:
                    default_str = str(default)[:20] if default else '-'
                    print(f"{col_name:<30} {data_type:<20} {nullable:<10} {default_str}")

                # Get row count
                cursor.execute(f'SELECT COUNT(*) FROM "{table_name}";')
                count = cursor.fetchone()[0]
                print(f"\n   📊 Row count: {count}")

            print("\n" + "=" * 70)
            print("Schema inspection complete!")
            print("=" * 70)

            # Generate Django model suggestions
            print("\n\n📝 DJANGO MODEL SUGGESTIONS:")
            print("=" * 70)

            for (table_name,) in tables:
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = %s
                    ORDER BY ordinal_position;
                """, [table_name])
                columns = cursor.fetchall()

                # Convert table name to class name
                class_name = ''.join(word.capitalize() for word in table_name.split('_'))

                print(f"\nclass {class_name}(models.Model):")
                for col_name, data_type, nullable in columns:
                    django_field = get_django_field(col_name, data_type, nullable)
                    print(f"    {django_field}")
                print(f"    \n    class Meta:")
                print(f"        db_table = '{table_name}'")
                print(f"        managed = False  # Table managed by mobile app")

    except Exception as e:
        print(f"\n❌ Error connecting to PostgreSQL: {e}")
        print("\nPlease check:")
        print("  1. PostgreSQL is running")
        print("  2. Database 'banelo_db' exists")
        print("  3. Credentials are correct (postgres/admin123)")
        print("  4. Port 5432 is accessible")
        sys.exit(1)


def get_django_field(col_name, data_type, nullable):
    """Convert PostgreSQL data type to Django field definition"""
    null_str = ", null=True, blank=True" if nullable == 'YES' else ""

    # Check if it's a primary key
    if col_name in ['id', 'recipe_id']:
        return f"{col_name} = models.AutoField(primary_key=True)"

    # Map PostgreSQL types to Django fields
    type_mapping = {
        'integer': 'IntegerField',
        'bigint': 'BigIntegerField',
        'smallint': 'SmallIntegerField',
        'real': 'FloatField',
        'double precision': 'FloatField',
        'numeric': 'DecimalField',
        'character varying': 'CharField',
        'varchar': 'CharField',
        'text': 'TextField',
        'boolean': 'BooleanField',
        'timestamp without time zone': 'DateTimeField',
        'timestamp with time zone': 'DateTimeField',
        'date': 'DateField',
        'time': 'TimeField',
    }

    field_type = type_mapping.get(data_type, 'CharField')

    # Add max_length for CharField
    if field_type == 'CharField':
        return f"{col_name} = models.{field_type}(max_length=255{null_str})"
    elif field_type == 'DecimalField':
        return f"{col_name} = models.{field_type}(max_digits=10, decimal_places=2{null_str})"
    else:
        return f"{col_name} = models.{field_type}({null_str.lstrip(', ') if null_str else 'default=0' if 'Int' in field_type or 'Float' in field_type else ''})"


if __name__ == '__main__':
    inspect_schema()
