import json,sys,os
sys.path.insert(0, os.path.abspath(r'C:\Users\User\OneDrive\Desktop\RapidsAI\agenti_rag'))
from rag_pipeline import build_upload_chunks
import vector_store
file_path = r'C:\Users\User\OneDrive\Desktop\RapidsAI\agenti_rag\user_uploads\c30718c0-0b86-458c-ba70-aadbe117034d.pdf'
orig_name = 'Chat_2026-07-22.pdf'
print('Building chunks for', file_path)
chunks = build_upload_chunks(file_path, source_label=orig_name)
print('Chunks:', len(chunks))
if not chunks:
    print('No chunks extracted; aborting indexing')
    sys.exit(1)
client = vector_store._get_client()
ef = vector_store._get_ef()
col = client.get_or_create_collection(name='user_uploads', embedding_function=ef, metadata={'hnsw:space':'cosine'})
texts = [c['chunk_text'] for c in chunks]
ids = [str(__import__('uuid').uuid4()) for _ in texts]
metas = []
for c in chunks:
    metas.append({'source_file': c.get('source_file'), 'page_num': c.get('page_num',0), 'file_id': 'c30718c0-0b86-458c-ba70-aadbe117034d', 'user_upload': True})
print('Adding', len(texts), 'docs to user_uploads')
for i in range(0, len(texts), 128):
    col.add(documents=texts[i:i+128], ids=ids[i:i+128], metadatas=metas[i:i+128])
print('Indexing complete. Collection now has', col.count())
# update meta file
meta_path = os.path.join(os.path.dirname(file_path), '.meta.json')
if os.path.exists(meta_path):
    m = json.load(open(meta_path))
    for u in m:
        if u.get('file_path')==file_path:
            u['status']='indexed'
            u['chunk_count']=len(chunks)
    json.dump(m, open(meta_path,'w'), indent=2)
    print('Updated meta.json')
else:
    print('No meta.json found at', meta_path)
