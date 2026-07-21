#!/usr/bin/env node
const fs = require('fs');

const ko = JSON.parse(fs.readFileSync('./locales/ko/game/champions.json', 'utf8'));
const en = JSON.parse(fs.readFileSync('./locales/en/game/champions.json', 'utf8'));

const knownAbilities = [
  'Grumpy Bomb', 'King Bomb', 'Harpoon', 'Booster',
  'Wings of Wrath', 'Fire Bomb', 'Frost Bomb',
  'Smoke Screen', 'Deadly Momentum', 'Obliteration',
  'Frag Grenade', 'Oppressor Mine', 'Heavy Blade',
  'Rend Soul', 'Rapid Shot', 'Smoke', 'Blossom',
  'Soul Orb', 'Inferno Blade', 'Dark Siphon',
  'Pyre Strike', 'Ire', 'Gourd', 'Massacre Axe',
  'Calamity Blast', 'Power Siphon', 'Cataclysm',
  'Nether Step', 'Reversal', 'Defiance', 'Talon Rifle',
  'Rocket Boots', 'Siege Shield', 'Kinetic Burst',
  'Heroic Leap', 'Lunar Leap', 'Second Chance', 'Dredge Anchor',
  'Chivalry', 'Flamethrower', 'Luna', 'Light Bow',
  'Dead Ringer', 'Sensor Drones', 'Booby Trap',
  'Transporter', 'Bloom', 'Bulwark', 'Recharge', 'Protection'
];

const violations = [];
for (const [key, koVal] of Object.entries(ko)) {
  const enVal = en[key];
  if (!enVal) continue;
  for (const ability of knownAbilities) {
    if (enVal.includes(ability) && !koVal.includes(ability)) {
      violations.push({ key, ability, en: enVal, ko: koVal });
    }
  }
}

console.log('TOTAL VIOLATIONS:', violations.length);
console.log('UNIQUE ABILITIES:', new Set(violations.map(v => v.ability)).size);

for (const v of violations) {
  const shortKey = v.key.split('.').slice(-2).join('.');
  console.log(`${v.ability} in ${shortKey}`);
  console.log(`  EN: ${v.en.substring(0, 100)}`);
  console.log(`  KO: ${v.ko.substring(0, 100)}`);
}