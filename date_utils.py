from datetime import datetime, timedelta, timezone
from dateutil import parser
import logging

logger = logging.getLogger(__name__)

def parse_date_flexible(date_string):
    """Parse date string with multiple format support"""
    if not date_string:
        return None

    try:
        parsed = parser.parse(date_string)
        # If no timezone info, assume UTC
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed
    except Exception as e:
        logger.warning(f"Could not parse date: {date_string}, error: {e}")
        return None


def is_from_last_24_hours(published_date, reference_time=None):
    """Check if article was published in the last 24 hours from reference time"""
    if not published_date:
        return False

    try:
        if reference_time is None:
            reference_time = datetime.now(timezone.utc)
        if isinstance(published_date, str):
            published_date = parse_date_flexible(published_date)
        if not published_date:
            return False

        if published_date.tzinfo:
            published_utc = published_date.astimezone(timezone.utc)
        else:
            published_utc = published_date.replace(tzinfo=timezone.utc)

        if reference_time.tzinfo:
            reference_utc = reference_time.astimezone(timezone.utc)
        else:
            reference_utc = reference_time.replace(tzinfo=timezone.utc)

        time_diff = reference_utc - published_utc
        return time_diff <= timedelta(hours=24) and time_diff >= timedelta(0)

    except Exception as e:
        logger.error(f"Error checking date: {e}")
        return False