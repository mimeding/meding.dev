"""Web versions of the Nordic Funds & Mines photo (Stockholm, 16 October 2026).
Run once from site-src with the original in UP. Saving through Pillow drops all EXIF data, including location."""
import os, sys
from PIL import Image, ImageOps

B = os.path.dirname(os.path.abspath(__file__)); A = os.path.join(B, 'assets', 'img')
UP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(B, 'originals')
im = ImageOps.exif_transpose(Image.open(f'{UP}/stockholm-2026-image.jpg')).convert('RGB')
for w, q, name in ((1600, 86, 'nordic-funds-mines-2026.jpg'), (800, 80, 'nordic-funds-mines-2026-800.jpg')):
    im.resize((w, round(im.height * w / im.width)), Image.LANCZOS).save(f'{A}/{name}', quality=q, optimize=True, progressive=True)
print(Image.open(f'{A}/nordic-funds-mines-2026.jpg').size)
