'use client';

import React, { useEffect, useRef, useState } from 'react';

// Map class slug to archetype ID
export function getClassArchetypeId(slug: string): number {
  switch (slug) {
    case 'artificer': return 1;
    case 'barbarian': return 2;
    case 'bard': return 3;
    case 'cleric': return 4;
    case 'druid': return 5;
    case 'fighter': return 6;
    case 'monk': return 7;
    case 'paladin': return 8;
    case 'ranger':
    case 'ranger-remake': return 9;
    case 'rogue': return 10;
    case 'sorcerer': return 11;
    case 'warlock': return 12;
    case 'wizard': return 13;
    case 'cavaleiro-da-morte': return 14;
    case 'cacador-de-demonios': return 15;
    case 'dovahkiin': return 16;
    case 'filho-da-magia': return 17;
    case 'heroi': return 18;
    case 'runescaper': return 19;
    case 'witcher': return 20;
    case 'xama': return 21;
    default: return 0;
  }
}

const VERTEX_SHADER = `
attribute vec2 a_position;
varying vec2 v_uv;

void main() {
  v_uv = (a_position + 1.0) * 0.5;
  gl_Position = vec4(a_position, 0.0, 1.0);
}
`;

const FRAGMENT_SHADER = `
precision highp float;

uniform vec2 u_resolution;
uniform float u_time;
uniform vec2 u_mouse;
uniform int u_class_id;
uniform float u_hover;

varying vec2 v_uv;

#define PI 3.14159265359

// Rotation helper
mat2 rot(float a) {
  float c = cos(a), s = sin(a);
  return mat2(c, -s, s, c);
}

// Pseudo-random noise
float hash(vec2 p) {
  p = fract(p * vec2(123.34, 456.21));
  p += dot(p, p + 45.32);
  return fract(p.x * p.y);
}

float noise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  f = f * f * (3.0 - 2.0 * f);
  float a = hash(i);
  float b = hash(i + vec2(1.0, 0.0));
  float c = hash(i + vec2(0.0, 1.0));
  float d = hash(i + vec2(1.0, 1.0));
  return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float fbm(vec2 p) {
  float v = 0.0;
  float a = 0.5;
  vec2 shift = vec2(100.0);
  mat2 r = mat2(cos(0.5), sin(0.5), -sin(0.5), cos(0.5));
  for (int i = 0; i < 4; ++i) {
    v += a * noise(p);
    p = r * p * 2.0 + shift;
    a *= 0.5;
  }
  return v;
}

// Distance to segment
float dfSegment(vec2 p, vec2 a, vec2 b) {
  vec2 pa = p - a, ba = b - a;
  float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
  return length(pa - ba * h);
}

// Distance to regular polygon
float dfPolygon(vec2 p, float r, int n) {
  float a = atan(p.x, p.y) + PI;
  float r_poly = 2.0 * PI / float(n);
  return cos(floor(0.5 + a / r_poly) * r_poly - a) * length(p) - r;
}

void main() {
  vec2 uv = (gl_FragCoord.xy - 0.5 * u_resolution) / min(u_resolution.x, u_resolution.y);
  vec2 mouse = u_mouse;
  uv += mouse * 0.04 * u_hover;

  float t = u_time * 0.8;
  vec3 col = vec3(0.0);

  // Background vignette & parchment texture
  float grain = hash(uv * 120.0 + fract(t * 0.01)) * 0.05;
  float vignette = 1.0 - smoothstep(0.4, 1.2, length(uv));

  // Base background
  vec3 bgDark = vec3(0.04, 0.03, 0.03);

  // 1: ARTIFICER (Gears, electric cyan circuits, brass core)
  if (u_class_id == 1) {
    vec3 cBrass = vec3(0.85, 0.65, 0.25);
    vec3 cCyan = vec3(0.1, 0.9, 1.0);
    vec2 p = uv;
    
    // Rotating gear
    vec2 pGear = rot(t * 0.3) * p;
    float r = length(pGear);
    float a = atan(pGear.y, pGear.x);
    float teeth = sin(a * 12.0) * 0.03;
    float gearBody = abs(r - 0.32 - teeth) - 0.015;
    float gearInner = abs(r - 0.22) - 0.01;
    float spokes = min(abs(pGear.x), abs(pGear.y)) - 0.01;
    if (r > 0.35 || r < 0.1) spokes = 1.0;
    
    float gear = min(min(gearBody, gearInner), spokes);
    float gearGlow = 0.015 / (abs(gear) + 0.015);

    // Circuit grid lines
    vec2 gridP = fract(p * 5.0) - 0.5;
    float grid = min(abs(gridP.x), abs(gridP.y)) - 0.02;
    float pulse = sin(p.x * 6.0 + p.y * 6.0 - t * 3.0);
    float spark = smoothstep(0.85, 1.0, pulse) * (0.01 / (abs(grid) + 0.01));

    col = bgDark + cBrass * gearGlow * 0.9 + cCyan * spark * 0.8;
    col += cCyan * 0.03 / (length(p) + 0.1);
  }

  // 2: BARBARIAN (Volcanic lava cracks, primal blood rage flame)
  else if (u_class_id == 2) {
    vec3 cBlood = vec3(0.9, 0.15, 0.05);
    vec3 cLava = vec3(1.0, 0.6, 0.1);
    vec2 p = uv;

    float n = fbm(p * 4.0 + vec2(0.0, -t * 0.5));
    float cracks = abs(sin(p.x * 8.0 + n * 4.0) * cos(p.y * 8.0 + n * 4.0));
    float heat = 0.03 / (cracks + 0.05);

    // Crossed battle axes silhouette / rune slash
    vec2 pSlash1 = rot(0.7) * p;
    vec2 pSlash2 = rot(-0.7) * p;
    float slash = min(abs(pSlash1.x) - 0.01, abs(pSlash2.x) - 0.01);
    float slashGlow = 0.02 / (abs(slash) + 0.02);

    col = bgDark + mix(cBlood, cLava, n) * heat * 0.8 + cLava * slashGlow * (0.5 + 0.5 * sin(t * 2.0));
  }

  // 3: BARD (Harmonic sound waves, magenta and starlight resonance)
  else if (u_class_id == 3) {
    vec3 cViolet = vec3(0.65, 0.2, 0.9);
    vec3 cGold = vec3(1.0, 0.85, 0.35);
    vec2 p = uv;

    float r = length(p);
    float wave1 = sin(r * 22.0 - t * 2.5);
    float wave2 = cos(atan(p.y, p.x) * 5.0 + t);
    float soundRing = abs(r - 0.28 - wave2 * 0.03) - 0.008;
    float ringGlow = 0.015 / (abs(soundRing) + 0.015);

    // Harmonic strings
    float stringLines = abs(sin(p.y * 18.0 + sin(p.x * 6.0 + t) * 0.4)) - 0.05;
    float stringGlow = 0.008 / (abs(stringLines) + 0.02);

    col = bgDark + cViolet * ringGlow + cGold * stringGlow * (1.0 - smoothstep(0.2, 0.6, r));
    col += cGold * 0.02 / (r + 0.05);
  }

  // 4: CLERIC (Divine sunburst, sacred solar mandala)
  else if (u_class_id == 4) {
    vec3 cHoly = vec3(1.0, 0.92, 0.55);
    vec3 cAura = vec3(0.9, 0.7, 0.2);
    vec2 p = uv;

    float r = length(p);
    float a = atan(p.y, p.x);
    float rays = abs(sin(a * 8.0 + t * 0.4)) * (1.0 - smoothstep(0.05, 0.6, r));
    float halo = abs(r - 0.28) - 0.01;
    float innerHalo = abs(r - 0.16) - 0.008;

    float haloGlow = 0.02 / (abs(halo) + 0.02) + 0.015 / (abs(innerHalo) + 0.015);
    float core = 0.04 / (r + 0.08);

    col = bgDark + cAura * rays * 0.7 + cHoly * (haloGlow + core);
  }

  // 5: DRUID (Emerald spiral of life, bioluminescent forest spores)
  else if (u_class_id == 5) {
    vec3 cEmerald = vec3(0.05, 0.85, 0.35);
    vec3 cAmber = vec3(0.95, 0.75, 0.2);
    vec2 p = uv;

    float r = length(p);
    float a = atan(p.y, p.x) + t * 0.6;
    float spiral = abs(r - mod(a * 0.08, 0.35)) - 0.012;
    float spiralGlow = 0.018 / (abs(spiral) + 0.018);

    // Spores
    vec2 pSpore = fract(p * 8.0 + vec2(sin(t + p.y), cos(t * 0.5))) - 0.5;
    float spore = length(pSpore) - 0.04;
    float sporeGlow = 0.006 / (abs(spore) + 0.01);

    col = bgDark + cEmerald * spiralGlow + cAmber * sporeGlow * (1.0 - smoothstep(0.3, 0.7, r));
  }

  // 6: FIGHTER (Crossed damascus steel blades, clashing sparks)
  else if (u_class_id == 6) {
    vec3 cSteel = vec3(0.75, 0.85, 0.95);
    vec3 cCrimson = vec3(0.8, 0.2, 0.2);
    vec3 cSpark = vec3(1.0, 0.8, 0.3);
    vec2 p = uv;

    // Crossed blades
    vec2 b1 = rot(0.65) * p;
    vec2 b2 = rot(-0.65) * p;
    float blade1 = max(abs(b1.x) - 0.025, abs(b1.y) - 0.4);
    float blade2 = max(abs(b2.x) - 0.025, abs(b2.y) - 0.4);
    float edge = min(abs(blade1), abs(blade2));
    float edgeGlow = 0.012 / (edge + 0.012);

    // Shield crest ring
    float shieldRing = abs(length(p) - 0.32) - 0.01;
    float shieldGlow = 0.01 / (abs(shieldRing) + 0.01);

    // Clash flash at center
    float flash = (0.04 + 0.02 * sin(t * 4.0)) / (length(p) + 0.05);

    col = bgDark + cSteel * edgeGlow + cCrimson * shieldGlow + cSpark * flash;
  }

  // 7: MONK (Enso circle, pulsating inner Ki energy)
  else if (u_class_id == 7) {
    vec3 cKi = vec3(0.2, 0.85, 0.95);
    vec3 cGoldKi = vec3(1.0, 0.7, 0.2);
    vec2 p = uv;

    float r = length(p);
    float a = atan(p.y, p.x);
    // Enso circle: varied thickness
    float thickness = 0.03 + 0.025 * sin(a + 1.2);
    float enso = abs(r - 0.3) - thickness;
    if (a > 2.5 && a < 3.0) enso = 1.0; // Enso gap
    float ensoGlow = 0.015 / (abs(enso) + 0.015);

    // Inner pulsating Ki core
    float kiWave = sin(r * 30.0 - t * 3.0);
    float core = (0.035 + 0.01 * sin(t * 2.0)) / (r + 0.06);

    col = bgDark + cGoldKi * ensoGlow + cKi * (core + kiWave * 0.1 * smoothstep(0.35, 0.0, r));
  }

  // 8: PALADIN (Sun-sword descending, righteous golden flames)
  else if (u_class_id == 8) {
    vec3 cHolyGold = vec3(1.0, 0.8, 0.25);
    vec3 cPlatinum = vec3(0.9, 0.95, 1.0);
    vec2 p = uv;

    // Sword blade along y
    float blade = max(abs(p.x) - 0.02, abs(p.y) - 0.38);
    float crossguard = max(abs(p.x) - 0.18, abs(p.y + 0.12) - 0.025);
    float sword = min(blade, crossguard);
    float swordGlow = 0.015 / (abs(sword) + 0.015);

    // Holy radiance aura
    float a = atan(p.y, p.x);
    float rays = sin(a * 12.0 + t) * (1.0 - smoothstep(0.1, 0.5, length(p)));

    col = bgDark + cPlatinum * swordGlow + cHolyGold * (rays * 0.4 + 0.03 / (length(p) + 0.1));
  }

  // 9: RANGER (Spectral bow & arrow drawn, wind trails, forest twilight)
  else if (u_class_id == 9) {
    vec3 cForest = vec3(0.1, 0.75, 0.4);
    vec3 cArrow = vec3(0.95, 0.85, 0.4);
    vec2 p = uv;

    // Arc of bow
    vec2 pBow = p - vec2(0.1, 0.0);
    float bowRing = abs(length(pBow) - 0.35) - 0.015;
    if (pBow.x < -0.1) bowRing = 1.0;
    float bowGlow = 0.012 / (abs(bowRing) + 0.015);

    // Arrow line
    float arrow = max(abs(p.y) - 0.015, abs(p.x) - 0.38);
    float arrowGlow = 0.015 / (abs(arrow) + 0.015);

    // Concentric reticle rings
    float reticle = abs(length(p) - 0.18) - 0.008;
    float reticleGlow = 0.008 / (abs(reticle) + 0.012);

    col = bgDark + cForest * (bowGlow + reticleGlow) + cArrow * arrowGlow;
  }

  // 10: ROGUE (Twin shadow daggers, venom smoke, purple darkness)
  else if (u_class_id == 10) {
    vec3 cShadow = vec3(0.55, 0.1, 0.85);
    vec3 cBlade = vec3(0.85, 0.9, 0.95);
    vec2 p = uv;

    // Swirling dark smoke
    float smoke = fbm(p * 5.0 + vec2(t * 0.3, t * 0.2));
    float smokeRing = smoothstep(0.2, 0.6, length(p) + smoke * 0.2);

    // Crossed curved daggers
    vec2 d1 = rot(0.5) * p;
    vec2 d2 = rot(-0.5) * p;
    float dagger1 = max(abs(d1.x) - 0.02, abs(d1.y) - 0.32);
    float dagger2 = max(abs(d2.x) - 0.02, abs(d2.y) - 0.32);
    float daggers = min(dagger1, dagger2);
    float dagGlow = 0.012 / (abs(daggers) + 0.012);

    // Venom drip glint
    float glint = (0.02 + 0.01 * sin(t * 3.0)) / (length(p) + 0.03);

    col = bgDark + cShadow * (1.0 - smokeRing) * 0.7 + cBlade * dagGlow + vec3(0.2, 0.9, 0.4) * glint * 0.6;
  }

  // 11: SORCERER (Wild magic chromatic plasma, chaotic lightning arcs)
  else if (u_class_id == 11) {
    vec3 cMagenta = vec3(1.0, 0.1, 0.6);
    vec3 cCyan = vec3(0.1, 0.8, 1.0);
    vec2 p = uv;

    float r = length(p);
    float a = atan(p.y, p.x);
    // Chaotic plasma tentacles
    float plasma = sin(a * 7.0 + sin(r * 15.0 - t * 4.0));
    float core = 0.04 / (abs(r - 0.25 - plasma * 0.04) + 0.02);

    // Inner storm
    float storm = 0.035 / (r + 0.05);

    col = bgDark + mix(cMagenta, cCyan, sin(a * 3.0 + t) * 0.5 + 0.5) * (core + storm);
  }

  // 12: WARLOCK (Cosmic eldritch eye, otherworldly violet tentacles)
  else if (u_class_id == 12) {
    vec3 cEldritchViolet = vec3(0.5, 0.05, 0.8);
    vec3 cEldritchEye = vec3(0.1, 0.95, 0.6);
    vec2 p = uv;

    // Eye shape: intersection of two offset circles
    vec2 pEye = p * vec2(1.0, 1.6);
    float eyeLen = length(pEye);
    float eyeOuter = abs(eyeLen - 0.3) - 0.015;
    float eyeGlow = 0.015 / (abs(eyeOuter) + 0.015);

    // Slit pupil
    vec2 pPupil = p * vec2(4.0, 1.0);
    float pupil = length(pPupil) - 0.15;
    float pupilGlow = 0.015 / (abs(pupil) + 0.02);

    // Tendrils
    float tentacle = sin(atan(p.y, p.x) * 6.0 + sin(length(p) * 10.0 - t * 2.0));
    float tenGlow = smoothstep(0.7, 1.0, tentacle) * 0.3;

    col = bgDark + cEldritchViolet * (eyeGlow + tenGlow) + cEldritchEye * pupilGlow;
  }

  // 13: WIZARD (Intricate arcane transmutation rings, orbiting constellations)
  else if (u_class_id == 13) {
    vec3 cArcaneBlue = vec3(0.1, 0.6, 1.0);
    vec3 cGoldSigil = vec3(1.0, 0.85, 0.35);
    vec2 p = uv;

    float r = length(p);
    // Rotating concentric sigil rings
    vec2 pR1 = rot(t * 0.2) * p;
    vec2 pR2 = rot(-t * 0.3) * p;

    float ring1 = abs(length(pR1) - 0.34) - 0.01;
    float ring2 = abs(length(pR2) - 0.22) - 0.008;
    float ring3 = abs(length(p) - 0.12) - 0.006;

    // Inscribed polygon inside ring
    float poly = abs(dfPolygon(pR1, 0.22, 6)) - 0.008;

    float sigils = min(min(min(ring1, ring2), ring3), poly);
    float sigilGlow = 0.015 / (abs(sigils) + 0.015);

    col = bgDark + cArcaneBlue * sigilGlow + cGoldSigil * (0.025 / (r + 0.05));
  }

  // 14: CAVALEIRO DA MORTE (Frost rune blade, chilling turquoise soul flames)
  else if (u_class_id == 14) {
    vec3 cFrost = vec3(0.3, 0.95, 1.0);
    vec3 cSoulGreen = vec3(0.05, 0.9, 0.5);
    vec2 p = uv;

    float r = length(p);
    // Rune frost shards
    float shard1 = abs(p.x * 2.0 + p.y) - 0.02;
    float shard2 = abs(p.x * 2.0 - p.y) - 0.02;
    float shards = min(shard1, shard2);
    if (r > 0.4) shards = 1.0;
    float shardGlow = 0.012 / (abs(shards) + 0.015);

    // Frost skull/ring
    float iceRing = abs(r - 0.26 + sin(atan(p.y, p.x) * 6.0) * 0.02) - 0.01;
    float iceGlow = 0.015 / (abs(iceRing) + 0.015);

    col = bgDark + cFrost * shardGlow + cSoulGreen * iceGlow + cFrost * (0.02 / (r + 0.08));
  }

  // 15: CAÇADOR DE DEMÔNIOS (Twin fel warglaives, radioactive fel flame)
  else if (u_class_id == 15) {
    vec3 cFel = vec3(0.2, 1.0, 0.1);
    vec3 cDarkFel = vec3(0.05, 0.4, 0.05);
    vec2 p = uv;

    // Curved crescent warglaive
    vec2 pGlaive1 = p - vec2(0.0, 0.05);
    float g1 = abs(length(pGlaive1 * vec2(0.8, 1.8)) - 0.3) - 0.02;
    vec2 pGlaive2 = p + vec2(0.0, 0.05);
    float g2 = abs(length(pGlaive2 * vec2(0.8, 1.8)) - 0.3) - 0.02;
    float glaives = min(g1, g2);
    float glaiveGlow = 0.018 / (abs(glaives) + 0.018);

    // Fel fire swirl
    float fire = fbm(p * 6.0 + vec2(0.0, -t * 2.0));
    float fireGlow = smoothstep(0.4, 0.8, fire) * 0.5;

    col = bgDark + cFel * (glaiveGlow + fireGlow) + cDarkFel * 0.2;
  }

  // 16: DOVAHKIIN (Dragon skull crest, Thu'um shockwaves, ancient dragon runes)
  else if (u_class_id == 16) {
    vec3 cDragonGold = vec3(0.95, 0.75, 0.2);
    vec3 cFlame = vec3(1.0, 0.35, 0.05);
    vec2 p = uv;

    float r = length(p);
    // Expanding Thu'um shockwave rings
    float shock1 = abs(mod(r - t * 0.2, 0.3) - 0.15) - 0.01;
    float shockGlow = 0.01 / (abs(shock1) + 0.015) * (1.0 - smoothstep(0.1, 0.5, r));

    // Dragon crest silhouette: angular horned shield
    vec2 pD = p;
    pD.x = abs(pD.x);
    float horns = dfSegment(pD, vec2(0.0, -0.25), vec2(0.25, 0.2));
    float hornGlow = 0.015 / (horns + 0.015);

    col = bgDark + cFlame * shockGlow + cDragonGold * hornGlow;
  }

  // 17: FILHO DA MAGIA (Pure crystalline mana core, dimensional weave fractures)
  else if (u_class_id == 17) {
    vec3 cPureMana = vec3(0.1, 0.95, 1.0);
    vec3 cVioletMana = vec3(0.7, 0.2, 1.0);
    vec2 p = uv;

    // Diamond crystal shape
    vec2 pC = abs(p);
    float diamond = abs(pC.x + pC.y - 0.28) - 0.012;
    float innerDiamond = abs(pC.x * 1.5 + pC.y * 1.5 - 0.22) - 0.008;
    float crystal = min(diamond, innerDiamond);
    float crystalGlow = 0.02 / (abs(crystal) + 0.02);

    float pulse = (0.04 + 0.02 * sin(t * 3.0)) / (length(p) + 0.05);

    col = bgDark + mix(cPureMana, cVioletMana, sin(t) * 0.5 + 0.5) * (crystalGlow + pulse);
  }

  // 18: HERÓI (Ascending golden wings of courage, blazing champion star)
  else if (u_class_id == 18) {
    vec3 cValorGold = vec3(1.0, 0.85, 0.3);
    vec3 cDawnWhite = vec3(1.0, 0.98, 0.9);
    vec2 p = uv;

    // 8-pointed star of destiny
    vec2 pStar = p;
    float starA = abs(dfPolygon(pStar, 0.2, 4));
    float starB = abs(dfPolygon(rot(PI * 0.25) * pStar, 0.2, 4));
    float star = min(starA, starB) - 0.01;
    float starGlow = 0.018 / (abs(star) + 0.018);

    // Halo of glory
    float halo = abs(length(p) - 0.32) - 0.01;
    float haloGlow = 0.01 / (abs(halo) + 0.01);

    col = bgDark + cValorGold * (starGlow + haloGlow) + cDawnWhite * (0.03 / (length(p) + 0.05));
  }

  // 19: RUNESCAPER (Orbital elemental runes, runic monument monolith)
  else if (u_class_id == 19) {
    vec3 cRuneGold = vec3(0.9, 0.8, 0.3);
    vec2 p = uv;

    float r = length(p);
    // Orbiting rune stones
    float orbit = abs(r - 0.28) - 0.008;
    float orbitGlow = 0.01 / (abs(orbit) + 0.01);

    // 5 orbiting colored elemental nodes
    float nodes = 0.0;
    vec3 nodeColor = vec3(0.0);
    for (int i = 0; i < 5; i++) {
      float ang = float(i) * (2.0 * PI / 5.0) + t * 0.5;
      vec2 pos = vec2(cos(ang), sin(ang)) * 0.28;
      float dNode = length(p - pos) - 0.035;
      if (dNode < 0.05) {
        float glow = 0.01 / (abs(dNode) + 0.01);
        if (i == 0) nodeColor += vec3(1.0, 0.2, 0.1) * glow; // Fire
        if (i == 1) nodeColor += vec3(0.1, 0.6, 1.0) * glow; // Water
        if (i == 2) nodeColor += vec3(0.1, 0.9, 0.4) * glow; // Nature
        if (i == 3) nodeColor += vec3(0.9, 0.9, 0.9) * glow; // Air
        if (i == 4) nodeColor += vec3(0.8, 0.3, 1.0) * glow; // Cosmic
      }
    }

    col = bgDark + cRuneGold * orbitGlow + nodeColor + cRuneGold * (0.02 / (r + 0.06));
  }

  // 20: WITCHER (Wolf medallion eyes, silver blade gleam, Igni sparks)
  else if (u_class_id == 20) {
    vec3 cSilver = vec3(0.8, 0.88, 0.95);
    vec3 cFeralYellow = vec3(1.0, 0.85, 0.1);
    vec3 cIgni = vec3(1.0, 0.35, 0.05);
    vec2 p = uv;

    // Wolf medallion polygon
    vec2 pWolf = p;
    pWolf.x = abs(pWolf.x);
    float muzzle = dfSegment(pWolf, vec2(0.0, -0.3), vec2(0.15, 0.1));
    float ears = dfSegment(pWolf, vec2(0.15, 0.1), vec2(0.25, 0.3));
    float head = min(muzzle, ears);
    float headGlow = 0.015 / (head + 0.015);

    // Glowing feral eyes
    vec2 eyeL = p - vec2(-0.08, 0.02);
    vec2 eyeR = p - vec2(0.08, 0.02);
    float eyes = min(length(eyeL), length(eyeR)) - 0.02;
    float eyeGlow = 0.012 / (abs(eyes) + 0.015);

    // Igni sparks
    float sparks = smoothstep(0.88, 1.0, hash(p * 20.0 + t)) * 0.4;

    col = bgDark + cSilver * headGlow + cFeralYellow * eyeGlow + cIgni * sparks;
  }

  // 21: XAMÃ (Ancestral spirit totem, ethereal spirit wind, feathers)
  else if (u_class_id == 21) {
    vec3 cSpiritCyan = vec3(0.2, 0.9, 0.8);
    vec3 cAncestralGold = vec3(0.95, 0.65, 0.2);
    vec2 p = uv;

    // Totem geometry
    vec2 pT = p;
    pT.x = abs(pT.x);
    float wings = dfSegment(pT, vec2(0.0, 0.1), vec2(0.3, 0.25));
    float spine = dfSegment(p, vec2(0.0, -0.35), vec2(0.0, 0.35));
    float totem = min(wings, spine);
    float totemGlow = 0.015 / (totem + 0.015);

    // Spirit wind ripples
    float wind = sin(p.y * 15.0 + sin(p.x * 5.0 + t * 2.0));
    float windGlow = smoothstep(0.8, 1.0, wind) * (1.0 - smoothstep(0.2, 0.6, length(p)));

    col = bgDark + cSpiritCyan * (totemGlow + windGlow * 0.6) + cAncestralGold * (0.02 / (length(p) + 0.08));
  }

  // DEFAULT (D&D d20 core facet crystal)
  else {
    vec3 cGold = vec3(0.9, 0.75, 0.35);
    vec3 cWine = vec3(0.7, 0.15, 0.2);
    vec2 p = uv;

    float r = length(p);
    float d20 = abs(dfPolygon(rot(t * 0.3) * p, 0.28, 6)) - 0.01;
    float d20Inner = abs(dfPolygon(rot(-t * 0.2) * p, 0.16, 3)) - 0.01;
    float crystal = min(d20, d20Inner);
    float glow = 0.018 / (abs(crystal) + 0.018);

    col = bgDark + cGold * glow + cWine * (0.03 / (r + 0.06));
  }

  // Add subtle grain & vignette
  col += vec3(grain);
  col *= vignette;

  // Enhance saturation and contrast
  col = pow(col, vec3(0.9));

  gl_FragColor = vec4(col, 1.0);
}
`;

