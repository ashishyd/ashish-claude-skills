// slop-check browser scan. Paste the whole file into the browser JavaScript tool; the last expression is the result.
// Reads computed styles of visible elements and returns AI-default tells with sample selectors. Read only.
(() => {
  const parse = (s) => [...s.matchAll(/rgba?\(([^)]+)\)/g)].map((m) => m[1].split(/[ ,/]+/).filter(Boolean).map(Number));
  const hsl = ([r, g, b, a = 1]) => {
    r /= 255; g /= 255; b /= 255;
    const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn, l = (mx + mn) / 2;
    const s = d === 0 ? 0 : d / (1 - Math.abs(2 * l - 1));
    let h = 0;
    if (d) h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4;
    return { h: (h * 60 + 360) % 360, s, l, a };
  };
  const colourful = (c) => c.s > 0.3 && c.a > 0.15 && c.l > 0.1 && c.l < 0.9;
  const hueSpread = (cs) => {
    const hs = cs.filter(colourful).map((c) => c.h);
    if (hs.length < 2) return 0;
    let best = 0;
    for (const a of hs) for (const b of hs) best = Math.max(best, Math.min(Math.abs(a - b), 360 - Math.abs(a - b)));
    return best;
  };
  const sel = (el) => el.id ? `#${el.id}` : el.tagName.toLowerCase() + (typeof el.className === 'string' && el.className.trim() ? '.' + el.className.trim().split(/\s+/).slice(0, 3).join('.') : '');
  const emoji = /\p{Extended_Pictographic}/u;
  const hits = {};
  const add = (k, el, v) => { (hits[k] ||= { count: 0, samples: [] }).count++; if (hits[k].samples.length < 5) hits[k].samples.push(v ? `${sel(el)} (${v})` : sel(el)); };
  const radii = new Set(), sizes = new Set(), shadows = new Set(), colours = new Set();
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect();
    const st = getComputedStyle(el);
    if (!r.width || !r.height || st.visibility === 'hidden' || st.display === 'none') continue;
    const bg = st.backgroundImage;
    if (bg.includes('gradient')) {
      const spread = hueSpread(parse(bg).map(hsl));
      if (spread >= 30) add('hue gradient', el, `${Math.round(spread)}° hue spread`);
      if (bg.includes('radial-gradient') && spread >= 30) add('radial colour wash', el);
    }
    if ((st.webkitBackgroundClip || st.backgroundClip) === 'text') add('gradient text', el);
    if (st.boxShadow !== 'none') {
      shadows.add(st.boxShadow);
      const blur = Math.max(0, ...[...st.boxShadow.matchAll(/(-?\d+(?:\.\d+)?)px/g)].map((m) => +m[1]));
      if (parse(st.boxShadow).map(hsl).some(colourful) && blur >= 8) add('coloured glow shadow', el, st.boxShadow.slice(0, 60));
    }
    if (st.textShadow !== 'none' && parse(st.textShadow).map(hsl).some(colourful)) add('glowing text', el);
    if (st.animationName !== 'none' && st.animationIterationCount === 'infinite') add('looping animation', el, st.animationName);
    if (st.backdropFilter && st.backdropFilter.includes('blur')) add('glass blur', el);
    const fs = parseFloat(st.fontSize), ls = parseFloat(st.letterSpacing) || 0;
    if (st.textTransform === 'uppercase' && fs <= 14 && ls / fs >= 0.05 && el.textContent.trim()) add('uppercase tracked label', el);
    if (/^H[1-3]$/.test(el.tagName) && +st.fontWeight >= 700) add('heavy heading (700+)', el, st.fontWeight);
    for (const n of el.childNodes) if (n.nodeType === 3 && emoji.test(n.textContent)) { add('emoji in UI text', el, n.textContent.trim().slice(0, 30)); break; }
    if (/lorem ipsum|acme|john doe|jane doe/i.test([...el.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent).join(' '))) add('placeholder copy', el);
    if (st.borderRadius !== '0px') radii.add(st.borderRadius);
    if (el.textContent.trim()) sizes.add(st.fontSize);
    colours.add(st.color);
  }
  return {
    url: location.href,
    viewport: `${innerWidth}x${innerHeight}`,
    tells: hits,
    sprawl: { radii: radii.size, fontSizes: sizes.size, shadows: shadows.size, textColours: colours.size },
  };
})();
