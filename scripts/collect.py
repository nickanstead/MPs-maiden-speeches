#!/usr/bin/env python3
"""Collect the 1961–1965 Commons maiden speeches from parliamentary sources."""
import csv
import hashlib
import json
import re
import subprocess
import time
import unicodedata
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from urllib.parse import urldefrag, urlsplit
from urllib.request import urlopen

from lxml import html
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache"
NEW = "https://researchbriefings.files.parliament.uk/documents/SN04588/SN04588.xlsx"
OLD = "https://researchbriefings.files.parliament.uk/documents/SN04587/SN04587.pdf"
DATES = r"\b(0?[1-9]|[12]\d|3[01]) ([A-Z][a-z]+) (196[1-5])\b"


def download(url):
    CACHE.mkdir(exist_ok=True)
    path = CACHE / hashlib.sha256(url.encode()).hexdigest()
    if not path.exists():
        for attempt in range(3):
            try:
                with urlopen(url, timeout=30) as response:
                    content = response.read()
                temporary = path.with_suffix(".tmp")
                temporary.write_bytes(content)
                temporary.replace(path)
                break
            except OSError:
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)
    return path


def index_rows():
    with download(NEW).open("rb") as source:
        workbook = load_workbook(source, read_only=True)
        try:
            for number, row in enumerate(workbook["Table"].values, 1):
                date = row[4]
                if isinstance(date, datetime) and 1961 <= date.year <= 1965:
                    yield dict(index_row=number, index_date=date.date().isoformat(),
                               member_name=row[5], surname=row[6].split(",")[0],
                               wikidata_id=row[7], mnis_id="" if row[8] == "[x]" else row[8],
                               constituency_at_speech=row[9], hansard_reference=row[12],
                               hansard_url=row[13])
        finally:
            workbook.close()


def legacy_rows():
    pdf = subprocess.check_output(["pdftotext", "-layout", str(download(OLD)), "-"],
                                  text=True, encoding="utf-8")
    rows = []
    for page, body in enumerate(pdf.split("\f"), 1):
        for line in body.splitlines():
            match = re.search(DATES, line)
            if not match:
                continue
            fields = re.split(r" {2,}", line[:match.start()].strip())
            reference = re.match(r"\s+(\d+)\s+c?\s*(\d+)", line[match.end():])
            rows.append((page, line.strip(), fields,
                         datetime.strptime(match[0], "%d %B %Y").date().isoformat(),
                         reference.groups() if reference else None))
    return rows


PEOPLE = "https://raw.githubusercontent.com/mysociety/parlparse/master/members/people.json"


