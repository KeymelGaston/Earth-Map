"""Assembles the standalone viewer (docs/index.html) and copies the final data files."""
import json,io,base64,os,shutil
from PIL import Image
D='sources/basemap-data/mpl_toolkits/basemap_data/'
imgs={}
for k,f in [('a','shadedrelief.jpg'),('s','bmng.jpg')]:
    im=Image.open(D+f).convert('RGB').resize((4096,2048),Image.LANCZOS)
    b=io.BytesIO();im.save(b,'JPEG',quality=80,optimize=True,progressive=True)
    imgs[k]=base64.b64encode(b.getvalue()).decode()
tpl=open('viewer/template.html',encoding='utf-8').read()
html=tpl.replace('__DATA__',open('build/grid.b64').read()).replace('__VJ__',open('build/vector.b64').read()).replace('__IMGS__',json.dumps(imgs))
os.makedirs('docs',exist_ok=True);open('docs/index.html','w',encoding='utf-8').write(html)
os.makedirs('data',exist_ok=True)
shutil.copy('build/world.bin','data/earth_1440x720.bin');shutil.copy('build/meta.json','data/earth_meta.json')
print('viewer %d KB'%(len(html)//1024))
