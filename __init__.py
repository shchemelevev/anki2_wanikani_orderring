from aqt.qt import *

from anki.cards import Card
from aqt.utils import tooltip
from anki.consts import QUEUE_TYPE_SUSPENDED, QUEUE_TYPE_REV
from aqt.reviewer import Reviewer
from anki.consts import BUTTON_ONE
from anki.hooks import wrap, schedv2_did_answer_review_card
from aqt.reviewer import Reviewer

from .utils import (
    mark_learned_radicals,
    mark_allowed_to_learn_kanji, mark_learned_kanji, mark_allowed_to_learn_vocabulary,
    split_components
)

from aqt import mw
from aqt.deckbrowser import DeckBrowser

from aqt import AnkiQt, gui_hooks

from .utils import log

def handler():
    if os.path.exists(os.path.join(os.path.dirname(__file__), "run")):
        os.unlink(os.path.join(os.path.dirname(__file__), "run"))
        with open(os.path.join(os.path.dirname(__file__), "code.py"), 'r') as f:
            exec('\n'.join(f.readlines()))

mw.progress.timer(500, handler, True)

CARD_TYPE_RADICAL = 'radical'
CARD_TYPE_KANJI = 'kanji'
CARD_TYPE_VOCAB = 'vocabulary'

def get_card_type(card: Card):
    tags = [t.lower() for t in card.note().tags]
    if CARD_TYPE_KANJI in tags:
        return CARD_TYPE_KANJI
    if CARD_TYPE_RADICAL in tags:
        return CARD_TYPE_RADICAL
    return CARD_TYPE_VOCAB

def suspend_with_log(card: Card, due_card:Card, due_components):
    if card.id == due_card:
        return
    due_card_type = get_card_type(due_card)
    if due_card.queue == QUEUE_TYPE_REV:
        if mw.col.sched.today == card.due:
            mw.col.sched.suspendCards([due_card.id])
            mw.col.flush()
            msg = "%s %s with same component suspended. components: %s, current_card: %s, due_card_id: %s" % (
                due_card_type, due_card.note().fields[0], due_components, card.note().fields[0], due_card.id
            )
            log(msg)
            tooltip(msg)
            mw.reset()

def get_wanikani_related_deck_ids():
    WK_DECK_NAME = 'Wanikani Ultimate 2: Electric Boogaloo'
    result = [mw.col.decks.nameMap()[WK_DECK_NAME]['id']]
    for deck_name, deck_info in mw.col.decks.nameMap().items():
        if WK_DECK_NAME in str(deck_info.get('terms', [])):
            result.append(deck_info['id'])
    log("WK related deck ids %s", result)
    return result


def onAnswer(reviewer, card: Card, ease):
    log('card.did=%s', card.did)
    if card.did not in get_wanikani_related_deck_ids():
        return

    card_type = get_card_type(card)

    log("card: %s, ease: %s, type: %s", card, ease, card_type)
    components = split_components(card.note().fields[2])
    components_types = split_components(card.note().fields[4])
    c_types = dict(zip(components, components_types))
    # skip vocabulary meaning disabling
    if card_type == CARD_TYPE_VOCAB and card.flags == 2:
        return

    tags = card.note().tags
    # suspend due cards with same components
    if card_type in (CARD_TYPE_VOCAB, CARD_TYPE_KANJI):
        log("component types: %s, c_types: %s", components_types, c_types)
        card_id_list = mw.col.find_cards('''"deck:Wanikani Ultimate 2: Electric Boogaloo" is:due flag:%s''' % (card.flags,))
        for card_id in card_id_list:
            due_card = mw.col.getCard(card_id)
            due_components = split_components(due_card.note().fields[2])
            due_components_types = split_components(due_card.note().fields[4])
            due_c_types = dict(zip(due_components, due_components_types))
            due_card_type = get_card_type(due_card)
            if card_type == CARD_TYPE_VOCAB:
                #log('components %s, due_components: %s, same_kanji: %s', components, due_components, same_kanji_components)
                # disable vocab reading with same kanji
                same_kanji_components = [
                    c for c in components if c in due_components and c_types[c].lower() == "kanji" and due_c_types[c] == 'kanji'
                ]
                if same_kanji_components and due_card_type == CARD_TYPE_VOCAB:
                    suspend_with_log(card, due_card, due_components)
                # disable kanji reading or meaning(depending on curren card) with same kanji
                if due_card.note().fields[0].strip() in components and due_card_type == CARD_TYPE_KANJI:
                    suspend_with_log(card, due_card, due_components)

            if card_type == CARD_TYPE_KANJI:
                # log('kanji %s, components: %s', kanji, due_components)
                if due_card_type == CARD_TYPE_VOCAB:
                    # we suspend vocab meaning consisting only from this component
                    kanji = card.note().fields[0].strip()
                    if kanji in due_components and due_c_types[kanji] == CARD_TYPE_VOCAB and due_card.flags == 2 and len(due_components) == 1:
                        # we disable vocabulary only same READING kanji
                        suspend_with_log(card, due_card, due_components)
                    # suspend any vocab reading with this component
                    if kanji in due_components and due_c_types[kanji] == CARD_TYPE_VOCAB and due_card.flags == 1:
                        suspend_with_log(card, due_card, due_components)

        # if ease == BUTTON_ONE:
        #     pass
        # else:


gui_hooks.reviewer_did_answer_card.append(onAnswer)


def _handleFilteredDeckButtons(self, url):
    if url in ["recalculateWanikani"]:
        mark_learned_radicals(mw)
        allowed_to_learn_kanji = mark_allowed_to_learn_kanji(mw)
        mark_learned_kanji(mw)
        allowed_to_learn_vocab = mark_allowed_to_learn_vocabulary(mw)
        card_id_list = [c_id for c_id in mw.col.find_cards('''"deck:Wanikani Ultimate 2: Electric Boogaloo" is:suspended''')]
        mw.col.sched.unsuspendCards(card_id_list)
        mw.col.flush()
        mw.reset()
        tooltip("Unsuspended: %s"%(len(card_id_list), ))

def _addButtons(self):
    # TODO rebuildDyn and emptyDyn are old: see scheduler/legacy.py
    # check if the new methods just have a new name or more
    drawLinks = [
        ["", "recalculateWanikani", "WK recalc"],
    ]
    # don't duplicate buttons every click
    if drawLinks[0] not in self.drawLinks:
        self.drawLinks += drawLinks

DeckBrowser._drawButtons = wrap(DeckBrowser._drawButtons, _addButtons, "before")
DeckBrowser._linkHandler = wrap(DeckBrowser._linkHandler, _handleFilteredDeckButtons, "after")