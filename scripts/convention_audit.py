#!/usr/bin/env python3
"""Screen Hansard maiden-speech conventions without changing verified classifications."""
import csv, hashlib, json, re
from collections import Counter
from pathlib import Path
from urllib.parse import urldefrag
from urllib.request import urlopen
from lxml import html

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
CACHE=ROOT/".cache"
MAIDEN=re.compile(r"\b(?:maiden speech|maiden contribution|maiden address|first speech in (?:this|the) House)\b",re.I)
ACK=re.compile(r"\b(?:maiden|first speech|first contribution|first address)\b",re.I)
PRAISE=re.compile(r"\b(?:congratulat\w*|pay tribute|commend|welcome)\b",re.I)

def rows(path):
    with path.open(encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f))

def page(url):
    key=hashlib.sha256(url.encode()).hexdigest()
    cached=CACHE/key
    if cached.exists(): return cached.read_bytes()
    with urlopen(url,timeout=40) as f: raw=f.read()
    CACHE.mkdir(exist_ok=True)
    cached.write_bytes(raw)
    return raw

def clean(value):
    return re.sub(r"\s+"," ",value or "").strip()

def turns(root):
    found=[]
    for node in root.xpath('//*[@data-contribution-id]'):
        blocks=node.xpath('./div[contains(concat(" ",normalize-space(@class)," ")," content ")]')
        if not blocks: continue
        found.append({"id":node.get("data-contribution-id"),
                      "speaker":clean(node.xpath('string(.//div[contains(@class,"primary-text")])')),
                      "text":clean(" ".join(b.text_content() for b in blocks))})
    return found

def inspect(row):
    out={"speech_id":row["speech_id"],"speech_date":row["speech_date"],
         "member_name":row["member_name"],"verification_status":row["verification_status"],
         "hansard_url":row["hansard_url"],
         "interruption_detected":"unknown","next_speaker_congratulates":"unknown",
         "maiden_convention_reference":"unknown","self_maiden_reference":"unknown",
         "next_speaker_excerpt":"","self_reference_excerpt":"",
         "intervening_speaker_ids":"","possible_continuations":row.get("possible_continuations",""),
         "review_status":"automated_screen_only","review_notes":""}
    url,_=urldefrag(row["hansard_url"])
    try:
        root=html.fromstring(page(url))
        if "/historic-hansard/" in url:
            out["review_notes"]="Historic Hansard: contribution structure requires manual inspection"
            return out
        entries=turns(root)
        positions=[i for i,t in enumerate(entries) if t["id"]==row["source_record_id"]]
        if len(positions)!=1:
            out["review_notes"]="Source contribution not uniquely found"
            return out
        start=positions[0]; first=entries[start]
        match=MAIDEN.search(first["text"])
        out["self_maiden_reference"]="yes" if match else "no_detected"
        if match: out["self_reference_excerpt"]=first["text"][max(0,match.start()-80):match.end()+100]
        continuation=set(filter(None,row.get("continuation_ids","").split("|")))
        end=max([start]+[i for i,t in enumerate(entries) if i>start and t["id"] in continuation])
        interveners=[t for t in entries[start+1:end] if t["speaker"]!=first["speaker"]]
        if continuation:
            out["interruption_detected"]="yes" if interveners else "no_detected"
            out["intervening_speaker_ids"]="|".join(t["id"] for t in interveners)
        elif not row.get("possible_continuations"):
            out["interruption_detected"]="no_detected_within_extracted_turn"
        next_turn=next((t for t in entries[end+1:] if t["speaker"] and t["speaker"]!=first["speaker"]),None)
        if next_turn:
            m=ACK.search(next_turn["text"])
            out["next_speaker_congratulates"]=("explicit_praise_and_acknowledgement" if m and PRAISE.search(next_turn["text"]) else
                "acknowledgement_only" if m else "no_explicit_acknowledgement")
            if m: out["next_speaker_excerpt"]=next_turn["text"][max(0,m.start()-100):m.end()+150]
        out["maiden_convention_reference"]=("yes" if match or (next_turn and ACK.search(next_turn["text"])) else
                                             "no_detected" if next_turn else "unknown")
        if interveners or row.get("possible_continuations"):
            out["review_status"]="manual_review_priority"
            out["review_notes"]="Check speech boundaries and intervening speaker turns"
    except (OSError,ValueError,KeyError,IndexError) as e:
        out["review_notes"]=f"Source inspection failed: {type(e).__name__}: {e}"
    return out

def main():
    source=[r for year in range(1961,1966) for r in rows(DATA/"maiden_speeches"/f"{year}.csv")]
    source+=rows(DATA/"unresolved.csv")
    evidence=[inspect(r) for r in source]
    with (DATA/"convention_evidence.csv").open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(evidence[0]));writer.writeheader();writer.writerows(evidence)
    summary={"total":len(evidence),"verified":sum(r["verification_status"]=="verified" for r in source),
             "indicators":{k:dict(Counter(r[k] for r in evidence)) for k in
                           ("interruption_detected","next_speaker_congratulates","maiden_convention_reference","review_status")}}
    (DATA/"convention_summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__": main()
