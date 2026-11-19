"""Reproducible paper theatre assets. Run in Blender 5.1 background mode.

  blender --background --factory-startup --python scripts/blender/build_book.py -- --milestone
  blender --background --factory-startup --python scripts/blender/build_book.py -- --chapters 3 4 ... 12

Coordinates are authored Z-up and exported as glTF Y-up. Portrait and facade
textures are bundled locally; no external models, simulation or UI state is needed.
"""
import bpy, math, random, sys, json, argparse, struct
from pathlib import Path
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[2]
MODELS = ROOT / 'public/models'
POSTERS = ROOT / 'public/posters'
SOURCE = ROOT / 'assets/source'
for path in (MODELS, POSTERS, SOURCE): path.mkdir(parents=True, exist_ok=True)
FPS = 30
M = {}

def srgb(c):
    c = c / 255
    return c / 12.92 if c < .04045 else ((c + .055) / 1.055) ** 2.4

def material(name, hexcolor, rough=.8, metallic=0):
    c = tuple(srgb(int(hexcolor[i:i+2], 16)) for i in (0,2,4))
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*c,1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*c,1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metallic
    M[name] = m
    return m

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    M.clear()
    material('paper','E8DDC7')
    material('paper_edge','C6B79A')
    material('paper_light','F2E8D4')
    material('paper_shadow','B0A187')
    material('leather','785039',.72)
    material('leather_dark','372017',.68)
    material('wood','422A20',.6)
    material('tobacco','785039')
    material('ink','27221E')
    material('ink_soft','454941')
    material('brass','A78B56',.55,.38)
    material('water','6E7774')
    material('red','7D392F')
    material('warm_light','CFB476')
    material('stone','D1C2A4')
    material('slate','424A47')
    material('leaf','626652')
    material('leaf_light','89896D')
    material('glass','8D907F')
    material('gilt_dark','856B3F',.6,.23)
    # Chapter 1-2 art pass (18 November): deeper foliage, bark and garden colours.
    material('leaf_deep','4C5243')
    material('bark','6A5342')
    material('terracotta','9C5A40')
    material('flower','B98A3E')
    material('cobble','A39A8B')
    material('cobble_light','C4BBAA')
    facade_path=ROOT/'assets/source/textures/paris-facade.webp'
    if facade_path.exists():
        material('paris_engraving','FFFFFF',.86)
        texture=bpy.data.images.load(str(facade_path));texture.pack()
        node=M['paris_engraving'].node_tree.nodes.new('ShaderNodeTexImage');node.image=texture
        M['paris_engraving'].node_tree.links.new(node.outputs['Color'],M['paris_engraving'].node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    # Shared packed texture: minute fibres on ivory and subtle leather grain.
    rng = random.Random(42)
    for key, amplitude in [('paper',.052),('leather',.09)]:
        size=256
        tex = bpy.data.images.new(f'{key}_grain',size,size)
        base = M[key].diffuse_color[:3]
        pixels=[]
        for y in range(size):
            for x in range(size):
                n = rng.gauss(0,amplitude) + .01*math.sin(x*.18+y*.08)
                pixels.extend([min(1,max(0,v*(1+n))) for v in base]+[1])
        tex.colorspace_settings.name='Linear Rec.709'
        tex.pixels = pixels
        tex.pack()
        nd=M[key].node_tree.nodes.new('ShaderNodeTexImage'); nd.image=tex
        M[key].node_tree.links.new(nd.outputs['Color'],M[key].node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    scene=bpy.context.scene
    scene.render.fps=FPS
    scene.render.engine='CYCLES'
    scene.cycles.samples=24
    scene.cycles.use_denoising=True
    scene.render.resolution_x=1440
    scene.render.resolution_y=1000
    scene.render.resolution_percentage=100
    scene.view_settings.view_transform='AgX'
    scene.world=bpy.data.worlds.new('Walnut reading room')
    scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.12,.09,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.45

def attach(obj,mat,parent=None):
    obj.data.materials.append(M[mat])
    if parent: obj.parent=parent
    return obj

def empty(name,loc=(0,0,0),parent=None):
    obj=bpy.data.objects.new(name,None); bpy.context.collection.objects.link(obj)
    obj.location=loc
    if parent: obj.parent=parent
    return obj

def box(name,loc,size,mat='paper',parent=None,bevel=.008):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,0))
    obj=bpy.context.object; obj.name=name
    obj.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    obj.location=loc
    attach(obj,mat,parent)
    if bevel:
        mod=obj.modifiers.new('Soft cut edges','BEVEL');mod.width=bevel;mod.segments=2
        bpy.context.view_layer.objects.active=obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj

def polygon(name,points,depth,y,mat='paper',parent=None):
    # points in the x/z plane, with thin, visible card-stock thickness.
    n=len(points)
    verts=[(x,y-d/2,z) for d in (depth,-depth) for x,z in points]
    faces=[tuple(range(n)),tuple(range(2*n-1,n-1,-1))]
    faces += [(i,i+n,(i+1)%n+n,(i+1)%n) for i in range(n)]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    uv=mesh.uv_layers.new(name='UVMap')
    for p in mesh.polygons:
        for li in p.loop_indices:
            v=mesh.vertices[mesh.loops[li].vertex_index].co;uv.data[li].uv=(v.x*.8,v.z*.8)
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
    attach(obj,mat,parent)
    return obj

def line(name,a,b,width,mat='ink',parent=None):
    a=Vector(a); b=Vector(b)
    obj=box(name,(a+b)/2,(width,width,(b-a).length),mat,parent,bevel=0)
    obj.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    return obj

def disk(name,x,y,z,r,mat,parent=None,n=48):
    return polygon(name,[(x+r*math.cos(i*math.tau/n),z+r*math.sin(i*math.tau/n)) for i in range(n)],.013,y,mat,parent)

def text(name,body,loc,size,mat='ink',parent=None,rotation=(math.pi/2,0,0),align='CENTER'):
    c=bpy.data.curves.new(name,'FONT');c.body=body;c.size=size;c.align_x=align;c.align_y='CENTER';c.extrude=.0006;c.resolution_u=3
    serif=str(ROOT/'node_modules/@fontsource/cormorant-garamond/files/cormorant-garamond-latin-600-normal.woff')
    if not Path(serif).exists():serif='/System/Library/Fonts/Supplemental/Baskerville.ttc'
    if Path(serif).exists():
        try: c.font=bpy.data.fonts.load(serif)
        except Exception: pass
    obj=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(obj);obj.location=loc;obj.rotation_euler=rotation
    attach(obj,mat,parent)
    bpy.context.view_layer.objects.active=obj;obj.select_set(True)
    bpy.ops.object.convert(target='MESH');obj.select_set(False)
    return obj

def portrait(name,loc,width,parent,rotation,artistic=False):
    material_name='simone_engraving' if artistic else 'simone_portrait'
    if material_name not in M:
        mat=material(material_name,'FFFFFF',.82)
        filename='simone-weil-spine.jpg' if artistic else 'simone-weil-portrait.png'
        image=bpy.data.images.load(str(ROOT/'assets/source/textures'/filename))
        image.pack()
        node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=image
        mat.node_tree.links.new(node.outputs['Color'],mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    height=width*(4/3 if artistic else 868/657)
    bpy.ops.mesh.primitive_plane_add(size=1)
    obj=bpy.context.object;obj.name=name
    obj.scale=(width,height,1)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    obj.location=loc;obj.rotation_euler=rotation
    attach(obj,material_name,parent)
    # A thin brass edge keeps the photograph inset like a bound frontispiece.
    for x in [-width/2-.009,width/2+.009]:
        box(name+' border',(x,0,-.001),(.010,height+.028,.002),'brass',obj,0)
    for y in [-height/2-.009,height/2+.009]:
        box(name+' border',(0,y,-.001),(width+.028,.010,.002),'brass',obj,0)
    return obj

def animate(obj,path,values,clip):
    for frame,value in values:
        setattr(obj,path,value);obj.keyframe_insert(data_path=path,frame=frame)
    action=obj.animation_data.action
    action.name=f'{clip}_{obj.name}'
    obj.animation_data.action=None
    track=obj.animation_data.nla_tracks.new();track.name=clip
    strip=track.strips.new(clip,int(values[0][0]),action)
    strip.name=clip
    strip.action_frame_start=values[0][0];strip.action_frame_end=values[-1][0]

def paper_height(x,y):
    u=max(0,min(1,(abs(x)-.018)/2.4));v=(y+1.55)/3.1
    return .202+.115*math.sin(math.pi*u)*math.exp(-1.8*u)-.007*u*u*math.cos((v-.5)*math.pi)

def hinge(name,x,y):
    h=empty(name,(x,y,paper_height(x,y)+.004))
    animate(h,'rotation_euler',[(0,(math.pi/2,0,0)),(30,(0,0,0))],'unfold')
    h['page_hinge']=True
    return h

def curved_sheet(name,side,zbase,parent,mat='paper',width=2.40,length=3.10):
    verts=[];faces=[];nx=48 if name in ['LeftPage','RightPage'] else 28;ny=8 if name in ['LeftPage','RightPage'] else 3
    for j in range(ny+1):
        for i in range(nx+1):
            u=i/nx;v=j/ny
            curl=.115*math.sin(math.pi*u)*math.exp(-u*1.8)
            # A slight dip at each fore-edge makes the stack read as real leaves.
            z=zbase+curl-.007*u*u*math.cos((v-.5)*math.pi)
            verts.append((side*(.018+u*width),(v-.5)*length,z))
    for j in range(ny):
        for i in range(nx):
            q=j*(nx+1)+i;faces.append((q,q+1,q+nx+2,q+nx+1))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    uv=mesh.uv_layers.new(name='UVMap')
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            v=mesh.vertices[mesh.loops[li].vertex_index].co;uv.data[li].uv=(abs(v.x)/2.4,(v.y+1.55)/3.1)
    ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob);attach(ob,mat,parent)
    if name in ['LeftPage','RightPage']:
        sol=ob.modifiers.new('Paper thickness','SOLIDIFY');sol.thickness=.005
        bpy.context.view_layer.objects.active=ob;bpy.ops.object.modifier_apply(modifier=sol.name)
    return ob

