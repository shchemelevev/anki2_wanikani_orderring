import os
import logging

from aqt import mw
from aqt.qt import *

from .utils import (
    output_card, log, split_components, is_learned, mark_learned_radicals,
    mark_allowed_to_learn_kanji, mark_learned_kanji, mark_allowed_to_learn_vocabulary,
    set_flags, mark_daily_cards, check_that_every_vocab_has_kanji_components
)

import anki.decks

logging.basicConfig(filename=os.path.join(os.path.dirname(__file__), "log"),
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    encoding='utf-8',
                    level=logging.DEBUG)



log("START %s START", "*"*50)
# wanikani_col = mw.col.find_cards('"deck:Wanikani Ultimate 2: Electric Boogaloo"')
# cardCount = len(mw.col.find_cards('"deck:Wanikani Ultimate 2: Electric Boogaloo"'))
# learned = 0
# unknown = 0
# for card_id in wanikani_col:
#     if is_learned(mw.col.backend, card_id):
#         learned += 1
#     else:
#         unknown += 1
#
# log("learned: %s, unknown: %s", learned, unknown)

try:

    if mw and mw.col:
        check_that_every_vocab_has_kanji_components(mw)
        # for i in range(100):
        #     card_id = mw.col.find_cards('"deck:Wanikani Ultimate 2: Electric Boogaloo"')[i]
        #     card = mw.col.getCard(card_id)

        #     characters, object_type, components, component_names, component_types, meaning, f7, f8, f9, f10, f11, f12, f13, f14, f15, f16, f17, f18, f19, f20, f21, f22, f23,f24, f25, f26, f27, f28 = card.note().fields

        #     log("Char: %s; type: %s; meaning: %s; components: %s; comp_names: %s; comp_types: %s; is_learned: %s",
        #         characters,
        #         object_type,
        #         meaning,
        #         split_components(components),
        #         component_names,
        #         component_types,
        #         is_learned(mw.col.backend, card_id)
        #     )

        # card_id = wanikani_col[23]
        # notes = mw.col.find_notes('"deck:Wanikani Ultimate 2: Electric Boogaloo" tag:Radical')
        # log("notes count: %s", len(notes))
        # note_id = notes[0]
        # mw.col.getNote(note_id)

        # card = mw.col.getCard(5639)
        # # card_stats = mw.col.backend.card_stats(5196)
        # card.did = int(mw.col.decks.id_for_name('WK_daily'))
        # card.flush()
        # log("card_did=%s", card.did)
        #
        # mw.col.flush()
        # mw.reset()
        # mw.col.flush()
        # output_card(card)
        # log("card_stats%s", card_stats)
        # log("reps: %s lapses: %s due: %s", card.reps, card.lapses, card.due)
        #log("card.__dict__=%s",card.__dict__ )
        # log("card_stats=%s", [i for i in card_stats.revlog])
        # import datetime
        # log('wk_daily_id=%s', mw.col.decks.id_for_name('WK_daily'))
        # revlog_item = card_stats.revlog[9]
        #log("revlog %s", card_stats.revlog)
        #log("revlog %s", revlog_item.review_kind)
        #log("revlog dir %s", dir(revlog_item))
        #log("revlog.review_kind %s", revlog_item.review_kind)
        # log("is_learned = %s", is_learned(mw.col.backend, card_id))

        # mark_learned_radicals(mw)
        # mark_allowed_to_learn_kanji(mw)
        # mark_learned_kanji(mw)
        #mark_allowed_to_learn_vocabulary(mw)
        # mark_daily_cards(mw)

        # set_flags(mw)

        # log("flags %s", card.flags)

        # note = mw.col.getNote(27)
        # card.note()
        # log("%s", dir(note.cards()[0]))
        # log("%s", note.cards()[0].template()['name'])
        # log("%s", note.cards()[1].template()['name'])
        #char = card.note().fields[0]
        #for note_id in notes:
        #    note = mw.col.getNote(note_id)
        #    char = note.fields[0]
        #    #log("note ===================== %s", note.__dict__)
        #    try:
        #        components = split_components(note.fields[2])
        #        log('components: %s, card_id: %s', components, note.cards()[0].id)
        #        note.addTag()

        #        if char.strip() in components:
        #            are_all_components_learned = False
        #            for components in components:
        #                for n in mw.col.find_notes("tag:Radical Characters:%s" % components):
        #                   if not "kanji_learned" in note.tags:
        #                    are_all_components_learned = False
        #                    break
        #            log("Found: %s, components: %s, all_comp_learned: %s", note.fields[0], components, are_all_components_learned)


        #     except Exception as ex:
        #         log("Exception on note %s %s", note_id, ex)


except Exception as ex:
   log('exception: %s', str(ex), )
   for line in str(ex.__traceback__.tb_frame).split('\n'):
       log("%s", line)
log("end %s end", "-"*50)
