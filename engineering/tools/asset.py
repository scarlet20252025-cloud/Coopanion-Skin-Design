"""Inspect transparent art and register matching landmarks without stretching a character."""
from pathlib import Path
import argparse
import json
import math
import sys
import project

def inspect_image(path):
    from PIL import Image
    import numpy as np
    p=Path(path);im=Image.open(p);rgba=im.convert('RGBA');a=np.array(rgba.getchannel('A'))
    return {'path':str(p.resolve()),'sha256':project.sha(p),'mode':im.mode,'canvas':list(im.size),'alpha_bounds':rgba.getbbox(),
            'transparent_pixels':int((a==0).sum()),'partial_alpha_pixels':int(((a>0)&(a<255)).sum()),
            'occupied_border_pixels':int((a[0]>0).sum()+(a[-1]>0).sum()+(a[:,0]>0).sum()+(a[:,-1]>0).sum()),
            'notes':'Opaque art needs semantic cutout; border contact can mean clipping. Neither implies automatic rejection.'}

def similarity(source,target,tolerance):
    import numpy as np
    x=np.array(source,dtype=float);y=np.array(target,dtype=float)
    if x.shape!=y.shape or x.ndim!=2 or x.shape[1]!=2 or len(x)<3 or not np.isfinite(x).all() or not np.isfinite(y).all(): raise ValueError('Supply at least 3 finite matching [x,y] pairs')
    xc=x-x.mean(axis=0);yc=y-y.mean(axis=0)
    if np.linalg.matrix_rank(xc)<2 or np.linalg.matrix_rank(yc)<2: raise ValueError('Landmarks must be noncollinear and spread over unchanged art')
    u,s,vt=np.linalg.svd(xc.T@yc);sign=np.eye(2);sign[-1,-1]=np.sign(np.linalg.det(u@vt));rotation=u@sign@vt
    scale=float(np.trace(np.diag(s)@sign)/(xc**2).sum())
    if not math.isfinite(scale) or scale<=0:raise ValueError('Invalid similarity scale')
    translation=y.mean(axis=0)-scale*x.mean(axis=0)@rotation
    error=np.linalg.norm(scale*x@rotation+translation-y,axis=1)
    if float(error.max())>tolerance: raise ValueError(f'Matching error {float(error.max()):.3f}px exceeds {tolerance}px; repair point pairing, do not add shear')
    # Column-vector SVG convention [a,b,c,d,e,f].
    matrix=[scale*rotation[0,0],scale*rotation[0,1],scale*rotation[1,0],scale*rotation[1,1],*translation]
    return [float(v) for v in matrix],{'scale':scale,'max_residual_px':float(error.max()),'rms_residual_px':float(np.sqrt((error**2).mean()))}

def register(args):
    from PIL import Image
    import numpy as np
    out=project.rooted(args.out)
    if not out.is_relative_to(project.ROOT/'scratch') or out.exists():raise ValueError('Choose a new scratch output directory; production assets are never overwritten')
    source=Image.open(args.source).convert('RGBA');master=Image.open(args.master).convert('RGBA')
    if source.getbbox() is None:raise ValueError('Source is empty')
    if args.identity:
        if source.size!=master.size:raise ValueError('Identity registration requires identical canvas sizes')
        matrix=[1,0,0,1,0,0];metrics={'identity':True,'landmark_fit':'not-tested'}
    else:
        pairs=project.read(args.points);matrix,metrics=similarity(pairs['source'],pairs['target'],args.tolerance)
    a,b,c,d,e,f=matrix;affine=np.array([[a,c,e],[b,d,f],[0,0,1]],dtype=float);inv=np.linalg.inv(affine)
    aligned=source.transform(master.size,Image.Transform.AFFINE,tuple(inv[:2].reshape(-1)),resample=Image.Resampling.BICUBIC)
    if aligned.getbbox() is None:raise ValueError('Registration placed the entire source outside the canvas')
    out.mkdir(parents=True);aligned.save(out/'registered.png')
    overlay=Image.new('RGBA',master.size);overlay.alpha_composite(master);layer=aligned.copy();layer.putalpha(layer.getchannel('A').point(lambda v:int(v*.5)));overlay.alpha_composite(layer);overlay.save(out/'overlay.png')
    for label,color in [('light','#e9e4f1'),('dark','#202124')]:
        background=Image.new('RGBA',master.size,color);background.alpha_composite(aligned);background.save(out/f'{label}.png')
    report={'source':inspect_image(args.source),'master':inspect_image(args.master),'matrix':matrix,'metrics':metrics,'registered_sha256':project.sha(out/'registered.png'),
            'alpha_policy':'new source alpha transformed with the same similarity; no old silhouette clipping','visual_review':'required: source ownership, unchanged regions, joining edges and full-character shape'}
    (out/'registration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2));return 0

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    i=sub.add_parser('inspect');i.add_argument('source')
    r=sub.add_parser('register');r.add_argument('--source',required=True);r.add_argument('--master',required=True);r.add_argument('--out',required=True)
    group=r.add_mutually_exclusive_group(required=True);group.add_argument('--points');group.add_argument('--identity',action='store_true');r.add_argument('--tolerance',type=float,default=2)
    args=parser.parse_args()
    try:
        if args.command=='inspect':print(json.dumps(inspect_image(args.source),ensure_ascii=False,indent=2));return 0
        if not math.isfinite(args.tolerance) or args.tolerance<=0:raise ValueError('Use a positive finite tolerance')
        return register(args)
    except (ValueError,OSError,KeyError) as e:print('ERROR: '+str(e),file=sys.stderr);return 1
    except ImportError:print('Install tools: uv sync --project engineering',file=sys.stderr);return 1

if __name__=='__main__':sys.exit(main())
