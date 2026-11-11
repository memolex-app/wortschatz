"""Affiche un lot de cartes pour relecture : rang|niveau|nature|mot|pluriel|traduction  (+ chunk).
Usage : python3 dump_batch.py DEBUT FIN   (rangs inclusifs)"""
import sys
from common import load, shown
cards, ex, ch = load('..')
a, b = int(sys.argv[1]), int(sys.argv[2])
for i, c in enumerate(cards, 1):
    if a <= i <= b:
        print(f"{i}|{c['nat']}|{shown(c)}|{c['fr']}")