// Shared WebGL Engine Singleton for all cards
class WebGLEngine {
  private canvas: HTMLCanvasElement | null = null;
  private gl: WebGLRenderingContext | null = null;
  private program: WebGLProgram | null = null;
  private uResolutionLoc: WebGLUniformLocation | null = null;
  private uTimeLoc: WebGLUniformLocation | null = null;
  private uMouseLoc: WebGLUniformLocation | null = null;
  private uClassIdLoc: WebGLUniformLocation | null = null;
  private uHoverLoc: WebGLUniformLocation | null = null;
  private isInitialized = false;

  public init(): boolean {
    if (this.isInitialized) return true;
    if (typeof window === 'undefined') return false;

    this.canvas = document.createElement('canvas');
    this.canvas.width = 360;
    this.canvas.height = 180;

    const gl = this.canvas.getContext('webgl', { preserveDrawingBuffer: true, alpha: false, antialias: true });
    if (!gl) return false;
    this.gl = gl;

    // Compile Shaders
    const vs = gl.createShader(gl.VERTEX_SHADER)!;
    gl.shaderSource(vs, VERTEX_SHADER);
    gl.compileShader(vs);

    const fs = gl.createShader(gl.FRAGMENT_SHADER)!;
    gl.shaderSource(fs, FRAGMENT_SHADER);
    gl.compileShader(fs);

    if (!gl.getShaderParameter(fs, gl.COMPILE_STATUS)) {
      console.error('Fragment shader compile error:', gl.getShaderInfoLog(fs));
      return false;
    }

    const prog = gl.createProgram()!;
    gl.attachShader(prog, vs);
    gl.attachShader(prog, fs);
    gl.linkProgram(prog);

    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
      console.error('Program link error:', gl.getProgramInfoLog(prog));
      return false;
    }

