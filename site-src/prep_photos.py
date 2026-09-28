"""Web versions of the 2026 studio portraits and Forbes Mining Summit stage photos, plus new Open Graph images.
Run once from site-src with the originals in UP (the uploaded files)."""
import os, sys, json
from PIL import Image, ImageDraw, ImageFont, ImageOps

B = os.path.dirname(os.path.abspath(__file__)); A = os.path.join(B, 'assets', 'img')
UP = sys.argv[1] if len(sys.argv) > 1 else '/root/.claude/uploads/3e6d935b-75c2-51e7-92ac-87d8ed38d14f'
def op(k): return ImageOps.exif_transpose(Image.open(f'{UP}/{k}-image.jpg')).convert('RGB')
def save(im, name, w, q=86):
    im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    im.save(f'{A}/{name}', quality=q, optimize=True, progressive=True)
    im.resize((800, round(im.height * 800 / im.width)), Image.LANCZOS).save(f'{A}/{name[:-4]}-800.jpg', quality=80, optimize=True, progressive=True)
    return im.size

sizes = {}
# studio portrait, vertical, arms crossed
sizes['portrait-studio-2026.jpg'] = save(op('f4690f17'), 'portrait-studio-2026.jpg', 1200)
# Forbes Mining Summit: on stage (hero) and with the sponsor wall
sizes['forbes-summit-stage.jpg'] = save(op('92c8d778'), 'forbes-summit-stage.jpg', 2000)
sizes['forbes-summit-sponsors.jpg'] = save(op('cb8cb25a'), 'forbes-summit-sponsors.jpg', 1600)
# square headshot, 1200 px, from the studio head-and-shoulders shot
hs = op('29525539')
hs.crop((743, 60, 2143, 1460)).resize((1200, 1200), Image.LANCZOS).save(f'{A}/michael-meding-headshot-2026.jpg', quality=90, optimize=True, progressive=True)
print(sizes)

# Open Graph image per language, same layout as before with the studio headshot
C = {l: json.load(open(f'{B}/content/{l}.json')) for l in ['en', 'es', 'de', 'ja', 'zh']}
serif = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'; sans = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
cjk_serif = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
cjk_sans = [p for p in ['/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc'] if os.path.exists(p)][0]
def wrap(draw, text, font, width):
    words = text.split(' '); lines = []; cur = ''
    for w in words:
        t = (cur + ' ' + w) if cur else w
        if draw.textlength(t, font=font) <= width: cur = t
        else: lines.append(cur); cur = w
    lines.append(cur); return lines
ph = hs.crop((700, 0, 2250, 1588)).resize((610, 625), Image.LANCZOS)
for l in C:
    og = Image.new('RGB', (1200, 630), '#0b1517'); og.paste(ph, (590, 3))
    grad = Image.new('L', (200, 630)); gd = ImageDraw.Draw(grad)
    for x in range(200): gd.line([(x, 0), (x, 630)], fill=int(255 * (1 - x / 200)))
    og.paste(Image.new('RGB', (200, 630), '#0b1517'), (590, 0), grad)
    d = ImageDraw.Draw(og); cjk = l in ('ja', 'zh')
    d.text((56, 70), 'Michael', font=ImageFont.truetype(serif, 78), fill='white')
    d.text((56, 158), 'Meding', font=ImageFont.truetype(serif, 78), fill='white')
    y = 262
    if cjk:
        d.text((58, y), {'ja': 'マイケル・メディング', 'zh': '迈克尔·梅丁'}[l], font=ImageFont.truetype(cjk_serif, 34, index=0 if l == 'zh' else 1), fill='#b9c9c8'); y += 62
    role = {'en': 'Managing Director, McEwen Copper', 'es': 'Director General, McEwen Copper', 'de': 'Geschäftsführer, McEwen Copper', 'ja': ['マッキュアン・カッパー', 'マネージングディレクター'], 'zh': ['麦克尤恩铜业（McEwen Copper）', '董事总经理']}[l]
    la = {'en': 'Los Azules copper project · San Juan, Argentina', 'es': 'Proyecto de cobre Los Azules · San Juan, Argentina', 'de': 'Kupferprojekt Los Azules · San Juan, Argentinien', 'ja': ['ロス・アスレス銅プロジェクト', 'アルゼンチン・サンフアン州'], 'zh': ['Los Azules铜矿项目', '阿根廷圣胡安省']}[l]
    fnt = ImageFont.truetype(cjk_sans, 27, index=0 if l == 'zh' else 1) if cjk else ImageFont.truetype(sans, 28)
    for line in (role if isinstance(role, list) else wrap(d, role, fnt, 500)): d.text((58, y), line, font=fnt, fill='#e7efee'); y += 40
    y += 6
    fnt2 = ImageFont.truetype(cjk_sans, 24, index=0 if l == 'zh' else 1) if cjk else ImageFont.truetype(sans, 24)
    for line in (la if isinstance(la, list) else wrap(d, la, fnt2, 500)): d.text((58, y), line, font=fnt2, fill='#57d0c0'); y += 36
    d.text((58, 560), 'MEDING.DEV', font=ImageFont.truetype(sans, 20), fill='#86a3a2')
    og.save(f'{A}/og2-{l}.jpg', quality=86, optimize=True)
print('ok')
