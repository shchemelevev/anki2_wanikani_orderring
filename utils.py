from functools import total_ordering
import os
import datetime
from aqt import mw
from aqt.main import AnkiQt  # isort:skip
from anki.consts import QUEUE_TYPE_LRN, QUEUE_TYPE_REV, QUEUE_TYPE_NEW
from anki.cards import Card
from werkzeug.wrappers.request import get_input_stream

KANJI_MEANING_ALLOW = "kanji_meaning_allow"
KANJI_READING_ALLOW = "kanji_reading_allow"
KANJI_READING_LEARNED = 'kanji_reading_learned'
KANJI_MEANING_LEARNED = 'kanji_meaning_learned'
VOCAB_READING_ALLOW = 'vocab_reading_allow'
VOCAB_MEANING_ALLOW = 'vocab_meaning_allow'

def split_components(components):
    return [c.strip() for c in components.split(',')]

def get_template_name_from_tag(tag):
    return {
        KANJI_READING_LEARNED: 'Reading',
        KANJI_MEANING_LEARNED: 'Meaning'
    }[tag]

def kanji_tag_to_vocab_tag(tag):
    return {
        KANJI_READING_LEARNED: VOCAB_READING_ALLOW,
        KANJI_MEANING_LEARNED: VOCAB_MEANING_ALLOW
    }[tag]


def log(fmtstr, *args):
    with open(os.path.join(os.path.dirname(__file__), "log"), 'w+', encoding='utf-8') as f:
        f.write(fmtstr % args)
        f.write("\n")
    # import logging
    # logger = logging.getLogger(__name__)
    # logger.debug(fmtstr % args)

def output_card(card):
    characters, object_type, components, component_names, component_types, meaning, f7, f8, f9, f10, f11, f12, f13, f14, f15, f16, f17, f18, f19, f20, f21, f22, f23,f24, f25, f26, f27, f28 = card.note().fields
    log("Char: %s; type: %s; meaning: %s; components: %s; comp_names: %s; comp_types: %s",
        characters,
        object_type,
        meaning,
        split_components(components),
        component_names,
        component_types,
        )

def is_learned(backend, card_id, lookback_overwrite=4):
    #check that the card is not new or learning
    # card = mw.col.getCard(card_id)
    card_stats = backend.card_stats(card_id)
    LOOKBACK = lookback_overwrite
    last_reviews = card_stats.revlog[:LOOKBACK]
    # new card
    if len(last_reviews) == 0:
        return False
    if len(last_reviews) < LOOKBACK:
        return False
    for review in last_reviews:
        # learning doesn't count, review_kind for all learning responses are 0
        if review.review_kind == 0:
            return False
        if review.review_kind != 1:
            return False
        if review.button_chosen == 1:
            return False
    # TODO: add interval check
    # TODO: possibly add ease check
    return True


def is_daily_card(backend, card_id):
    #check that the card is not new or learning
    card_stats = backend.card_stats(card_id)
    first_review = card_stats.first_review
    # if first_review == 0:
    #     return True

    # last_reviews = card_stats.revlog
    # count = 0
    # for review in last_reviews:
    #     # learning doesn't count, review_kind for all learning responses are 0
    #     if review.review_kind:
    #         count += 1
    # if count < 3:
    #     return True

    # last_reviews = card_stats.revlog
    return len(card_stats.revlog)>=1 and card_stats.interval < 30

    #
    # now = datetime.datetime.now()
    # first_review_date = datetime.datetime.fromtimestamp(first_review)
    # td = now - first_review_date
    # return td.days < 45


def mark_learned_radicals(mw):
    notes = mw.col.find_notes('"deck:Wanikani Ultimate 2: Electric Boogaloo" tag:Radical')
    log("Number of radicals: %s", len(notes))
    for note_id in notes:
        note = mw.col.getNote(note_id)
        card_id = note.cards()[0].id
        if is_learned(mw.col.backend, card_id, lookback_overwrite=2):
            #log('learned %s', note.fields[0])
            if 'radical_learned' not in note.tags:
                note.addTag('radical_learned')
                note.flush()
        else:
            if 'radical_learned' in note.tags:
                note.delTag('radical_learned')
                note.flush()

