import caldav
import ics


def load_from_caldav(
    dav_url: str,
    username: str,
    password: str,
    calendar_url: str,
) -> ics.Calendar:
    with caldav.DAVClient(url=dav_url, username=username, password=password) as client:
        calendar = client.calendar(url=calendar_url)
        davtodos = calendar.todos()
    calendars = (ics.Calendar(imports=d.data) for d in davtodos)
    aggregated_calendar = next(calendars)
    for calendar in calendars:
        aggregated_calendar.todos.update(calendar.todos)
    return aggregated_calendar


