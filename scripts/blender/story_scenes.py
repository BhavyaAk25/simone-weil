"""Chapter-specific paper theatres using the frozen book hinge contract.
All illustrations are cut meshes, with fine relief detail; no live physics.
"""
import math


def build(number, kit):
    globals().update({k: kit[k] for k in ['hinge','polygon','box','line','disk','text','facade','tree','canopy','desk','figure','steps','lamp','arch','window']})
    return {3: teaching, 4: power, 5: factory, 6: spain, 7: threshold,
            8: force, 9: attention, 10: roots, 11: unfinished, 12: legacy}[number]()


def card(name,x,y,w,h,parent,mat='paper'):
    return polygon(name,[(x-w/2,0),(x+w/2,0),(x+w/2,h),(x-w/2,h)],.014,y,mat,parent)


def manuscript(name,x,y,w,h,parent,mat='paper'):
    card(name,x,y,w,h,parent,mat)
    for i in range(11):
        z=h*(.16+i*.064)
        # Uneven ruled lines suggest handwriting without inventing readable quotations.
        line(name+' ink line',(x-w*.36,y-.012,z),(x+w*(.18+.14*math.sin(i*2.3)**2),y-.012,z),.004,'paper_shadow',parent)
    line(name+' margin',(x-w*.40,y-.012,h*.1),(x-w*.40,y-.012,h*.9),.003,'red',parent)


def book_card(name,x,y,w,h,parent,mat='tobacco'):
    card(name,x,y,w,h,parent,mat)
    for xx in [x-w*.43,x+w*.43]:line(name+' border',(xx,y-.012,.03),(xx,y-.012,h-.03),.005,'brass',parent)
    for zz in [.04,h-.04]:line(name+' border',(x-w*.43,y-.012,zz),(x+w*.43,y-.012,zz),.005,'brass',parent)
    for zz in [h*.72,h*.66,h*.25]:line(name+' blind tooling',(x-w*.29,y-.013,zz),(x+w*.29,y-.013,zz),.008,'paper_edge',parent)


def gear(name,x,y,z,r,parent,mat='gilt_dark'):
    pts=[]
    for i in range(64):
        angle=i*math.tau/64;rr=r*(1 if i%4 in [1,2] else .84)
        pts.append((x+rr*math.cos(angle),z+rr*math.sin(angle)))
    polygon(name+' toothed wheel',pts,.019,y,mat,parent)
    disk(name+' recessed face',x,y-.016,z,r*.68,'paper_shadow',parent)
    for i in range(6):
        a=i*math.tau/6
        line(name+' spoke',(x,y-.024,z),(x+r*.63*math.cos(a),y-.024,z+r*.63*math.sin(a)),.022,mat,parent)
    disk(name+' axle',x,y-.030,z,r*.16,'ink_soft',parent)


def clock_face(name,x,y,z,r,parent):
    disk(name+' bezel',x,y,z,r,'gilt_dark',parent)
    disk(name+' ivory dial',x,y-.013,z,r*.91,'paper_light',parent)
    for i in range(12):
        a=i*math.tau/12
        line(name+' hour mark',(x+r*.70*math.sin(a),y-.025,z+r*.70*math.cos(a)),(x+r*.83*math.sin(a),y-.025,z+r*.83*math.cos(a)),.008,'ink',parent)
    line(name+' minute',(x,y-.032,z),(x+r*.56,y-.032,z+r*.20),.011,'ink',parent)
    line(name+' hour',(x,y-.033,z),(x-r*.16,y-.033,z+r*.40),.016,'ink',parent)


def teaching():
    town=hinge('Le Puy town square fold',-.78,1.32)
    for x,w,h in [(-.60,.56,.78),(0,.64,1.04),(.62,.54,.82)]:facade('Le Puy street',x,0,w,h,town,3,2)
    room=hinge('Classroom portal fold',1.11,1.12)
    for x in [-.81,.81]:
        card('Classroom carved pier',x,0,.13,1.75,room,'stone')
        for z in [.10,1.54,1.68]:box('Classroom capital',(x,-.013,z),(.22,.035,.055),'paper_light',room,.002)
    polygon('Classroom lintel',[(-.95,1.68),(.95,1.68),(.95,1.83),(-.95,1.83)],.015,0,'paper',room)
    card('Chalkboard',0,.014,1.19,1.14,room,'slate')
    for z in [.10,1.05]:line('Board frame',(-.60,-.009,z),(.60,-.009,z),.036,'tobacco',room)
    for i in range(5):line('Chalk lesson',(-.45,-.014,.83-i*.115),(.37-i*.024,-.014,.83-i*.115),.006,'paper_edge',room)
    teaching_desk=hinge('Teacher and lesson fold',.60,-.23)
    desk('School desk',0,0,0,teaching_desk,1.08);figure('Teacher Simone',-.28,-.024,.76,teaching_desk)
    square=hinge('Workers in square fold',1.67,.20)
    for x,h in [(-.24,.65),(0,.78),(.24,.70)]:figure('Worker',x,0,h,square)
    civic=hinge('Town lantern fold',.22,.72);lamp('Town lantern',0,0,1.13,civic)
    garden=hinge('Square plane tree fold',2.05,.80);tree('Plane branches',0,0,.93,garden,'leaf',31)


