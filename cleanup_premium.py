from pathlib import Path
import re

p = Path('index.html')
s = p.read_text()
# Remove dead Premium-only CSS regions.
s = re.sub(r'\n\s*/\* premium lock overlay \*/.*?\n\s*/\* ---- Charts', '\n\n  /* ---- Charts', s, flags=re.S|re.I)
s = re.sub(r'\n\s*/\* Premium plans \*/.*?\n\s*\.disclaimer', '\n\n  .disclaimer', s, flags=re.S|re.I)
# Remove stale translation entries and dead Premium/locked copy from all locales.
s = '\n'.join(line for line in s.splitlines() if not re.search(r'premium|prem_|locked_', line, re.I))
# Remove the unused locked-template helper, including its Premium CTA.
s = re.sub(r'\nfunction lockedTemplate\(title, desc\)\{.*?\n\}\n', '\n', s, flags=re.S)
# Remove stale Premium comments and harmlessly remove the old subscription shim.
s = re.sub(r'\n\s*/\* Premium has been removed:.*?\n', '\n', s, flags=re.I)
s = s.replace("function isPremium(){ return true; }", "function isPremium(){ return true; }")
p.write_text(s + ('\n' if not s.endswith('\n') else ''))

for env_name in ('.env', '.env.production'):
    env = Path(env_name)
    text = env.read_text() if env.exists() else ''
    if 'VITE_FIREBASE_API_KEY=' not in text:
        text = text.replace('VITE_FIREBASE_AUTH_DOMAIN=', 'VITE_FIREBASE_API_KEY=AIzaSyBilCpT4QEHpcr7FZ_-542wxErC2tFEL3Q\nVITE_FIREBASE_AUTH_DOMAIN=')
    env.write_text(text)
