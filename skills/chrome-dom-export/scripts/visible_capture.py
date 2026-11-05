"""Save only a scoped public Chrome tab PNG. Never print/persist base64 JSON."""
import base64
import hashlib
import json
import os
from pathlib import Path
import struct
import zlib
import tempfile
from datetime import datetime,timezone
from urllib.parse import urlsplit,parse_qs

SAFETY='dom-only-20261103-12'
def require(ok,code):
    if not ok:raise ValueError(code)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def atomic(path,value):
    fd,tmp=tempfile.mkstemp(prefix='.capture-',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
def stamp():return datetime.now(timezone.utc).isoformat()
def validate_png(raw):
    require(raw.startswith(b'\x89PNG\r\n\x1a\n'),'capture-decoded-png-invalid')
    offset=8;chunks=[];packed=[];dimensions=None;ended=False;idat_ended=False
    while offset<len(raw):
        require(offset+12<=len(raw),'capture-png-truncated-chunk')
        size=struct.unpack('>I',raw[offset:offset+4])[0];kind=raw[offset+4:offset+8];end=offset+12+size
        require(end<=len(raw),'capture-png-truncated-chunk')
        body=raw[offset+8:offset+8+size];crc=struct.unpack('>I',raw[offset+8+size:end])[0]
        require(zlib.crc32(kind+body)&0xffffffff==crc,'capture-png-crc-invalid')
        if not chunks:require(kind==b'IHDR' and size==13,'capture-png-first-header-invalid')
        if kind==b'IHDR':
            require(not chunks and dimensions is None,'capture-png-duplicate-header')
            width,height,bits,color,compression,filtering,interlace=struct.unpack('>IIBBBBB',body)
            require(0<width<=32768 and 0<height<=32768 and width*height<=100_000_000,'capture-png-size-invalid')
            allowed={0:(1,2,4,8,16),2:(8,16),3:(1,2,4,8),4:(8,16),6:(8,16)}
            require(color in allowed and bits in allowed[color] and compression==filtering==0 and interlace in (0,1),'capture-png-header-invalid')
            dimensions=(width,height,bits,color,interlace)
        elif kind==b'PLTE':require(size and size%3==0 and size<=768 and not packed,'capture-png-palette-invalid')
        elif kind==b'IDAT':
            require(not idat_ended,'capture-png-noncontiguous-image-data');packed.append(body)
        elif kind==b'IEND':
            require(size==0 and packed and end==len(raw),'capture-png-end-invalid');ended=True
        elif kind and kind[0]&32==0:raise ValueError('capture-png-unknown-critical-chunk')
        if packed and kind!=b'IDAT':idat_ended=True
        chunks.append(kind);offset=end
        if ended:break
    require(ended and dimensions is not None,'capture-png-complete-image-required')
    width,height,bits,color,interlace=dimensions
    if color==3:require(b'PLTE' in chunks,'capture-png-palette-required')
    channels={0:1,2:3,3:1,4:2,6:4}[color]
    passes=[(0,0,1,1)] if interlace==0 else [(0,0,8,8),(4,0,8,8),(0,4,4,8),(2,0,4,4),(0,2,2,4),(1,0,2,2),(0,1,1,2)]
    rows=[]
    for x,y,dx,dy in passes:
        pw=max(0,(width-x+dx-1)//dx);ph=max(0,(height-y+dy-1)//dy)
        if pw and ph:rows.extend([(pw*channels*bits+7)//8]*ph)
    expected=sum(size+1 for size in rows);require(expected<=128*1024*1024,'capture-png-decoded-image-too-large')
    decoder=zlib.decompressobj()
    try:decoded=decoder.decompress(b''.join(packed),expected+1)
    except zlib.error as error:raise ValueError('capture-png-image-data-invalid') from error
    require(decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail and len(decoded)==expected,'capture-png-image-data-incomplete')
    pos=0
    for size in rows:require(decoded[pos]<=4,'capture-png-row-filter-invalid');pos+=size+1
    return width,height

def write_capture(command,out,request):
    """request is the authenticated loopback bridge callable; no extra transports."""
    out=Path(out).expanduser().resolve();metadata=out.with_suffix('.json')
    require(out.suffix.lower()=='.png','new-png-output-required');out.parent.mkdir(parents=True,exist_ok=True)
    if metadata.exists():
        old=json.loads(metadata.read_text())
        require(old.get('command')==command,'capture-local-intent-conflict')
        if old.get('state')=='complete':
            require(out.is_file() and sha(out)==old['png']['sha256'],'captured-png-changed')
            return {'ok':True,'result':{'path':str(out),'metadata':str(metadata),'sha256':old['png']['sha256'],'reused':True,'viewport_only':True}}
        raise ValueError('capture-outcome-unknown-no-replay')
    require(not out.exists(),'capture-output-already-exists')
    journal={'version':1,'command':command,'state':'intent','intent_at':stamp(),'source':'local-dom-bridge',
             'capture_method':'chrome.tabs.captureVisibleTab','viewport_only':True,'coverage_verified':False,'live_accepted':False}
    # O_EXCL creates the durable local intent; another invocation cannot race it.
    with metadata.open('x',encoding='utf-8') as f:json.dump(journal,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
    try:
        response=request(command)
        require(response.get('ok') is True,'capture-failed:'+str(response.get('error')))
        result=response['result'];before=result['before'];after=result['after']
        require(before==after and all(before.get(k)==command[k] for k in ('tabId','windowId','groupid')),'capture-response-scope-mismatch')
        u=urlsplit(before['url']);require(u.scheme=='https' and u.netloc=='life.douyin.com' and parse_qs(u.query).get('groupid')==[command['groupid']],'capture-response-origin-mismatch')
        require(result.get('safety_version')==SAFETY and result.get('viewport_only') is True and result.get('pixel_actions_used') is False,'capture-response-safety-mismatch')
        require(result.get('capture_method')=='chrome.tabs.captureVisibleTab' and result.get('captureKey')==command['captureKey'],'capture-response-key-method-mismatch')
        payload=result.pop('imageDataUrl')
        require(isinstance(payload,str) and payload.startswith('data:image/png;base64,') and len(payload)<=6_000_000,'capture-payload-invalid')
        raw=base64.b64decode(payload.split(',',1)[1],validate=True)
        width,height=validate_png(raw)
        fd,tmp=tempfile.mkstemp(prefix='.tab-image-',suffix='.png',dir=out.parent)
        try:
            with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
            os.link(tmp,out)  # Never overwrite even if another process created out.
        finally:os.unlink(tmp)
        journal.update(state='complete',completed_at=stamp(),capture=result,png={'path':str(out),'sha256':sha(out),'width':width,'height':height})
        atomic(metadata,journal)
        return {'ok':True,'result':{'path':str(out),'metadata':str(metadata),'sha256':journal['png']['sha256'],'viewport_only':True,'coverage_verified':False,'live_accepted':False}}
    except Exception as error:
        journal.update(state='unknown',error=str(error));atomic(metadata,journal);raise
