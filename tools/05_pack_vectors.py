import json,zlib,base64,tarfile
from shapely.geometry import LineString
def simp(flat,tol,minlen):
    pts=[(flat[i]/100,flat[i+1]/100) for i in range(0,len(flat),2)]
    if len(pts)<3:return flat if len(flat)>=minlen else None
    s=list(LineString(pts).simplify(tol,preserve_topology=False).coords)
    o=[];last=None
    for x,y in s:
        q=(round(x*100),round(y*100))
        if q!=last:o+=[q[0],q[1]];last=q
    return o if len(o)>=minlen else None
G=json.load(open('build/geo.json'))
def red(L,minlen):
    out=[]
    for r,ps in L:
        q=[s for s in (simp(p,.012,minlen) for p in ps) if s]
        if q:out.append([r,q])
    return out
rv=red(G['rivers'],4);lk=red(G['lakes'],6)
topo=json.load(tarfile.open('sources/world-atlas.tgz').extractfile('package/countries-10m.json'));t=topo['transform']
arc=[]
for a in topo['arcs']:
    x=y=0;f=[]
    for dx,dy in a:
        x+=dx;y+=dy;f+=[round((x*t['scale'][0]+t['translate'][0])*100),round((y*t['scale'][1]+t['translate'][1])*100)]
    s=simp(f,.012,4)
    arc.append(s if s else f[:2]*2)
V=json.dumps({'meta':json.load(open('build/meta.json')),'geo':{'rivers':rv,'lakes':lk},'arc':arc,'isl':json.load(open('build/isl.json'))},separators=(',',':'),ensure_ascii=False)
z=zlib.compress(V.encode(),9);open('build/vector.b64','w').write(base64.b64encode(z).decode())
print('json',len(V)//1024,'KB comprimido',len(z)//1024,'KB',len(rv),len(lk),len(arc))