# ---- Book object (Stripe-quality rebuild, 18 November 2026) -----------------
# One continuous skinned leather binding (back board, rounded spine, front
# board, edges and turn-ins), bent by a chain of 11 bones that follows an
# analytic spine curve; two backed page blocks with paper top, toned sheet-line
# edges, endpaper sheets and silk headbands, and a "Closed" thickness morph
# that rounds the spine/concaves the fore-edge and closes the gap between the
# blocks. Atlas constants are shared with scripts/make-cover-textures.py.
BK_XJ,BK_XF,BK_BT,BK_TS,BK_YH=.06,2.49,.042,.020,1.645   # joint x, fore-edge x, board, spine shell, half height
BK_THICK=.52                    # closed outer thickness (CoverHinge pivot at .26)
BK_PIVOT=(0.0,.26)
BK_L_CLOSED,BK_L_OPEN=.52,.12   # spine Hermite handle length closed/open
BK_BONES=11
BK_CORNER=.05                   # plan-view corner radius of the boards
BLOCK_BOTTOM=.045               # page blocks rest on the pastedowns
BLOCK_TOP_CLOSED=.2585          # closed: both blocks flatten to meet (2*.26 - 3 mm gap)
BLOCK_ROUND=.035                # rounding shift of the middle sheets toward the spine
U_BACK,U_SPINE,U_FRONT=(.01,.43),(.43,.57),(.57,.99)
V_OUT,V_IN=(.012,.848),(.875,.990)

def _rot(a,p):
    """Rotate (x,z) about the cover pivot by a (Blender rotation about +Y)."""
    x,z=p[0]-BK_PIVOT[0],p[1]-BK_PIVOT[1]
    return (BK_PIVOT[0]+x*math.cos(a)+z*math.sin(a),BK_PIVOT[1]-x*math.sin(a)+z*math.cos(a))

def _hermite(u,a):
    """Outer spine curve at cover angle a (pi closed, 0 open): point, unit tangent."""
    p0=(BK_XJ,0.0);t0=(-1.0,0.0)
    p1=_rot(a,(-BK_XJ,0.0));c,s=math.cos(a),math.sin(a);t1=(-c,s)   # arrival direction
    L=BK_L_OPEN+(BK_L_CLOSED-BK_L_OPEN)*(a/math.pi)
    h00,h10,h01,h11=2*u**3-3*u**2+1,u**3-2*u**2+u,-2*u**3+3*u**2,u**3-u**2
    d00,d10,d01,d11=6*u**2-6*u,3*u**2-4*u+1,-6*u**2+6*u,3*u**2-2*u
    P=tuple(h00*p0[i]+h10*L*t0[i]+h01*p1[i]+h11*L*t1[i] for i in (0,1))
    D=tuple(d00*p0[i]+d10*L*t0[i]+d01*p1[i]+d11*L*t1[i] for i in (0,1))
    n=math.hypot(*D) or 1
    return P,(D[0]/n,D[1]/n)

def _spine_arc(a=math.pi,n=400):
    pts=[_hermite(i/n,a)[0] for i in range(n+1)]
    cum=[0.0]
    for i in range(n):cum.append(cum[-1]+math.dist(pts[i],pts[i+1]))
    return cum

def _spine_u_at_arc(frac):
    cum=_spine_arc();total=cum[-1];target=frac*total
    for i in range(len(cum)-1):
        if cum[i+1]>=target:
            t=(target-cum[i])/max(1e-9,cum[i+1]-cum[i]);return (i+t)/(len(cum)-1)
    return 1.0

def _sgnpow(v,e):return math.copysign(abs(v)**e,v)

def _ease(s):return s*s*(3-2*s)

def _cover_angle(frame):return math.pi*(1-_ease(min(1,max(0,frame/60))))

def binding_stations():
    """Cross-section stations from the back fore-edge to the front fore-edge,
    in the closed rest pose: outer point, inner point, region, spine u,
    atlas U (outer), physical arc s."""
    st=[];e=.5;r=BK_BT/2
    def board(front):
        out=[]
        # Fore-edge round (superellipse) from the tip to the flat face.
        cx=BK_XF-r
        for k in range(7):
            phi=math.pi/2*k/6            # 0 at tip
            dx=r*_sgnpow(math.cos(phi),e);dz=r*_sgnpow(math.sin(phi),e)
            o=(cx+dx,r-dz);i=(cx+dx,r+dz)
            out.append((o,i,'round',phi))
        # Flat face with a joint groove near the spine.
        xs=[cx-.04*t for t in (.25,.5,1)]+[cx-.04-(cx-.04-(BK_XJ+.09))*t for t in (.2,.4,.6,.8,1.)]
        xs+=[BK_XJ+.09-.09*t for t in (1/6,2/6,3/6,4/6,5/6)]
        for x in xs:
            g=.0075*math.exp(-((x-(BK_XJ+.032))/.012)**2)            # hinge groove
            ramp=min(1,max(0,(x-BK_XJ)/.07));th=BK_TS+(BK_BT-BK_TS)*_ease(ramp)
            out.append(((x,g),(x,th+g*.5),'board',x))
        if front:
            out=[(( _rot(math.pi,(-o[0],o[1])) ),( _rot(math.pi,(-i[0],i[1])) ),reg,val) for o,i,reg,val in out]
        return out
    back=board(False)
    for o,i,reg,val in back:st.append(dict(o=o,i=i,region='back',kind=reg,val=val))
    # Spine: stations evenly spaced in arc length (u excludes the joint ends).
    for k in range(1,24):
        u=_spine_u_at_arc(k/24);P,T=_hermite(u,math.pi);n=(-T[1],T[0])   # outward
        st.append(dict(o=P,i=(P[0]-BK_TS*n[0],P[1]-BK_TS*n[1]),region='spine',kind='spine',val=k/24,u=u))
    front=board(True)
    for o,i,reg,val in reversed(front):st.append(dict(o=o,i=i,region='front',kind=reg,val=val))
    # Physical arc length along the outer path and atlas U.
    s=0.0;prev=None
    for d in st:
        if prev:s+=math.dist(prev,d['o'])
        d['s']=s;prev=d['o']
    flat=(BK_XF-BK_BT/2)-BK_XJ
    for d in st:
        if d['region']=='spine':d['U']=U_SPINE[0]+(U_SPINE[1]-U_SPINE[0])*d['val']
        else:
            x=d['o'][0] if d['region']=='back' else d['o'][0]
            if d['kind']=='round':
                f=1-d['val']/(math.pi/2)               # 0 at the flat face, 1 at the tip
                d['U']=U_BACK[0]-.01*f if d['region']=='back' else U_FRONT[1]+.01*f
            else:
                t=(x-BK_XJ)/flat                       # 0 at the joint, 1 at the fore-edge face
                d['U']=U_BACK[1]-(U_BACK[1]-U_BACK[0])*t if d['region']=='back' else U_FRONT[0]+(U_FRONT[1]-U_FRONT[0])*t
        # Plan-view corner rounding of the boards.
        if d['region']=='spine':d['Y']=BK_YH
        else:
            dist=BK_XF-d['o'][0];rc=BK_CORNER
            d['Y']=BK_YH-rc+math.sqrt(max(0,rc*rc-max(0,rc-dist)**2)) if dist<rc else BK_YH
    return st

def binding_bone_frame(u,a):
    P,T=_hermite(u,a)
    X=Vector((T[0],0,T[1]));Yv=Vector((0,1,0));Z=X.cross(Yv)
    m=Matrix.Identity(4)
    for r in range(3):m[r][0],m[r][1],m[r][2]=X[r],Yv[r],Z[r]
    m[0][3],m[1][3],m[2][3]=P[0],0,P[1]
    return m

def build_binding():
    st=binding_stations();n=len(st)
    # Loop around the cross-section: outer stations, then inner stations back.
    loop=[(k,'o') for k in range(n)]+[(k,'i') for k in range(n-2,0,-1)]
    NB,NY=5,9
    verts=[];uvs={};uv1={};rows=[]
    def point(d,side,row):
        o,i=Vector((d['o'][0],0,d['o'][1])),Vector((d['i'][0],0,d['i'][1]))
        if d['kind']=='round' and d['val']<1e-6:i=o
        m=(o+i)/2;p=o if side=='o' else i;b=(o-i).length/2
        kind,idx=row
        if kind=='mid':
            y=(d['Y']-b)*idx;q=p.copy()
        else:
            phi=math.pi/2*idx/NB;sgn=1 if kind=='head' else -1
            c=_sgnpow(math.cos(phi),.5);q=m+(p-m)*c
            y=sgn*((d['Y']-b)+b*_sgnpow(math.sin(phi),.5))
        return Vector((q.x,y,q.z)),y,b
    rowspec=[('tail',NB-j) for j in range(NB)]+[('mid',-1+2*j/(NY-1)) for j in range(NY)]+[('head',j+1) for j in range(NB)]
    grid=[]
    for li,(k,side) in enumerate(loop):
        col=[]
        for row in rowspec:
            p,y,b=point(st[k],side,row);col.append(len(verts));verts.append(p)
        grid.append(col)
    faces=[];face_meta=[]
    L=len(loop)
    for li in range(L):
        lj=(li+1)%L
        for r in range(len(rowspec)-1):
            faces.append((grid[li][r],grid[lj][r],grid[lj][r+1],grid[li][r+1]));face_meta.append((li,lj,r))
    mesh=bpy.data.meshes.new('Binding');mesh.from_pydata([tuple(v) for v in verts],[],faces);mesh.update()
    # Materials: leather everywhere except the inner face of the spine (lining).
    for name in ['leather','crash']:mesh.materials.append(M[name])
    ua=mesh.uv_layers.new(name='UVMap');ub=mesh.uv_layers.new(name='Physical')
    yb=BK_YH-BK_BT/2
    def atlas(k,side,row,y,face_side):
        d=st[k]
        if face_side=='o':
            U=d['U'];
            kind,idx=row
            if kind=='mid':V=V_OUT[0]+(yb-y)/(2*yb)*(V_OUT[1]-V_OUT[0])
            else:
                f=idx/NB;V=V_OUT[0]*(1-f) if kind=='head' else V_OUT[1]+.012*f
            return (U,1-V)
        U=d['U'];kind,idx=row
        t=(yb-max(-yb,min(yb,y)))/(2*yb)
        V=V_IN[0]+t*(V_IN[1]-V_IN[0])
        return (min(.999,max(.001,U)),1-V)
    for poly,(li,lj,r) in zip(mesh.polygons,face_meta):
        ka,sa=loop[li];kb,sb=loop[lj]
        face_side='o' if (sa=='o' and sb=='o') else 'i'
        inner_spine=face_side=='i' and st[ka]['region']=='spine' and st[kb]['region']=='spine'
        poly.material_index=1 if inner_spine and rowspec[r][0]=='mid' and rowspec[r+1][0]=='mid' else 0
        for corner,li_x,r_x in zip(poly.loop_indices,(li,lj,lj,li),(r,r,r+1,r+1)):
            k,side=loop[li_x]
            p,y,b=point(st[k],side,rowspec[r_x])
            ua.data[corner].uv=atlas(k,side,rowspec[r_x],y,face_side)
            # Physical units for the tiled grain: outer arc length and length along y.
            kind,idx=rowspec[r_x]
            if kind=='mid':v1=-y
            else:
                # Across the head/tail round the grain advances by arc length, not y.
                arc=b*math.pi/2*idx/NB
                v1=-((st[k]['Y']-b)+arc) if kind=='head' else (st[k]['Y']-b)+arc
            ub.data[corner].uv=(st[k]['s']/.6,v1/.6)
    for poly in mesh.polygons:poly.use_smooth=True
    obj=bpy.data.objects.new('Binding',mesh);bpy.context.collection.objects.link(obj)
    # Skin weights by station: rigid boards, spine shared between neighbouring bones.
    groups=[obj.vertex_groups.new(name=f'binding.{b:02}') for b in range(BK_BONES)]
    for li,(k,side) in enumerate(loop):
        d=st[k]
        if d['region']=='back':w=[(0,1.)]
        elif d['region']=='front':w=[(BK_BONES-1,1.)]
        else:
            x=d['val']*(BK_BONES-1);b0=int(math.floor(x));f=x-b0
            w=[(b0,1-f)]+([(b0+1,f)] if f>1e-6 and b0+1<BK_BONES else [])
        for vi in grid[li]:
            for b,wt in w:groups[b].add([vi],wt,'REPLACE')
    return obj,st

