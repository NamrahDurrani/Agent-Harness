import os, zipfile, sys
ROOT = r'C:\Users\User\OneDrive\Desktop\RapidsAI\agenti_rag'
OUT = os.path.join(ROOT, 'agriBot_release_excluded.zip')
EXCLUDE = {'node_modules', '.git', 'chroma_db', 'user_uploads', 'pdfs', '.cache', '__pycache__', '.venv', 'venv'}

with zipfile.ZipFile(OUT, 'w', compression=zipfile.ZIP_DEFLATED) as z:
    for dirpath, dirnames, filenames in os.walk(ROOT):
        # Skip excluded dirs
        if any(part in EXCLUDE for part in dirpath.split(os.sep)):
            continue
        for f in filenames:
            if f.endswith('.pyc'):
                continue
            full = os.path.join(dirpath, f)
            arc = os.path.relpath(full, ROOT)
            z.write(full, arc)

print('Created', OUT)
