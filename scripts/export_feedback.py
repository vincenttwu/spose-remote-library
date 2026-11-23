"""Export an existing remote pose revision into a compact review ZIP."""
import argparse,sys,zipfile,datetime,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pose_common import ROOT,read_json

def main():
 p=argparse.ArgumentParser();p.add_argument('pose_id');p.add_argument('--revision',type=int,default=None);p.add_argument('--output',type=Path);a=p.parse_args()
 pair=read_json(ROOT/'project.json')['default_pair']
 base=ROOT/'poses'/a.pose_id/pair['pair_id']/pair['version']
 revisions=sorted([x for x in base.glob('r[0-9][0-9][0-9]') if x.is_dir()])
 if not revisions:raise SystemExit('No remote revisions found')
 rev=base/f'r{a.revision:03d}' if a.revision is not None else revisions[-1]
 if not rev.is_dir():raise SystemExit('Revision not found')
 ts=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
 dest=a.output or (ROOT/'reports'/f'{a.pose_id}_{rev.name}_feedback_{ts}.zip')
 dest.parent.mkdir(parents=True,exist_ok=True)
 patterns=['pose.json','validation.json','checksums.json','blender-result.json','build.log']
 files=[rev/name for name in patterns if (rev/name).is_file()]
 files+=list((rev/'previews').glob('*.png')) if (rev/'previews').exists() else []
 # Preserve the exact declarative input so a fresh session can diagnose targets.
 files+=list((rev/'inputs').glob('*.json')) if (rev/'inputs').exists() else []
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
  for file in files:z.write(file,file.relative_to(rev).as_posix())
 print(dest)
if __name__=='__main__':main()