def build_spine_rig(binding):
    data=bpy.data.armatures.new('Spine rig');arm=bpy.data.objects.new('Spine',data)
    bpy.context.collection.objects.link(arm);bpy.context.view_layer.objects.active=arm
    bpy.ops.object.select_all(action='DESELECT');arm.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    us=[k/(BK_BONES-1) for k in range(BK_BONES)]
    # Bones sit on the outer curve, evenly spaced in arc length.
    us=[_spine_u_at_arc(u) for u in us]
    for k,u in enumerate(us):
        P,_=_hermite(u,math.pi)
        b=data.edit_bones.new(f'binding.{k:02}');b.head=(P[0],0,P[1]);b.tail=(P[0],.08,P[1]);b.roll=0
    bpy.ops.object.mode_set(mode='OBJECT')
    binding.parent=arm
    mod=binding.modifiers.new('Skin','ARMATURE');mod.object=arm
    rest=[binding_bone_frame(u,math.pi) for u in us]
    for f in range(61):
        a=_cover_angle(f)
        for k,u in enumerate(us):
            pb=arm.pose.bones[f'binding.{k:02}'];pb.rotation_mode='QUATERNION'
            D=binding_bone_frame(u,a)@rest[k].inverted()
            pb.matrix=D@data.bones[pb.name].matrix_local
            pb.keyframe_insert('location',frame=f);pb.keyframe_insert('rotation_quaternion',frame=f)
    ad=arm.animation_data;action=ad.action;action.name='open_Spine';ad.action=None
    tr=ad.nla_tracks.new();tr.name='open';strip=tr.strips.new('open',0,action);strip.name='open'
    return arm,us

def block_mesh(name,side):
    """A backed page block for one side (side=1 right, -1 left), open pose, with
    paper top, sheet-line edges, endpaper underside and silk headbands."""
    top=lambda x,y:paper_height(x,y)
    rr=.014;x0=.018;xend=2.418;ys=[-1.55+3.1*j/12 for j in range(13)];NZ=6
    roll=[(x0-rr*math.sin(a),-rr*(1-math.cos(a))) for a in [math.pi/2*k/4 for k in range(4,0,-1)]]
    xs=[x0+2.4*(k/36)**1.35 for k in range(37)]
    stations=[(x,dz) for x,dz in roll]+[(x,0.0) for x in xs]
    zt=lambda i,y:top(max(x0,stations[i][0]),y)+stations[i][1]
    verts=[];faces=[];mats=[];uvs=[];closed=[]
    def V(x,y,z,uv,fz):
        verts.append((x,y,z));uvs.append(uv)
        # Closed morph: keep each sheet's height fraction, flatten the top to
        # meet the other block, and shift middle sheets toward the spine.
        t=top(max(x0,x),y);f=min(1,max(0,(z-BLOCK_BOTTOM)/(t-BLOCK_BOTTOM)))
        f=fz if fz is not None else f
        zc=BLOCK_BOTTOM+f*(BLOCK_TOP_CLOSED-BLOCK_BOTTOM)+(z-BLOCK_BOTTOM-f*(t-BLOCK_BOTTOM))
        closed.append((x-BLOCK_ROUND*(2*f-f*f),y,zc))
        return len(verts)-1
    def quadgrid(rows,mat):
        for r in range(len(rows)-1):
            for c in range(len(rows[r])-1):
                faces.append((rows[r][c],rows[r][c+1],rows[r+1][c+1],rows[r+1][c]));mats.append(mat)
    # Paper top (with gutter roll).
    rows=[[V(x,y,zt(i,y),(abs(x)/2.4,(y+1.55)/3.1),None) for i,(x,_) in enumerate(stations)] for y in ys]
    quadgrid(rows,0)
    # Head and tail edges, fore-edge, back: toned sheet lines. v = height fraction.
    for y,flip in [(-1.55,False),(1.55,True)]:
        rows=[[V(x,y,BLOCK_BOTTOM+(zt(i,y)-BLOCK_BOTTOM)*k/NZ,(x/2.5,k/NZ),k/NZ) for i,(x,_) in enumerate(stations)] for k in range(NZ+1)]
        if flip:rows=[list(reversed(r)) for r in rows]
        quadgrid(rows,1)
    for x,ix,flip in [(xend,len(stations)-1,False),(stations[0][0],0,True)]:
        rows=[[V(x,y,BLOCK_BOTTOM+(zt(ix,y)-BLOCK_BOTTOM)*k/NZ,((y+1.55)/3.1,k/NZ),k/NZ) for y in ys] for k in range(NZ+1)]
        if flip:rows=[list(reversed(r)) for r in rows]
        quadgrid(rows,1)
    rows=[[V(x,y,BLOCK_BOTTOM,(x/.9,y/.9),0.0) for x,_ in stations] for y in ys]
    rows=[list(reversed(r)) for r in rows];quadgrid(rows,2)
    # Headbands: silk beads along the back of the block at head and tail.
    for yc in (-1.556,1.556):
        ring=10;zs=[BLOCK_BOTTOM+.004+(top(x0,yc)-.006-BLOCK_BOTTOM)*k/8 for k in range(9)]
        rows=[]
        for k,z in enumerate(zs):
            row=[]
            for j in range(ring+1):
                a=math.tau*j/ring
                f=(z-BLOCK_BOTTOM)/(top(x0,yc)-BLOCK_BOTTOM)
                row.append(V(.012+.0095*math.cos(a),yc+.0095*math.sin(a),z,(k/8,j/ring),f))
            rows.append(row)
        quadgrid(rows,3)
    if side<0:
        verts=[(-x,y,z) for x,y,z in verts];closed=[(-x,y,z) for x,y,z in closed]
        faces=[tuple(reversed(f)) for f in faces]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    for m in ['paper','page_edge','endpaper','headband']:mesh.materials.append(M[m])
    uv=mesh.uv_layers.new(name='UVMap')
    for poly,mi in zip(mesh.polygons,mats):
        poly.material_index=mi;poly.use_smooth=mi==3 or mi==0
        for li in poly.loop_indices:
            vi=mesh.loops[li].vertex_index;uv.data[li].uv=uvs[vi]
    return mesh,closed

def page_block(name,side,parent,zoff):
    mesh,closed=block_mesh(name,side)
    if zoff:
        for v in mesh.vertices:v.co.z+=zoff
        closed=[(x,y,z+zoff) for x,y,z in closed]
    ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob);ob.parent=parent
    ob.shape_key_add(name='Basis');key=ob.shape_key_add(name='Closed')
    for p,c in zip(key.data,closed):p.co=c
    for f in range(61):
        key.value=(_cover_angle(f)/math.pi)**1.3;key.keyframe_insert(data_path='value',frame=f)
    ad=mesh.shape_keys.animation_data;action=ad.action;action.name=f'open_{name}';ad.action=None
    tr=ad.nla_tracks.new();tr.name='open';strip=tr.strips.new('open',0,action);strip.name='open'
    return ob

def flat_plane(name,x0,x1,y0,y1,z,mat,parent,uvscale=None,nx=1,ny=1):
    verts=[(x0+(x1-x0)*i/nx,y0+(y1-y0)*j/ny,z) for j in range(ny+1) for i in range(nx+1)]
    faces=[(j*(nx+1)+i,j*(nx+1)+i+1,(j+1)*(nx+1)+i+1,(j+1)*(nx+1)+i) for j in range(ny) for i in range(nx)]
    if x1<x0:faces=[tuple(reversed(f)) for f in faces]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    uv=mesh.uv_layers.new(name='UVMap')
    for p in mesh.polygons:
        for li in p.loop_indices:
            v=mesh.vertices[mesh.loops[li].vertex_index].co;uv.data[li].uv=(v.x/(uvscale or 1),v.y/(uvscale or 1))
    ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob);attach(ob,mat,parent)
    return ob

def ribbon(parent):
    """Silk marker: from between the leaves at the gutter, over the tail edge
    and the board's square, ending with a swallowtail just past the board."""
    path=[(-1.40,.199),(-1.52,.199),(-1.548,.193),(-1.553,.17),(-1.553,.08),(-1.556,.054),(-1.575,.0455),
          (-1.63,.0445),(-1.652,.041),(-1.664,.030),(-1.676,.014),(-1.695,.004),(-1.735,.0015)]
    xa,xb=.072,.116;verts=[];faces=[]
    for y,z in path:verts+=[(xa,y,z+.0012),(xb,y,z+.0012)]
    last=len(path)-1
    for k in range(last-1):faces.append((2*k,2*k+2,2*k+3,2*k+1))
    notch=len(verts);verts.append(((xa+xb)/2,path[-1][0]+.024,path[-1][1]+.0012))
    k=last-1;faces.append((2*k,2*k+2,notch,2*k+3,2*k+1))
    mesh=bpy.data.meshes.new('Ribbon');mesh.from_pydata(verts,[],faces);mesh.update()
    uv=mesh.uv_layers.new(name='UVMap')
    for p in mesh.polygons:
        p.use_smooth=True
        for li in p.loop_indices:
            v=mesh.vertices[mesh.loops[li].vertex_index].co;uv.data[li].uv=((v.x-xa)/(xb-xa),v.y)
    ob=bpy.data.objects.new('Ribbon',mesh);bpy.context.collection.objects.link(ob);attach(ob,'ribbon',parent)
    sol=ob.modifiers.new('Silk','SOLIDIFY');sol.thickness=.0012;sol.offset=-1
    bpy.context.view_layer.objects.active=ob;bpy.ops.object.modifier_apply(modifier=sol.name)
    return ob

