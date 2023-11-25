import getpass
import os

import caldav
import ics
from . import caldav, cli, review

example_dict = {
    "card": "die Karte",
    "learn": "lernen",
    "correct": "richtig",
}


def make_examples():
    return {
        ics.Todo(name=front, description=back)
        for front, back in example_dict.items()
    }


if __name__ == "__main__":
    url = os.environ.get("TODOLEARN_CALDAV_URL")
    if url is not None:
        username = os.environ["TODOLEARN_CALDAV_USERNAME"]
        calendar_url = os.environ["TODOLEARN_CALDAV_CALENDAR_URL"]
        password = getpass.getpass("Password: ")
        cal = caldav.load_from_caldav(
            dav_url=url,
            username=username,
            password=password,
            calendar_url=calendar_url,
        )
    else:
        example_todos = make_examples()
        cal = ics.Calendar(todos=example_todos)
    deck = review.CardDeck(cal)
    cli.interactive_review(deck)
    out = cal.serialize()
    print(out)