    gl.useProgram(prog);
    this.program = prog;

    // Full screen quad buffer
    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([
      -1, -1,
       1, -1,
      -1,  1,
      -1,  1,
       1, -1,
       1,  1,
    ]), gl.STATIC_DRAW);

    const aPos = gl.getAttribLocation(prog, 'a_position');
    gl.enableVertexAttribArray(aPos);
    gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);

    // Uniform locations
    this.uResolutionLoc = gl.getUniformLocation(prog, 'u_resolution');
    this.uTimeLoc = gl.getUniformLocation(prog, 'u_time');
    this.uMouseLoc = gl.getUniformLocation(prog, 'u_mouse');
    this.uClassIdLoc = gl.getUniformLocation(prog, 'u_class_id');
    this.uHoverLoc = gl.getUniformLocation(prog, 'u_hover');

    gl.viewport(0, 0, this.canvas.width, this.canvas.height);
    this.isInitialized = true;
    return true;
  }

  public render(classId: number, time: number, mouse: [number, number], hover: number): HTMLCanvasElement | null {
    if (!this.init() || !this.gl || !this.canvas) return null;
    const gl = this.gl;

    gl.useProgram(this.program);
    gl.uniform2f(this.uResolutionLoc, this.canvas.width, this.canvas.height);
    gl.uniform1f(this.uTimeLoc, time);
    gl.uniform2f(this.uMouseLoc, mouse[0], mouse[1]);
    gl.uniform1i(this.uClassIdLoc, classId);
    gl.uniform1f(this.uHoverLoc, hover);

    gl.drawArrays(gl.TRIANGLES, 0, 6);
    return this.canvas;
  }
}

