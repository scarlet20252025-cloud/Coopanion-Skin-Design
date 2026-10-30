from pathlib import Path
from PIL import Image
import cv2,numpy as np
P=Path(__file__).resolve().parent
a=np.asarray(Image.open(P/'raw/mother-without-far-rear-02.png').convert('RGBA')).copy();h,w=a.shape[:2];yy,xx=np.mgrid[:h,:w]
roi=(yy>=600)&(yy<1060)&(xx>770)&(xx<1000)
n,l,s,_=cv2.connectedComponentsWithStats(((a[:,:,3]>50)&roi).astype('uint8'))
k=l[890,960];assert k>0
mark=(l==k)&(yy>950)
a[mark,:3]=(a[mark,:3].astype(float)*.25+np.array([255,20,20])*.75).astype('uint8')
Image.fromarray(a).save(P/'references/far-rear-residue-guide.png')
