import dataclasses
import datetime
import typing

import arrow
import ics

example_dict = {
    "card": "die Karte",
    "learn": "lernen",
    "correct": "richtig",
}


@dataclasses.dataclass(frozen=True)
class Review:
    card: ics.Todo
    response: str
    reviewd_at: datetime.datetime

    @property
    def correct_response(self) -> str:
        return self.card.description

    def get_delay_time(self) -> datetime.timedelta:
        previous_delay = (
            self.reviewd_at - self.card.due
            if self.card.due is not None else datetime.timedelta()
        )
        if self.response == self.correct_response:
            if previous_delay <= datetime.timedelta():
                return datetime.timedelta(minutes=1)
            return 2 * previous_delay
        else:
            if previous_delay <= datetime.timedelta(minutes=1):
                return datetime.timedelta()
            return datetime.timedelta(minutes=1)

    def update_due(self) -> None:
        delay_time = self.get_delay_time()
        self.card.due = self.reviewd_at + delay_time


class CardDeck:
    def __init__(self, calendar: typing.Optional[ics.Calendar] = None) -> None:
        if calendar is None:
            calendar = ics.Calendar()
        self.calendar = calendar

    def get_card_by_uid(self, card_uid: str) -> ics.Todo:
        return next(
            card for card in self.calendar.todos
            if card.uid == card_uid
        )

    def get_next_due_card(
        self,
        prefer_new_cards_until: datetime.datetime,
    ) -> ics.Todo:
        try:
            return min(
                (
                    card for card in self.calendar.todos
                    if card.due is not None
                    and card.due < prefer_new_cards_until
                ),
                key=lambda card: card.due,
            )
        except ValueError:
            pass
        try:
            return next(
                card for card in self.calendar.todos if card.due is None
            )
        except StopIteration:
            return min(
                (card for card in self.calendar.todos if card.due is not None),
                key=lambda card: card.due,
            )


def make_examples():
    todos = [
        ics.Todo(name=front, description=back)
        for front, back in example_dict.items()
    ]
    return ics.Calendar(todos=todos)


def interactive_review(card_deck: CardDeck) -> None:
    while True:
        reviewed_at = arrow.now().datetime
        card = card_deck.get_next_due_card(reviewed_at)
        print(f"Front: {card.name}")
        response = input("Back ([q]uit): ")
        if response == "q":
            break
        review = Review(card, response, reviewed_at)
        if review.response == review.correct_response:
            print("🎉")
        else:
            print(f"❌ (Correct: {review.correct_response})")
        review.update_due()


if __name__ == "__main__":
    c = make_examples()
    interactive_review(CardDeck(c))
    out = c.serialize()
    print(out)
