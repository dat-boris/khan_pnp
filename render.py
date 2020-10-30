#!/usr/bin/env python
"""Render output cards
"""
import os
import re
import argparse
import logging
import random

from typing import Dict

from playtest_cards import read_gsheet, render_all, Layout, read_csv

from gensim.summarization import keywords

asset_folder = os.path.dirname(os.path.abspath(__file__))

# Ask for access (except for people in KA)
# https://docs.google.com/spreadsheets/d/1GgKq9ti7Zq40I67XF_izHv7sf6OIp87J2jUc27SL01g/edit#gid=0
CSV_LINK = '1GgKq9ti7Zq40I67XF_izHv7sf6OIp87J2jUc27SL01g'
SHEET_NAME = 'card_setup'

# Decide if you want to do highlight (might break rendering)
DO_HIGHLIGHT = False

COLOR_CHOICE = ['red', 'orange', 'green', 'blue']

subject_color: Dict[str, str] = {}


def get_subject_color(subj):
    new_filled_colors = COLOR_CHOICE[len(subject_color) % len(COLOR_CHOICE)]
    return subject_color.setdefault(subj, new_filled_colors)


def annoate_keyword(text, highlight=None):
    if highlight is None:
        highlight = keywords(text).split('\n')
    logging.warn(f"Keywords: {highlight}")
    for kw in highlight:
        if len(kw) <= 3:
            logging.warn(f"Short keyword: '{kw}' skipping")
            continue
        text = re.sub('({})'.format(kw), '__\g<1>__', text,
                      flags=re.MULTILINE | re.IGNORECASE)
    return text


def render(layout):
    to_render = [
        'hint',
        'question',
    ]
    csv_data = read_gsheet(CSV_LINK, sheet_name=SHEET_NAME)
    #csv_data = read_csv(CSV_FILE)
    for card_type in to_render:
        type_col = "type"
        template_col = "template_file"
        # Switch into printing backside
        if '_backside' in card_type:
            template_col = 'template_file_backside'
            type_col = 'type_backside'

        # annotate keyword and setup dice
        for c in csv_data:
            if c.get('hint_text'):
                if DO_HIGHLIGHT:
                    keywords = map(
                        lambda s: s.strip(),
                        c['keywords'].lower().split(','),
                    )
                    c['hint_text'] = annoate_keyword(
                        c['hint_text'], highlight=keywords
                    )
            c['dice'] = str(random.randint(1, 6))
            c['colour'] = random.choice(COLOR_CHOICE)
            c['subject_color'] = get_subject_color(c['subject'])

        render_all(
            csv_data,
            asset_folder,
            asset_folder,
            output_filename=card_type,
            type_filter=card_type,
            temp_folder=os.path.join(asset_folder, "./genfile"),
            dimensions=layout,
            output_ext="png" if layout is not Layout.letter_landscape else "pdf",
            normalize_col_name=True,
            template_col=template_col,
            type_col=type_col,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--tabletopia', action='store_true')
    parser.add_argument('--tts', action='store_true')
    args = parser.parse_args()

    layout = Layout.letter_landscape
    if args.tts:
        layout = Layout.tts
    elif args.tabletopia:
        layout = Layout.tabletopia_card
    render(layout)
