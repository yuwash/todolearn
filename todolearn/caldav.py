import dataclasses

import caldav
import ics


@dataclasses.dataclass
class CaldavClient:
    url: str
    username: str
    password: str
    calendar_url: str

    def load(self) -> ics.Calendar:
        with caldav.DAVClient(url=self.url, username=self.username, password=self.password) as client:
            calendar = client.calendar(url=self.calendar_url)
            davtodos = calendar.todos()
        calendars = (ics.Calendar(imports=d.data) for d in davtodos)
        aggregated_calendar = next(calendars)
        for calendar in calendars:
            aggregated_calendar.todos.update(calendar.todos)
        return aggregated_calendar

    def save(self, calendar: ics.Calendar) -> None:
        avoid_overwrite = False
        with caldav.DAVClient(url=self.url, username=self.username, password=self.password) as client:
            davcalendar = client.calendar(url=self.calendar_url)
            for todo in calendar.todos:
                self._save_todo(davcalendar, todo)

    def _save_todo(self, davcalendar: caldav.Calendar, todo: ics.Todo) -> None:
        serialized = todo.serialize()
        existing_todo = davcalendar.todo_by_uid(todo.uid)
        if existing_todo is None:
            davcalendar.add_todo(serialized)
            return
        existing_todo_as_ics = next(iter(
            ics.Calendar(imports=existing_todo.data).todos
        ))
        if serialized == existing_todo_as_ics.serialize():
            # Hacky but only way to check for equality.
            # The todo instance themselves are equal regardless of content.
            # Comparing the temp_todo from below would always fail as some
            # header lines are missing.
            return
        if not avoid_overwrite:
            # Very hacky way to create data in python-caldav format.
            try:
                save_ = caldav.Todo.save
                caldav.Todo.save = lambda *args, **kwargs: None
                temp_todo = davcalendar.add_todo(serialized)
            finally:
                caldav.Todo.save = save_
            existing_todo.data = temp_todo.data
            try:
                existing_todo.save(no_create=True)
                # Never worked with any server, so the usefulness of this
                # whole block is questionable.
            except caldav.lib.error.PutError:
                avoid_overwrite = True
            else:
                return
        existing_todo.delete()
        davcalendar.add_todo(serialized)
