import os
import subprocess
import sys

frontend_dir = os.path.abspath('frontend')
env_local = os.path.join(frontend_dir, '.env.local')
env_local_bak = os.path.join(frontend_dir, '.env.local.bak')

try:
    if os.path.exists(env_local):
        os.rename(env_local, env_local_bak)

    env = os.environ.copy()
    env['NEXT_PUBLIC_API_URL'] = 'https://wikifolfier.duckdns.org'
    print("Building Next.js frontend with NEXT_PUBLIC_API_URL=https://wikifolfier.duckdns.org...")
    res = subprocess.run(['npm', 'run', 'build'], cwd=frontend_dir, env=env, shell=True)
    if res.returncode != 0:
        print("Build failed with code:", res.returncode)
        sys.exit(res.returncode)
    print("Build successful!")
finally:
    if os.path.exists(env_local_bak):
        if os.path.exists(env_local):
            os.remove(env_local)
        os.rename(env_local_bak, env_local)
