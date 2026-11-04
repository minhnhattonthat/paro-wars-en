"""Graphics text: which disc files the build redraws, and the rects it may change in each (docs/re/graphics.md)."""
FILES = {}  # rel path -> {"lz": offset of the LZ stream or None, "rects": [(start, end) byte spans in the decoded file]}


def lz_at(rel):
    return FILES[rel]["lz"] if rel in FILES else None


def spans(rel):
    return FILES[rel]["rects"] if rel in FILES else []
