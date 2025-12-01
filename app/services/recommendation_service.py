"""Recommendation report service for business logic."""
import logging
from datetime import datetime, timedelta
from database import get_db_connection
from app.constants.database import TABLE_RECOMMENDATION_REPORTS
from openai import OpenAI

logger = logging.getLogger(__name__)


def check_existing_report(cve_id: str):
    """Check if a report exists for the given CVE within the last 7 days.
    
    Args:
        cve_id: CVE ID to check
        
    Returns:
        dict: Report info if exists (id, cve_id, created_at), None otherwise
    """
    connection = get_db_connection()
    if not connection:
        raise Exception("数据库连接失败")
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Check for reports created within last 7 days
        query = f"""
        SELECT id, cve_id, created_at
        FROM {TABLE_RECOMMENDATION_REPORTS}
        WHERE cve_id = %s 
          AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        ORDER BY created_at DESC
        LIMIT 1
        """
        cursor.execute(query, (cve_id,))
        result = cursor.fetchone()
        
        if result:
            # Format datetime
            if result.get('created_at'):
                if isinstance(result['created_at'], datetime):
                    result['created_at'] = result['created_at'].isoformat()
                elif isinstance(result['created_at'], str):
                    pass  # Already a string
            return result
        return None
    finally:
        cursor.close()
        connection.close()


def generate_report_with_ai(cve_id: str, ai_config: dict) -> str:
    """Generate recommendation report using AI.
    
    Args:
        cve_id: CVE ID to generate report for
        ai_config: AI configuration (apiKey, baseUrl, model, etc.)
        
    Returns:
        str: Generated report content
    """
    try:
        api_key = ai_config.get('apiKey')
        base_url = ai_config.get('baseUrl')
        model = ai_config.get('model', 'deepseek-chat')
        temperature = ai_config.get('temperature', 0.7)
        max_tokens = ai_config.get('maxTokens', 2000)
        system_prompt = ai_config.get('systemPrompt') or 'You are a security expert specializing in vulnerability analysis and recommendations.'
        
        if not api_key or not base_url:
            raise ValueError('AI configuration is required')
        
        # Initialize OpenAI client
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        prompt = f"Generate a recommendation report for CVE {cve_id}."
        
        # Call AI API
        logger.info(f"Generating report for CVE {cve_id} using AI")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False
        )
        
        report_content = response.choices[0].message.content
        logger.info(f"Successfully generated report for CVE {cve_id}")
        
        return report_content
        
    except Exception as e:
        logger.error(f"Error generating report with AI: {e}", exc_info=True)
        raise


def save_report(cve_id: str, report_content: str, ai_prompt: str = ''):
    """Save recommendation report to database.
    
    Args:
        cve_id: CVE ID
        report_content: Generated report content
        ai_prompt: AI prompt used (optional, can be empty)
        
    Returns:
        int: Report ID
    """
    connection = get_db_connection()
    if not connection:
        raise Exception("数据库连接失败")
    
    try:
        cursor = connection.cursor()
        
        query = f"""
        INSERT INTO {TABLE_RECOMMENDATION_REPORTS} (cve_id, report_content, ai_prompt)
        VALUES (%s, %s, %s)
        """
        cursor.execute(query, (cve_id, report_content, ai_prompt))
        connection.commit()
        
        report_id = cursor.lastrowid
        logger.info(f"Saved report for CVE {cve_id} with ID {report_id}")
        
        return report_id
    except Exception as e:
        logger.error(f"Error saving report: {e}", exc_info=True)
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def get_report_history(limit: int = 50, offset: int = 0):
    """Get report history.
    
    Args:
        limit: Maximum number of reports to return
        offset: Offset for pagination
        
    Returns:
        list: List of reports
    """
    connection = get_db_connection()
    if not connection:
        raise Exception("数据库连接失败")
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        query = f"""
        SELECT id, cve_id, report_content, ai_prompt, created_at, updated_at
        FROM {TABLE_RECOMMENDATION_REPORTS}
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """
        cursor.execute(query, (limit, offset))
        results = cursor.fetchall()
        
        # Format datetime fields
        for row in results:
            if row.get('created_at') and isinstance(row['created_at'], datetime):
                row['created_at'] = row['created_at'].isoformat()
            if row.get('updated_at') and isinstance(row['updated_at'], datetime):
                row['updated_at'] = row['updated_at'].isoformat()
        
        return results
    finally:
        cursor.close()
        connection.close()


def get_report_by_id(report_id: int):
    """Get a specific report by ID.
    
    Args:
        report_id: Report ID
        
    Returns:
        dict: Report data or None if not found
    """
    connection = get_db_connection()
    if not connection:
        raise Exception("数据库连接失败")
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        query = f"""
        SELECT id, cve_id, report_content, ai_prompt, created_at, updated_at
        FROM {TABLE_RECOMMENDATION_REPORTS}
        WHERE id = %s
        """
        cursor.execute(query, (report_id,))
        result = cursor.fetchone()
        
        if result:
            # Format datetime fields
            if result.get('created_at') and isinstance(result['created_at'], datetime):
                result['created_at'] = result['created_at'].isoformat()
            if result.get('updated_at') and isinstance(result['updated_at'], datetime):
                result['updated_at'] = result['updated_at'].isoformat()
        
        return result
    finally:
        cursor.close()
        connection.close()


def get_report_by_cve_id(cve_id: str):
    """Get the latest report for a CVE ID.
    
    Args:
        cve_id: CVE ID
        
    Returns:
        dict: Report data or None if not found
    """
    connection = get_db_connection()
    if not connection:
        raise Exception("数据库连接失败")
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        query = f"""
        SELECT id, cve_id, report_content, ai_prompt, created_at, updated_at
        FROM {TABLE_RECOMMENDATION_REPORTS}
        WHERE cve_id = %s
        ORDER BY created_at DESC
        LIMIT 1
        """
        cursor.execute(query, (cve_id,))
        result = cursor.fetchone()
        
        if result:
            # Format datetime fields
            if result.get('created_at') and isinstance(result['created_at'], datetime):
                result['created_at'] = result['created_at'].isoformat()
            if result.get('updated_at') and isinstance(result['updated_at'], datetime):
                result['updated_at'] = result['updated_at'].isoformat()
        
        return result
    finally:
        cursor.close()
        connection.close()
