from pathlib import Path
import re

p = Path('/home/ubuntu/sog-lig-im/index.html')
s = p.read_text()

old = '''const firebaseConfig = {
  apiKey: "AIzaSyBpA8xbmZRM_Du2TArMxwN798Q70955lAY",
  authDomain: "sogligim-113ae.firebaseapp.com",
  projectId: "sogligim-113ae",
  storageBucket: "sogligim-113ae.firebasestorage.app",
  messagingSenderId: "939640657660",
  appId: "1:939640657660:web:23fce8a66fe5f29ac7a979",
  measurementId: "G-6HK7HP6EQ4"
};'''
new = '''const firebaseConfig = {
  apiKey: "AIzaSyBilCpT4QEHpcr7FZ_-542wxErC2tFEL3Q",
  authDomain: "sogligim-prod-db270.firebaseapp.com",
  projectId: "sogligim-prod-db270",
  storageBucket: "sogligim-prod-db270.firebasestorage.app",
  messagingSenderId: "1098824868523",
  appId: "1:1098824868523:web:e1d24706723187a7bccdee",
  measurementId: "G-9NGCRV3G6E"
};'''
s = s.replace(old, new)

# Remove Premium navigation and section completely.
s = re.sub(r'\s*<button class="tab" data-tab="premium">.*?</button>', '', s, flags=re.S)
s = re.sub(r'\s*<!-- PREMIUM -->.*?</section>\s*', '\n', s, flags=re.S)
s = s.replace(' <span class="lock" data-i18n="premium_badge">Premium</span>', '')
s = s.replace('<!-- CLINICS (premium) -->', '<!-- CLINICS -->').replace('<!-- DRUG INFO (premium) -->', '<!-- DRUG INFO -->')

# Add Family Mode navigation and panel.
needle = '    <button class="tab" data-tab="steps">'
family_tab = '''    <button class="tab" data-tab="family"><svg class="tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="8" r="3"/><circle cx="17" cy="9" r="2.5"/><path d="M3 20c0-3 2.4-5 6-5s6 2 6 5"/><path d="M15 15c3 0 5 1.7 5 5"/></svg><span>Oila rejimi</span></button>\n'''
s = s.replace(needle, family_tab + needle)
family_panel = '''\n    <!-- FAMILY MODE -->\n    <section class="panel" id="panel-family">\n      <div class="grid cols-2" style="align-items:start;">\n        <div class="card">\n          <h3>Oila rejimi</h3>\n          <p class="muted">Oila aʼzolaringizni qoʻshing va ularning sogʻliq odatlarini bir joyda kuzating.</p>\n          <div class="field"><label>Ism</label><input id="familyName" placeholder="masalan: Onam"></div>\n          <div class="field"><label>Qarindoshlik</label><input id="familyRelation" placeholder="masalan: ona"></div>\n          <button class="btn" onclick="addFamilyMember()">Aʼzo qoʻshish</button>\n        </div>\n        <div class="card"><h3>Oila aʼzolari</h3><div id="familyList"><div class="empty">Hali aʼzo qoʻshilmagan</div></div></div>\n      </div>\n    </section>\n'''
s = s.replace('    <!-- CLINICS -->', family_panel + '\n    <!-- CLINICS -->')

# Add AI food controls while keeping existing card styling.
food_anchor = '          <button class="btn" onclick="addFood()" data-i18n="btn_add">Qoʻshish</button>'
ai_block = '''          <div class="field" style="margin-top:16px;"><label>Matn orqali AI kaloriya</label><div class="row"><input id="foodAiText" placeholder="masalan: 2 dona tuxum va non"><button class="btn ghost" onclick="parseFoodWithAI()">Hisoblash</button></div></div>\n          <div class="field"><label>Rasm orqali AI kaloriya</label><input id="foodPhoto" type="file" accept="image/*" onchange="analyzeFoodPhoto(event)"></div>\n          <div class="row"><button class="btn ghost" onclick="startVoiceInput()">Ovozli kiritish</button><span id="voiceStatus" class="muted" style="align-self:center;"></span></div>\n'''
s = s.replace(food_anchor, food_anchor + '\n' + ai_block, 1)

# Replace storage/subscription block with collection-backed storage and no subscriptions.
start = s.index('async function storageGet(key, shared=false){')
end = s.index('/* ---------------- MEDICATIONS ---------------- */')
replacement = '''function collectionForKey(key){\n  if(key === 'medications') return ['medicines','current'];\n  if(key.startsWith('calories:')) return ['food_logs', key.slice(9)];\n  if(key.startsWith('steps:')) return ['steps_logs', key.slice(6)];\n  if(key.startsWith('family:')) return ['family_members', key.slice(7)];\n  return null;\n}\nasync function storageGet(key, shared=false){\n  if(!currentUser) return null;\n  const route = collectionForKey(key);\n  try{\n    if(route){ const snap = await db.collection(route[0]).doc(route[1]).get(); return snap.exists ? (snap.data().value ?? snap.data()) : null; }\n    if(key in userDataCache) return userDataCache[key];\n    const snap = await db.collection('users').doc(currentUser.uid).get();\n    userDataCache = snap.exists ? snap.data() : {};\n    return userDataCache[key] ?? null;\n  }catch(e){ console.error('Firestore read failed', e); return null; }\n}\nasync function storageSet(key, value, shared=false){\n  userDataCache[key] = value;\n  if(!currentUser) return;\n  try{\n    const route = collectionForKey(key);\n    if(route) await db.collection(route[0]).doc(route[1]).set({value, uid: currentUser.uid, updatedAt: firebase.firestore.FieldValue.serverTimestamp()},{merge:true});\n    else await db.collection('users').doc(currentUser.uid).set({ [key]: value, uid: currentUser.uid, updatedAt: firebase.firestore.FieldValue.serverTimestamp() }, { merge:true });\n  }catch(e){ console.error('Firestore save failed', e); showToast('Saqlashda xatolik, internetni tekshiring'); }\n}\n\n/* ---------------- Tabs ---------------- */\nfunction goTab(name){\n  document.querySelectorAll('.tab').forEach(b=>b.classList.toggle('active', b.dataset.tab===name));\n  document.querySelectorAll('.panel').forEach(p=>p.classList.toggle('active', p.id==='panel-'+name));\n  if(name==='clinics') renderClinicsPanel();\n  if(name==='druginfo') renderDrugInfoPanel();\n  if(name==='family') loadFamilyMembers();\n}\ndocument.getElementById('tabs').addEventListener('click', (e)=>{ const btn=e.target.closest('.tab'); if(btn) goTab(btn.dataset.tab); });\n\n/* Premium has been removed: all health tools are available on the free plan. */\nlet sub = {status:'free'};\nfunction isPremium(){ return true; }\nfunction updatePlanPill(){ const pill=document.getElementById('planPill'); if(pill){ pill.textContent='Bepul reja'; pill.classList.remove('premium'); } }\nfunction renderSubStatus(){}\nasync function loadSub(){ updatePlanPill(); }\n\n'''
s = s[:start] + replacement + s[end:]

