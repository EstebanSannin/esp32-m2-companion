"""Single source of the board revision for generated review artifacts.

Rev B artifacts (docs/review/rev_b_*) document the ordered rev-B board and
stay as history; v2 writes its own (docs/review/v2_reva_*).
"""
REV_LABEL = "v2.0 Rev A"      # matches the board silkscreen
REV_TAG = "v2_reva"           # docs/review/<REV_TAG>_*.{pdf,md}
GATE = "GATE V3"
