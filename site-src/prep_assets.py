import os, re, json, shutil
from PIL import Image, ImageDraw, ImageFont
B=os.path.dirname(os.path.abspath(__file__)); A=os.path.join(B,'assets'); SRC=os.path.join(B,'..','site','public')
os.makedirs(A+'/img',exist_ok=True)
# keep legacy folders so old links and previews keep working
if os.path.exists(A+'/images'): shutil.rmtree(A+'/images')
shutil.copytree(SRC+'/images',A+'/images')
for f in os.listdir(SRC+'/img'): shutil.copy(SRC+'/img/'+f, A+'/img/'+f)
# colour original of the Washington 2026 photo replaces the monochrome version
_w=Image.open(SRC+'/images/benchmark-giga-usa-2026.jpg').convert('RGB'); _w.resize((1600,round(_w.height*1600/_w.width)),Image.LANCZOS).save(A+'/img/washington-2026.jpg',quality=84,optimize=True,progressive=True)
shutil.copy(SRC+'/favicon.svg',A+'/favicon.svg')
used=['portrait.jpg','site-delegations.jpg','ifc-2025.jpg','entrepreneur-2025.jpg','diploma-2024.jpg','new-york-2024.jpg','washington-2026.jpg']
for f in used:
    im=Image.open(A+'/img/'+f).convert('RGB'); w,h=im.size
    im.resize((800,round(h*800/w)),Image.LANCZOS).save(A+'/img/'+f[:-4]+'-800.jpg',quality=80,optimize=True,progressive=True)
# square headshot from the cut-out portrait
hs=Image.open(SRC+'/images/michael-meding.jpg').convert('RGB'); m=min(hs.size)
hs.crop((0,0,m,m)).save(A+'/img/michael-meding-headshot.jpg',quality=92,optimize=True)
# apple touch icon
ic=Image.new('RGB',(180,180),'#0b1517'); d=ImageDraw.Draw(ic)
f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',92)
d.text((90,92),'M',font=f,fill='#57d0c0',anchor='mm'); ic.save(A+'/apple-touch-icon.png')
# Open Graph image per language
C={l:json.load(open(f'{B}/content/{l}.json')) for l in ['en','es','de','ja','zh']}
serif='/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'; sans='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
cjk_serif='/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
cjk_sans=[p for p in ['/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc','/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc'] if os.path.exists(p)][0]
photo=Image.open(A+'/img/portrait.jpg').convert('RGB')
def wrap(draw,text,font,width):
    words=list(text) if any(ord(ch)>0x3000 for ch in text) else text.split(' ')
    joiner='' if len(words)==len(text) else ' '
    lines=[];cur=''
    for w in words:
        t=(cur+joiner+w) if cur else w
        if draw.textlength(t,font=font)<=width: cur=t
        else: lines.append(cur); cur=w
    lines.append(cur); return lines
