#!/usr/bin/env python3
"""Regenerate the web-sized images in images/ from the originals in raw/.

raw/ is gitignored and holds the full-resolution files; images/ holds the
compressed copies the site actually serves. Drop a new photo into the right
raw/ folder and re-run this script.

    python3 scripts/optimize_images.py          # only what changed
    python3 scripts/optimize_images.py --force  # rebuild everything

Output names are the original names with any leading "_", "." or "#" stripped,
because GitHub Pages runs Jekyll and Jekyll refuses to publish files starting
with those -- they 404 on the live site while working fine locally.

Sizes are driven by how large each image is actually displayed, times 3 for
high-DPI screens:
  headshots   rendered  100px  ->  shorter side 300px
  avatar      rendered  225px  ->  width        900px
  photography rendered ~265px  ->  longest side 1200px
"""

import argparse
import os
import re
import sys

from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (source dir, output dir, fit mode, target px, jpeg quality)
JOBS = [
    ("raw/people",      "images/people", "min", 300,  82),
    ("raw/photography", "images/photos", "max", 1200, 80),
]

# Originals that live in a raw/ folder but ship elsewhere and/or at their own
# size: (output path, fit mode, target px, jpeg quality).
SPECIAL = {
    os.path.join("raw", "people", "jentsehuang.jpg"):
        (os.path.join("images", "jentsehuang.jpg"), "min", 700, 82),
}

EXTS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}

# Jekyll (which GitHub Pages runs by default) skips names starting with these,
# so a raw/ file called _DSC0761.JPG would 404 once pushed. Camera exports are
# full of them, so rename on the way out instead of policing raw/.
UNSAFE_PREFIX = re.compile(r"^[_.#]+")

# Pages that list their images by hand, so a new file needs an edit there too.
# images/photos is not here: that gallery is generated, see GALLERY below.
SHOWN_BY = {
    "images/people": "team.html",
}

# Output folders that mirror a raw/ folder exactly: anything here without a
# matching original is deleted. Only images/photos qualifies -- images/people
# is left alone, since team.html names each headshot by hand.
PRUNE = {
    "images/photos": "raw/photography",
}

# The photography gallery is rewritten from whatever is in its source folder.
# about.html shuffles it client-side, so the order written here does not matter;
# it is sorted only to keep git diffs readable.
GALLERY = {
    "page": "about.html",
    "img_dir": "images/photos",
    "start": "<!-- photos:start",
    "end": "<!-- photos:end -->",
    "element_id": "photos",
}


def web_name(name):
    """The name an original ships under: same name, minus any Jekyll-hostile prefix."""
    stem, ext = os.path.splitext(name)
    stem = UNSAFE_PREFIX.sub("", stem)
    return stem + ext if stem else name


def target_size(size, mode, target):
    w, h = size
    ref = min(w, h) if mode == "min" else max(w, h)
    if ref <= target:
        return None  # never upscale
    s = target / ref
    return max(1, round(w * s)), max(1, round(h * s))


def encode(src, dst, mode, target, quality):
    im = Image.open(src)
    im = ImageOps.exif_transpose(im)  # bake in rotation before metadata is dropped

    new = target_size(im.size, mode, target)
    before = im.size
    if new:
        im = im.resize(new, Image.LANCZOS)

    ext = os.path.splitext(dst)[1].lower()
    os.makedirs(os.path.dirname(dst), exist_ok=True)

    if ext == ".png":
        # every source here is opaque; RGBA would just store a constant channel
        if im.mode in ("RGBA", "LA", "P"):
            alpha = im.convert("RGBA").getchannel("A")
            im = im.convert("RGBA") if alpha.getextrema()[0] < 255 else im.convert("RGB")
        im.save(dst, "PNG", optimize=True)
    else:
        if im.mode != "RGB":
            im = im.convert("RGB")
        im.save(dst, "JPEG", quality=quality, optimize=True, progressive=True)

    return before, im.size


def prune_orphans(dry_run=False):
    """Delete outputs whose original is gone from raw/.

    Only files with an image extension are ever removed, and a missing or empty
    source folder aborts the prune rather than emptying the output folder.
    """
    removed = {}
    for out_dir, src_dir in sorted(PRUNE.items()):
        abs_out = os.path.join(ROOT, out_dir)
        abs_src = os.path.join(ROOT, src_dir)
        if not os.path.isdir(abs_out):
            continue
        if not os.path.isdir(abs_src):
            print(f"  ! {src_dir}/ is missing, not pruning {out_dir}/")
            continue

        expected = {web_name(f) for f in os.listdir(abs_src)
                    if os.path.splitext(f)[1].lower() in EXTS}
        if not expected:
            print(f"  ! {src_dir}/ has no images, not pruning {out_dir}/")
            continue

        present = {f for f in os.listdir(abs_out)
                   if os.path.splitext(f)[1].lower() in EXTS}
        for name in sorted(present - expected):
            verb = "would remove" if dry_run else "removed"
            print(f"  {verb} {out_dir}/{name} (no original in {src_dir}/)")
            if not dry_run:
                os.remove(os.path.join(abs_out, name))
            removed.setdefault(out_dir, set()).add(name)
    return removed


