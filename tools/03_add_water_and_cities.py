import json,zlib,base64,tarfile,numpy as np
from PIL import Image,ImageDraw
W,H=1440,720;n=W*H
raw=open('build/world.bin','rb').read()[:4*n]
a=np.frombuffer(raw,np.uint8).copy().reshape(4,H,W)
def parts(g):
    t=g['type'];c=g['coordinates']
    if t=='LineString':return [c]
    if t=='MultiLineString':return c
    if t=='Polygon':return [c[0]]
    if t=='MultiPolygon':return [p[0] for p in c]
    return []
def flat(c):
    o=[];last=None
    for p in c:
        q=(round(p[0]*100),round(p[1]*100))
        if q!=last:o+=[q[0],q[1]];last=q
    return o
def load(f,minlen):
    out=[]
    for ft in json.load(open(f))['features']:
        ps=[flat(c) for c in parts(ft['geometry'])];ps=[p for p in ps if len(p)>=minlen]
        if ps:out.append([int(ft['properties'].get('scalerank') or 9),ps])
    return out
riv=load('sources/ne_10m_rivers_lake_centerlines.geojson',4);lak=load('sources/ne_10m_lakes.geojson',6)
px=lambda p:((p[0]/100+180)/360*W,(90-p[1]/100)/180*H)
im=Image.new('L',(W,H),0);d=ImageDraw.Draw(im)
for r,ps in riv:
    if r<=8:
        for p in ps:d.line([px(p[i:i+2]) for i in range(0,len(p),2)],fill=1,width=1)
for r,ps in lak:
    for p in ps:
        pts=[px(p[i:i+2]) for i in range(0,len(p),2)]
        if len(pts)>2:d.polygon(pts,fill=2)
wat=np.array(im,np.uint8)
a[0]=np.where((wat==2)&(a[0]>=3),11,a[0])
raw2=a.tobytes()+wat.tobytes()
open('build/world.bin','wb').write(raw2)
open('build/grid.b64','w').write(base64.b64encode(zlib.compress(raw2,9)).decode())
json.dump({'rivers':riv,'lakes':lak},open('build/geo.json','w'),separators=(',',':'))
open('build/topo10.json','w').write(json.dumps(json.load(tarfile.open('sources/world-atlas.tgz').extractfile('package/countries-10m.json')),separators=(',',':')))
m=json.load(open('build/meta.json'))
pp=json.load(open('sources/ne_10m_populated_places_simple.geojson'))['features'];C=[]
for f in pp:
    p=f['properties'];cap=(p.get('featurecla') or '').startswith('Admin-0 capital')
    if p['pop_max']>=100000 or cap:C.append([p['name'],round(f['geometry']['coordinates'][0],2),round(f['geometry']['coordinates'][1],2),int(p['pop_max']),1 if cap else 0])
C.sort(key=lambda c:-c[3]);m['cities']=C
json.dump(m,open('build/meta.json','w'),ensure_ascii=False,separators=(',',':'))
import os
print(len(riv),len(lak),len(C),{k:os.path.getsize(k)//1024 for k in['build/geo.json','build/topo10.json','build/grid.b64','build/meta.json']},'lagos px',int((wat==2).sum()),'rios px',int((wat==1).sum()))
