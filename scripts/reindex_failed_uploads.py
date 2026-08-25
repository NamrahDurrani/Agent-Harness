import os, sys, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from rag_pipeline import build_upload_chunks
import vector_store
from uuid import uuid4

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', 'user_uploads')
META = os.path.join(UPLOAD_DIR, '.meta.json')

if not os.path.exists(META):
    print('No uploads meta found at', META)
    sys.exit(0)

m = json.load(open(META))
errors = [u for u in m if u.get('status') == 'error']
if not errors:
    print('No failed uploads to reindex')
    sys.exit(0)

client = vector_store._get_client()
ef = vector_store._get_ef()
col = client.get_or_create_collection(name='user_uploads', embedding_function=ef, metadata={'hnsw:space':'cosine'})

for u in errors:
    path = u.get('file_path')
    fid = u.get('file_id') or str(uuid4())
    if not path or not os.path.exists(path):
        print('Skipping missing file:', path)
        continue
    print('Reindexing', path)
    chunks = build_upload_chunks(path, source_label=u.get('original_name') or os.path.basename(path))
    if not chunks:
        print('No chunks extracted for', path)
        u['status'] = 'error'
        continue
    texts = [c['chunk_text'] for c in chunks]
    ids = [str(uuid4()) for _ in texts]
    metas = []
    for c in chunks:
        metas.append({'source_file': c.get('source_file'), 'page_num': c.get('page_num',0), 'file_id': fid, 'user_upload': True})
    for i in range(0, len(texts), 128):
        col.add(documents=texts[i:i+128], ids=ids[i:i+128], metadatas=metas[i:i+128])
    print('Indexed', len(texts), 'chunks for', path)
    u['status'] = 'indexed'
    u['chunk_count'] = len(texts)

json.dump(m, open(META, 'w'), indent=2)
print('Reindexing complete')
