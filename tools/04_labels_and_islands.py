import json,tarfile
tf=tarfile.open('sources/world-atlas.tgz')
def dec(topo):
    sc,tr=topo['transform']['scale'],topo['transform']['translate'];arcs=[]
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
    return ring
c=json.load(tf.extractfile('package/countries-10m.json'));ring=dec(c);labels=[]
for g in c['objects']['countries']['geometries']:
    P=g['arcs'] if g['type']=='MultiPolygon' else [g['arcs']];best=None
    for poly in P:
        r=ring(poly[0]);xs=[q[0] for q in r];ys=[q[1] for q in r]
        if max(xs)-min(xs)>300:continue
        a=(max(xs)-min(xs))*(max(ys)-min(ys))
        if not best or a>best[0]:best=(a,(max(xs)+min(xs))/2,(max(ys)+min(ys))/2,max(xs)-min(xs))
    if best and best[0]>1.5:labels.append([g['properties']['name'],round(best[1],2),round(best[2],2),round(best[3],1)])
m=json.load(open('build/meta.json'));m['labels']=labels;json.dump(m,open('build/meta.json','w'),ensure_ascii=False,separators=(',',':'))
l=json.load(tf.extractfile('package/land-10m.json'));ring=dec(l);isl=[]
for poly in l['objects']['land']['geometries'][0]['arcs']:
    r=ring(poly[0]);xs=[q[0] for q in r];ys=[q[1] for q in r]
    if max(xs)-min(xs)<.6 and max(ys)-min(ys)<.6:
        f=[];last=None
        for q in r:
            k=(round(q[0]*1000),round(q[1]*1000))
            if k!=last:f+=[k[0],k[1]];last=k
        if len(f)<6:f=[round((max(xs)+min(xs))/2*1000),round((max(ys)+min(ys))/2*1000)]
        isl.append(f)
json.dump(isl,open('build/isl.json','w'),separators=(',',':'))
print(len(labels),'etiquetas',len(isl),'islas pequeñas',sum(1 for i in isl if len(i)==2),'puntos')
