import os
from aqt import mw
from anki.consts import QUEUE_TYPE_LRN, QUEUE_TYPE_REV, QUEUE_TYPE_NEW
from anki.cards import Card

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

def is_learned(backend, card_id):
    #check that the card is not new or learning
    # card = mw.col.getCard(card_id)
    card_stats = backend.card_stats(card_id)
    LOOKBACK = 4
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

def mark_learned_radicals(mw):
    notes = mw.col.find_notes('"deck:Wanikani Ultimate 2: Electric Boogaloo" tag:Radical')
    log("Number of radicals: %s", len(notes))
    for note_id in notes:
        note = mw.col.getNote(note_id)
        card_id = note.cards()[0].id
        if is_learned(mw.col.backend, card_id):
            #log('learned %s', note.fields[0])
            if 'radical_learned' not in note.tags:
                note.addTag('radical_learned')
                note.flush()
        else:
            if 'radical_learned' in note.tags:
                note.delTag('radical_learned')
                note.flush()


def mark_allowed_to_learn_kanji(mw):
    all_radicals = []
    notes = mw.col.find_notes('''"deck:Wanikani Ultimate 2: Electric Boogaloo" tag:Radical''')
    for note_id in notes:
        note = mw.col.getNote(note_id)
        all_radicals.append(note.fields[0])
    notes = mw.col.find_notes('''"deck:Wanikani Ultimate 2: Electric Boogaloo" tag:Kanji''')
    for note_id in notes:
        note = mw.col.getNote(note_id)
        all_radicals.append(note.fields[0])

    notes = mw.col.find_notes('''"deck:Wanikani Ultimate 2: Electric Boogaloo" tag:radical_learned''')
    log("Number of learned radicals: %s", len(notes))
    learned_radicals = []
    for note_id in notes:
        note = mw.col.getNote(note_id)
        # log("tags: %s", note.tags)
        learned_radicals.append(note.fields[0])
    log("Number of learned radicals: %s", len(learned_radicals))

    notes = mw.col.find_notes('''"deck:Wanikani Ultimate 2: Electric Boogaloo" tag:Kanji tag:KANJI_READING_LEARNED''')
    for note_id in notes:
        note = mw.col.getNote(note_id)
        learned_radicals.append(note.fields[0].strip())
    log("Number of learned components: %s", len(learned_radicals))

    notes = mw.col.find_notes('''"deck:Wanikani Ultimate 2: Electric Boogaloo" tag:Kanji''')
    log("Number of kanji: %s", len(notes))
    allowed_to_learn = 0
    tag = 'kanji_allowed_to_learn'
    for note_id in notes:
        note = mw.col.getNote(note_id)
        components = split_components(note.fields[2])
        if ( len([c for c in components if c in learned_radicals]) == len(components)
            or any([c for c in components if c not in all_radicals])
        ):
            allowed_to_learn += 1
            if tag not in note.tags:
                note.addTag(tag)
                note.flush()
                continue
            #log("Allowed to %s learn: %s", tag, note.fields[0])
        else:
            learned_components = [c for c in components if c in learned_radicals]
            # if len(learned_components) > 0:
            #     log("Not allowed %s, comps: %s, learned: %s", note.fields[0], components, learned_components)
            if tag in note.tags:
                note.delTag(tag)
                note.flush()
                continue
    log("Allowed to learn kanji(reading+meaning, or x2): %s", allowed_to_learn*2)
    return allowed_to_learn*2


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


def mark_allowed_to_learn_vocabulary(mw):
    allowed_to_learn_dict = {}
    for kanji_tag in [KANJI_MEANING_LEARNED, KANJI_READING_LEARNED]:
        allowed_to_learn = 0
        notes = mw.col.find_notes('''"deck:Wanikani Ultimate 2: Electric Boogaloo" tag:%s''' % kanji_tag)
        log("Number of %s kanji: %s", kanji_tag, len(notes))
        learned_kanji = []
        for note_id in notes:
            note = mw.col.getNote(note_id)
            # log("tags: %s", note.tags)
            learned_kanji.append(note.fields[0])

        card_id_list = mw.col.find_cards('''"deck:Wanikani Ultimate 2: Electric Boogaloo" tag:Vocabulary''')
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
                #log("Allowed to %s learn: %s", kanji_tag, card.note().fields[0])
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