"""Read exported GLB metadata and write the runtime asset catalogue.

This reports the files actually present; it does not establish browser acceptance.
"""
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def update():
    assets=[]
    for path in sorted((ROOT/'public/models').glob('*.glb')):
        data=path.read_bytes()
        length=struct.unpack_from('<I',data,12)[0]
        scene=json.loads(data[20:20+length])
        clips={a['name']:max(scene['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in scene.get('animations',[])}
        assets.append({'file':path.name,'bytes':len(data),'meshes':len(scene.get('meshes',[])),
            'materialPrimitives':sum(len(m['primitives']) for m in scene.get('meshes',[])),
            'animations':clips,'poster':f'../posters/{path.stem}.webp','source':f'../../assets/source/{path.stem}.blend'})
    manifest={'version':2,'coordinates':'gltf-y-up','pageSurfaceY':.202,
        'pageSurfaceFormula':'.202+.115*sin(pi*u)*exp(-1.8*u)-.007*u*u*cos((v-.5)*pi), u=(abs(X)-.018)/2.4, v=(1.55-Z)/3.1',
        'leftTextRect':[-2.25,-.90,-.20,1.43],
        'readingPanel':{'hinge':'ReadingHinge','mesh':'ReadingPanel','clip':'reading','degrees':18,'duration':1,
            'localExtentX':[-1.025,1.025],'localExtentZ':[-2.33,0],'textOffsetY':.010},
        'bookDefaultPose':'open','readingDefaultPose':'flat','chapterDefaultPose':'unfolded','assets':assets}
    (ROOT/'public/models/asset-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

if __name__=='__main__':update()
