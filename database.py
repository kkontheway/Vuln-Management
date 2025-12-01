"""Database connection and utility functions."""
import logging
from mysql.connector import Error
import mysql.connector
from config import config

logger = logging.getLogger(__name__)


def get_db_connection():
    """Create and return a database connection.
    
    Returns:
        mysql.connector.connection.MySQLConnection or None: Database connection object,
        or None if connection fails.
    """
    try:
        connection = mysql.connector.connect(**config.db_config)
        if connection.is_connected():
            return connection
    except Error as e:
        logger.error(f"连接数据库时出错: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected database error: {e}")
        return None

