import json,zlib,base64,tarfile,subprocess,os,urllib.request
import numpy as np
from PIL import Image,ImageDraw
W,H=1440,720
topo=json.load(tarfile.open('sources/world-atlas.tgz').extractfile('package/countries-10m.json'))
sc,tr=topo['transform']['scale'],topo['transform']['translate']
arcs=[]
for a in topo['arcs']:
    x=y=0;p=[]
    for dx,dy in a:
        x+=dx;y+=dy;p.append((x*sc[0]+tr[0],y*sc[1]+tr[1]))
    arcs.append(p)
def ring(ix):
    pts=[]
    for i in ix:
        p=arcs[i] if i>=0 else arcs[~i][::-1]
        pts+=p if not pts else p[1:]
    return pts
geoms=topo['objects']['countries']['geometries']
names=[g['properties']['name'] for g in geoms]
def px(p):return[((p[0]+180)/360*W),((90-p[1])/180*H)]
polys=[]
for k,g in enumerate(geoms):
    P=g['arcs'] if g['type']=='MultiPolygon' else [g['arcs']]
    for poly in P:
        r=[px(p) for p in ring(poly[0])]
        xs=[q[0] for q in r];ys=[q[1] for q in r]
        polys.append(((max(xs)-min(xs))*(max(ys)-min(ys)),k+1,r))
polys.sort(key=lambda t:-t[0])
im=Image.new('L',(W,H),0);d=ImageDraw.Draw(im)
for _,k,r in polys:
    if names[k-1]!='Antarctica' and max(q[0] for q in r)-min(q[0] for q in r)>W/2:
        r2=[(q[0]+W if q[0]<W/2 else q[0],q[1]) for q in r]
        d.polygon(r2,fill=k);d.polygon([(x-W,y) for x,y in r2],fill=k)
    else:d.polygon([tuple(q) for q in r],fill=k)
country=np.array(im,dtype=np.uint8)
T='sources/earth-visualization/package/dist/textures/topography_2048x1024.png'
topo_a=np.array(Image.open(T).convert('L').resize((W,H),Image.LANCZOS))
bm=np.array(Image.open('sources/basemap-data/mpl_toolkits/basemap_data/bmng.jpg').convert('RGB').resize((W,H),Image.LANCZOS)).astype(float)/255
et=np.array(Image.open('sources/basemap-data/mpl_toolkits/basemap_data/etopo1.jpg').convert('RGB').resize((W,H),Image.LANCZOS))
latrow=(90-(np.arange(H)+.5)/H*180)[:,None]*np.ones((1,W))
country=np.where((topo_a>2)&(latrow<-60)&(country==0),names.index('Antarctica')+1,country).astype(np.uint8)

lt=json.load(tarfile.open('sources/world-atlas.tgz').extractfile('package/land-10m.json'));lsc,ltr=lt['transform']['scale'],lt['transform']['translate']
larcs=[]
for a in lt['arcs']:
    x=y=0;p=[]
    for dx,dy in a:
        x+=dx;y+=dy;p.append((x*lsc[0]+ltr[0],y*lsc[1]+ltr[1]))
    larcs.append(p)
def lring(ix):
    pts=[]
    for i in ix:
        p=larcs[i] if i>=0 else larcs[~i][::-1]
        pts+=p if not pts else p[1:]
    return pts
li=Image.new('L',(W,H),0);ld=ImageDraw.Draw(li)
for poly in lt['objects']['land']['geometries'][0]['arcs']:
    r=[tuple(px(p)) for p in lring(poly[0])]
    xs=[q[0] for q in r];ys=[q[1] for q in r]
    if max(xs)-min(xs)<12 and max(ys)-min(ys)<12:
        ld.polygon(r,fill=255);ld.line(r+[r[0]],fill=255,width=1)