const engine = new WebGLEngine();

interface ClassCardWebGLProps {
  slug: string;
  title: string;
}

export function ClassCardWebGL({ slug, title }: ClassCardWebGLProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [isHovered, setIsHovered] = useState(false);
  const mouseRef = useRef<[number, number]>([0, 0]);
  const animFrameRef = useRef<number | null>(null);
  const startTimeRef = useRef<number>(Date.now() + Math.random() * 1000);
  const hoverFactorRef = useRef<number>(0);

  const archetypeId = getClassArchetypeId(slug);

  // Initial single-frame static render on mount
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const source = engine.render(archetypeId, 1.5, [0, 0], 0);
    if (source) {
      ctx.drawImage(source, 0, 0, canvas.width, canvas.height);
    }
  }, [archetypeId]);

  // Live animation loop when hovered
  useEffect(() => {
    if (!isHovered) {
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
        animFrameRef.current = null;
      }
      return;
    }

    let running = true;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const animate = () => {
      if (!running) return;

      const elapsed = (Date.now() - startTimeRef.current) / 1000;
      // Smoothly transition hover factor up
      hoverFactorRef.current = Math.min(1.0, hoverFactorRef.current + 0.08);

      const source = engine.render(
        archetypeId,
        elapsed,
        mouseRef.current,
        hoverFactorRef.current
      );

      if (source) {
        ctx.drawImage(source, 0, 0, canvas.width, canvas.height);
      }

      animFrameRef.current = requestAnimationFrame(animate);
    };

    animFrameRef.current = requestAnimationFrame(animate);

    return () => {
      running = false;
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
      }
    };
  }, [isHovered, archetypeId]);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    mouseRef.current = [x, -y];
  };

  return (
    <div
      className="class-card__webgl-wrapper"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => {
        setIsHovered(false);
        hoverFactorRef.current = 0;
        mouseRef.current = [0, 0];
      }}
      onMouseMove={handleMouseMove}
      aria-label={`Ilustração WebGL da classe ${title}`}
      style={{
        position: 'relative',
        width: '100%',
        height: '160px',
        overflow: 'hidden',
        background: '#0d0a0b',
        cursor: 'pointer',
      }}
    >
      <canvas
        ref={canvasRef}
        width={360}
        height={180}
        style={{
          width: '100%',
          height: '100%',
          display: 'block',
          objectFit: 'cover',
          transition: 'transform 0.4s ease, filter 0.4s ease',
          transform: isHovered ? 'scale(1.04)' : 'scale(1.0)',
          filter: isHovered ? 'brightness(1.15) contrast(1.05)' : 'brightness(1.0)',
        }}
      />
      {/* Subtle atmospheric vignette gradient overlay */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          boxShadow: 'inset 0 0 35px rgba(0,0,0,0.85), inset 0 -15px 20px rgba(0,0,0,0.9)',
          borderBottom: '1px solid var(--line, rgba(216, 173, 88, 0.2))',
        }}
      />
    </div>
  );
}
