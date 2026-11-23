"""Exact-pixel render conversion for compact SPOSE feedback.

Lossless WebP is the default *only* when Pillow supports it. Decode verification
compares the source and result in RGBA space, including transparency. Original
PNG files are never modified. Fallback is original PNG (also lossless).

CLI:
    python scripts/compress_images.py review/DOGG-DOGG-V00_front.png --output test.webp
    python scripts/compress_images.py review --output upload/compressed --format webp
    python scripts/compress_images.py review --output upload/compressed --format png
"""
from __future__ import annotations
import argparse, io, json
from pathlib import Path


def _pil():
    try:
        from PIL import Image, features
    except ImportError as exc:
        raise RuntimeError('Pillow not installed; run: python -m pip install Pillow') from exc
    return Image, features


def encode_verified(src: Path, fmt='webp', effort=6):
    """Return (bytes, extension, metadata). Raises on *any* pixel mismatch.

    Keep binary source PNG for ZIP fallback if no Pillow is installed, but
    never claim that a lossy transformation was performed.
    """
    src = Path(src)
    if fmt == 'original-png':
        return src.read_bytes(), '.png', {'codec':'original-png','lossless':True,'pixel_verification':'original-bytes'}
    Image, features = _pil()
    if fmt == 'webp' and not features.check('webp'):
        raise RuntimeError('Installed Pillow has no WebP encoder')
    with Image.open(src) as source:
        source.load()
        reference = source.convert('RGBA')
        # Opaque RGBA is semantically RGB. This saves a substantial amount.
        opaque = reference.getextrema()[3] == (255, 255)
        canonical = source.convert('RGB') if opaque else reference
        buf = io.BytesIO()
        if fmt == 'webp':
            canonical.save(buf, format='WEBP', lossless=True, method=effort, exact=True)
        elif fmt == 'png':
            canonical.save(buf, format='PNG', optimize=True, compress_level=9)
        else:
            raise ValueError('Unsupported lossless image format: ' + fmt)
        encoded = buf.getvalue()
        with Image.open(io.BytesIO(encoded)) as result:
            result.load()
            decoded = result.convert('RGBA')
            if decoded.size != reference.size or decoded.tobytes() != reference.tobytes():
                raise ValueError('LOSSLESS IMAGE VERIFICATION FAILED: ' + str(src))
        return encoded, '.webp' if fmt == 'webp' else '.png', {
            'codec': 'lossless-' + fmt,
            'lossless': True,
            'pixel_verification':'RGBA-byte-identical',
            'width':reference.width, 'height':reference.height,
            'source_bytes':src.stat().st_size, 'encoded_bytes':len(encoded),
        }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('path',type=Path,help='PNG image or folder of images')
    p.add_argument('--output',type=Path,required=True,help='Output file or directory')
    p.add_argument('--format',choices=['webp','png'],default='webp')
    p.add_argument('--effort',type=int,choices=range(7),metavar='{0..6}',default=6)
    args=p.parse_args()
    sources=sorted(args.path.glob('*.png')) if args.path.is_dir() else [args.path]
    if not sources or not all(x.is_file() and x.suffix.lower()=='.png' for x in sources):
        p.error('Supply a PNG file or folder with PNG files')
    if args.path.is_dir():args.output.mkdir(parents=True,exist_ok=True)
    records=[]
    for src in sources:
        payload,ext,metadata=encode_verified(src,args.format,args.effort)
        out=(args.output/src.with_suffix(ext).name) if args.path.is_dir() else args.output
        if args.path.is_file() and out.suffix.lower()!=ext:
            p.error(f'Output filename must end in {ext}')
        out.parent.mkdir(parents=True,exist_ok=True)
        if out.resolve()==src.resolve():
            p.error('Never overwrite authoritative input images')
        out.write_bytes(payload)
        records.append({'source':str(src),'output':str(out),**metadata})
    print(json.dumps({'ok':True,'count':len(records),'images':records},indent=2))


if __name__=='__main__':main()
