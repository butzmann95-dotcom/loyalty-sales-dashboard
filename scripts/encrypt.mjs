// Cifra data/data.json -> docs/data.enc.json (AES-256-GCM, clave derivada con PBKDF2)
// Uso: node scripts/encrypt.mjs [passphrase]  (o variable de entorno DASH_KEY)
import { readFileSync, writeFileSync } from 'node:fs';
import { randomBytes, pbkdf2Sync, createCipheriv } from 'node:crypto';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const pass = process.argv[2] || process.env.DASH_KEY;
if (!pass) { console.error('Falta passphrase (arg o DASH_KEY)'); process.exit(1); }

const plain = readFileSync(join(root, 'data/data.json'));
const salt = randomBytes(16);
const iv = randomBytes(12);
const key = pbkdf2Sync(pass, salt, 150000, 32, 'sha256');
const cipher = createCipheriv('aes-256-gcm', key, iv);
const ct = Buffer.concat([cipher.update(plain), cipher.final(), cipher.getAuthTag()]);

writeFileSync(join(root, 'docs/data.enc.json'), JSON.stringify({
  v: 1,
  salt: salt.toString('base64'),
  iv: iv.toString('base64'),
  ct: ct.toString('base64'),
}));
console.log('OK -> docs/data.enc.json (' + ct.length + ' bytes)');
