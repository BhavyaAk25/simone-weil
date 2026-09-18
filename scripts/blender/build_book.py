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
    serif='/System/Library/Fonts/Supplemental/Baskerville.ttc'
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

def book():
    root=empty('BookRoot')
    box('BackCover',(1.24,0,.024),(2.55,3.30,.092),'leather',root,.039)
    # Slightly inset endpaper and a second leather lip create a substantial binding.
    box('Back board inset',(1.24,0,.076),(2.48,3.23,.023),'leather_dark',root,.026)
    cover=empty('CoverHinge',(0,0,.26),root)
    box('FrontCover',(-1.24,0,-.236),(2.55,3.30,.092),'leather',cover,.039)
    box('Front board inset',(-1.24,0,-.184),(2.48,3.23,.023),'leather_dark',cover,.026)
    for inset,weight in [(.0,.006),(.046,.003)]:
        for x in [-2.34+inset,-.14-inset]:box('Blind tooled gilt rule',(x,0,-.284),(weight,2.94-2*inset,.002),'brass',cover,0)
        for y in [-1.47+inset,1.47-inset]:box('Blind tooled gilt rule',(-1.24,y,-.284),(2.20-2*inset,weight,.002),'brass',cover,0)
    for x in [-2.23,-.25]:
        for y in [-1.34,1.34]:
            for sign in [-1,1]:line('Embossed corner flourish',(x,y,-.285),(x+sign*.055,y+.05,-.285),.004,'brass',cover)
    text('Front title','THE LIFE OF\nSIMONE WEIL',(-1.24,.94,-.287),.235,'brass',cover,rotation=(math.pi,0,math.pi))
    portrait('Front portrait',(-1.24,-.18,-.289),1.04,cover,(math.pi,0,math.pi))
    text('Front subtitle','A LIFE IN 12 CHAPTERS',(-1.24,-1.08,-.287),.067,'brass',cover,rotation=(math.pi,0,math.pi))
    spine=empty('Spine')
    box('Spine leather',(-.045,0,.255),(.13,3.30,.49),'leather',spine,.054)
    for y in [-1.40,-1.23,1.23,1.40]:
        box('Raised sewn band',(-.118,y,.255),(.021,.052,.447),'leather_dark',spine,.015)
        box('Fine spine gilt',(-.132,y,.255),(.004,.009,.405),'brass',spine,.001)
    text('Spine title','The Life of Simone Weil',(-.134,.20,.255),.142,'brass',spine,rotation=(math.pi/2,0,-math.pi/2))
    portrait('Spine portrait',(-.135,-.91,.255),.31,spine,(math.pi,math.pi/2,0),artistic=True)
    animate(spine,'scale',[(0,(1,1,1)),(60,(1,1,.2))],'open')
    # Individually curved layers, alternating tiny offsets: no rectangular page blocks.
    rng=random.Random(104)
    for side,parent,zoff in [(1,root,0),(-1,cover,-.26)]:
        for i in range(32):
            width=2.39+rng.uniform(-.008,.009)
            curved_sheet('Bound ivory leaf',side,.090+i*.00323+zoff,parent,'paper_edge' if i%5==0 else 'paper',width,3.105+rng.uniform(-.008,.008))
        curved_sheet('RightPage' if side==1 else 'LeftPage',side,.202+zoff,parent)
    animate(cover,'rotation_euler',[(0,(0,math.pi,0)),(60,(0,0,0))],'open')
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
    # Seam thread remains beneath the gutter and never intersects the turning leaf.
    for y in [-1.31,-.86,-.42,0,.42,.86,1.31]:
        line('Binding stitch',(-.03,y-.021,.073),(.03,y+.021,.073),.005,'tobacco',root)
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
            # Curl along the sheet's arc length: the free edge rolls inward as
            # the sheet rises, keeping the turn inside the reading composition.
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
    box('Ribbon',(1.90,-1.47,.074),(.095,.32,.007),'red',root,.003)
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

