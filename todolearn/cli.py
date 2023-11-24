from . import review


def interactive_review(card_deck: review.CardDeck) -> None:
    ireviews = card_deck.iter_reviews()
    try:
        __, review = next(ireviews)
    except StopIteration:
        return
    while True:
        question = review.get_question()
        print(f"Front: {question}")
        response = input(f"Back ([q]uit): ")
        if response == "q":
            return
        review_result, review = ireviews.send(response)
        last_card = review_result.review.card
        suffix = (
            "" if review_result.mark == 1
            else f" (Correct: {last_card.correct_response})"
        )
        if review_result.mark >= 0.8:
            print(f"🎉{suffix}")
        else:
            print(f"❌{suffix}")