def power():
    map_h=hinge('Europe map fold',-.72,1.33)
    manuscript('Map paper',0,0,1.98,1.16,map_h,'stone')
    outline=[(-.74,.25),(-.58,.38),(-.70,.58),(-.35,.72),(-.22,1.02),(-.02,.85),(.19,.98),(.27,.78),(.61,.78),(.78,.48),(.55,.37),(.38,.17),(.17,.27),(.03,.11),(-.12,.43),(-.39,.32)]
    polygon('Europe cut map',outline,.008,-.025,'paper_light',map_h)
    for a,b in [((-.4,.5),(.25,.65)),((.25,.65),(.5,.45)),((-.1,.7),(.10,.3))]:line('Map connection',(a[0],-.04,a[1]),(b[0],-.04,b[1]),.008,'red',map_h)
    machine=hinge('Power mechanism fold',1.13,1.14)
    polygon('Machine arch frame',[(-.83,0),(-.69,0),(-.69,1.53),(.69,1.53),(.69,0),(.83,0),(.83,1.69),(-.83,1.69)],.023,.02,'ink_soft',machine)
    for x,z,r in [(-.38,.56,.38),(.31,.95,.43),(-.39,1.25,.24),(.43,.29,.23)]:
        line('Wheel support',(x,.015,0),(x,.015,z),.025,'stone',machine)
        gear('Interconnected gear',x,0,z,r,machine)
    for x in [-.76,.76]:
        for z in [.08,.47,.86,1.3,1.62]:disk('Frame rivet',x,-.023,z,.019,'brass',machine)
    worker=hinge('Individual before machinery fold',.58,-.32);figure('Individual',0,0,.74,worker)
    pages=hinge('Freedom essay fold',1.65,-.09);manuscript('Essay paper',0,0,.64,.69,pages)
    olive=hinge('Freedom olive fold',2.10,.64);tree('Olive branch',0,0,.83,olive,'leaf',18)


def factory():
    skyline=hinge('Industrial skyline fold',-.75,1.35)
    polygon('Sawtooth workshop',[(-1.02,0),(1.02,0),(1.02,.76),(.62,1.02),(.62,.76),(.19,1.02),(.19,.76),(-.26,1.02),(-.26,.76),(-.70,1.02),(-.70,.76),(-1.02,.76)],.021,0,'paper_shadow',skyline)
    for x in [-.82,-.41,0,.41,.82]:window('Workshop glazing',x,-.02,.15,.26,.44,skyline)
    card('Brick chimney',.70,.015,.17,1.57,skyline,'tobacco')
    for z in [.17+i*.075 for i in range(18)]:line('Chimney brick course',(.62,-.006,z),(.78,-.006,z),.005,'stone',skyline)
    press=hinge('Factory press fold',1.13,1.08)
    for x in [-.65,.65]:
        card('Press upright',x,0,.17,1.72,press,'slate')
        for z in [.15,.43,.73,1.02,1.43]:disk('Press bolt',x,-.025,z,.024,'brass',press)
    for z,h in [(.14,.20),(1.48,.22)]:box('Heavy press crossbeam',(0,-.012,z),(1.50,.035,h),'ink_soft',press,.01)
    card('Press ram',0,-.010,.32,1.45,press,'paper_shadow')
    box('Press head',(0,-.043,.81),(.97,.035,.20),'slate',press,.008)
    box('Press table',(0,-.045,.38),(1.14,.035,.11),'stone',press,.004)
    clock_face('Factory clock',0,-.040,1.56,.24,press)
    wheel=hinge('Flywheel fold',2.00,.22);gear('Press flywheel',0,0,.50,.37,wheel,'ink_soft');line('Flywheel stand',(0,0,0),(0,0,.50),.054,'ink_soft',wheel)
    worker=hinge('Factory worker fold',.53,-.28);figure('Exhausted worker',0,0,.74,worker)
    note=hinge('Factory notebook fold',1.31,-.43);manuscript('Workers notebook',0,0,.64,.48,note)