def apartment_scene(basic=False):
    # Layered Paris street at the rear, with a taller home on the right and two desks in front.
    distant=hinge('Paris garden skyline fold',-.91,1.39)
    canopy('Tuileries silhouettes',0,.01,2.08,.75,distant,'paper_shadow',9)
    street=hinge('Paris townhouse fold',-.84,1.20)
    for xx,w,h in [(-.72,.53,.91),(-.14,.62,1.14),(.49,.61,.98)]:facade('Paris roofline',xx,0,w,h,street,3,2)
    home=hinge('Apartment facade fold',1.09,.98)
    facade('Family apartment',0,0,1.31,1.64,home,4,3)
    # Lower portico and classical doorway establish a place rather than generic blocks.
    # Low paper rails and a lamp enrich the street without invading the reserved writing rectangle.
    promenade=hinge('Paris promenade fold',.24,.81)
    for i in range(14):line('Promenade railing',(-.28+i*.043,0,0),(-.28+i*.043,0,.23),.010,'ink_soft',promenade)
    line('Promenade rail',(-.32,0,.235),(.32,0,.235),.014,'stone',promenade)
    lamp('Paris street lamp',-.30,-.025,.74,promenade)
    trees=hinge('Plane tree fold',1.97,.68)
    tree('Plane tree',0,0,1.23,trees,'leaf',13)
    # Separate real card hinges avoid turning a thick desk group through the page.
    study1=hinge('Simone desk fold',.77,-.22)
    desk('Simone desk',0,0,0,study1,1.02);figure('Young Simone',-.25,-.023,.62,study1,True)
    study2=hinge('Andre desk fold',1.53,.11)
    desk('Andre desk',0,0,0,study2,.87)
    figure('Andre',.25,-.020,.67,study2,True)
    for i in range(4):
        box('Stacked reading volume',(-.11,-.023,.52+i*.020),(.20,.014,.019),['tobacco','paper','ink_soft','paper_light'][i],study2,.001)
    garden=hinge('Front botanical fold',1.96,-.52)
    tree('Olive paper branches',0,0,.60,garden,'leaf',42)
    return [distant,street,home,promenade,trees,study1,study2,garden]

def education_scene():
    # Detailed institutional pediment at the back; the large empty arch is genuinely cut through.
    rear=hinge('School horizon fold',-.70,1.30)
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
    desk('Lecture writing desk',0,0,0,ledge,1.27);figure('Student Simone',-.38,-.024,.80,ledge)
    shelf=hinge('Library paper fold',1.97,.28)
    polygon('Library shelf back',[(-.24,0),(.24,0),(.24,1.08),(-.24,1.08)],.012,0,'tobacco',shelf)
    for zz in [.035,.37,.70,1.06]:box('Library shelf',(0,-.014,zz),(.50,.025,.025),'paper_light',shelf,.002)
    rng=random.Random(70)
    for zz in [.05,.385,.715]:
        for i in range(7):
            hh=rng.uniform(.21,.28);xx=-.20+i*.065
            box('Detailed bound volume',(xx,-.020,zz+hh/2),(.051,.014,hh),['paper','ink_soft','brass','stone','tobacco'][i%5],shelf,.002)
            for dz in [.027,hh-.027]:box('Tiny book gilt band',(xx,-.029,zz+dz),(.041,.003,.004),'paper_edge',shelf,0)
    botanical=hinge('Bay laurel fold',.36,.55)
    tree('Laurel of learning',0,0,.99,botanical,'leaf',59)
    return [rear,frame,ledge,shelf,botanical]

def normalize_hinges():
    # Convert each card's children into hinge-local coordinates, reducing only
    # layered stock depth. Faces and silhouettes retain their authored outlines.
    for h in [o for o in bpy.context.scene.objects if o.get('page_hinge')]:
        children=[o for o in bpy.context.scene.objects if o.parent==h and o.type=='MESH']
        for o in children:
            o.data.transform(o.matrix_basis);o.matrix_basis=Matrix.Identity(4)
            for v in o.data.vertices:v.co.y*=.60
        miny=min(v.co.y for o in children for v in o.data.vertices)
        shift=.003-miny
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

def build_book():
    reset();root,leaf=book();batch_book_layers();export_asset('book')
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
    normalize_hinges()
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
