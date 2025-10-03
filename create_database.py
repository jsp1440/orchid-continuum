"""
Auto-create database if it doesn't exist (for Render deployment)
"""
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_database_if_not_exists():
    """Create orchid_continuum database if it doesn't exist"""
    database_url = os.environ.get("DATABASE_URL")
    
    if not database_url:
        logger.error("DATABASE_URL not set")
        return False
    
    # Parse the URL to get connection details
    # Format: postgresql://user:pass@host:port/dbname
    try:
        parts = database_url.replace("postgresql://", "").replace("postgres://", "")
        auth_host = parts.split("@")
        user_pass = auth_host[0].split(":")
        host_port_db = auth_host[1].split("/")
        host_port = host_port_db[0].split(":")
        
        user = user_pass[0]
        password = user_pass[1] if len(user_pass) > 1 else ""
        host = host_port[0]
        port = host_port[1] if len(host_port) > 1 else "5432"
        target_db = host_port_db[1] if len(host_port_db) > 1 else "orchid_continuum"
        
        # Try multiple default databases to connect
        logger.info(f"Attempting to connect to create {target_db}...")
        
        # Try these databases in order: postgres, template1, user's default
        default_dbs = ["postgres", "template1", user]
        conn = None
        
        for default_db in default_dbs:
            try:
                conn_string = f"postgresql://{user}:{password}@{host}:{port}/{default_db}"
                logger.info(f"Trying to connect to {default_db}...")
                conn = psycopg2.connect(conn_string)
                logger.info(f"✅ Connected to {default_db}")
                break
            except Exception as e:
                logger.warning(f"Could not connect to {default_db}: {e}")
                continue
        
        if not conn:
            logger.error("Could not connect to any default database")
            return False
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname=%s", (target_db,))
        exists = cursor.fetchone()
        
        if not exists:
            logger.info(f"Creating database {target_db}...")
            cursor.execute(f'CREATE DATABASE "{target_db}"')
            logger.info(f"✅ Database {target_db} created successfully!")
        else:
            logger.info(f"Database {target_db} already exists.")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        return False

if __name__ == "__main__":
    create_database_if_not_exists()
