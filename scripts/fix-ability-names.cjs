const fs = require('fs');

const ko = JSON.parse(fs.readFileSync('./locales/ko/game/champions.json', 'utf8'));
const en = JSON.parse(fs.readFileSync('./locales/en/game/champions.json', 'utf8'));

// First, find all keys that contain "작살" (Harpoon) or "부스터" (Booster)
// and fix them
const replacements = {
  '작살': 'Harpoon',
  '부스터': 'Booster',
  '심술 폭탄': 'Grumpy Bomb',
  'Naughty Bombs': 'Grumpy Bomb',
  'Ire의 날개': 'Wings of Wrath',
  'Wrath of Wrath': 'Wings of Wrath',
  '발사하세요. Bomb': 'Fire Bomb',
  'Kinetic Burst': '', // wrong ability name, need to find correct one
  'Deadly Momentum': '', // wrong ability name
  'Disengage': '', // wrong ability name
  'Cluster Grenade': '', // wrong ability name
};

let fixed = 0;
for (const [key, koVal] of Object.entries(ko)) {
  const enVal = en[key];
  if (!enVal) continue;
  
  for (const [koTerm, enTerm] of Object.entries(replacements)) {
    if (koTerm === '' || enTerm === '') continue;
    if (koVal.includes(koTerm)) {
      // Check if EN actually contains the proper noun
      const properNoun = enTerm;
      if (enVal.includes(properNoun)) {
        ko[key] = koVal.replace(new RegExp(koTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), properNoun);
        fixed++;
      }
    }
  }
}

fs.writeFileSync('./locales/ko/game/champions.json', JSON.stringify(ko, null, 2) + '\n');
console.log('Fixed', fixed, 'violations');