def book():
    material('page_edge','E2D6BD',.85)
    material('endpaper','606648',.82)
    material('headband','8A3A2E',.45)
    material('ribbon','6E2A22',.38)
    material('crash','8A7458',.95)
    root=empty('BookRoot')
    cover=empty('CoverHinge',(0,0,.26),root)
    animate(cover,'rotation_euler',[(f,(0,_cover_angle(f),0)) for f in range(61)],'open')
    # Continuous skinned binding and its spine rig. 'Spine' is the armature,
    # a sibling of BookRoot as before; the 'open' clip bends its bones.
    binding,_=build_binding()
    arm,us=build_spine_rig(binding)
    bpy.context.scene.frame_set(0)
    # Stable marker nodes kept for other code and the validator.
    back=empty('BackCover',(1.27,0,BK_BT/2),root)
    front=empty('FrontCover',(-1.27,0,BK_BT/2-.26),cover)
    empty('Front cover art',(-1.27,0,-.26),cover)
    title=empty('Spine title');title.parent=arm;title.parent_type='BONE';title.parent_bone=f'binding.{BK_BONES//2:02}'
    bpy.context.view_layer.update()
    P,_=_hermite(us[BK_BONES//2],math.pi);title.matrix_world=Matrix.Translation((P[0],0,P[1]))
    # Printed endpapers (pastedowns) inside the leather turn-ins.
    ti=.105;z=BK_BT+.0012
    flat_plane('Back endpaper',BK_XJ+.035,BK_XF-ti,-(BK_YH-ti),BK_YH-ti,z,'endpaper',back,.9,1,1)
    back_ep=bpy.data.objects['Back endpaper'];back_ep.location=(-1.27,0,-BK_BT/2)
    flat_plane('Front endpaper',-(BK_XJ+.035),-(BK_XF-ti),-(BK_YH-ti),BK_YH-ti,z,'endpaper',front,.9,1,1)
    bpy.data.objects['Front endpaper'].location=(1.27,0,-BK_BT/2)
    # Backed page blocks: the top surface is exactly paper_height().
    page_block('RightPage',1,root,0)
    page_block('LeftPage',-1,cover,-.26)
    ribbon(root)
    # Raised reading panel (contract unchanged).
    reading_h=empty('ReadingHinge',(-1.225,-1.43,paper_height(-1.225,-1.43)+.008-.26),cover)
    reading_h['reading_panel']=True
    verts=[(-1.025,0,0),(1.025,0,0),(1.025,2.33,0),(-1.025,2.33,0)]
    mesh=bpy.data.meshes.new('Reading paper panel');mesh.from_pydata(verts,[],[(0,1,2,3)]);mesh.update()
    uv=mesh.uv_layers.new(name='UVMap')
    for li,coord in enumerate([(0,0),(1,0),(1,1),(0,1)]):uv.data[li].uv=coord
    panel=bpy.data.objects.new('ReadingPanel',mesh);bpy.context.collection.objects.link(panel);attach(panel,'paper',reading_h)
    sol=panel.modifiers.new('Thin ivory writing card','SOLIDIFY');sol.thickness=.006;sol.offset=-1
    bpy.context.view_layer.objects.active=panel;bpy.ops.object.modifier_apply(modifier=sol.name)
    animate(reading_h,'rotation_euler',[(0,(0,0,0)),(30,(math.radians(18),0,0))],'reading')
    reading_h['runtime_flat_unless_reading']=True
    # Turning leaf (contract unchanged): four baked curl poses.
    verts=[];faces=[];nx=48;ny=8
    for j in range(ny+1):
        for i in range(nx+1):
            xx=.02+i/nx*2.40;yy=-1.54+j/ny*3.08
            verts.append((xx,yy,paper_height(xx,yy)+.006))
    for j in range(ny):
        for i in range(nx):
            q=j*(nx+1)+i;faces.append((q,q+1,q+nx+2,q+nx+1))
    mesh=bpy.data.meshes.new('Flexible turned leaf');mesh.from_pydata(verts,[],faces);mesh.update()
    leaf=bpy.data.objects.new('TurnPage',mesh);bpy.context.collection.objects.link(leaf);attach(leaf,'paper',root)
    leaf.shape_key_add(name='Basis');keys=[]
    for t in [.25,.5,.75,1.]:
        key=leaf.shape_key_add(name=f'Turn{int(t*100)}');keys.append(key)
        for idx,p in enumerate(key.data):
            u=(idx%(nx+1))/nx;r=.02+u*2.4
            bend=2.6*math.sin(t*math.pi)
            base=t*math.pi-bend/2
            if abs(bend)<1e-6:
                xx=r*math.cos(t*math.pi);zz=r*math.sin(t*math.pi)
            else:
                radius=2.4/bend
                xx=.02*math.cos(base)+radius*(math.sin(base+bend*u)-math.sin(base))
                zz=.02*math.sin(base)+radius*(math.cos(base)-math.cos(base+bend*u))
            p.co=(xx,verts[idx][1],paper_height(r,verts[idx][1])+.006+zz)
    for frame in [0,10.5,21,31.5,42]:
        for k,key in enumerate(keys):
            key.value=1 if abs(frame-(k+1)*10.5)<.1 else 0;key.keyframe_insert(data_path='value',frame=frame)
    ad=leaf.data.shape_keys.animation_data;action=ad.action;action.name='turn_FlexibleLeaf';ad.action=None
    tr=ad.nla_tracks.new();tr.name='turn';st=tr.strips.new('turn',0,action);st.name='turn'
    leaf['runtime_hidden_at_rest']=True
    bpy.context.scene.frame_set(60)
    return root,leaf

def arch(name,x,y,z,width,height,mat,parent):
    radius=width/2; spring=height-radius
    pts=[(x-width/2,z),(x+width/2,z),(x+width/2,z+spring)]
    pts += [(x+radius*math.cos(a),z+spring+radius*math.sin(a)) for a in [i*math.pi/20 for i in range(21)]]
    return polygon(name,pts,.02,y,mat,parent)

def window(name,x,y,z,w,h,parent,arched=False):
    if arched:arch(name+' deep opening',x,y,z,w,h,'slate',parent)
    else:box(name+' deep opening',(x,y,z+h/2),(w,.009,h),'slate',parent,.001)
    # Four narrow framing rules make every window read as joinery, rather than a black square.
    for dx in [-w/2,w/2]:box(name+' jamb',(x+dx,y-.009,z+h/2),(.015,.009,h+.035),'paper_light',parent,.001)
    for zz in [z,z+h]:box(name+' architrave',(x,y-.010,zz),(w+.05,.012,.018),'stone',parent,.001)
    line(name+' mullion',(x,y-.014,z+.012),(x,y-.014,z+h-.012),.009,'paper_edge',parent)
    line(name+' transom',(x-w*.44,y-.014,z+h*.55),(x+w*.44,y-.014,z+h*.55),.008,'paper_edge',parent)
    # One shaded and one illuminated pane, restrained variation in the glazing.
    box(name+' pane light',(x-w*.21,y-.006,z+h*.72),(w*.35,.002,h*.35),'glass',parent,0)
    box(name+' sill',(x,y-.018,z-.016),(w+.06,.022,.020),'paper_light',parent,.002)

def balcony(name,x,y,z,w,parent):
    box(name+' balcony ledge',(x,y-.018,z),(w,.024,.025),'paper_light',parent,.002)
    for i in range(9):
        xx=x-w*.47+w*.94*i/8
        line(name+' ironwork',(xx,y-.037,z+.018),(xx,y-.037,z+.115),.006,'ink_soft',parent)
    line(name+' rail',(x-w/2,y-.039,z+.118),(x+w/2,y-.039,z+.118),.010,'ink_soft',parent)

def facade(name,x,y,w,h,parent,rows=4,cols=3,roof=True):
    engraved=roof and 'paris_engraving' in M
    wall=polygon(name+' carved wall',[(x-w/2,0),(x+w/2,0),(x+w/2,h),(x-w/2,h)],.015,y,'paris_engraving' if engraved else 'paper',parent)
    if engraved:
        for poly in wall.data.polygons:
            for li in poly.loop_indices:
                vertex=wall.data.vertices[wall.data.loops[li].vertex_index].co
                wall.data.uv_layers.active.data[li].uv=((vertex.x-x+w/2)/w,vertex.z/h)
    floor=(h-.21)/rows
    for row in range(0 if engraved else rows):
        z=.17+row*floor
        for col in range(cols):
            xx=x+(col-(cols-1)/2)*w/(cols+.25)
            ww=w/(cols+1.35);hh=min(.255,floor*.71)
            window(name+' casement',xx,y-.014,z,ww,hh,parent,arched=(row==0))
            if row in [1,rows-1]:balcony(name+' balustrade',xx,y-.018,z-.020,ww+.05,parent)
    for zz in [.07,h-.017]+[.135+r*floor for r in range(1,rows)]:
        box(name+' stone stringcourse',(x,y-.018,zz),(w+.025,.027,.016),'stone',parent,.002)
    for xx in [x-w/2+.024,x+w/2-.024]:
        for i in range(int(h/.095)):
            box(name+' corner quoin',(xx,y-.013,.045+i*.095),(.052,.023,.051),'paper_light',parent,.001)
    if roof:
        polygon(name+' slate mansard',[(x-w*.54,h),(x+w*.54,h),(x+w*.40,h+.24),(x-w*.40,h+.24)],.016,y,'slate',parent)
        # Slate courses are sparse enough to remain legible at browser scale.
        for zz in [h+.075,h+.14,h+.205]:line(name+' roof course',(x-w*.45,y-.012,zz),(x+w*.45,y-.012,zz),.003,'glass',parent)
        for k in range(cols):
            xx=x+(k-(cols-1)/2)*w/(cols+.25)
            polygon(name+' dormer stone',[(xx-.067,h+.04),(xx+.067,h+.04),(xx+.067,h+.19),(xx,h+.26),(xx-.067,h+.19)],.012,y-.020,'stone',parent)
            window(name+' dormer',xx,y-.030,h+.07,.074,.105,parent)
        for xx in [x-w*.31,x+w*.31]:
            box(name+' brick chimney',(xx,y,h+.286),(.058,.024,.13),'tobacco',parent,.002)
            for j in range(2):box(name+' terracotta pot',(xx+(j-.5)*.024,y,h+.367),(.017,.020,.043),'red',parent,.001)
        box(name+' roof ridge',(x,y,h+.243),(w*.82,.018,.013),'stone',parent,.002)

def leaf_shape(name,base,tip,width,y,mat,parent):
    a=Vector(base);b=Vector(tip);d=b-a;side=Vector((-d.y,d.x)).normalized()*width
    points=[tuple(a),tuple(a+d*.30+side*.78),tuple(a+d*.62+side),tuple(b),tuple(a+d*.64-side*.6),tuple(a+d*.27-side*.47)]
    return polygon(name,points,.006,y,mat,parent)

def tree(name,x,y,h,parent,mat='leaf',seed=1):
    rng=random.Random(seed)
    polygon(name+' tapered stem',[(x-.018,0),(x+.019,0),(x+.026,h*.79),(x+.008,h*.93),(x-.012,h*.71)],.009,y,mat,parent)
    for i in range(11):
        z=h*(.15+i*.057);sign=(-1)**i
        tip=(x+sign*h*(.18+.11*rng.random()),z+h*(.20+.06*rng.random()))
        line(name+' twig',(x,y,z),(tip[0],y,tip[1]),.009,mat,parent)
        # Stagger overlapping cut leaves so their printed faces are never coplanar.
        layer_y=y-.006-i*.002
        leaf_shape(name+' pointed leaf',(x+sign*.012,z),tip,h*.065,layer_y,mat if i%3 else 'leaf_light',parent)
        tx,tz=tip
        leaf_shape(name+' secondary leaf',(tx-sign*h*.08,tz-h*.06),(tx+sign*h*.105,tz+h*.08),h*.045,layer_y-.001,mat,parent)
    leaf_shape(name+' crown',(x+.01,h*.70),(x+.04,h),h*.08,y-.030,mat,parent)

def canopy(name,x,y,w,h,parent,mat='paper_shadow',seed=1):
    rng=random.Random(seed)
    points=[(x-w*.50,0),(x+w*.5,0)]
    for i in range(36):
        t=i/35*math.pi
        xx=x+w*.5*math.cos(t)
        zz=h*(.50+.50*math.sin(t)) + .038*math.sin(i*2.7)+rng.uniform(-.009,.009)
        points.append((xx,zz))
    polygon(name+' connected crown',points,.009,y,mat,parent)
    # Fine tree branches are cut into the canopy colour with a lighter ink.
    for sign in [-1,1]:
        for i in range(4):
            line(name+' branch',(x,y-.008,.12),(x+sign*w*(.10+i*.09),y-.008,h*(.52+i*.09)),.008,'stone',parent)

def desk(name,x,y,z,parent,scale=1):
    # A single folded paper desk silhouette. Its feet meet the same page hinge as its top.
    s=scale
    pts=[(x-.28*s,0),(x-.25*s,.36*s),(x-.33*s,.40*s),(x-.33*s,.45*s),(x+.32*s,.45*s),(x+.32*s,.40*s),(x+.25*s,.36*s),(x+.28*s,0),(x+.24*s,0),(x+.21*s,.36*s),(x-.21*s,.36*s),(x-.24*s,0)]
    polygon(name+' cut desk',pts,.012,y,'stone',parent)
    line(name+' apron',(x-.26*s,y-.009,.355*s),(x+.26*s,y-.009,.355*s),.018,'tobacco',parent)
    polygon(name+' open notebook',[(x-.12*s,.46*s),(x,.48*s),(x+.12*s,.46*s),(x+.12*s,.54*s),(x,.56*s),(x-.12*s,.54*s)],.006,y-.005,'paper_light',parent)
    line(name+' notebook seam',(x,y-.010,.478*s),(x,y-.010,.558*s),.004,'paper_shadow',parent)
    line(name+' pencil',(x+.12*s,y-.016,.46*s),(x+.21*s,y-.016,.51*s),.008,'ink',parent)

def figure(name,x,y,h,parent,child=False):
    # Continuous coat, head and feet silhouette attached to the page at both shoes.
    pts=[(x-.075*h,0),(x-.063*h,.06*h),(x-.045*h,.27*h),(x-.14*h,.28*h),(x-.115*h,.49*h),(x-.17*h,.40*h),(x-.195*h,.43*h),(x-.09*h,.72*h),(x-.055*h,.76*h)]
    for i in range(19):
        ang=math.radians(225-i*270/18);pts.append((x+.078*h*math.cos(ang),.864*h+.095*h*math.sin(ang)))
    pts += [(x+.057*h,.76*h),(x+.095*h,.70*h),(x+.165*h,.45*h),(x+.138*h,.42*h),(x+.106*h,.52*h),(x+.137*h,.28*h),(x+.04*h,.27*h),(x+.056*h,.055*h),(x+.087*h,.025*h),(x+.087*h,0),(x+.014*h,0),(x,.235*h),(x-.017*h,0)]
    polygon(name+' silhouette',pts,.012,y,'ink',parent)
    line(name+' collar',(x-.045*h,y-.009,.76*h),(x+.045*h,y-.009,.745*h),.008,'stone',parent)

def steps(name,x,y,w,h,parent,count=5):
    for i in range(count):
        zz=h*(i+1)/count;xx=x-w*.5+i*w/count
        polygon(name+' riser',[(xx,0),(xx+w/count+.005,0),(xx+w/count+.005,zz),(xx,zz)],.012,y+i*.004,'paper',parent)
        line(name+' tread',(xx,y-.013,zz),(xx+w/count,y-.013,zz),.010,'paper_light',parent)

def lamp(name,x,y,h,parent):
    line(name+' iron stem',(x,y,0),(x,y,h*.83),.016,'ink_soft',parent)
    polygon(name+' lantern',[(x-.065*h,h*.77),(x+.065*h,h*.77),(x+.087*h,h*.96),(x-.087*h,h*.96)],.010,y,'ink_soft',parent)
    polygon(name+' warm panes',[(x-.04*h,h*.80),(x+.04*h,h*.80),(x+.06*h,h*.93),(x-.06*h,h*.93)],.006,y-.01,'warm_light',parent)
    polygon(name+' crown',[(x-.105*h,h*.96),(x+.105*h,h*.96),(x,h*1.055)],.010,y,'ink_soft',parent)
    for dx in [-.055,.055]:line(name+' lantern bars',(x+dx*h,y-.017,h*.78),(x+dx*h,y-.017,h*.95),.006,'ink',parent)

# ---- Chapter 1-2 art pass helpers (18 November 2026) ----------------------

def lobed(cx,cz,rx,rz,lobes,notch,rng,start=0.0,end=math.tau):
    # Leafy outline: rounded lobes with small notches between leaf tips.
    closed=end-start>=math.tau-1e-6
    n=lobes*4
    pts=[]
    for i in range(n if closed else n+1):
        a=start+(end-start)*i/n
        r=1+.06*math.sin(a*lobes*.5+rng.random())+rng.uniform(-.03,.03)
        if i%2:r*=1-notch
        pts.append((cx+rx*r*math.cos(a),cz+rz*r*math.sin(a)))
    return pts

def broadleaf(name,x,y,h,parent,seed=1,width=.36,bark_patches=False,palette=('leaf_deep','leaf','leaf_light')):
    # A connected tree: forked trunk, limbs, and an irregular crown made of
    # several overlapping lobed masses at three depths (shade, mid, sunlit).
    rng=random.Random(seed)
    t=h*.042
    polygon(name+' forked trunk',[(x-t*1.7,0),(x+t*1.6,0),(x+t*.95,h*.20),(x+t*1.05,h*.44),(x+h*.15,h*.63),(x+h*.12,h*.67),(x+t*.25,h*.52),
        (x-t*.25,h*.56),(x-h*.16,h*.70),(x-h*.19,h*.67),(x-t*1.15,h*.44),(x-t*.95,h*.20)],.010,y,'bark',parent)
    if bark_patches:
        # Plane-tree bark sheds in pale patches.
        for i in range(4):
            zz=h*(.06+i*.09);xx=x+rng.uniform(-.4,.4)*t
            polygon(name+' pale bark',[(xx-t*.55,zz),(xx+t*.5,zz+h*.012),(xx+t*.45,zz+h*.05),(xx-t*.5,zz+h*.04)],.004,y-.006,'stone',parent)
    cz=h*.72;rx=h*width;rz=rx*.80
    masses=[(0,0,.78),(-.52,-.18,.55),(.55,-.14,.58),(-.30,.40,.52),(.28,.44,.50),(.02,.68,.36)]
    # Each overlapping mass gets its own minute depth: coincident faces render
    # black in the Cycles poster even though the browser hides it.
    for k,(dx,dz,sc) in enumerate(masses):
        polygon(name+' shaded crown',lobed(x+dx*rx,cz+dz*rz,rx*sc,rz*sc,12,.16,rng),.007,y-.005-k*.0008,palette[0],parent)
    # Limbs show through gaps between the shaded and sunlit masses.
    for sign,dz in [(-1,.10),(1,.0),(-1,.42),(1,.46)]:
        line(name+' limb',(x,y-.009,h*.60),(x+sign*rx*.55,y-.009,cz+dz*rz),.014,'bark',parent)
    for k,(dx,dz,sc) in enumerate(masses[:5]):
        polygon(name+' mid crown',lobed(x+(dx-.10)*rx,cz+(dz+.10)*rz,rx*sc*.66,rz*sc*.66,10,.16,rng),.007,y-.014-k*.0008,palette[1],parent)
    # Sunlit sprays from the upper left, where the room's window light falls.
    for i in range(6):
        a=math.pi*rng.uniform(.35,.95);r=rng.uniform(.25,.62)
        polygon(name+' sunlit spray',lobed(x+math.cos(a)*r*rx,cz+math.sin(a)*r*rz,rx*.17,rz*.17,8,.18,rng),.006,y-.022-i*.0008,palette[2],parent)
    for i in range(9):
        a=math.pi*(.02+.96*i/8)+rng.uniform(-.08,.08)
        bx=x+math.cos(a)*rx*.86;bz=cz+math.sin(a)*rz*.86
        tip=(bx+math.cos(a)*h*.11,bz+math.sin(a)*h*.09)
        leaf_shape(name+' edge leaf',(bx,bz),tip,h*.030,y-.005,palette[0],parent)

def laurel_bush(name,x,y,h,parent,seed=5,pot=False):
    # Dense laurel built from many pointed leaves in three depth layers.
    rng=random.Random(seed)
    base=h*.30 if pot else 0
    if pot:
        polygon(name+' terracotta pot',[(x-h*.17,0),(x+h*.17,0),(x+h*.21,base*.86),(x-h*.21,base*.86)],.012,y,'terracotta',parent)
        polygon(name+' pot rim',[(x-h*.235,base*.80),(x+h*.235,base*.80),(x+h*.235,base),(x-h*.235,base)],.010,y-.006,'terracotta',parent)
        line(name+' rim shadow',(x-h*.21,y-.012,base*.80),(x+h*.21,y-.012,base*.80),.006,'tobacco',parent)
    polygon(name+' stem',[(x-h*.025,base*.9),(x+h*.025,base*.9),(x+h*.02,h*.55),(x-h*.02,h*.55)],.008,y,'bark',parent)
    cz=base+(h-base)*.55;rx=h*.27;rz=(h-base)*.45
    polygon(name+' shaded mass',lobed(x,cz,rx*.92,rz*.92,18,.10,rng),.007,y-.004,'leaf_deep',parent)
    for layer,mat in enumerate(['leaf_deep','leaf','leaf_light']):
        for i in range(24-layer*6):
            a=rng.uniform(0,math.tau);r=math.sqrt(rng.random())*(1-.18*layer)
            bx=x+math.cos(a)*r*rx*.85;bz=cz+math.sin(a)*r*rz*.85
            direction=a+rng.uniform(-.6,.6);length=h*rng.uniform(.10,.15)
            leaf_shape(name+' laurel leaf',(bx,bz),(bx+math.cos(direction)*length,bz+math.sin(direction)*length),length*.26,y-.010-layer*.007,mat,parent)

def person(name,x,y,h,parent,hair='bob',glasses=False,cape=False,carry=None):
    # Front-facing cut-paper figure with a readable outline: hair, coat, legs, shoes.
    leg=.032*h
    for side in (-1,1):
        lx=x+side*.045*h
        polygon(name+' leg',[(lx-leg,.035*h),(lx+leg,.035*h),(lx+leg*.9,.34*h),(lx-leg*.9,.34*h)],.012,y,'ink',parent)
        # Toes turn slightly outward.
        polygon(name+' shoe',[(lx-leg*1.2+min(0,side)*leg*.7,0),(lx+leg*1.2+max(0,side)*leg*.7,0),(lx+leg*1.1,.045*h),(lx-leg*1.1,.045*h)],.012,y,'ink',parent)
    if cape:
        coat=[(x-.24*h,.27*h),(x+.24*h,.27*h),(x+.12*h,.66*h),(x+.075*h,.735*h),(x-.075*h,.735*h),(x-.12*h,.66*h)]
    else:
        coat=[(x-.15*h,.30*h),(x+.15*h,.30*h),(x+.115*h,.52*h),(x+.155*h,.42*h),(x+.19*h,.44*h),(x+.12*h,.71*h),(x+.075*h,.74*h),
              (x-.075*h,.74*h),(x-.12*h,.71*h),(x-.19*h,.44*h),(x-.155*h,.42*h),(x-.115*h,.52*h)]
    polygon(name+' coat',coat,.012,y,'ink',parent)
    polygon(name+' neck',[(x-.025*h,.72*h),(x+.025*h,.72*h),(x+.025*h,.79*h),(x-.025*h,.79*h)],.012,y,'ink',parent)
    hr=.075*h;hz=.855*h
    polygon(name+' head',[(x+hr*math.cos(i*math.tau/32),hz+hr*1.08*math.sin(i*math.tau/32)) for i in range(32)],.012,y,'ink',parent)
    if hair=='bob':
        # Chin-length bob with a straight fringe, as in her childhood photographs.
        pts=[(x-hr*1.22,hz-hr*.55)]+[(x+hr*1.18*math.cos(a),hz+hr*.1+hr*1.12*math.sin(a)) for a in [math.pi*(1-i/16) for i in range(17)]]+[(x+hr*1.22,hz-hr*.55),(x+hr*.95,hz-hr*.55)]
        polygon(name+' bob hair',pts,.012,y,'ink',parent)
    elif hair=='scarf':
        # Headscarf knotted at the nape, as factory women wore it.
        polygon(name+' headscarf',[(x-hr*1.18,hz-hr*.15),(x-hr*1.1,hz+hr*.7),(x-hr*.5,hz+hr*1.2),(x+hr*.5,hz+hr*1.2),(x+hr*1.1,hz+hr*.7),(x+hr*1.18,hz-hr*.15),(x+hr*1.5,hz-hr*.55),(x+hr*1.2,hz-hr*.65),(x+hr*.95,hz-hr*.3)],.012,y,'ink',parent)
    elif hair=='short':
        polygon(name+' short hair',[(x-hr*1.08,hz+hr*.05)]+[(x+hr*1.08*math.cos(a),hz+hr*.12+hr*1.05*math.sin(a)) for a in [math.pi*(1-i/14) for i in range(15)]]+[(x+hr*1.08,hz+hr*.05)],.012,y,'ink',parent)
    elif hair=='cap':
        polygon(name+' cap',[(x-hr*1.15,hz+hr*.35),(x+hr*1.55,hz+hr*.35),(x+hr*1.1,hz+hr*.55),(x+hr*.8,hz+hr*1.15),(x-hr*.8,hz+hr*1.15),(x-hr*1.1,hz+hr*.6)],.012,y,'ink',parent)
    elif hair=='beret':
        polygon(name+' beret',[(x-hr*1.45,hz+hr*.55),(x+hr*1.3,hz+hr*.75),(x+hr*1.05,hz+hr*1.2),(x-hr*.2,hz+hr*1.38),(x-hr*1.15,hz+hr*1.05)],.012,y,'ink',parent)
        polygon(name+' beret stalk',[(x-hr*.05,hz+hr*1.3),(x+hr*.12,hz+hr*1.3),(x+hr*.1,hz+hr*1.55),(x-hr*.03,hz+hr*1.55)],.012,y,'ink',parent)
    # Light cut details sit one layer forward of the silhouette.
    line(name+' collar',(x-.05*h,y-.009,.735*h),(x+.05*h,y-.009,.725*h),.0075,'stone',parent)
    if glasses:
        for side in (-1,1):
            gx=x+side*hr*.42
            polygon(name+' round lens',[(gx+hr*.30*math.cos(i*math.tau/20),hz+hr*.05+hr*.30*math.sin(i*math.tau/20)) for i in range(20)],.004,y-.009,'paper_light',parent)
            polygon(name+' lens glint',[(gx+hr*.17*math.cos(i*math.tau/16),hz+hr*.05+hr*.17*math.sin(i*math.tau/16)) for i in range(16)],.004,y-.013,'ink_soft',parent)
        line(name+' bridge',(x-hr*.13,y-.012,hz+hr*.1),(x+hr*.13,y-.012,hz+hr*.1),.004,'paper_light',parent)
    if carry=='book':
        polygon(name+' book',[(x+.12*h,.40*h),(x+.22*h,.42*h),(x+.21*h,.55*h),(x+.11*h,.53*h)],.006,y-.010,'red',parent)
        line(name+' book page edge',(x+.215*h,y-.014,.425*h),(x+.205*h,y-.014,.545*h),.004,'paper_light',parent)
    if carry=='paper':
        polygon(name+' newspaper',[(x+.10*h,.42*h),(x+.27*h,.45*h),(x+.26*h,.62*h),(x+.09*h,.59*h)],.005,y-.011,'paper_light',parent)
        for k in range(3):line(name+' newsprint',(x+.12*h,y-.015,(.56-k*.04)*h),(x+.24*h,y-.015,(.585-k*.04)*h),.003,'ink_soft',parent)
    if carry=='case':
        polygon(name+' suitcase',[(x+.12*h,.02*h),(x+.36*h,.02*h),(x+.36*h,.22*h),(x+.12*h,.22*h)],.010,y-.010,'tobacco',parent)
        line(name+' case handle',(x+.20*h,y-.014,.235*h),(x+.28*h,y-.014,.235*h),.008,'bark',parent)
        line(name+' case strap',(x+.24*h,y-.014,.03*h),(x+.24*h,y-.014,.21*h),.005,'bark',parent)
        line(name+' carrying arm',(x+.16*h,y-.008,.45*h),(x+.24*h,y-.008,.24*h),.012,'ink',parent)
    if carry=='pick':
        line(name+' pick handle',(x-.20*h,y-.012,.20*h),(x+.18*h,y-.012,.78*h),.012,'bark',parent)
        polygon(name+' pick head',[(x+.06*h,.86*h),(x+.30*h,.70*h),(x+.31*h,.72*h),(x+.10*h,.90*h)],.008,y-.014,'slate',parent)
    if carry=='basket':
        polygon(name+' harvest basket',[(x+.10*h,.30*h),(x+.34*h,.30*h),(x+.31*h,.44*h),(x+.13*h,.44*h)],.010,y-.010,'flower',parent)
        for k in range(4):line(name+' wicker',(x+.12*h,y-.014,(.32+k*.03)*h),(x+.32*h,y-.014,(.32+k*.03)*h),.003,'bark',parent)
    if carry=='satchel':
        line(name+' satchel strap',(x-.07*h,y-.010,.72*h),(x+.12*h,y-.010,.42*h),.006,'tobacco',parent)
        polygon(name+' satchel',[(x+.07*h,.31*h),(x+.20*h,.31*h),(x+.20*h,.43*h),(x+.07*h,.43*h)],.006,y-.012,'tobacco',parent)

def kerb(name,x,y,w,parent,seed=3):
    # Stone kerb with a row of rounded setts along its top edge.
    rng=random.Random(seed)
    polygon(name+' kerb',[(x-w/2,0),(x+w/2,0),(x+w/2,.05),(x-w/2,.05)],.012,y,'cobble',parent)
    line(name+' kerb edge',(x-w/2,y-.008,.048),(x+w/2,y-.008,.048),.008,'cobble_light',parent)
    xx=x-w/2+.01
    i=0
    while xx<x+w/2-.07:
        cw=rng.uniform(.075,.10);ch=rng.uniform(.045,.06)
        pts=[(xx,.045),(xx+cw,.045)]+[(xx+cw/2+cw/2*math.cos(a),.045+ch*.55+ch*.45*math.sin(a)) for a in [i2*math.pi/8 for i2 in range(9)]]
        polygon(name+' sett',pts,.010,y,'cobble_light' if i%3 else 'cobble',parent)
        xx+=cw+.010;i+=1

def flower_hedge(name,x,y,w,h,parent,seed=4):
    rng=random.Random(seed)
    top=[(x+w/2,0),(x-w/2,0)]
    n=int(w/.045)
    for i in range(n+1):
        xx=x-w/2+w*i/n;top.append((xx,h*(.82+.18*abs(math.sin(i*1.3)))+rng.uniform(-.01,.01)))
    polygon(name+' clipped hedge',top,.012,y,'leaf_deep',parent)
    polygon(name+' sunlit hedge face',[(x-w/2+.02,.02),(x+w/2-.02,.02),(x+w/2-.03,h*.62),(x-w/2+.03,h*.66)],.006,y-.007,'leaf',parent)
    for i in range(int(w/.07)):
        fx=x-w/2+.05+i*.07+rng.uniform(-.015,.015);fz=h*rng.uniform(.62,.86)
        polygon(name+' flower',[(fx+.016*math.cos(a),fz+.016*math.sin(a)) for a in [k*math.tau/10 for k in range(10)]],.004,y-.013,'flower' if i%3 else 'red',parent)

def grass(name,x,y,w,h,parent,seed=6):
    rng=random.Random(seed)
    for layer,mat in enumerate(['leaf_deep','leaf_light']):
        pts=[(x+w/2,0),(x-w/2,0)]
        n=int(w/.03)
        for i in range(n):
            xx=x-w/2+w*(i+.5)/n
            pts.append((xx-.01,h*.25));pts.append((xx+rng.uniform(-.02,.02),h*rng.uniform(.55,1.0)*(1-.25*layer)))
        pts.append((x+w/2,h*.2))
        polygon(name+' grass tuft',pts,.006,y-layer*.007,mat,parent)

def park_bench(name,x,y,s,parent):
    # Green-painted Paris park bench: two iron legs, slatted seat and back.
    for side in (-1,1):
        lx=x+side*.30*s
        polygon(name+' iron leg',[(lx-.025*s,0),(lx+.025*s,0),(lx+.018*s,.20*s),(lx+.05*s*side,.46*s),(lx+.02*s*side,.47*s),(lx-.012*s,.20*s)],.010,y,'slate',parent)
    for zz in [.18,.215]:box(name+' seat slat',(x,y-.006,zz*s),(.70*s,.010,.022*s),'slate',parent,.002)
    for zz in [.30,.35,.40]:box(name+' back slat',(x,y-.006,zz*s),(.72*s,.010,.026*s),'slate',parent,.002)

def paving(name,x,y,w,parent,seed=8):
    rng=random.Random(seed)
    polygon(name+' courtyard edge',[(x-w/2,0),(x+w/2,0),(x+w/2,.07),(x-w/2,.07)],.012,y,'cobble',parent)
    xx=x-w/2+.01;i=0
    while xx<x+w/2-.1:
        fw=rng.uniform(.17,.26)
        polygon(name+' flagstone',[(xx,.012),(xx+fw,.012),(xx+fw,.062),(xx,.062)],.005,y-.007,'cobble_light' if i%2 else 'stone',parent)
        xx+=fw+.012;i+=1

def book_pile(name,x,y,s,parent,seed=9):
    rng=random.Random(seed);zz=0
    for i,(mat,w) in enumerate([('tobacco',.36),('slate',.32),('red',.34),('paper_light',.28),('ink_soft',.30)]):
        hh=.042*s;dx=rng.uniform(-.03,.03)*s
        polygon(name+' bound volume',[(x+dx-w*s/2,zz),(x+dx+w*s/2,zz),(x+dx+w*s/2,zz+hh),(x+dx-w*s/2,zz+hh)],.010,y,mat,parent)
        line(name+' gilt band',(x+dx-w*s*.38,y-.008,zz+hh/2),(x+dx-w*s*.30,y-.008,zz+hh/2),.004,'brass',parent)
        zz+=hh+.004*s
    polygon(name+' satchel',[(x+.25*s,0),(x+.50*s,0),(x+.48*s,.17*s),(x+.27*s,.17*s)],.010,y,'tobacco',parent)
    polygon(name+' satchel flap',[(x+.26*s,.10*s),(x+.49*s,.10*s),(x+.47*s,.18*s),(x+.28*s,.18*s)],.006,y-.007,'bark',parent)
    line(name+' buckle',(x+.375*s,y-.012,.10*s),(x+.375*s,y-.012,.13*s),.010,'brass',parent)

def versailles_planter(name,x,y,h,parent,seed=12):
    # Luxembourg-garden planter: a slatted box with a clipped round orange tree.
    rng=random.Random(seed);bw=h*.36;bh=h*.34
    polygon(name+' planter box',[(x-bw/2,0),(x+bw/2,0),(x+bw/2,bh),(x-bw/2,bh)],.012,y,'slate',parent)
    for dx in [-bw/2,bw/2]:polygon(name+' finial post',[(x+dx-.018,0),(x+dx+.018,0),(x+dx+.018,bh+.035),(x+dx-.018,bh+.035)],.010,y-.006,'ink_soft',parent)
    for k in range(3):line(name+' slat',(x-bw*.4+k*bw*.4,y-.008,.02),(x-bw*.4+k*bw*.4,y-.008,bh-.02),.006,'ink_soft',parent)
    polygon(name+' trunk',[(x-.012,bh),(x+.012,bh),(x+.010,h*.62),(x-.010,h*.62)],.008,y,'bark',parent)
    for k,mat in enumerate(['leaf_deep','leaf']):
        polygon(name+' clipped crown',lobed(x,h*.76,h*.23*(1-.18*k),h*.22*(1-.18*k),16,.07,rng),.007,y-.004-k*.007,mat,parent)
    for i in range(5):
        a=rng.uniform(0,math.tau);r=rng.uniform(.3,.75)
        fx=x+math.cos(a)*r*h*.18;fz=h*.76+math.sin(a)*r*h*.17
        polygon(name+' small orange',[(fx+.017*math.cos(t),fz+.017*math.sin(t)) for t in [k2*math.tau/10 for k2 in range(10)]],.004,y-.020,'flower',parent)

def apartment_scene(basic=False):
    # Right page only: the left page belongs to the raised writing, so nothing
    # tall folds over it. Rear garden and Pantheon dome, the family home, a
    # street promenade, two study desks, and a foreground of kerb, hedge and bench.
    distant=hinge('Luxembourg garden fold',1.22,1.42)
    canopy('Luxembourg chestnut silhouettes',0,.01,2.18,.86,distant,'paper_shadow',9)
    # The dome stands left of the family home so it reads against the shelves.
    dome_x=-.92
    polygon('Pantheon drum',[(dome_x-.20,.55),(dome_x+.20,.55),(dome_x+.20,.92),(dome_x-.20,.92)],.012,-.004,'stone',distant)
    for i in range(7):line('Pantheon colonnade',(dome_x-.17+i*.0567,-.012,.58),(dome_x-.17+i*.0567,-.012,.89),.012,'paper_light',distant)
    polygon('Pantheon dome',[(dome_x-.21,.92)]+[(dome_x+.21*math.cos(a),.92+.24*math.sin(a)) for a in [math.pi*(1-i/20) for i in range(21)]],.012,-.004,'stone',distant)
    polygon('Pantheon lantern',[(dome_x-.035,1.14),(dome_x+.035,1.14),(dome_x+.03,1.24),(dome_x,1.28),(dome_x-.03,1.24)],.010,-.004,'stone',distant)
    home=hinge('Apartment facade fold',1.09,.98)
    facade('Family apartment',0,0,1.31,1.64,home,4,3)
    promenade=hinge('Paris promenade fold',.44,.80)
    for i in range(14):line('Promenade railing',(-.28+i*.043,0,0),(-.28+i*.043,0,.23),.010,'ink_soft',promenade)
    line('Promenade rail',(-.32,0,.235),(.32,0,.235),.014,'stone',promenade)
    lamp('Paris street lamp',-.30,-.025,.74,promenade)
    trees=hinge('Plane tree fold',1.93,.68)
    broadleaf('Paris plane tree',0,0,1.30,trees,13,.34,True)
    study1=hinge('Simone desk fold',.77,-.22)
    desk('Simone desk',0,0,0,study1,1.02)
    person('Young Simone',-.27,-.023,.60,study1,'bob',True,False,'satchel')
    study2=hinge('Andre desk fold',1.53,.11)
    desk('Andre desk',0,0,0,study2,.87)
    person('Andre',.27,-.020,.66,study2,'cap',False,False,'book')
    for i in range(4):
        box('Stacked reading volume',(-.11,-.023,.52+i*.020),(.20,.014,.019),['tobacco','paper','ink_soft','paper_light'][i],study2,.001)
    garden=hinge('Garden planter fold',2.03,-.50)
    versailles_planter('Luxembourg planter',0,0,.62,garden,42)
    hedge=hinge('Flower hedge fold',.62,-1.02)
    flower_hedge('Paris flower bed',0,0,.82,.19,hedge,4)
    bench=hinge('Park bench fold',1.58,-.98)
    park_bench('Luxembourg bench',0,0,.62,bench)
    tufts=hinge('Grass tuft fold',2.16,-1.12)
    grass('Garden grass',0,0,.40,.15,tufts,6)
    street=hinge('Kerb fold',1.22,-1.30)
    kerb('Paris kerb',0,0,2.26,street,3)
    return [distant,home,promenade,trees,study1,study2,garden,hedge,bench,tufts,street]

def education_scene():
    # Detailed institutional pediment at the back; the large empty arch is genuinely cut through.
    # The Lycee Henri-IV front now stands on the right page, seen through the
    # cut window, so nothing tall folds over the writing on the left page.
    rear=hinge('School horizon fold',1.20,1.40)
    facade('Lycee Henri IV',0,0,1.94,.99,rear,3,5,False)
    polygon('Classical pediment',[(-1.03,.99),(1.03,.99),(0,1.40)],.014,0,'stone',rear)
    polygon('Inset tympanum',[(-.84,1.04),(.84,1.04),(0,1.33)],.009,-.012,'paper_light',rear)
    disk('School clock',0,-.021,1.15,.067,'paper_shadow',rear)
    line('Clock hand',(0,-.03,1.15),(.035,-.03,1.18),.007,'ink',rear)
    for xx in [-.92,-.46,0,.46,.92]:box('School pilaster',(xx,-.027,.46),(.028,.024,.91),'paper_light',rear,.001)
    frame=hinge('Unfolding window fold',1.14,.97)
    r=.77; spring=1.04
    for sign in [-1,1]:
        x=sign*.83
        box('Window stone pier',(x,0,spring/2),(.14,.032,spring),'paper',frame,.008)
        for zz in [.06,.13,spring-.035]:box('Carved column capital',(x,-.008,zz),(.20,.047,.040),'paper_light',frame,.003)
        for zz in [.22,.42,.62,.82]:line('Ashlar joint',(x-.066,-.020,zz),(x+.066,-.020,zz),.003,'paper_shadow',frame)
    for i in range(32):
        a=i*math.pi/32;b=(i+1)*math.pi/32
        polygon('Cut arch stone',[(r*math.cos(a),spring+r*math.sin(a)),(r*math.cos(b),spring+r*math.sin(b)),((r+.14)*math.cos(b),spring+(r+.14)*math.sin(b)),((r+.14)*math.cos(a),spring+(r+.14)*math.sin(a))],.033,0,'paper' if i%3 else 'stone',frame)
    line('Fine window mullion',(0,-.007,0),(0,-.007,spring+r-.014),.019,'gilt_dark',frame)
    line('Fine window transom',(-r,-.007,spring),(r,-.007,spring),.019,'gilt_dark',frame)
    for sign in [-1,1]:line('Upper window tracery',(0,-.010,spring),(sign*.54,-.010,spring+.54),.012,'gilt_dark',frame)
    # Brass medallion is structurally carried by the window mullion, never floating.
    disk('Window sun medallion',0,-.013,1.35,.18,'brass',frame)
    for i in range(20):
        a=i*math.tau/20;line('Medallion incised ray',(.08*math.cos(a),-.025,1.35+.08*math.sin(a)),(.165*math.cos(a),-.025,1.35+.165*math.sin(a)),.003,'gilt_dark',frame)
    ledge=hinge('Lecture desk fold',.85,-.34)
    desk('Lecture writing desk',0,0,0,ledge,1.27)
    person('Student Simone',-.40,-.024,.80,ledge,'beret',True,True,'book')
    shelf=hinge('Library paper fold',1.97,.28)
    polygon('Library shelf back',[(-.24,0),(.24,0),(.24,1.08),(-.24,1.08)],.012,0,'tobacco',shelf)
    for zz in [.035,.37,.70,1.06]:box('Library shelf',(0,-.014,zz),(.50,.025,.025),'paper_light',shelf,.002)
    rng=random.Random(70)
    for zz in [.05,.385,.715]:
        for i in range(7):
            hh=rng.uniform(.21,.28);xx=-.20+i*.065
            box('Detailed bound volume',(xx,-.020,zz+hh/2),(.051,.014,hh),['paper','ink_soft','brass','stone','tobacco'][i%5],shelf,.002)
            for dz in [.027,hh-.027]:box('Tiny book gilt band',(xx,-.029,zz+dz),(.041,.003,.004),'paper_edge',shelf,0)
    botanical=hinge('Bay laurel fold',.40,.50)
    laurel_bush('Laurel of learning',0,0,.88,botanical,59)
    court=hinge('Courtyard paving fold',1.22,-1.30)
    paving('School courtyard',0,0,2.26,court,8)
    books=hinge('Book pile fold',1.48,-1.02)
    book_pile('Lecture books',0,0,.72,books,9)
    potted=hinge('Potted laurel fold',2.10,-.98)
    laurel_bush('Potted laurel',0,0,.48,potted,23,True)
    ivy=hinge('Courtyard grass fold',.42,-1.14)
    grass('Courtyard grass',0,0,.50,.13,ivy,15)
    return [rear,frame,ledge,shelf,botanical,court,books,potted,ivy]

def normalize_hinges(stack_folds=False):
    # Convert each card's children into hinge-local coordinates, reducing only
    # layered stock depth. Faces and silhouettes retain their authored outlines.
    hinges=[o for o in bpy.context.scene.objects if o.get('page_hinge')]
    # Folded, a rear card lies on top of the cards in front of it. A tiny
    # per-rank lift keeps those flat layers from sharing a depth (the folded
    # spread is now printed onto the turning leaf).
    rank={h.name:i for i,h in enumerate(sorted(hinges,key=lambda o:o.location.y))}
    for h in hinges:
        children=[o for o in bpy.context.scene.objects if o.parent==h and o.type=='MESH']
        for o in children:
            o.data.transform(o.matrix_basis);o.matrix_basis=Matrix.Identity(4)
            for v in o.data.vertices:v.co.y*=.60
        miny=min(v.co.y for o in children for v in o.data.vertices)
        shift=.003-miny+(.0009*rank[h.name] if stack_folds else 0)
        for o in children:
            for v in o.data.vertices:v.co.y+=shift
        h.location.y-=shift
        h.location.z=paper_height(h.location.x,h.location.y)+.004
        # Ground cut-card feet on the actual curved page rather than a flat plane.
        for o in children:
            for v in o.data.vertices:
                if v.co.z<.018:
                    v.co.z+=paper_height(h.location.x+v.co.x,h.location.y+v.co.y)+.004-h.location.z
        # A minute bow follows the page crown when a broad card is folded.
        # This alters paper depth, never the upright foot height.
        for o in children:
            for v in o.data.vertices:
                folded_page=paper_height(h.location.x+v.co.x,h.location.y-v.co.z)
                v.co.y=max(v.co.y,folded_page+.004-h.location.z)
        h['fold_depth_shift']=shift
    bpy.context.view_layer.update()

def batch_book_layers():
    for parent_name in ['BookRoot','CoverHinge']:
        children=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('Bound ivory leaf') and o.parent and o.parent.name==parent_name]
        if not children:continue
        bpy.ops.object.select_all(action='DESELECT')
        for o in children:o.select_set(True)
        bpy.context.view_layer.objects.active=children[0];bpy.ops.object.join();bpy.context.object.name='Layered page edges '+parent_name

def consolidate():
    # Material batches retain the hinge hierarchy and all original mesh vertices.
    groups={}
    for obj in list(bpy.context.scene.objects):
        if obj.type=='MESH' and obj.parent and obj.parent.animation_data:
            groups.setdefault(obj.parent,[]).append(obj)
    for parent,children in groups.items():
        if len(children)<2:continue
        bpy.ops.object.select_all(action='DESELECT')
        for child in children:child.select_set(True)
        bpy.context.view_layer.objects.active=children[0]
        bpy.ops.object.join()
        bpy.context.object.name=parent.name+' card-stock'

def export_asset(name,objects=None):
    reading=bpy.data.objects.get('ReadingHinge')
    if reading:
        for track in reading.animation_data.nla_tracks:track.mute=True
        reading.rotation_euler=(0,0,0)
        bpy.context.view_layer.update()
        for track in reading.animation_data.nla_tracks:track.mute=False
    bpy.ops.object.select_all(action='DESELECT')
    for obj in (objects if objects is not None else list(bpy.context.scene.objects)):
        if obj.type not in {'LIGHT','CAMERA'}:obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(MODELS/f'{name}.glb'),export_format='GLB',use_selection=True,
        export_animations=True,export_animation_mode='NLA_TRACKS',export_frame_range=False,
        export_force_sampling=True,export_anim_slide_to_zero=True,export_skins=True,
        export_morph=True,export_materials='EXPORT',export_extras=True,export_yup=True)