def spain():
    hills=hinge('Spanish frontier fold',-.73,1.34)
    polygon('Layered border hills',[(-1.1,0),(1.1,0),(1.1,.70),(.73,1.12),(.35,.73),(-.04,1.18),(-.36,.86),(-.72,1.00),(-1.1,.62)],.012,.02,'paper_shadow',hills)
    polygon('Near ochre hills',[(-1.05,0),(1.05,0),(1.05,.42),(.62,.70),(.15,.45),(-.28,.80),(-.66,.48),(-1.05,.58)],.012,-.026,'stone',hills)
    village=hinge('Aragon village fold',1.11,1.17)
    for x,w,h in [(-.62,.47,.77),(-.08,.61,1.02),(.57,.54,.79)]:
        facade('Aragon village house',x,0,w,h,village,2,2,False)
        polygon('Terracotta pitched roof',[(x-w*.57,h),(x+w*.57,h),(x,h+.27)],.018,-.005,'tobacco',village)
    bridge=hinge('Border crossing fold',.92,.50)
    for x in [-.60,.60]:card('Bridge parapet post',x,0,.13,.42,bridge,'stone')
    for z in [.23,.37]:line('Border bridge rail',(-.64,0,z),(.64,0,z),.033,'paper_shadow',bridge)
    people=hinge('Paper witnesses fold',1.30,-.17)
    for x,h in [(-.44,.61),(-.1,.76),(.30,.67)]:figure('Witness',x,0,h,people)
    letter=hinge('Bernanos letter fold',.35,-.27);manuscript('Letter about violence',0,0,.48,.62,letter)
    olive=hinge('Aragon olive fold',2.10,.52);tree('Dry olive',0,0,.94,olive,'leaf',66)


def threshold():
    landscape=hinge('Assisi hillside fold',-.72,1.34)
    canopy('Umbrian cypress landscape',0,.03,2.1,.61,landscape,'leaf',3)
    facade('Assisi stone houses',0,0,1.68,.80,landscape,2,4,False)
    chapel=hinge('Chapel portal fold',1.17,1.19)
    # Cut-through portal is assembled as voussoirs so the light is a true opening.
    r=.57;spring=1.05
    for x in [-.66,.66]:
        card('Chapel pier',x,0,.18,spring,chapel,'stone')
        for z in [.08,.21,.99]:box('Chapel capital',(x,-.012,z),(.27,.042,.05),'paper_light',chapel,.004)
    for i in range(28):
        a=i*math.pi/28;b=(i+1)*math.pi/28
        polygon('Chapel arch stone',[(r*math.cos(a),spring+r*math.sin(a)),(r*math.cos(b),spring+r*math.sin(b)),((r+.18)*math.cos(b),spring+(r+.18)*math.sin(b)),((r+.18)*math.cos(a),spring+(r+.18)*math.sin(a))],.025,0,'paper' if i%2 else 'stone',chapel)
    polygon('Chapel pediment',[(-.85,1.63),(.85,1.63),(0,1.98)],.020,.026,'paper',chapel)
    line('Stone cross upright',(0,-.017,1.70),(0,-.017,1.92),.023,'gilt_dark',chapel)
    line('Stone cross arm',(-.08,-.017,1.84),(.08,-.017,1.84),.022,'gilt_dark',chapel)
    stairs=hinge('Chapel steps fold',1.14,.48);steps('Chapel stair',0,0,1.1,.37,stairs,6)
    poem=hinge('Herbert poem fold',1.80,-.27);manuscript('Poem on the lectern',0,0,.65,.68,poem)
    visitor=hinge('Visitor at threshold fold',.66,-.29);figure('Simone at threshold',0,0,.73,visitor)
    branch=hinge('Sacred olive fold',2.12,.61);tree('Silver olive',0,0,.85,branch,'leaf',71)