# Remove premium gates from free sections.
s = s.replace("  if(!isPremium()){\n    gate.innerHTML = lockedTemplate(t('clinics_locked_title'), t('clinics_locked_desc'));\n    return;\n  }\n", '')
s = s.replace("  if(!isPremium()){\n    gate.innerHTML = lockedTemplate(t('druginfo_locked_title'), t('druginfo_locked_desc'));\n    return;\n  }\n", '')

# Add free family helpers before initialization.
insert_at = s.index('async function init(){')
family_js = '''let familyMembers = [];\nasync function loadFamilyMembers(){\n  const snap = currentUser ? await db.collection('family_members').where('uid','==',currentUser.uid).get() : {docs:[]};\n  familyMembers = snap.docs.map(d=>({id:d.id,...d.data()}));\n  const el=document.getElementById('familyList'); if(!el) return;\n  el.innerHTML = familyMembers.length ? familyMembers.map(m=>`<div class="list-item"><div><b>${escapeHtml(m.name)}</b><div class="meta">${escapeHtml(m.relation||'')}</div></div><button class="btn danger-ghost" onclick="removeFamilyMember('${m.id}')">Oʻchirish</button></div>`).join('') : '<div class="empty">Hali aʼzo qoʻshilmagan</div>';\n}\nasync function addFamilyMember(){\n  const name=document.getElementById('familyName').value.trim(), relation=document.getElementById('familyRelation').value.trim();\n  if(!name || !currentUser) return showToast('Ismni kiriting');\n  await db.collection('family_members').add({uid:currentUser.uid,name,relation,createdAt:firebase.firestore.FieldValue.serverTimestamp()});\n  document.getElementById('familyName').value=''; document.getElementById('familyRelation').value=''; await loadFamilyMembers(); showToast('Oila aʼzosi qoʻshildi');\n}\nasync function removeFamilyMember(id){ await db.collection('family_members').doc(id).delete(); await loadFamilyMembers(); }\nasync function parseFoodWithAI(){\n  const text=document.getElementById('foodAiText').value.trim(); if(!text) return showToast('Ovqat tavsifini kiriting');\n  showToast('AI hisoblamoqda…');\n  try{ const r=await fetch('https://us-central1-sogligim-prod-db270.cloudfunctions.net/parseFood',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text})}); const d=await r.json(); if(d.name){ const opt=[...document.getElementById('foodSelect').options].find(o=>o.textContent.toLowerCase().includes(d.name.toLowerCase())); if(opt) document.getElementById('foodSelect').value=opt.value; document.getElementById('foodQty').value=d.quantity||1; showToast(`${d.name}: ${d.calories} kkal`); } else showToast('AI javobini olishda xatolik'); }catch(e){ showToast('AI xizmati vaqtincha mavjud emas'); }\n}\nasync function analyzeFoodPhoto(event){ const file=event.target.files?.[0]; if(!file) return; showToast('Rasm tahlil qilinmoqda…'); const reader=new FileReader(); reader.onload=async()=>{ try{ const r=await fetch('https://us-central1-sogligim-prod-db270.cloudfunctions.net/analyzeFoodPhoto',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({image:reader.result})}); const d=await r.json(); if(d.calories) showToast(`${d.name||'Ovqat'}: ${d.calories} kkal`); else showToast('Rasmni tahlil qilib bo‘lmadi'); }catch(e){ showToast('AI xizmati vaqtincha mavjud emas'); } }; reader.readAsDataURL(file); }\nfunction startVoiceInput(){ const SR=window.SpeechRecognition||window.webkitSpeechRecognition; if(!SR) return showToast('Brauzer ovozli kiritishni qoʻllab-quvvatlamaydi'); const r=new SR(); r.lang='uz-UZ'; r.onstart=()=>document.getElementById('voiceStatus').textContent='Tinglanmoqda…'; r.onresult=e=>{ document.getElementById('foodAiText').value=e.results[0][0].transcript; document.getElementById('voiceStatus').textContent='Tayyor'; }; r.onerror=()=>document.getElementById('voiceStatus').textContent='Xatolik'; r.start(); }\n\n'''
s = s[:insert_at] + family_js + s[insert_at:]

# Ensure init loads family and plan pill; retain existing init body.
s = s.replace('  await loadSub();\n', '  await loadSub();\n  await loadFamilyMembers();\n', 1)

p.write_text(s)