def studio(camera_target=(0,.10,.75)):
    box('Render walnut desk',(0,0,-.14),(200,200,.18),'wood',bevel=.01)
    # Actual inset wood seams, restrained so the sculpture remains the subject.
    for y in range(-8,9): box('Desk join',(0,y*.65,-.044),(20,.009,.002),'leather_dark',bevel=0)
    for name,loc,power,size,color in [('Window key',(-3,-4,7),850,5,(1,.82,.61)),('Paper fill',(4,-1,5),550,4,(1,.9,.73)),('Back rim',(0,5,5),850,3,(1,.70,.39))]:
        data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=color
        obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj);obj.location=loc
        obj.rotation_euler=(Vector((0,0,.5))-obj.location).to_track_quat('-Z','Y').to_euler()
    data=bpy.data.cameras.new('Poster Camera');obj=bpy.data.objects.new('Poster Camera',data);bpy.context.collection.objects.link(obj)
    obj.location=(3.2,-9.4,6.7);obj.rotation_euler=(Vector(camera_target)-obj.location).to_track_quat('-Z','Y').to_euler()
    data.type='ORTHO';data.ortho_scale=6.65;bpy.context.scene.camera=obj

def save_render(name):
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/f'{name}.blend'))
    if globals().get('SKIP_RENDER',False):return
    bpy.context.scene.render.image_settings.file_format='WEBP'
    bpy.context.scene.render.image_settings.quality=85
    bpy.context.scene.render.filepath=str(POSTERS/f'{name}.webp')
    bpy.ops.render.render(write_still=True)

