import calendar
import datetime
import pytz

now = datetime.datetime.now(pytz.timezone('Asia/Singapore')).timetuple()

print(calendar.month(now[0], now[1]))