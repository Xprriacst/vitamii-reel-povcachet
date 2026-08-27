"""
scrape-sfx-library.py — constitue la librairie SFX locale (une fois, réutilisable
pour toutes tes vidéos).

Télécharge les previews MP3 de Mixkit par catégorie, les range dans
sfx/library/<catégorie>/ et écrit un CATALOG.md.
Licence : Mixkit Sound Effects Free License — usage commercial OK, sans attribution.
Idempotent : relancer ne re-télécharge pas ce qui est déjà là.

Deux modes :

    python3 scripts/scrape-sfx-library.py              # LA SÉLECTION (défaut) : 16 sons,
                                                       #   ~2 Mo, ~20 s. C'est tout ce qu'il
                                                       #   faut pour monter.
    python3 scripts/scrape-sfx-library.py --full       # toute la librairie : ~530 fichiers,
                                                       #   ~86 Mo, quelques minutes.

La sélection est décrite dans scripts/sfx-selection.json : quels sons, et surtout avec quel
réglage (coupure passe-bas, troncature, normalisation). Trouver 16 sons utilisables sur 530
est la partie longue du travail — c'est elle qui est transmise, pas les fichiers.

⚠️ Les fichiers audio ne sont volontairement PAS livrés avec ce kit : les conditions Mixkit
(clause 9.4) interdisent de mettre un Item à disposition d'un tiers. Ce script les télécharge
depuis Mixkit sous TON acceptation de leur licence. Tu peux les utiliser dans tes vidéos, y
compris commerciales, sans attribution — mais pas les rediffuser en tant que fichiers.
"""
import os
import re
import time
import urllib.request
import urllib.error


# Run from project root regardless of where script is invoked
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Chaque tag = un dossier dans sfx/library/.
#
# La sélection ci-dessous suit la signature sonore par défaut : GRAVES + passe-bas.
# Les familles aigües (chime, bell, ding, sparkle, magic, notification, success,
# confirmation) sont VOLONTAIREMENT absentes : sur un haut-parleur de téléphone elles
# piquent et sonnent cheap. Si tu choisis une autre signature, ajoute-les ici — mais
# alors assume-la partout, la constance vaut mieux qu'un choix au cas par cas.
CATEGORIES = [
    # Transitions
    "whoosh",
    "swipe",
    "swoosh",
    "transition",
    # Clics (compteurs, sélections) — à filtrer vers 800-1000 Hz
    "click",
    "tap",
    "button",
    "tick",
    # Papier / cartes / dossiers
    "paper",
    "page",
    # Pops, snaps (apparitions rapides)
    "pop",
    "snap",
    # Impacts (tampons, chutes)
    "impact",
    "stamp",
    "hit",
    "boom",
    # Frappe clavier
    "typing",
    "keyboard",
    # Montées / chutes (tension, relâche)
    "riser",
    "drop",
]

OUT_ROOT = "sfx/library"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}


def slugify(s):
    s = re.sub(r"[^\w\s-]", "", s).strip().lower()
    return re.sub(r"[-\s]+", "-", s)[:50]


def fetch_html(url):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read().decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def parse_tracks(html):
    """Return list of (id, name, mp3_url) tuples from a discover page."""
    items = re.findall(
        r'data-audio-player-preview-url-value="(https://assets\.mixkit\.co/active_storage/sfx/(\d+)/[^"]+\.mp3)".*?<h2 class="item-grid-card__title">\s*([^<]+?)\s*</h2>',
        html, re.DOTALL,
    )
    return [(sfxid, name.strip(), url) for url, sfxid, name in items]