def texture_cover_for_render():
    # Posters only: the exported GLB keeps plain materials and the browser
    # loads the same images from public/textures (src/book/materials.ts).
    def image(name,colour):
        img=bpy.data.images.load(str(ROOT/'public/textures'/name),check_existing=True)
        img.colorspace_settings.name='sRGB' if colour else 'Non-Color';return img
    def textured(mat_name,colour_name,orm=None,normal=None,uv=None):
        mat=M.get(mat_name)
        if not mat:return
        nodes=mat.node_tree.nodes;links=mat.node_tree.links;bsdf=nodes['Principled BSDF']
        tex=nodes.new('ShaderNodeTexImage');tex.image=image(colour_name,True)
        if uv:
            mapping=nodes.new('ShaderNodeUVMap');mapping.uv_map=uv;links.new(mapping.outputs['UV'],tex.inputs['Vector'])
        links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
        if orm:
            o=nodes.new('ShaderNodeTexImage');o.image=image(orm,False);split=nodes.new('ShaderNodeSeparateColor')
            links.new(o.outputs['Color'],split.inputs['Color'])
            links.new(split.outputs['Green'],bsdf.inputs['Roughness']);links.new(split.outputs['Blue'],bsdf.inputs['Metallic'])
        if normal:
            nm=nodes.new('ShaderNodeTexImage');nm.image=image(normal,False);nmap=nodes.new('ShaderNodeNormalMap')
            links.new(nm.outputs['Color'],nmap.inputs['Color']);links.new(nmap.outputs['Normal'],bsdf.inputs['Normal'])
    textured('leather','cover-color.webp','cover-orm.webp','cover-normal.webp','UVMap')
    textured('page_edge','paper-stock-edge.webp')
    textured('endpaper','endpaper-color.webp')
    textured('headband','binding-headband.webp')