def force():
    ancient=hinge('Ancient wall fold',-.71,1.32)
    polygon('Broken Troy wall',[(-1.04,0),(1.04,0),(1.04,1.12),(.85,1.12),(.85,1.34),(.58,1.34),(.58,1.13),(.23,1.13),(.23,1.39),(-.08,1.39),(-.08,1.18),(-.40,1.18),(-.40,1.32),(-.74,1.32),(-.74,1.13),(-1.04,1.13)],.030,0,'paper',ancient)
    for j in range(8):
        z=.09+j*.135;line('Ancient stone course',(-1.02,-.022,z),(1.02,-.022,z),.005,'paper_shadow',ancient)
        for i in range(7):
            x=-.92+i*.30+(j%2)*.15
            if x<1:line('Ancient stone joint',(x,-.023,z),(x,-.023,z+.13),.004,'paper_shadow',ancient)
    rail=hinge('Railway station fold',1.17,1.16)
    for x in [-.79,.79]:
        card('Platform iron column',x,0,.06,1.70,rail,'ink_soft')
        line('Station brace',(x,0,1.17),(x*.30,0,1.68),.025,'ink_soft',rail)
    polygon('Station canopy',[(-.96,1.69),(.96,1.69),(.86,1.87),(-.86,1.87)],.027,0,'slate',rail)
    line('Clock hanger',(0,0,1.37),(0,0,1.75),.020,'ink_soft',rail);clock_face('Station clock',0,-.016,1.28,.23,rail)
    train=hinge('Displacement carriage fold',1.17,.43)
    card('Railway carriage',0,0,1.76,.68,train,'ink_soft')
    for x in [-.59,-.20,.20,.59]:window('Carriage window',x,-.018,.28,.26,.25,train)
    for x in [-.55,.55]:disk('Carriage wheel',x,-.016,.12,.10,'slate',train)
    travellers=hinge('Displaced travellers fold',.75,-.36)
    figure('Traveller one',-.18,0,.67,travellers);figure('Traveller two',.20,0,.73,travellers)
    case=hinge('Travel case fold',1.72,-.36);book_card('Travel case',0,0,.50,.34,case,'tobacco')


def attention():
    port=hinge('Marseille port fold',-.72,1.34)
    for x,w,h in [(-.66,.58,.73),(-.04,.62,1.0),(.60,.57,.83)]:facade('Marseille quayside',x,0,w,h,port,3,2)
    harbor=hinge('Harbor sail fold',1.09,1.12)
    polygon('Boat hull',[(-.81,.24),(.79,.24),(.59,.04),(-.58,.04)],.026,0,'tobacco',harbor)
    line('Sailing mast',(0,0,0),(0,0,1.85),.027,'ink_soft',harbor)
    polygon('Full paper sail',[(.05,.39),(.05,1.73),(.79,.39)],.009,0,'paper_light',harbor)
    polygon('Fore sail',[(-.06,.42),(-.06,1.53),(-.67,.42)],.009,.035,'stone',harbor)
    for x in [-.77,-.53,-.29,.22,.47,.70]:line('Harbor ripples',(x,-.027,.03),(x+.12,-.027,.03),.008,'water',harbor)
    vines=hinge('Vineyard trellis fold',1.45,.40)
    for x in [-.65,0,.65]:line('Vineyard stake',(x,.015,0),(x,.015,.87),.025,'tobacco',vines)
    for z in [.33,.64]:line('Vineyard wire',(-.70,.01,z),(.70,.01,z),.007,'ink_soft',vines)
    for x in [-.50,0,.50]:
        tree('Vine leaf',x,0,.73,vines,'leaf',int((x+1)*42))
        for dx,dz in [(0,0),(.045,.025),(-.045,.025),(.02,-.06)]:disk('Grape cluster',x+dx,-.022,.37+dz,.035,'slate',vines,12)
    writing=hinge('Marseille writing fold',.64,-.34);desk('Writing table',0,0,0,writing,1.10);figure('Writing Simone',-.25,-.023,.67,writing)
    notebook=hinge('Attention notebook fold',1.83,-.40);manuscript('Attention pages',0,0,.45,.40,notebook)