for l,c in C.items():
    og=Image.new('RGB',(1200,630),'#0b1517')
    ph=photo.crop((560,0,1600,1066)).resize((610,625)); og.paste(ph,(590,3))
    grad=Image.new('L',(200,630)); 
    for x in range(200): ImageDraw.Draw(grad).line([(x,0),(x,630)],fill=int(255*(1-x/200)))
    og.paste(Image.new('RGB',(200,630),'#0b1517'),(590,0),grad)
    d=ImageDraw.Draw(og)
    cjk=l in ('ja','zh')
    d.text((56,70),'Michael',font=ImageFont.truetype(serif,78),fill='white')
    d.text((56,158),'Meding',font=ImageFont.truetype(serif,78),fill='white')
    y=262
    if cjk:
        d.text((58,y),{'ja':'マイケル・メディング','zh':'迈克尔·梅丁'}[l],font=ImageFont.truetype(cjk_serif,34,index=0 if l=='zh' else 1),fill='#b9c9c8'); y+=62
    role={'en':'Managing Director, McEwen Copper','es':'Director General, McEwen Copper','de':'Geschäftsführer, McEwen Copper','ja':['マッキュアン・カッパー','マネージングディレクター'],'zh':['麦克尤恩铜业（McEwen Copper）','董事总经理']}[l]
    la={'en':'Los Azules copper project · San Juan, Argentina','es':'Proyecto de cobre Los Azules · San Juan, Argentina','de':'Kupferprojekt Los Azules · San Juan, Argentinien','ja':['ロス・アスレス銅プロジェクト','アルゼンチン・サンフアン州'],'zh':['Los Azules铜矿项目','阿根廷圣胡安省']}[l]
    fnt=ImageFont.truetype(cjk_sans,27,index=0 if l=='zh' else 1) if cjk else ImageFont.truetype(sans,28)
    for line in (role if isinstance(role,list) else wrap(d,role,fnt,500)): d.text((58,y),line,font=fnt,fill='#e7efee'); y+=40
    y+=6
    fnt2=ImageFont.truetype(cjk_sans,24,index=0 if l=='zh' else 1) if cjk else ImageFont.truetype(sans,24)
    for line in (la if isinstance(la,list) else wrap(d,la,fnt2,500)): d.text((58,y),line,font=fnt2,fill='#57d0c0'); y+=36
    d.text((58,560),'MEDING.DEV',font=ImageFont.truetype(sans,20),fill='#86a3a2')
    og.save(f'{A}/img/og-{l}.jpg',quality=86,optimize=True)
# per-language diagram SVG from the approved diagram
old=open(os.path.join(B,'..','old_diagram.svg'),encoding='utf-8').read()
key={'leads since 2022':'leads','Managing Director':'md','owns':'owns','approved 2025':'approved','President':'president','Vice President':'vp','President 2026':'president26','Entrepreneur of the Year ×2':'eoy','shareholder':'shareholder','collaboration':'collab','Calingasta':'calingasta','San Juan':'sanjuan'}
style=('<style>.e{stroke:#2e4e53;stroke-width:1.4}.l{font:500 11px/1 "Public Sans","Helvetica Neue",Arial,"Hiragino Sans","Noto Sans CJK JP","Noto Sans JP","PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif;fill:#9bb5b4}'
       '.n rect{fill:#0f1d20;stroke:#3b6268;stroke-width:1.2}.n text{font:600 13.5px/1 "Public Sans","Helvetica Neue",Arial,sans-serif;fill:#e7efee}'
       '.p rect{fill:#57d0c0;stroke:#57d0c0}.p text{fill:#062022;font-size:17px;font-weight:700}.o rect{fill:#123236;stroke:#57d0c0}</style>')
for l,c in C.items():
    dg=c['home']['diagram']
    s=old
    s=re.sub(r'<title.*?</desc>','',s,flags=re.S)
    def rep(m):
        en=re.search(r'<tspan class="l-en">([^<]*)</tspan>',m.group(0)).group(1)
        lab=dg[key[en]] if en in key and m.group(1).find('eg-l')>=0 else en
        return f'<text{m.group(1).replace("eg-l","l")}>{lab.replace("&","&amp;")}</text>'
    s=re.sub(r'<text([^>]*)>(?:<tspan[^>]*>[^<]*</tspan>)+</text>',rep,s)
    s=re.sub(r'<a href="[^"]*" class="eg-n(?: eg-(\w))?">',lambda m:'<g class="n'+(' '+m.group(1) if m.group(1) in ('p','o') else '')+'">',s)
    s=s.replace('</a>','</g>').replace('class="eg-e"','class="e"')
    s=s.replace('<svg class="eg" viewBox="0 0 820 380" role="img" aria-labelledby="eg-t eg-d">',f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 820 380" width="820" height="380">{style}')
    assert 'tspan' not in s and '<a ' not in s, l
    open(f'{A}/img/diagram-{l}.svg','w',encoding='utf-8').write(s)
print('assets ok', sorted(os.listdir(A+'/img')))
