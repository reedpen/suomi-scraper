import libvoikko
import sys

print(f"Python version: {sys.version}")
try:
    v = libvoikko.Voikko("fi")
    print("Voikko initialized successfully!")
    print(f"Analysis of 'taloissa': {v.analyze('taloissa')}")
except Exception as e:
    print(f"Voikko error: {e}")
    sys.exit(1)
