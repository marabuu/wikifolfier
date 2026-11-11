import tarfile
import os

base_dir = os.path.abspath('.')
output_archive = os.path.join(base_dir, 'update_prod.tar.gz')

def should_exclude(path):
    parts = path.replace('\\', '/').split('/')
    if any(p in {'__pycache__', 'node_modules', '.git', '.env', '.env.local', 'staticfiles', 'media', '.agents', '.system_generated'} for p in parts):
        return True
    if path.endswith(('.pyc', '.pyo')):
        return True
    return False

def add_file_or_dir(tar, rel_path):
    full_path = os.path.join(base_dir, rel_path)
    if not os.path.exists(full_path):
        print(f"Skipping missing: {rel_path}")
        return
    if os.path.isfile(full_path):
        tar.add(full_path, arcname=rel_path.replace('\\', '/'))
    elif os.path.isdir(full_path):
        for root, dirs, files in os.walk(full_path):
            dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d))]
            for f in files:
                fpath = os.path.join(root, f)
                if not should_exclude(fpath):
                    rpath = os.path.relpath(fpath, base_dir)
                    tar.add(fpath, arcname=rpath.replace('\\', '/'))

with tarfile.open(output_archive, 'w:gz') as tar:
    # Backend
    add_file_or_dir(tar, 'backend')
    # Docker and Nginx configs
    add_file_or_dir(tar, 'docker-compose.yml')
    add_file_or_dir(tar, 'docker-compose.prod.yml')
    add_file_or_dir(tar, 'nginx')
    # Frontend prebuilt
    add_file_or_dir(tar, 'frontend/public')
    add_file_or_dir(tar, 'frontend/Dockerfile.prebuilt')
    add_file_or_dir(tar, 'frontend/.next/standalone')
    add_file_or_dir(tar, 'frontend/.next/static')

print("Archive created successfully:", output_archive, os.path.getsize(output_archive), "bytes")
