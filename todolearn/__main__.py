import ics
from . import cli, review

example_dict = {
    "card": "die Karte",
    "learn": "lernen",
    "correct": "richtig",
}


def make_examples():
    todos = [
        ics.Todo(name=front, description=back)
        for front, back in example_dict.items()
    ]
    return ics.Calendar(todos=todos)


if __name__ == "__main__":
    cal = make_examples()
    deck = review.CardDeck(cal)
    cli.interactive_review(deck)
    out = cal.serialize()
    print(out)