def download(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        return os.path.getsize(dest)
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
        with open(dest, "wb") as f:
            f.write(data)
        return len(data)
    except Exception as e:
        return -1


def download_selection():
    """Télécharge uniquement les sons de sfx-selection.json (le mode par défaut)."""
    import json
    sel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sfx-selection.json")
    if not os.path.exists(sel_path):
        print(f"❌ {sel_path} introuvable.")
        return 1
    with open(sel_path) as f:
        sel = json.load(f)

    sounds = sel["sounds"]
    print(f"=== LA SÉLECTION — {len(sounds)} sons ===")
    print("(licence Mixkit : usage commercial OK, sans attribution ; rediffusion des")
    print(" fichiers interdite — voir l'en-tête de ce script)\n")

    ok = failed = 0
    total = 0
    for snd in sounds:
        cat_dir = os.path.join(OUT_ROOT, snd["category"])
        os.makedirs(cat_dir, exist_ok=True)
        dest = os.path.join(cat_dir, snd["file"])
        url = f"https://assets.mixkit.co/active_storage/sfx/{snd['id']}/{snd['id']}-preview.mp3"
        size = download(url, dest)
        if size > 0:
            ok += 1
            total += size
            print(f"  ✓ {snd['role']:14s} {snd['category']}/{snd['file'][:38]:38s} "
                  f"LPF {snd['lpf']:>5} Hz  ({size//1024:3d} Ko)")
        else:
            failed += 1
            print(f"  ✗ {snd['role']:14s} échec — id {snd['id']} n'existe plus sur le CDN ?")
        time.sleep(0.10)

    print(f"\n=== {ok} son(s) dans {OUT_ROOT}/ ({total//1024} Ko)"
          + (f", {failed} échec(s)" if failed else "") + " ===")
    print("\nLe réglage de chaque son (passe-bas, troncature, volume) est dans")
    print("scripts/sfx-selection.json, et déjà appliqué dans la banque de build-sfx.py.")
    print("Il te manque une famille ? --full télécharge les 27 catégories.")
    return 0 if failed == 0 else 1


def main():
    os.makedirs(OUT_ROOT, exist_ok=True)
    catalog = {}  # category → [(id, name, file_path, size_kb)]
    total_files = 0
    total_bytes = 0

    for category in CATEGORIES:
        url = f"https://mixkit.co/free-sound-effects/discover/{category}/"
        print(f"\n=== {category.upper()} ===")
        html = fetch_html(url)
        if html is None:
            print(f"  (404 - tag does not exist)")
            continue
        tracks = parse_tracks(html)
        if not tracks:
            print(f"  (0 tracks parsed)")
            continue
        print(f"  Found {len(tracks)} tracks")

        cat_dir = os.path.join(OUT_ROOT, category)
        os.makedirs(cat_dir, exist_ok=True)
        items = []
        for sfxid, name, mp3_url in tracks:
            slug = slugify(name)
            fname = f"{sfxid}-{slug}.mp3"
            dest = os.path.join(cat_dir, fname)
            size = download(mp3_url, dest)
            if size > 0:
                items.append((sfxid, name, fname, size))
                total_files += 1
                total_bytes += size
                print(f"  ✓ [{sfxid:6s}] {name[:40]:40s} ({size//1024:4d} KB)")
            else:
                print(f"  ✗ [{sfxid:6s}] {name[:40]:40s} (download failed)")
            time.sleep(0.10)  # polite throttle
        catalog[category] = items

    # Build markdown catalog
    md_path = os.path.join(OUT_ROOT, "CATALOG.md")
    with open(md_path, "w") as f:
        f.write("# Mixkit SFX Library — Local Catalog\n\n")
        f.write(f"Total: **{total_files} SFX**, **{total_bytes // 1024 // 1024} MB**\n\n")
        f.write("License: Mixkit Sound Effects Free License — commercial OK, no attribution.\n\n")
        f.write("---\n\n")
        for category, items in catalog.items():
            if not items:
                continue
            f.write(f"## {category.title()} ({len(items)} tracks)\n\n")
            f.write("| ID | Name | File |\n|---|---|---|\n")
            for sfxid, name, fname, _ in items:
                f.write(f"| {sfxid} | {name} | [{fname}]({category}/{fname}) |\n")
            f.write("\n")

    print(f"\n=== TERMINÉ ===")
    print(f"Total : {total_files} SFX téléchargés, {total_bytes // 1024 // 1024} Mo")
    print(f"Catalog: {md_path}")


if __name__ == "__main__":
    import sys
    if "--full" in sys.argv:
        main()
    else:
        sys.exit(download_selection())
