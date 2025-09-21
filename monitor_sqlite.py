#!/usr/bin/env python3
"""
SQLite Performance Monitor for Production CRM
Monitor database size, query performance, and provide recommendations
"""
import sqlite3
import os
import time
from datetime import datetime

def get_db_stats(db_path):
    """Get comprehensive database statistics"""
    if not os.path.exists(db_path):
        return None
    
    stats = {}
    
    # File size
    stats['file_size_mb'] = round(os.path.getsize(db_path) / (1024 * 1024), 2)
    
    # Connect and get internal stats
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Table counts
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        stats['tables'] = {}
        
        total_rows = 0
        for table in tables:
            table_name = table[0]
            if table_name.startswith('sqlite_'):
                continue
                
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            stats['tables'][table_name] = count
            total_rows += count
        
        stats['total_rows'] = total_rows
        
        # Page count and size
        cursor.execute("PRAGMA page_count")
        page_count = cursor.fetchone()[0]
        
        cursor.execute("PRAGMA page_size")
        page_size = cursor.fetchone()[0]
        
        stats['page_count'] = page_count
        stats['page_size'] = page_size
        stats['database_size_pages'] = page_count * page_size
        
        # Cache hit ratio (if available)
        cursor.execute("PRAGMA cache_size")
        cache_size = cursor.fetchone()[0]
        stats['cache_size'] = cache_size
        
        # WAL mode status
        cursor.execute("PRAGMA journal_mode")
        journal_mode = cursor.fetchone()[0]
        stats['journal_mode'] = journal_mode
        
        # Integrity check
        cursor.execute("PRAGMA quick_check")
        integrity = cursor.fetchone()[0]
        stats['integrity'] = integrity
        
    except Exception as e:
        stats['error'] = str(e)
    finally:
        conn.close()
    
    return stats

def benchmark_queries(db_path, num_tests=10):
    """Benchmark common CRM queries"""
    if not os.path.exists(db_path):
        return None
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    benchmarks = {}
    
    queries = {
        'select_all_users': "SELECT * FROM users",
        'select_all_leads': "SELECT * FROM leads", 
        'join_assignments': """
            SELECT u.full_name, l.company_name, a.assigned_at 
            FROM assignments a 
            JOIN users u ON a.salesperson_id = u.id 
            JOIN leads l ON a.lead_id = l.id
        """,
        'count_leads_by_status': "SELECT status, COUNT(*) FROM leads GROUP BY status",
        'search_leads': "SELECT * FROM leads WHERE company_name LIKE '%Tech%'"
    }
    
    try:
        for query_name, query in queries.items():
            times = []
            
            for _ in range(num_tests):
                start_time = time.time()
                cursor.execute(query)
                results = cursor.fetchall()
                end_time = time.time()
                
                times.append((end_time - start_time) * 1000)  # Convert to ms
            
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            benchmarks[query_name] = {
                'avg_ms': round(avg_time, 2),
                'min_ms': round(min_time, 2),
                'max_ms': round(max_time, 2),
                'result_count': len(results)
            }
            
    except Exception as e:
        benchmarks['error'] = str(e)
    finally:
        conn.close()
    
    return benchmarks

def get_recommendations(stats):
    """Provide performance recommendations"""
    recommendations = []
    
    if stats.get('file_size_mb', 0) > 1000:  # 1GB
        recommendations.append("⚠️  Database size > 1GB. Consider PostgreSQL for better performance.")
    
    if stats.get('journal_mode') != 'wal':
        recommendations.append("💡 Enable WAL mode for better concurrent access.")
    
    if stats.get('total_rows', 0) > 100000:
        recommendations.append("📊 Consider adding database indexes for frequently queried columns.")
    
    if stats.get('file_size_mb', 0) > 100:
        recommendations.append("💾 Set up automated backups (file size > 100MB).")
    
    if len(recommendations) == 0:
        recommendations.append("✅ Database is well-optimized for current size!")
    
    return recommendations

def main():
    """Main monitoring function"""
    db_path = "./crm_database.db"
    
    print("🔍 SQLite Production Monitor")
    print("=" * 50)
    print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🗄️  Database: {db_path}")
    print()
    
    # Get stats
    stats = get_db_stats(db_path)
    if not stats:
        print("❌ Database file not found!")
        return
    
    # Display stats
    print("📊 DATABASE STATISTICS")
    print("-" * 30)
    print(f"File Size: {stats['file_size_mb']} MB")
    print(f"Total Rows: {stats['total_rows']:,}")
    print(f"Journal Mode: {stats['journal_mode']}")
    print(f"Cache Size: {stats['cache_size']}")
    print(f"Integrity: {stats['integrity']}")
    print()
    
    print("📋 TABLE BREAKDOWN")
    print("-" * 30)
    for table, count in stats.get('tables', {}).items():
        print(f"{table}: {count:,} rows")
    print()
    
    # Benchmark queries
    print("⚡ PERFORMANCE BENCHMARKS")
    print("-" * 30)
    benchmarks = benchmark_queries(db_path)
    
    if benchmarks and 'error' not in benchmarks:
        for query, metrics in benchmarks.items():
            print(f"{query}:")
            print(f"  Average: {metrics['avg_ms']}ms")
            print(f"  Results: {metrics['result_count']} rows")
    else:
        print("❌ Benchmark failed:", benchmarks.get('error', 'Unknown error'))
    print()
    
    # Recommendations
    print("💡 RECOMMENDATIONS")
    print("-" * 30)
    recommendations = get_recommendations(stats)
    for rec in recommendations:
        print(rec)

if __name__ == "__main__":
    main()