land10=np.array(li)>0
from scipy import ndimage
newisl=land10&(country==0)
dist,(iy,ix)=ndimage.distance_transform_edt(country==0,return_indices=True)
country=np.where(newisl&(dist<100),country[iy,ix],country).astype(np.uint8)
newisl=newisl&(latrow>-60)
country=np.where(newisl&(country==0),0,country)
print('pixeles de islas añadidos',int(newisl.sum()))
land=(country>0)|newisl
r,g,b=bm[...,0],bm[...,1],bm[...,2]
v=bm.max(2);mn=bm.min(2);s=(v-mn)/np.maximum(v,1e-6)
lat=np.abs(90-(np.arange(H)+.5)/H*180)[:,None]*np.ones((1,W))
bio=np.zeros((H,W),np.uint8)
rd=et[...,0]
bio[:]=np.where(rd>95,2,np.where(rd>40,1,0))
L=np.full((H,W),6,np.uint8)
green=(g>=r*0.97)&(g>=b)
L=np.where(green&(v<.30)&(lat<28),8,L)
L=np.where(green&(v<.36)&(lat>=28),7,L)
L=np.where(green&(v>=.30)&(v<.5)&(lat<28),7,L)
L=np.where(green&(v>=.36)&(v<.5)&(lat>=28),7,L)
L=np.where(~green&(s>.18)&(v>.45)&(lat<50),5,L)
L=np.where(~green&(s>.18)&(v>.45)&(lat<50)&(r>g*1.25),5,L)
L=np.where((lat>58)&(L!=7),4,L)
L=np.where((v>.82)&(s<.2),3,L)
L=np.where((topo_a>150)&(L!=3),9,L)
L=np.where((topo_a>215)&(L!=3),10,L)
bio=np.where(land,L,bio).astype(np.uint8)
bio=np.where(newisl,np.where(np.abs(latrow)<40,7,6),bio).astype(np.uint8)
depth=np.where(land,0,rd).astype(np.uint8)
elev=np.where(land,topo_a,0).astype(np.uint8)

def clean(a):
    a=a.copy();bad=[]
    for y in range(1,H-1):
        n=(a[y-1]==a[y+1]).mean();m=((a[y]!=a[y-1])&(a[y]!=a[y+1])).mean()
        if n>.85 and m>.25:bad.append(y)
    for y in bad:a[y]=a[y-1]
    return a,bad
bio,bad=clean(bio);print('filas corregidas',bad)
for y in bad:
    country[y]=country[y-1];elev[y]=elev[y-1];depth[y]=depth[y-1]
raw=bio.tobytes()+country.tobytes()+elev.tobytes()+depth.tobytes()
open('build/world.bin','wb').write(raw)
Image.fromarray(bio*20).save('build/preview_bio_raw.png')
pal=np.array([[23,55,102],[36,81,143],[74,134,194],[240,244,246],[154,168,154],[216,189,120],[141,189,88],[61,140,69],[28,104,56],[122,115,106],[228,231,234]],np.uint8)
Image.fromarray(pal[bio]).resize((1080,540)).save('build/preview_biomes.png')
pp=json.load(open('sources/ne_50m_populated_places_simple.geojson'))['features']
cities=[[f['properties']['name'],round(f['geometry']['coordinates'][0],2),round(f['geometry']['coordinates'][1],2),f['properties']['pop_max'],1 if 'capital' in (f['properties'].get('featurecla') or '') else 0] for f in pp if f['properties']['pop_max']>=1000000 or (f['properties']['pop_max']>=300000 and 'capital' in (f['properties'].get('featurecla') or ''))]
json.dump({'W':W,'H':H,'names':names,'cities':cities},open('build/meta.json','w'),ensure_ascii=False)
json.dump(topo,open('build/topo.json','w'),separators=(',',':'))
open('build/grid.b64','w').write(base64.b64encode(zlib.compress(raw,9)).decode())
print(len(cities),len(names),os.path.getsize('build/grid.b64'),os.path.getsize('build/topo.json'))
