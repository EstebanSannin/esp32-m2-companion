import json, sys, collections
d = json.load(open(sys.argv[1]))
skip_zone = lambda v: any("Zone" in i["description"] for i in v["items"])
c = collections.Counter()
for v in d["violations"]:
    if skip_zone(v):
        continue  # stale fills / pour artefacts
    c[v["type"]] += 1
    if v["type"] not in ("silk_overlap", "silk_over_copper", "silk_edge_clearance", "text_height",
                         "text_thickness", "lib_footprint_mismatch", "lib_footprint_issues",
                         "footprint_symbol_mismatch", "extra_footprint", "missing_footprint",
                         "track_dangling", "via_dangling"):
        print(v["type"], "::", " | ".join(i["description"] for i in v["items"])[:180])
print(dict(c)); print("unconnected", len(d["unconnected_items"]))
