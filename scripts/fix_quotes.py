import os

base = r'c:\Users\vigne\Desktop\SIH2026\SIH_Proj\AI-Powered Email Threat Detection, GeoLocation & Forensic Intelligence Platform Project\backend'
for root, dirs, files in os.walk(base):
    for f in files:
        if f.endswith('.py'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8') as fp:
                c = fp.read()
            if '\\"' in c:
                c_fixed = c.replace('\\"', '"')
                with open(p, 'w', encoding='utf-8') as fp:
                    fp.write(c_fixed)
                print('Fixed backslash-quotes in:', p)
