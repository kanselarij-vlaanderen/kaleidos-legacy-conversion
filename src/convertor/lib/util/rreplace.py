#!/usr/bin/python3

# https://stackoverflow.com/a/2556252
def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)
