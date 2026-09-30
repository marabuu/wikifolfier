import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "importer"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "compendium.settings")

import django

django.setup()

from django.conf import settings
from wiki.rendering import render

print("DB host :", settings.DATABASES["default"]["HOST"])
print("DB port :", settings.DATABASES["default"]["PORT"])
print("DB name :", settings.DATABASES["default"]["NAME"])
print("DEBUG   :", settings.DEBUG)
print("render  :", "OK" if "<h2>x</h2>" in render("## x").html else "FAIL")