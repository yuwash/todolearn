# todolearn
Experimental project using iCalender `VTODO`s via
[ics](http://pypi.python.org/pypi/ics) for learning (flashcards).

## Idea

Flashcards are like todos. They are to be reviewed before a given due
date. There are different review modes with different difficulties and
purposes. Therefore it should be possible to enable modes for each card
individually. There’s also a due date for each mode. VTODOs allow
representing subtasks (as represented in NextCloud Tasks for example).
While there isn’t any established format for flashcards used by more
than one application other than a simple CSV containing only front and
back side, VTODO is an excellent standard that has all necessary
fields for representing important metadata of flashcards.
You can use any existing CalDAV client to create VTODOs that can be
used in this application.

## How VTODOs are used

Basic data of flash cards are stored in “root cards”, i.e. those
without a `RELATED-TO` value.
Data on progress in each review mode is stored in “mode cards”,
i.e. those with a `RELATED-TO` value referring to the root card.
Root cards without a corresponding mode card are considered
“unlearned” and they can be “staged” by adding mode cards.

| Field | Usage in root cards | Usage in mode cards |
|--|--|--|
| SUMMARY (ics.Todo.name) | Front side of the flashcard | Mode name |
| DESCRIPTION | Back side of the flashcard | – |
| DUE | – | Optimal next review date of the flashcard for the mode |
| PERCENT-COMPLETE (ics.Todo.percent) | – | Progress of the flashcard for the mode |
| PRIORITY | Priority of the flashcard for the mode; Considered when “staging” unlearned cards | – |
| RELATED-TO | – | Root card UID |
| UID | To be referenced in mode cards | Filled but not used directly |

## What’s already there

* Fetch flashcards from WebDAV
* Supporting VTODO fields as described above
* Rudimentary CLI for learning

## Next steps

* Push changes to WebDAV
* Enable interactively modifying priority
* Update percent on review
* Enable more session options like
  * Only learn learned resp. unlearned cards
  * Choose whether to consider cards not yet due (esp. when limited to
    learned cards)
* Add more review modes
* Handle difficulties of different modes when choosing the card to
  review next
