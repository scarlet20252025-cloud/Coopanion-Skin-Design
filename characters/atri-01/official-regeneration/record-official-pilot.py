from pathlib import Path
import ast,hashlib,io,json,zipfile,xml.etree.ElementTree as ET
from PIL import Image
P=Path(__file__).resolve().parent;R=P.parents[2];O=P/'official-visible'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,data):p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lock=load(P/'expression-lock.json');baseline=R/lock['baseline']
checks={name:sha(baseline/name)==expected for name,expected in lock['files'].items()}
assert all(checks.values()),'Approved expression baseline changed'
assert sha(P.parent/'master.png')==load(P/'contract.json')['master_sha256']
for f in P.glob('*.py'):ast.parse(f.read_text(encoding='utf-8'),filename=str(f))
# Preserve the earlier generation input reconstructed from its recorded script
# state, because the working visible source was subsequently matte-corrected.
snapshot=P/'references/near-generation-v1';snapshot.mkdir(exist_ok=True)
code=(P/'trace-near-visible.py').read_text(encoding='utf-8')
code=code.replace("O=P/'official-visible'","O=P/'references/near-generation-v1'")
code=code.replace("Image.open(O/'mother-source-matte.png')","Image.open(P.parent/'master.png')")
code=code.replace(',[930,190],[940,187]','').replace('(ys>940)','(ys>920)')
exec(compile(code,'reconstructed-near-input','exec'),{'__file__':str(P/'trace-near-visible.py')})
for i in [36,37]:
 p=P/f'attempt-{i}.json';a=load(p);a['input_preservation_note']='Working visible source later changed; pre-matte/pre-tail-extension image reconstructed from the exact script state, not claimed as a separately captured original tool-input hash.';a['reconstructed_input']='references/near-generation-v1/near-visible-mother.png';write(p,a)
for i in range(35,41):
 p=P/f'attempt-{i}.json';a=load(p);a['output_sha256']=sha(P/a['output']);write(p,a)
hashes=load(P/'source-hashes.json')
for folder in [P/'raw',O,snapshot]:
 for f in folder.glob('*.png'):hashes[f.relative_to(P).as_posix()]=sha(f)
write(P/'source-hashes.json',hashes)
c=load(P/'contract.json');c['generation']='Official removal edits + mother visible pixels + generated concealed fill + computed/visually corrected ownership masks; built-in imagegen used for new pixels.'
c['continuation_method_decision']={'user_message':'继续完成','interpretation':'Continue the immediately proposed official visible-pixel preservation workflow; this is an interpretation of continuation, not an explicit option-selection quote.'}
c['state']='Official workflow pilot exists; far hidden fill FAILS motion art acceptance; not promoted or installed.'
write(P/'contract.json',c)
progress=load(P/'progress.json');progress.pop('pending_user_choice',None)
progress['phase']='official visible-pixel pilot; hidden far hair failed motion QA'
progress['official_pilot']='official-visible/pair-pilot-report.json'
progress['pending_adobe_confirmation']={'question':'Allow one Photoshop selection-based Generative Fill attempt using existing Adobe credits?','reason':'Built-in image generation did not preserve the exact masked completion; credits may be consumed.','answer':None,'action_taken':False}
progress['promotion_allowed']=False;write(P/'progress.json',progress)
report={'expression_files_checked':len(checks),'all_expression_hashes_unchanged':all(checks.values()),'locked_master_unchanged':True,'python_syntax':'pass','browser_module_syntax':'node --check passed','browser_manual_review':['neutral full figure','far outward 6px detail','dark background and mirrored far detail'],'browser_console_errors':0,'visual_result':'FAIL: far lower cut and colour discontinuity; static reconstruction does not prove motion quality','runtime_candidate_created':False,'installed':False,'review_url':'http://127.0.0.1:4319/characters/atri-01/official-regeneration/official-visible/review.html','adobe_capabilities_check':'tool reports Photoshop 2024 and generative_fill support; app connection/credits not verified; no Adobe generation called'}
write(O/'validation.json',report)
# Editable neutral stack with explicit diagnostic names and a hidden reference.
root=ET.Element('image',{'w':'1145','h':'1374','name':'ATRI official pilot - NOT ACCEPTED'});stack=ET.SubElement(root,'stack')
layers=[('Mother reference - 50 percent - hidden','mother-source-matte.png','hidden','0.5'),('Diagnostic remaining figure - NOT final body','pair-remainder.png','visible','1.0'),('Near pony - hidden tip pending QA','near-pony-complete.png','visible','1.0'),('Far pony - FAIL motion QA','far-pony-complete.png','visible','1.0'),('Generated rear fills','pair-rear-fill.png','visible','1.0')]
with zipfile.ZipFile(O/'ATRI-official-pilot-NOT-ACCEPTED.ora','w') as z:
 z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
 for i,(name,file,visibility,opacity) in enumerate(layers):
  dst=f'data/layer{i}.png';z.write(O/file,dst);ET.SubElement(stack,'layer',{'name':name,'src':dst,'x':'0','y':'0','opacity':opacity,'visibility':visibility,'composite-op':'svg:src-over'})
 z.writestr('stack.xml',ET.tostring(root,encoding='utf-8',xml_declaration=True));z.write(O/'pair-neutral.png','mergedimage.png')
 im=Image.open(O/'pair-neutral.png');im.thumbnail((256,256));buf=io.BytesIO();im.save(buf,format='PNG');z.writestr('Thumbnails/thumbnail.png',buf.getvalue())
with zipfile.ZipFile(O/'ATRI-official-pilot-NOT-ACCEPTED.ora') as z:assert z.testzip() is None
note='''
## 2026-10-15 官方保形试验（覆盖“方法待回复”状态）

用户在方法提议之后回复“继续完成”，本轮按继续该提议理解，实施官方可见母版像素＋生成隐藏补全流程。不是声称用户逐项选择了某个选项。

完成近、远侧马尾去除编辑（attempt 35、38），未变区域相似配准分别为 320 / 301 内点、约 0.91 / 0.85px RMS。直接颜色差分漏根部、夹入后发细线，已判失败；依据母版墨线与透明间隙修正像素归属，保留诊断遮罩。旧透明母版局部 alpha 已带缺陷，另从原始带背景母版恢复边缘，母版原文件没有覆盖。

生成隐藏补全 attempt 36–40，保留所有原始输出与逐字提示词。近侧过长发尾没有采用；远侧普通生成、品红遮罩生成仍没有严格保持隐藏区域，隐藏源平移及颜色补偿试验也失败并撤回。禁止以该试验作为新的生成参考或成品。

现有双马尾诊断层可以原位重组：相对本轮边缘恢复源，无新增明显外轮廓像素。但 6px 远侧摆动暴露斜切缝、缺底和混色，已在 Coopanion 官方 kit/rig.js 实际渲染器中确认，深色及反向也能看到。近侧 12px 压力帧下段交叠仍需修复。因此没有新运行候选，没有替换当前预览包，没有安装或发布。

入口 official-visible/review.html 明确显示失败状态；ORA 只是带半透明母版参考的可编辑诊断分层。29 个原表情文件哈希仍全部一致。

只读能力检查返回 Photoshop 2024 支持 Generative Fill，但尚未确认实际应用连接或额度。已询问是否允许用现有 Adobe 额度做一次真实选区补画，答复前不执行，不能将未回复视为授权。原先禁止 OpenArt / 付费 API 回退仍有效。
'''
with (P/'STATUS.md').open('a',encoding='utf-8') as f:f.write(note)
print(json.dumps(report,ensure_ascii=False))
