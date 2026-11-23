"""Validate appearance metadata and the required region QA image, not image content.

Usage: python validate_appearance_record.py path/to/pose.json
The Blender material/control checks remain separate from this metadata check.
"""
from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[2]

def validate_record(path):
    path=Path(path).resolve()
    record=json.loads(path.read_text(encoding='utf-8'))
    project=json.loads((ROOT/'project.json').read_text(encoding='utf-8'))
    configured=project['visual_profile']
    profile=json.loads((ROOT/configured['config']).read_text(encoding='utf-8'))
    appearance=record.get('appearance')
    if not isinstance(appearance,dict):raise ValueError('appearance metadata is required')
    for field in ['visual_profile_id','visual_profile_version','actor_palette_ids','mode','qa_regions_preview','muscle_group_slider_x']:
        if field not in appearance:raise ValueError('Missing appearance field: '+field)
    if appearance['visual_profile_id']!=profile['visual_profile_id'] or appearance['visual_profile_version']!=profile['version']:
        raise ValueError('Output appearance does not match the configured visual profile')
    expected={actor:palette['palette_id'] for actor,palette in profile['actor_palettes'].items()}
    if appearance['actor_palette_ids']!=expected:raise ValueError('Actor palettes missing or swapped')
    mode=appearance['mode']
    if mode not in profile['modes']:raise ValueError('Unknown appearance mode')
    sliders=appearance['muscle_group_slider_x']
    expected_value=profile['control']['regions_value' if mode=='regions' else 'plain_value']
    if not isinstance(sliders,dict) or set(sliders)!=set(expected):raise ValueError('Slider values required for both actors')
    if any(not isinstance(v,(int,float)) or abs(v-expected_value)>1e-6 for v in sliders.values()):
        raise ValueError('Recorded slider values do not match the appearance mode')
    preview=appearance['qa_regions_preview']
    if not isinstance(preview,str) or not preview:raise ValueError('A body-region QA preview is required')
    resolved=(path.parent/preview).resolve()
    if not resolved.is_relative_to(path.parent):raise ValueError('QA preview must belong to this pose revision')
    if not resolved.is_file() or resolved.read_bytes()[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('Missing or invalid QA PNG')
    if record.get('status')=='accepted' and profile.get('approved_at') is None:
        raise ValueError('Cannot accept an output using an unapproved visual profile')
    return {'appearance_metadata':'passed','visual_profile':profile['visual_profile_id']+'/'+profile['version'],
            'qa_preview_exists':True,'pixel_content_verified':False,'blender_materials_verified':False}

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit(__doc__)
    try:print(json.dumps(validate_record(sys.argv[1]),indent=2))
    except (ValueError,KeyError,OSError) as exc:raise SystemExit('Appearance validation failed: '+str(exc))