def key(value):
    value = unicodedata.normalize("NFKD", value.casefold()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", value)


def seat_key(value):
    return key(re.sub(r"\b(and|upon)\b", "", value, flags=re.I))


def reference(value):
    match = re.search(r"(\d+) cc?\s*(\d+)(?:[–-](\d+))?", value)
    if not match:
        raise ValueError(f"Unrecognised Hansard reference: {value}")
    volume, start, end = match.groups()
    end = int(start[:len(start) - len(end)] + end) if end else int(start)
    if end < int(start):
        end += 10 ** len(match[3])
    return volume, start, end


def match_legacy(row, old, volume, column):
    exact = [entry for entry in old if entry[4] == (volume, column)]
    if len(exact) == 1 and (
        key(exact[0][2][0]) == key(row["surname"])
        or (row["member_name"], exact[0][2][0]) == ("James Bennett", "Bennet")
    ):
        return exact[0]
    same_name = [entry for entry in old if entry[3] == row["index_date"]
                 and key(entry[2][0]) == key(row["surname"])]
    if len(same_name) == 1:
        return same_name[0]
    return None


def memberships():
    people = json.loads(download(PEOPLE).read_bytes())
    persons = {p["id"]: p for p in people["persons"]}
    posts = {p["id"]: p["area"]["name"] for p in people["posts"]
             if p["organization_id"] == "house-of-commons"}
    for m in people["memberships"]:
        if m.get("post_id") in posts and m["start_date"] <= "1965-12-31" and m.get("end_date", "9999") >= "1961-01-01":
            yield m, persons[m["person_id"]], posts[m["post_id"]]


SEAT_ALIASES = {
    "northamptonshire south": ("Northampton South", "Northants South"),
    "wandsworth putney": ("Putney",),
    "wandsworth clapham": ("Clapham",),
    "camberwell dulwich": ("Dulwich",),
    "hartlepools, the": ("The Hartlepools", "Hartlepool"),
}
SPEAKER_ALIASES = {"Joan Quennell": "Miss J. M. Qnennell", "James Tinn": "Mr. James Tina"}
ALLDRITT = "https://hansard.parliament.uk/Commons/1964-06-16/debates/290e0db9-01c4-4efb-a12c-f9ee704475c1/NewMemberSworn"
GRIFFITHS = "https://api.parliament.uk/historic-hansard/commons/1964/jun/16/foreign-affairs"
DUFFY = "https://researchbriefings.files.parliament.uk/documents/RP08-12/RP08-12.pdf"
ANDERSON_CONTINUATION = "4d27a049-c70a-4846-ba53-112fca2848df"


def same_seat(official, value):
    return any(seat_key(candidate) == seat_key(value)
               for candidate in (official, *SEAT_ALIASES.get(official.lower(), ())))


def modern_hansard(row, root, base, anchor, volume, first, last):
    node = root.get_element_by_id(anchor)
    record_id = node.get("data-contribution-id")
    if not record_id:
        raise ValueError("The linked anchor is not a speech contribution")
    heading = root.xpath('string(//div[contains(@class,"hero-banner-debate")]//h2)')
    parsed = re.search(r"Volume (\d+): debated on \w+ (\d+ \w+ \d{4})", heading)
    if not parsed:
        raise ValueError("Hansard volume or date missing")
    date = datetime.strptime(parsed[2], "%d %B %Y").date().isoformat()
    if f"/Commons/{date}/" not in base:
        raise ValueError("Hansard chamber or date mismatch")
    if parsed[1] != volume:
        if (row["member_name"], volume, parsed[1], date) != ("Eldon Griffiths", "696", "698", "1964-06-16"):
            raise ValueError("Hansard volume does not match index")
        historic = html.fromstring(download(GRIFFITHS).read_bytes())
        if "vol 696" not in historic.text_content() or "Eldon Griffiths" not in historic.text_content():
            raise ValueError("Historic Hansard volume corroboration missing")
        row.update(supplementary_hansard_url=GRIFFITHS,
                   citation_note="Modern sitting heading shows 698. Historic Hansard and both indexes give 696.")
    speaker = node.xpath('normalize-space(.//div[@class="primary-text"])')
    secondary = node.xpath('normalize-space(.//div[@class="secondary-text"])')
    seat = "" if key(row["surname"]) in key(secondary) else secondary.strip("()")
    if secondary and not seat:
        speaker += " (" + secondary.strip("()") + ")"
    cols = node.xpath('preceding::*[contains(@class,"column-number") and @data-column-number][1]/@data-column-number')
    row["hansard_start_column"] = cols[0] if cols else ""
    if row["hansard_start_column"] != first:
        row["column_note"] = "Nearest preceding Hansard column marker differs from index start"
    blocks = node.xpath('./div[@class="content"]')
    if len(blocks) != 1:
        raise ValueError("Expected one Hansard content block")
    continuation = []
    primary = node.xpath('normalize-space(.//div[@class="primary-text"])')
    for other in node.xpath('following::div[@data-contribution-id]'):
        position = other.xpath('preceding::*[contains(@class,"column-number") and @data-column-number][1]/@data-column-number')
        if not position or not position[0].isdigit() or int(position[0]) > last:
            break
        if primary == other.xpath('normalize-space(.//div[@class="primary-text"])'):
            continuation.append(other.get("data-contribution-id"))
    if row["member_name"] == "David Anderson" and continuation == [ANDERSON_CONTINUATION]:
        blocks.extend(root.get_element_by_id("contribution-" + ANDERSON_CONTINUATION)
                      .xpath('./div[@class="content"]'))
        row["continuation_ids"] = ANDERSON_CONTINUATION
        row["boundary_note"] = "Included the resumption after George Lawson's intervention, before William Ross congratulated Anderson."
        continuation.clear()
    if continuation:
        row["possible_continuations"] = "|".join(continuation)
    return date, record_id, speaker, seat, blocks


def historic_hansard(root, base, anchor, volume, first):
    title = root.xpath('string(//title)')
    match = re.search(r"\(Hansard, (\d+ \w+ \d{4})\)", title)
    if not match or "/historic-hansard/commons/" not in base or not anchor.startswith(f"S5CV{int(volume):04d}P"):
        raise ValueError("Historic Hansard chamber, volume or date mismatch")
    anchors = root.xpath('//*[@name=$name]', name=anchor)
    if len(anchors) != 1:
        raise ValueError("Historic Hansard speech anchor unavailable")
    node = anchors[0].getparent()
    speaker = node.xpath('normalize-space(.//cite)')
    seat = node.xpath('normalize-space(.//span[@class="member_constituency"])').strip("()")
    start = node.xpath('preceding::a[starts-with(@id,"column_")][1]/text()')
    if start != [first]:
        raise ValueError("Historic Hansard column differs from index")
    return (datetime.strptime(match[1], "%d %B %Y").date().isoformat(),
            anchor, speaker, seat, node.xpath('./blockquote/p'))


def speech_text(blocks):
    paragraphs = []
    for block in blocks:
        for marker in block.xpath('.//a[contains(@class,"column-permalink")]'):
            marker.drop_tree()
        paragraphs.append("\n".join(line.rstrip() for line in block.text_content().strip().splitlines()))
    return "\n\n".join(paragraphs)


def collect(row, old, members, used_legacy):
    row = dict(row, chamber="House of Commons", index_url=NEW, legacy_index_url=OLD,
               verification_status="candidate")
    notes = []
    try:
        volume, first, last = reference(row["hansard_reference"])
        legacy = match_legacy(row, old, volume, first)
        if legacy:
            page, line, fields, legacy_date, _ = legacy
            used_legacy.add((page, line))
            row.update(legacy_index_page=page, legacy_index_entry=line)
            row["party_at_speech"] = fields[2] if len(fields) == 4 else ""
            if row["member_name"] == "Geoffrey Rhodes" and "Labour Party/Co-operative Party (Joint" in line:
                row["party_at_speech"] = "Labour Party/Co-operative Party (Joint)"
            if "Made no speeches" in line:
                notes.append("The legacy index excludes this contribution from its maiden-speech list.")
        else:
            legacy_date = None
        base, anchor = urldefrag(row["hansard_url"])
        if urlsplit(base).hostname not in {"hansard.parliament.uk", "api.parliament.uk"}:
            raise ValueError("Index entry has no supported parliamentary transcript URL")
        source = download(base).read_bytes()
        row["transcript_sha256"] = hashlib.sha256(source).hexdigest()
        root = html.fromstring(source)
        if "/historic-hansard/" in base:
            date, record_id, speaker, seat, blocks = historic_hansard(root, base, anchor, volume, first)
            row["hansard_start_column"] = first
        else:
            date, record_id, speaker, seat, blocks = modern_hansard(row, root, base, anchor, volume, first, last)
        if not "1961-01-01" <= date <= "1965-12-31":
            raise ValueError("Hansard sitting outside pilot window")
        row.update(speech_date=date, source_record_id=record_id,
                   speech_id="commons-" + record_id)
        if row["index_date"] != date or (legacy_date and legacy_date != date):
            row["date_correction"] = "Date taken from Hansard sitting heading and URL"
        row.update(speaker_name_hansard=speaker, constituency_hansard=seat)
        if key(row["surname"]) not in key(speaker):
            if SPEAKER_ALIASES.get(row["member_name"]) == speaker:
                row["speaker_note"] = "Index identity and constituency corroborate the Hansard transcription variant."
            else:
                notes.append("Linked speaker surname differs from the index.")
        if row["member_name"] == "Patrick Duffy" and date == "1963-07-08":
            row.update(party_at_speech="Labour", party_source=DUFFY,
                       citation_note="The legacy index cites a later speech. The July transcript identifies this as his first address.")
        if row["member_name"] == "Walter Alldritt" and date == "1964-07-08":
            sworn = html.fromstring(download(ALLDRITT).read_bytes()).text_content()
            if "Walter Harold Alldritt" in sworn and "Liverpool, Scotland" in sworn:
                row["membership_override_url"] = ALLDRITT
                row["membership_override_note"] = "Hansard records Alldritt sworn in June, before ParlParse's first term."
        matches = [(m, p, constituency) for m, p, constituency in members
                   if (m["start_date"] <= date <= m.get("end_date", "9999")
                       or (row.get("membership_override_url") and m["start_date"] == "1964-10-15"))
                   and (any(same_seat(constituency, variant) for variant in (row["constituency_at_speech"], seat))
                        or any(i["scheme"] == "datadotparl_id" and str(i["identifier"]) == str(row["mnis_id"])
                               for i in p.get("identifiers", [])))
                   and any(key(n.get("family_name", "")) == key(row["surname"])
                           for n in p["other_names"])]
        identities = {p["id"]: constituency for _, p, constituency in matches}
        if len(identities) == 1:
            row["member_id"], row["constituency_membership"] = next(iter(identities.items()))
            row["member_id_source"] = PEOPLE
        else:
            notes.append("Dated Commons membership could not be uniquely matched.")
        row["original_text"] = speech_text(blocks)
        row["word_count"] = len(row["original_text"].split())
        row["text_sha256"] = hashlib.sha256(row["original_text"].encode()).hexdigest()
        row["party_source"] = row.get("party_source") or (OLD if row.get("party_at_speech") else "")
        if row.get("possible_continuations"):
            notes.append("Additional same-speaker contributions fall within the cited columns.")
        if not row["original_text"]:
            notes.append("Hansard contribution contains no text.")
        if not row.get("party_at_speech"):
            notes.append("Party at speech date has not been established.")
        if not notes:
            row["verification_status"] = "verified"
            row["identification_basis"] = "Commons Library maiden-speech index and anchored Hansard contribution"
    except (OSError, ValueError, KeyError) as exc:
        notes.append(str(exc))
    row["verification_notes"] = " ".join(notes)
    return row


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def main():
    index = list(index_rows())
    urls = sorted({urldefrag(row["hansard_url"]).url for row in index})
    def fetch(url):
        try:
            download(url)
        except OSError as exc:
            print(url, exc, flush=True)
    with ThreadPoolExecutor(max_workers=12) as pool:
        list(pool.map(fetch, urls))
    old = legacy_rows()
    members = list(memberships())
    used_legacy = set()
    rows = [collect(row, old, members, used_legacy) for row in index]
    verified = sorted((row for row in rows if row["verification_status"] == "verified"),
                      key=lambda row: (row["speech_date"], row["index_row"]))
    fields = sorted({field for row in rows for field in row})
    output = ROOT / "data"
    for year in range(1961, 1966):
        write_csv(output / "maiden_speeches" / f"{year}.csv",
                  [row for row in verified if row["speech_date"].startswith(str(year))], fields)
    write_csv(output / "unresolved.csv",
              [row for row in rows if row["verification_status"] != "verified"], fields)
    older_only = [
        dict(page=p, entry=line, index_date=date,
             disposition=("superseded_by_1963-07-08_transcript"
                          if date == "1964-01-21" and line.startswith("Duffy ") else "candidate"))
        for p, line, _, date, _ in old if (p, line) not in used_legacy
    ]
    write_csv(output / "legacy_only.csv", older_only, ["page", "entry", "index_date", "disposition"])
    manifest = {
        "index_rows": [row["index_row"] for row in index],
        "legacy_index_entries": len(old),
        "linked_hansard_pages": len(urls),
        "verified_by_year": dict(sorted(Counter(row["speech_date"][:4] for row in verified).items())),
        "source_sha256": {url: hashlib.sha256(download(url).read_bytes()).hexdigest()
                          for url in (NEW, OLD, PEOPLE)},
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"{len(verified)} verified and {len(rows) - len(verified)} unresolved")


if __name__ == "__main__":
    main()
