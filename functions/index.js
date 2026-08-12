const functions = require('firebase-functions');
const admin = require('firebase-admin');
const { GoogleGenerativeAI } = require('@google/generative-ai');
require('dotenv').config();

admin.initializeApp();
const db = admin.firestore();
const REGION = 'us-central1';
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || '');

function json(res, body, status = 200) {
  res.set('Access-Control-Allow-Origin', 'https://wffwff56-ai.github.io');
  res.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.set('Access-Control-Allow-Methods', 'POST, OPTIONS');
  if (res.method === 'OPTIONS') return res.status(204).send('');
  return res.status(status).json(body);
}

async function generate(prompt, image) {
  const model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash' });
  const contents = image ? [{ inlineData: { mimeType: image.mimeType, data: image.data } }, prompt] : prompt;
  const result = await model.generateContent(contents);
  return result.response.text();
}

exports.parseFood = functions.region(REGION).https.onRequest(async (req, res) => {
  if (req.method === 'OPTIONS') return json(res, {});
  try {
    const text = String(req.body?.text || '').trim();
    if (!text) return json(res, { error: 'text required' }, 400);
    const raw = await generate(`O'zbekcha ovqat tavsifini tahlil qiling: ${text}. Faqat JSON qaytaring: {"name":"qisqa nom","quantity":1,"calories":0}. Kaloriyani taxminiy hisoblang.`, null);
    const match = raw.match(/\{[\s\S]*\}/);
    return json(res, match ? JSON.parse(match[0]) : { name: text, quantity: 1, calories: 0 });
  } catch (e) { console.error(e); return json(res, { error: 'AI parse failed' }, 500); }
});

exports.analyzeFoodPhoto = functions.region(REGION).https.onRequest(async (req, res) => {
  if (req.method === 'OPTIONS') return json(res, {});
  try {
    const encoded = String(req.body?.image || '');
    const match = encoded.match(/^data:(image\/[a-zA-Z0-9.+-]+);base64,(.+)$/);
    if (!match) return json(res, { error: 'image required' }, 400);
    const raw = await generate('Rasmda ko\'rsatilgan ovqatni tanib, taxminiy porsiya va kaloriyani hisoblang. Faqat JSON qaytaring: {"name":"nom","calories":0,"portion":"porsiya"}.', { mimeType: match[1], data: match[2] });
    const obj = raw.match(/\{[\s\S]*\}/);
    return json(res, obj ? JSON.parse(obj[0]) : { name: 'Ovqat', calories: 0 });
  } catch (e) { console.error(e); return json(res, { error: 'AI vision failed' }, 500); }
});

exports.weeklyReport = functions.region(REGION).pubsub.schedule('0 20 * * 0').timeZone('Asia/Tashkent').onRun(async () => {
  const users = await db.collection('users').get();
  const batch = db.batch();
  for (const user of users.docs) {
    const report = { uid: user.id, weekEnding: new Date().toISOString().slice(0, 10), createdAt: admin.firestore.FieldValue.serverTimestamp(), message: 'Haftalik sogʻliq hisoboti tayyor.' };
    batch.set(db.collection('users').doc(user.id).collection('reports').doc(report.weekEnding), report);
  }
  await batch.commit();
  return null;
});

exports.medicineReminder = functions.region(REGION).firestore.document('medicines/{medicineId}').onWrite(async (change, context) => {
  const data = change.after.exists ? change.after.data() : null;
  if (!data || !data.uid || !data.time) return null;
  const message = { notification: { title: 'Dori vaqti — SogʻlomYoʻl', body: `${data.name} ichish vaqti keldi (${data.time})` }, data: { medicineId: context.params.medicineId, uid: data.uid } };
  const tokens = await db.collection('users').doc(data.uid).collection('fcm_tokens').get();
  if (tokens.empty) return null;
  await admin.messaging().sendEachForMulticast({ tokens: tokens.docs.map(d => d.id), ...message });
  return null;
});