def _get_notes_and_items(mw, query: str):
    all_items = []
    notes = mw.col.find_notes('''"deck:Wanikani Ultimate 2: Electric Boogaloo" %s ''' % query)
    for note_id in notes:
        note = mw.col.getNote(note_id)
        all_items.append(note.fields[0])
    return notes, all_items


def mark_allowed_to_learn_kanji(mw):
    # Kanji component can contain not only radicals but also other kanji
    # We need to learn kanji meaning first and then we learn reading
    _, only_radicals = _get_notes_and_items(mw, "tag:Radical")
    all_radicals = []
    all_radicals.extend(only_radicals)

    _, only_kanji = _get_notes_and_items(mw, "tag:Kanji")
    all_radicals.append(only_kanji)

    _, learned_radicals = _get_notes_and_items(mw, "tag:radical_learned")
    log("Number of learned radicals: %s", len(learned_radicals))
    tag_transform = {
        KANJI_READING_LEARNED: KANJI_READING_ALLOW,
        KANJI_MEANING_LEARNED: KANJI_MEANING_ALLOW
    }

    total_allowed_to_learn = 0
    for kanji_tag in [KANJI_MEANING_LEARNED, KANJI_READING_LEARNED]:
        allowed_to_learn = 0
        _, learned_kanji = _get_notes_and_items(mw, "tag:%s" % kanji_tag)
        learned_combined = []
        learned_combined.extend(learned_radicals)
        learned_combined.extend(learned_kanji)
        log("Number of learned components: %s", len(learned_combined))

        notes, _ = _get_notes_and_items(mw, "tag:Kanji")
        log("Number of kanji: %s", len(notes))
        tag = tag_transform[kanji_tag]
        for note_id in notes:
            note = mw.col.getNote(note_id)
            components = split_components(note.fields[2])
            if any([c for c in components if c not in all_radicals]):
                log("component not found for %s", components)
            if ( len([c for c in components if c in learned_radicals]) == len(components)
                or any([c for c in components if c not in all_radicals])
            ):
                allowed_to_learn += 1
                total_allowed_to_learn += 1
                if tag not in note.tags:
                    note.addTag(tag)
                    note.flush()
                # for card in note.cards():
                #log("Allowed to %s learn: %s", tag, note.fields[0])
            else:
                #learned_components = [c for c in components if c in learned_radicals]
                # if len(learned_components) > 0:
                #     log("Not allowed %s, comps: %s, learned: %s", note.fields[0], components, learned_components)
                if tag in note.tags:
                    note.delTag(tag)
                    note.flush()
                    continue
        log("Allowed to learn kanji(%s): %s", tag, allowed_to_learn)
    return total_allowed_to_learn


def mark_learned_kanji(mw):
    notes = mw.col.find_notes('"deck:Wanikani Ultimate 2: Electric Boogaloo" tag:Kanji')
    log("Number of kanji: %s", len(notes))
    learned = 0
    for note_id in notes:
        note = mw.col.getNote(note_id)
        for card in note.cards():
            ltag_name = KANJI_READING_LEARNED if card.template()['name'] == 'Reading' else KANJI_MEANING_LEARNED

            card_id = card.id
            if is_learned(mw.col.backend, card_id):
                learned += 1
                if ltag_name not in note.tags:
                    note.addTag(ltag_name)
                    note.flush()
            else:
                if ltag_name in note.tags:
                    note.delTag(ltag_name)
                    note.flush()
    log("Kanji learned: %s", learned)


