import abc
import bisect
import collections.abc
import dataclasses
import datetime
import itertools
import typing

import arrow
import ics

try:
    from ics import ContentLine
except ImportError:
    from ics.grammar.parse import ContentLine

review_modes = {}

Question = str
Response = str


class ReviewMode(abc.ABC):
    @abc.abstractmethod
    def get_question(self, card: "ModeCard") -> Question:
        ...

    @abc.abstractmethod
    def mark(self, response: Response, correct_response: Response) -> int:
        ...

    @abc.abstractmethod
    def rate_difficulty(self, card: "ModeCard") -> int:
        ...


@dataclasses.dataclass
class ModeCard:
    root_todo: ics.Todo
    mode_todo: ics.Todo
    mode: ReviewMode

    @classmethod
    def for_mode_todo(self, mode_todo: ics.Todo, card_deck: "CardDeck") -> "ModeCard":
        mode_name = mode_todo.name
        mode = review_modes[mode_name]
        root_uid = get_card_related_to(mode_todo)
        root_todo = card_deck.get_card_by_uid(root_uid)
        return ModeCard(
            root_todo=root_todo,
            mode_todo=mode_todo,
            mode=mode,
        )

    @property
    def raw_question(self) -> str:
        return self.root_todo.name

    @property
    def correct_response(self) -> Response:
        return self.root_todo.description

    @property
    def percent(self) -> int:
        return self.mode_todo.percent

    @property
    def due(self) -> datetime.datetime:
        return self.mode_todo.due

    @due.setter
    def due(self, due: datetime.datetime) -> None:
        self.mode_todo.due = due


@dataclasses.dataclass(frozen=True)
class Review:
    card: ModeCard
    started_at: datetime.datetime = dataclasses.field(
        default_factory=lambda: arrow.now().datetime
    )

    def get_question(self) -> Question:
        return self.card.mode.get_question(self.card)


@dataclasses.dataclass(frozen=True)
class ReviewResult:
    review: Review
    response: Response
    duration: datetime.timedelta
    mark: int

    @classmethod
    def respond(cls, review: Review, response: Response) -> "ReviewResult":
        mark = review.card.mode.mark(
            response, review.card.correct_response
        )
        return cls(
            review=review,
            response=response,
            duration=arrow.now().datetime - review.started_at,
            mark=mark,
        )

    def get_next_delay_time(self) -> datetime.timedelta:
        previous_delay = (
            self.review.started_at - self.review.card.due
            if self.review.card.due is not None else datetime.timedelta()
        )
        if self.response == self.review.card.correct_response:
            if previous_delay <= datetime.timedelta():
                return datetime.timedelta(minutes=1)
            return 2 * previous_delay
        else:
            if previous_delay <= datetime.timedelta(minutes=1):
                return datetime.timedelta()
            return datetime.timedelta(minutes=1)

    def update_due(self) -> None:
        delay_time = self.get_next_delay_time()
        self.review.card.due = self.review.started_at + delay_time


def get_card_related_to(card: ics.Todo) -> typing.Optional[str]:
    try:
        content_line: ContentLine = next(
            content_line for content_line in card.extra
            if content_line.name == "RELATED-TO"
        )
    except StopIteration:
        return None
    return content_line.value


def set_card_related_to(card: ics.Todo, card_uid: str) -> ContentLine:
    content_line = ContentLine.parse(f"RELATED-TO:{card_uid}")
    card.extra.append(content_line)
    return content_line


class FullAnswerReviewMode(ReviewMode):
    def get_question(self, card: ModeCard) -> Question:
        return card.raw_question

    def mark(self, response: Response, correct_response: Response) -> int:
        if response == correct_response:
            return 1
        return 0

    def rate_difficulty(self, card: ModeCard) -> int:
        return 100 - card.percent


review_modes["full-answer"] = FullAnswerReviewMode()


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

    def get_mode_of_card(self, card_uid: str, mode_name: str) -> ics.Todo:
        return next(
            card for card in self.calendar.todos
            if get_card_related_to(card) == card_uid
            and card.name == mode_name
        )

    def add_mode_to_card(
        self,
        card_uid: str,
        mode_name: str,
        due: datetime.datetime
    ) -> ics.Todo:
        mode_todo = ics.Todo(name=mode_name, due=due)
        set_card_related_to(mode_todo, card_uid)
        self.calendar.todos.add(mode_todo)
        return mode_todo

    def select_unlearned_cards(
        self,
        mode_names: typing.Container[str],
        max_count: typing.Optional[int] = None,
    ) -> collections.abc.Collection[ics.Todo]:
        root_cards = []  # Sorted by priority.
        referenced_card_uids = set()
        # Referenced cards are those were at least a mode is
        # already added.
        for card in self.calendar.todos:
            referenced_card_uid = get_card_related_to(card)
            if referenced_card_uid is None:
                bisect.insort(
                    root_cards,
                    (-(card.priority or 0), card),
                    # Adding the negative priority for sorting.
                )
            elif card.name in mode_names:
                referenced_card_uids.add(referenced_card_uid)
            # Ignoring mode cards of other (potentially unknown) modes.
        cards = (
            card for __, card in root_cards
            if card.uid not in referenced_card_uids
        )
        if max_count is None:
            return cards
        return itertools.islice(cards, max_count)

    def get_next_due_card(
        self,
        mode_names: typing.Container[str],
        due_until: typing.Optional[datetime.datetime] = None
    ) -> typing.Optional[ModeCard]:
        iter_cards = (
            card for card in self.calendar.todos
            if card.due is not None and card.name in mode_names
        )
        if due_until is not None:
            iter_cards = (
                card for card in iter_cards if card.due <= due_until
            )
        try:
            mode_todo = min(iter_cards, key=lambda card: card.due)
        except ValueError:
            return None
        return ModeCard.for_mode_todo(mode_todo, self)

    def iter_reviews(
        self,
        mode_names: typing.Optional[typing.Container[str]] = None
    ) -> typing.Iterator[Review]:
        if mode_names is None:
            mode_names = review_modes.keys()
        review_result = None
        while True:
            started_at = arrow.now().datetime
            card = self.get_next_due_card(
                mode_names=mode_names, due_until=started_at
            )
            if card is None:
                # Try adding new cards before reviewing cards that
                # aren’t due yet.
                next_batch = self.select_unlearned_cards(
                    mode_names=mode_names, max_count=10
                )
                for root_todo in next_batch:
                    for mode_name in mode_names:
                        self.add_mode_to_card(
                            card_uid=root_todo.uid,
                            mode_name=mode_name,
                            due=started_at,
                        )
                card = self.get_next_due_card(mode_names=mode_names)
                if card is None:
                    return
            review = Review(card=card)
            response = yield review_result, review
            if response is None:
                return
            review_result = ReviewResult.respond(review, response)
            review_result.update_due()
