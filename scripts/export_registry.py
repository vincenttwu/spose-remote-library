"""Write a portable JSON copy of the registry (not an authoritative second DB)."""
import argparse,json
from pathlib import Path
from registry import ROOT,export_dict,write

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=ROOT)
    ap.add_argument('--output',type=Path)
    a=ap.parse_args();root=a.root.resolve()
    p=a.output or root/'tracking/registry.json'
    if not p.is_absolute():p=root/p
    if not p.resolve().is_relative_to((root/'tracking').resolve()):raise ValueError('Export must stay in tracking/')
    out=export_dict(root);write(p,out)
    print(json.dumps({'path':str(p),'batches':len(out['batches']),'passes':len(out['passes']),'runs':len(out['runs'])},indent=2))
if __name__=='__main__':main()
