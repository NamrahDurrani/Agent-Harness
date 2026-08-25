import os, zipfile, sys
ROOT = r'C:\Users\User\OneDrive\Desktop\RapidsAI\agenti_rag'
OUT = os.path.join(ROOT, 'agriBot_minimal_release.zip')
INCLUDE = [
    'agent_harness', 'scripts', 'api_server.py', 'rag_pipeline.py', 'tts.py', 'vector_store.py', 'mcp_pdf_export.py', 'README.md', 'PROJECT_SUMMARY.md', 'requirements.txt', 'package.json', 'src'
]
paths=[]
for p in INCLUDE:
    full = os.path.join(ROOT, p)
    if os.path.exists(full):
        paths.append(full)
    else:
        print('Missing, skipping', p)

if not paths:
    print('No files found to include. Aborting.')
    sys.exit(1)

try:
    with zipfile.ZipFile(OUT, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for p in paths:
            if os.path.isfile(p):
                arc = os.path.relpath(p, ROOT)
                z.write(p, arc)
            else:
                for dirpath, dirnames, filenames in os.walk(p):
                    # skip node_modules, .git, chroma_db, user_uploads, pdfs
                    if any(x in dirpath for x in ('node_modules', '.git', 'chroma_db', 'user_uploads', 'pdfs', '.venv', '__pycache__')):
                        continue
                    for f in filenames:
                        if f.endswith('.pyc'):
                            continue
                        full = os.path.join(dirpath, f)
                        arc = os.path.relpath(full, ROOT)
                        z.write(full, arc)
    print('Created', OUT)
except Exception as e:
    print('ZIP failed:', e)
    sys.exit(2)