def mark_daily_cards(mw):
    notes = mw.col.find_notes('"deck:Wanikani Ultimate 2: Electric Boogaloo"')
    log("Number of items: %s", len(notes))
    daily_count = 0
    ltag_name = "WANIKANI_DAILY"
    total = 0

    main_did = int(mw.col.decks.id_for_name('Wanikani Ultimate 2: Electric Boogaloo'))
    radical_did = int(mw.col.decks.id_for_name('WK _radical'))
    kanji_meaning_did = int(mw.col.decks.id_for_name('WK kanji meaning'))
    kanji_reading_did = int(mw.col.decks.id_for_name('WK kanji reading'))
    meaning_did = int(mw.col.decks.id_for_name('WK meaning'))
    reading_did = int(mw.col.decks.id_for_name('WK reading'))

    # move all cards to the main deck
    for note_id in notes:
        note = mw.col.getNote(note_id)
        for card in note.cards():
            card.did = main_did
            card.flush()

    mw.col.flush()
    mw.reset()

    card_id_list = mw.col.find_cards('"deck:Wanikani Ultimate 2: Electric Boogaloo" is:due')

    for card_id in card_id_list:
        card = mw.col.getCard(card_id)
        total += 1
        log('card_id=%s due=%d odue=%s', card.id, card.due, card.odue)
        # output_card(card)
        card_id = card.id
        # card_stats = mw.col.backend.card_stats(card_id)
        # log("stats.interval=%s", card_stats.interval)
        # log("card_stats=%s", [i for i in card_stats.revlog])
        if is_daily_card(mw.col.backend, card_id):
            found_did = main_did
            if "Radical" in card.note().tags:
                found_did = radical_did
            elif "Kanji" in card.note().tags:
                if card.template()['name'] == 'Reading':
                    found_did = kanji_reading_did
                else:
                    found_did = kanji_meaning_did
            elif "Vocabulary":
                if card.template()['name'] == 'Reading':
                    found_did = reading_did
                else:
                    found_did = meaning_did 

            card.odid = main_did
            card.did = found_did
            card.flush()
            daily_count += 1
            # if ltag_name not in note.tags:
            #     note.addTag(ltag_name)
            #     note.flush()
        # else:
        #     if ltag_name in note.tags:
        #         note.delTag(ltag_name)
        #         note.flush()

    log("Daily cards: %s", daily_count)


def mark_allowed_to_learn_vocabulary(mw):
    allowed_to_learn_dict = {}
    kanji_tag_to_flag = {
        KANJI_READING_LEARNED: 1,
        KANJI_MEANING_LEARNED: 2
    }
    for kanji_tag in [KANJI_MEANING_LEARNED, KANJI_READING_LEARNED]:
        allowed_to_learn = 0
        notes = mw.col.find_notes('''"deck:Wanikani Ultimate 2: Electric Boogaloo" tag:%s''' % kanji_tag)
        log("Number of %s kanji: %s", kanji_tag, len(notes))
        learned_kanji = []
        for note_id in notes:
            note = mw.col.getNote(note_id)
            # log("tags: %s", note.tags)
            learned_kanji.append(note.fields[0])

        card_id_list = mw.col.find_cards('''"deck:Wanikani Ultimate 2: Electric Boogaloo" tag:Vocabulary flag:%s''' % kanji_tag_to_flag[kanji_tag])
        log("Number of vocabulary items: %s", len(card_id_list))
        for card_id in card_id_list:
            card = mw.col.getCard(card_id)
            components = split_components(card.note().fields[2])
            note = card.note()
            tag = kanji_tag_to_vocab_tag(kanji_tag)

            if all([c in learned_kanji for c in components]):
                allowed_to_learn += 1
                if tag not in card.note().tags:
                    note.addTag(tag)
                    note.flush()
                log("Allowed to %s learn: %s flag %s", tag, card.note().fields[0], card.flags)
            else:
                if tag in note.tags:
                    note.delTag(tag)
                    note.flush()
            allowed_to_learn_dict[kanji_tag] = allowed_to_learn
        log("Allowed to learn %s vocab: %s", kanji_tag, allowed_to_learn)
    return allowed_to_learn_dict

def set_flags(mw):
    card_id_list = mw.col.find_cards('''"deck:Wanikani Ultimate 2: Electric Boogaloo" tag:Vocabulary''')
    for card_id in card_id_list:
        card = mw.col.getCard(card_id)
        flag = 1 if card.template()['name'] == 'Reading' else 2
        card.setUserFlag(flag)
        card.flush()
    card_id_list = mw.col.find_cards('''"deck:Wanikani Ultimate 2: Electric Boogaloo" tag:Kanji''')
    log('Number of kanji cards to set flags: %s', len(card_id_list))
    flags_counters = {1: 0, 2:0}
    for card_id in card_id_list:
        card = mw.col.getCard(card_id)
        flag = 1 if card.template()['name'] == 'Reading' else 2
        card.setUserFlag(flag)
        card.flush()
        flags_counters[flag] += 1

    log('all flags set %s', flags_counters)