def build_book():
    reset();root,leaf=book();batch_book_layers();export_asset('book')
    texture_cover_for_render()
    leaf.hide_render=True;studio();save_render('book')

def build_chapter(number):
    reset()
    if number==1: apartment_scene()
    elif number==2: education_scene()
    elif 3 <= number <= 12:
        import importlib.util
        spec=importlib.util.spec_from_file_location('story_scenes',Path(__file__).with_name('story_scenes.py'))
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        module.build(number,globals())
    else: raise ValueError('Chapter must be between 1 and 12.')
    bpy.context.scene.frame_set(30)
    normalize_hinges(stack_folds=True)
    consolidate()
    chapter_objects=list(bpy.context.scene.objects)
    export_asset(f'chapter-{number:02}')
    _,leaf=book();batch_book_layers();leaf.hide_render=True
    bpy.context.scene.frame_set(60)
    studio();save_render(f'chapter-{number:02}')

if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    p=argparse.ArgumentParser();p.add_argument('--milestone',action='store_true');p.add_argument('--book',action='store_true');p.add_argument('--chapters',nargs='*',type=int);p.add_argument('--no-render',action='store_true')
    opts=p.parse_args(args)
    SKIP_RENDER=opts.no_render
    if opts.book:
        build_book()
    elif opts.milestone or not opts.chapters:
        build_book();build_chapter(1);build_chapter(2)
    else:
        for number in opts.chapters:build_chapter(number)
    import runpy
    runpy.run_path(str(Path(__file__).with_name('update_manifest.py')),run_name='__main__')