def roots():
    cities=hinge('Across the Atlantic fold',-.74,1.34)
    for x,w,h in [(-.85,.24,1.02),(-.54,.28,1.23),(-.20,.26,.93),(.15,.29,.81),(.50,.26,.98),(.81,.24,.72)]:
        facade('Across ocean skyline',x,0,w,h,cities,4,1,False)
    line('Manhattan spire',(-.54,0,1.21),(-.54,0,1.54),.024,'stone',cities)
    homes=hinge('Rooted houses fold',1.17,1.19)
    for x,w,h in [(-.60,.49,.84),(0,.61,1.13),(.64,.52,.93)]:
        # Houses rise on branching roots: connected paper rather than floating symbols.
        for sign in [-1,1]:
            line('Branching root',(x,0,.44),(x+sign*w*.42,0,.04),.035,'tobacco',homes)
            line('Fine root',(x+sign*w*.20,0,.24),(x+sign*w*.49,0,.14),.014,'tobacco',homes)
        polygon('Rooted house wall',[(x-w/2,.39),(x+w/2,.39),(x+w/2,h+.39),(x,h+.69),(x-w/2,h+.39)],.019,0,'paper',homes)
        polygon('House roof',[(x-w*.56,h+.39),(x,h+.72),(x+w*.56,h+.39),(x+w*.48,h+.34),(x,h+.63),(x-w*.48,h+.34)],.020,-.008,'slate',homes)
        window('Rooted home window',x,-.017,.69,w*.39,.29,homes)
    ocean=hinge('Atlantic crossing fold',1.13,.39)
    polygon('Ocean liner hull',[(-.76,.30),(.76,.30),(.56,.04),(-.55,.04)],.02,0,'ink_soft',ocean)
    box('Liner upper deck',(0,0,.38),(1.04,.025,.17),'paper_light',ocean,.004)
    for x in [-.28,0,.28]:card('Steam funnel',x,.005,.12,.72,ocean,'tobacco')
    for x in [-.48,-.31,-.14,.03,.20,.37,.54]:disk('Liner porthole',x,-.020,.22,.026,'brass',ocean,16)
    duties=hinge('Obligations manuscript fold',.53,-.37);manuscript('Obligations and needs',0,0,.64,.56,duties)
    branch=hinge('Belonging tree fold',2.11,.37);tree('Rooted tree',0,0,.91,branch,'leaf',12)


def unfinished():
    horizon=hinge('English garden fold',-.72,1.34)
    canopy('Quiet garden silhouette',0,.02,2.10,.80,horizon,'paper_shadow',9)
    for x in [-.69,.06,.70]:tree('Garden branches',x,-.01,.76,horizon,'leaf',int((x+1)*39))
    room=hinge('Ashford quiet window fold',1.15,1.16)
    for x in [-.74,.74]:card('Window frame pier',x,0,.16,1.84,room,'paper')
    for z in [.09,1.74]:box('Window lintel',(0,0,z),(1.62,.033,.14),'paper',room,.008)
    for x in [-.34,0,.34]:line('Fine window vertical',(x,-.012,.16),(x,-.012,1.67),.024,'stone',room)
    for z in [.67,1.21]:line('Fine window horizontal',(-.66,-.012,z),(.66,-.012,z),.023,'stone',room)
    # Light curtains are continuous folded silhouettes carried by the frame.
    for sign in [-1,1]:
        pts=[(sign*.64,.16),(sign*.50,.22),(sign*.57,.68),(sign*.46,1.23),(sign*.41,1.67),(sign*.66,1.67)]
        polygon('Quiet paper curtain',pts,.009,-.032,'paper_light',room)
    table=hinge('Unfinished writing table fold',1.13,.29);desk('Unfinished desk',0,0,0,table,1.75)
    pages=hinge('Last manuscript fold',.52,-.28);manuscript('Unfinished manuscript',0,0,.54,.58,pages)
    second=hinge('Loose leaf fold',1.39,-.45);manuscript('Loose paper',0,0,.56,.39,second)
    flower=hinge('Quiet botanical fold',2.09,.42);tree('Quiet branch',0,0,.87,flower,'leaf',93)


def legacy():
    archive=hinge('Archive manuscripts fold',-.73,1.34)
    for x,w,h in [(-.75,.39,.88),(-.27,.42,1.16),(.24,.44,1.05),(.76,.40,.90)]:manuscript('Archive manuscript',x,0,w,h,archive,'stone')
    books=hinge('Posthumous books fold',1.10,1.17)
    for x,w,h,mat in [(-.65,.43,1.21,'ink_soft'),(-.12,.53,1.81,'tobacco'),(.49,.51,1.43,'slate')]:
        book_card('Published book',x,0,w,h,books,mat)
        # Fine ivory page edges beside each leather board.
        for i in range(4):line('Bound paper edge',(x+w*.47+i*.006,.007,.03),(x+w*.47+i*.006,.007,h-.025),.003,'paper_light',books)
    opening=hinge('Open future pages fold',1.12,.33)
    polygon('Open book wings',[(-.74,0),(0,.06),(.74,0),(.74,.76),(.38,.83),(0,.75),(-.38,.83),(-.74,.76)],.014,0,'paper',opening)
    line('Open book crease',(0,-.012,.06),(0,-.012,.75),.010,'tobacco',opening)
    for sign in [-1,1]:
        for i in range(8):line('Open book printed line',(sign*.09,-.013,.20+i*.065),(sign*.61,-.013,.17+i*.065),.004,'paper_shadow',opening)
    reader=hinge('Continuing reader fold',.53,-.40);figure('Reader',0,0,.66,reader)
    branch=hinge('Living ideas fold',2.02,.52);tree('Living olive',0,0,1.04,branch,'leaf',103)
