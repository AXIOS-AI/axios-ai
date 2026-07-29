/**
 * Vittoria Farmacie — Facebook OSINT Scan via ofacebook prefix library
 * Genera URL variants per ogni farmacia usando la prefix library
 */
import {
  THUMPERSECURE_PREFIXES,
  METHOD_COMBINATIONS,
  buildUrl,
} from './src/prefix-library.js';

import { getPrefixIndex, resolvePrefixHost } from './src/domain/prefixes.js';

const FARMACIE = [
  { nome: "Amica SRL", email: "farmaciamicasrl@gmail.com", fb_known: "https://www.facebook.com/p/Farmacia-Amica-100057152632043/" },
  { nome: "Bianculli", email: "biancullifarmacia@gmail.com", fb_known: "https://www.facebook.com/farmacia.bianculli/" },
  { nome: "Calí-Mancuso", email: "farmacista.farmacali@outlook.com", fb_known: "https://www.facebook.com/farmacia.cali.3/" },
  { nome: "Cannizzo", email: "farmaciacannizzoelsamaria@virgilio.it", fb_known: "https://www.facebook.com/p/Farmacia-Cannizzo-100048470153425/" },
  { nome: "De Pasquale", email: "farmadep@gmail.com", fb_known: "https://www.facebook.com/farmadepasquale/" },
  { nome: "Emaia", email: "farmacia.emaia@virgilio.it", fb_known: "https://www.facebook.com/p/Farmacia-Emaia-100063644186184/" },
  { nome: "Guastella SNC", email: "info@farmaciaguastella.com", fb_known: "https://www.facebook.com/p/Farmacia-Guastella-100063568809250/" },
  { nome: "Iacono G.A.", email: "info@farmaciajacono.it", fb_known: "https://www.facebook.com/farmacia.jacono/" },
  { nome: "Incardona Luigi", email: "incardona.farma@tiscali.it", fb_known: "https://www.facebook.com/farmacia.incardona/" },
  { nome: "Mangione", email: "farmaciamangionerg@gmail.com", fb_known: "https://www.facebook.com/FarmaciaMangione/" },
  { nome: "Michele Arcangelo SRL", email: "farmacia.michelearcangelo90@gmail.com", fb_known: "https://www.facebook.com/farmaciamichelearcangelovittoria/" },
  { nome: "Roma", email: "farmaciaromavittoria@gmail.com", fb_known: "https://www.facebook.com/farmaciaromavittoria/" },
  { nome: "Vittoria 15", email: "farmaciavitroria15@gmail.com", fb_known: "https://www.facebook.com/farmaciavittoria15/" },
];

// Genera username candidates da nome farmacia
function genUsernames(nome, email) {
  const slug = nome.toLowerCase()
    .replace(/[^a-z0-9]/g, '')
    .replace(/\s+/g, '');
  
  const candidates = [slug];
  
  // Varianti con prefisso farmacia
  if (!slug.startsWith('farmacia')) candidates.unshift(`farmacia${slug}`);
  if (!slug.startsWith('farmaci')) candidates.unshift(`farmaci${slug}`);
  
  // Varianti con separatori
  const spaced = nome.toLowerCase().replace(/[^a-z0-9]/g, ' ').trim().replace(/\s+/g, '.');
  if (spaced && !candidates.includes(spaced)) candidates.push(spaced);
  
  const dashed = nome.toLowerCase().replace(/[^a-z0-9]/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '');
  if (dashed && !candidates.includes(dashed)) candidates.push(dashed);

  // Da email (username parte prima @)
  if (email) {
    const emailUser = email.split('@')[0].toLowerCase();
    if (!candidates.includes(emailUser)) candidates.push(emailUser);
  }

  return [...new Set(candidates)].slice(0, 8);
}

// Estrai username da URL FB noto
function getUsernameFromUrl(url) {
  if (!url) return null;
  const parts = url.replace(/\/+$/, '').split('/');
  const last = parts[parts.length - 1];
  // Salta pagine con ID numerico p/...
  if (last.startsWith('p/')) return null;
  if (/^\d/.test(last)) return null;
  if (last === 'facebook.com') return null;
  return last;
}

const prefixIndex = getPrefixIndex();

// Prefix rilevanti per profile discovery + mobile
const SEARCH_PREFIXES = [
  // Profile discovery method
  ...METHOD_COMBINATIONS.find(m => m.id === 'profile-discovery')?.prefixes || [],
  // Mobile variants
  ...METHOD_COMBINATIONS.find(m => m.id === 'mobile-variants')?.prefixes || [],
  // Aggiungi altri prefix utili per profile lookup
  'l', 'lm', 't', // link tracking
  '0', 'c', 'd', 'h', 'o', 'p', 'w', 'x', 'z', // single char
  'pages', 'web',
  'ww', 'wwww',
];

function resolveHost(prefix) {
  return resolvePrefixHost(prefixIndex, prefix) || 
    (prefix.includes('.') ? prefix : `${prefix}.facebook.com`);
}

console.log('='.repeat(80));
console.log('  FACEBOOK OSINT SCAN — FARMACIE VITTORIA');
console.log('  Via ofacebook prefix library');
console.log('  Target: 13 farmacie');
console.log('='.repeat(80));

for (const farmacia of FARMACIE) {
  console.log(`\n${'─'.repeat(80)}`);
  console.log(`  🏥 ${farmacia.nome}`);
  console.log(`  📧 ${farmacia.email}`);
  console.log(`  🔗 FB noto: ${farmacia.fb_known || '❌'}`);
  console.log(`${'─'.repeat(80)}`);

  const usernames = genUsernames(farmacia.nome, farmacia.email);
  const knownUser = getUsernameFromUrl(farmacia.fb_known);
  if (knownUser && !usernames.includes(knownUser)) usernames.unshift(knownUser);

  console.log(`  Username variants: ${usernames.join(', ')}\n`);

  // Per ogni username, genera URL con ogni prefix
  for (const username of usernames.slice(0, 3)) { // top 3 username
    console.log(`  ── @${username} ──`);
    const hosts = [...new Set(SEARCH_PREFIXES.map(resolveHost).filter(Boolean))];
    
    for (const host of hosts.slice(0, 15)) { // top 15 prefix
      const url = buildUrl(host, `/${username}`);
      console.log(`    ${url}`);
    }
  }
}

console.log(`\n${'='.repeat(80)}`);
console.log('  SCAN COMPLETATO');
console.log(`  Prefix usati: ${SEARCH_PREFIXES.length}`);
console.log(`  Farmacie processate: ${FARMACIE.length}`);
console.log('='.repeat(80));
console.log('\n  📋 Per aprire i link: usa ofacebook webapp');
console.log('  💻 Avvia: python3 -m http.server 5173');
console.log('  🌐 Apri: http://localhost:5173');
