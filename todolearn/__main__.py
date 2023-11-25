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
    client = None
    if url is not None:
        password = getpass.getpass("Password: ")
        client = caldav.CaldavClient(
            url=url,
            username=os.environ["TODOLEARN_CALDAV_USERNAME"],
            calendar_url=os.environ["TODOLEARN_CALDAV_CALENDAR_URL"],
            password=password,
        )
        cal = client.load()
    else:
        example_todos = make_examples()
        cal = ics.Calendar(todos=example_todos)
    deck = review.CardDeck(cal)
    cli.interactive_review(deck)
    if client is not None:
        client.save(cal)
    out = cal.serialize()
    print(out)