def sync_gallery(dry_run=False, pruned=None, planned=None):
    """Rewrite the generated photo gallery in about.html from images/photos/."""
    page = os.path.join(ROOT, GALLERY["page"])
    img_dir = os.path.join(ROOT, GALLERY["img_dir"])
    if not (os.path.exists(page) and os.path.isdir(img_dir)):
        return

    # on a dry run the orphans are still on disk and the new files are not
    # there yet; correct for both so the report matches what a real run gives
    gone = (pruned or {}).get(GALLERY["img_dir"], set())
    coming = (planned or {}).get(GALLERY["img_dir"], set())
    names = sorted(coming | {f for f in os.listdir(img_dir)
                             if os.path.splitext(f)[1].lower() in EXTS
                             and f not in gone})

    html = open(page, encoding="utf-8").read()
    i = html.find(GALLERY["start"])
    j = html.find(GALLERY["end"])
    if i == -1 or j == -1:
        print(f"  ! {GALLERY['page']}: gallery markers not found, leaving it alone")
        return
    j += len(GALLERY["end"])

    indent = " " * (i - html.rfind("\n", 0, i) - 1)
    inner = indent + "    "
    block = (
        f"{GALLERY['start']} -- generated by scripts/optimize_images.py "
        f"from raw/photography/; do not edit by hand -->\n"
        f"{indent}<div class=\"masonry\" id=\"{GALLERY['element_id']}\">\n"
        + "".join(f"{inner}<img src=\"{GALLERY['img_dir']}/{n}\" alt=\"\">\n" for n in names)
        + f"{indent}</div>\n"
        f"{indent}<script>shuffleChildren(\"{GALLERY['element_id']}\");</script>\n"
        f"{indent}{GALLERY['end']}"
    )

    new = html[:i] + block + html[j:]
    if new == html:
        print(f"  {GALLERY['page']} gallery already up to date ({len(names)} photos)")
    elif dry_run:
        print(f"  would rewrite {GALLERY['page']} gallery ({len(names)} photos)")
    else:
        open(page, "w", encoding="utf-8").write(new)
        print(f"  {GALLERY['page']} gallery rewritten ({len(names)} photos)")


def check_references():
    """Warn about images that exist but no page shows, and refs with no file.

    The script can put a file in the right folder, but the pages list their
    images explicitly, so a new photo stays invisible until it is added there.
    """
    pages = {}
    for page in sorted(set(SHOWN_BY.values())):
        path = os.path.join(ROOT, page)
        pages[page] = open(path, encoding="utf-8").read() if os.path.exists(path) else ""

    problems = False
    for out_dir, page in sorted(SHOWN_BY.items()):
        abs_dir = os.path.join(ROOT, out_dir)
        if not os.path.isdir(abs_dir):
            continue
        on_disk = {f for f in os.listdir(abs_dir)
                   if os.path.splitext(f)[1].lower() in EXTS}
        referenced = set(re.findall(re.escape(out_dir) + r"/([^\"']+)", pages[page]))

        for f in sorted(on_disk - referenced):
            problems = True
            print(f"  ! {out_dir}/{f} exists but {page} does not show it "
                  f"-- add it to {page}")
        for f in sorted(referenced - on_disk):
            problems = True
            print(f"  ! {page} references {out_dir}/{f} but the file is missing "
                  f"-- add the original to raw/ and re-run")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true",
                    help="re-encode even when the output is newer than the original")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would change without writing or deleting anything")
    args = ap.parse_args()

    pairs = []
    for src_dir, out_dir, mode, target, quality in JOBS:
        abs_src = os.path.join(ROOT, src_dir)
        if not os.path.isdir(abs_src):
            print(f"skip {src_dir}/ (not found)")
            continue
        for name in sorted(os.listdir(abs_src)):
            if os.path.splitext(name)[1].lower() not in EXTS:
                continue
            rel = os.path.join(src_dir, name)
            if rel in SPECIAL:
                pairs.append((rel,) + SPECIAL[rel])
            else:
                pairs.append((rel, os.path.join(out_dir, web_name(name)),
                              mode, target, quality))

    claimed = {}
    clash = False
    for rel, dst_rel, *_ in pairs:
        if dst_rel in claimed:
            clash = True
            print(f"  ! {rel} and {claimed[dst_rel]} both ship as {dst_rel} "
                  f"-- rename one of them in raw/")
        claimed[dst_rel] = rel
    if clash:
        return 1

    total_in = total_out = 0
    done = skipped = 0
    for rel, dst_rel, mode, target, quality in pairs:
        src, dst = os.path.join(ROOT, rel), os.path.join(ROOT, dst_rel)
        in_sz = os.path.getsize(src)
        total_in += in_sz

        if not args.force and os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
            total_out += os.path.getsize(dst)
            skipped += 1
            continue

        if args.dry_run:
            print(f"  would encode {dst_rel}")
            done += 1
            continue

        before, after = encode(src, dst, mode, target, quality)
        out_sz = os.path.getsize(dst)
        total_out += out_sz
        done += 1
        print(f"  {dst_rel:34s} {before[0]}x{before[1]} -> {after[0]}x{after[1]}  "
              f"{in_sz/1024:8.0f} KB -> {out_sz/1024:7.0f} KB")

    if not pairs:
        print("nothing to do")
        return 0
    print(f"\n{done} written, {skipped} up to date")
    print(f"originals {total_in/1048576:.1f} MB -> shipped {total_out/1048576:.1f} MB "
          f"({100 * (1 - total_out / total_in):.0f}% smaller)")

    print()
    pruned = prune_orphans(args.dry_run)
    planned = {}
    for dst_rel in claimed:
        out_dir, name = os.path.split(dst_rel)
        planned.setdefault(out_dir, set()).add(name)
    sync_gallery(args.dry_run, pruned, planned)
    print()
    if check_references():
        print("\nthe pages list their images by hand, so fix the lines above "
              "or the new files will not appear on the site")
    else:
        print("every image is referenced by its page, and every reference has a file")
    return 0


if __name__ == "__main__":
    sys.exit(main())
