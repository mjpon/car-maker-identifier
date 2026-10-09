/* Vehicle parts origin: the static version of the car maker identifier.
   Reads data/vehicles.json (built from the NHTSA AALA reports by scripts/build_static.py) and draws
   every chart in the browser. No framework, no server, no external requests. */
(function () {
  'use strict';

  var RED = '#E2001A', BLUE = '#0C4DA2', INK = '#2D2D2D', MUTED = '#686868', LINE = '#D5D5D5';
  var GRAY_MID = '#9A9A9A', GRAY_LIGHT = '#DCDCDC';
  var BANDS = [0, 10, 25, 50, 75, 100];
  var BAND_LABELS = ['0–10%', '10–25%', '25–50%', '50–75%', '75–100%'];
  var C = { year: 0, maker: 1, line: 2, us: 3, pc: 4, pp: 5, sc: 6, sp: 7, eng: 8, trans: 9, asm: 10 };
  var EXPECTED = ['Year', 'Manufacturer', 'Car Line', '% US/Canada', 'Primary Country', 'Primary %',
    'Secondary Country', 'Secondary %', 'Engine Source', 'Transmission Source', 'Assembly Country'];
  var TABLE_COLS = [
    { i: C.year, label: 'Year' },
    { i: C.maker, label: 'Manufacturer' },
    { i: C.line, label: 'Car line' },
    { i: C.us, label: 'US/Canada', kind: 'pct' },
    { i: C.pc, label: 'Main source' },
    { i: C.pp, label: 'Share', kind: 'share', country: C.pc },
    { i: C.sc, label: 'Second source' },
    { i: C.sp, label: 'Share', kind: 'share', country: C.sc },
    { i: C.eng, label: 'Engine' },
    { i: C.trans, label: 'Transmission' },
    { i: C.asm, label: 'Assembled in' }
  ];
  var PAGE = 100;
  var TABS = ['overview', 'assembly', 'components', 'content', 'data'];

  var DATA = [];
  var COLUMNS = [];
  var YEARS = [];
  var view = { rows: [], trendRows: [] };
  var state = { years: [], makers: [], line: '', tab: 'overview', breakdown: '', sortCol: -1, sortDir: 1, shown: PAGE };

  function $(id) { return document.getElementById(id); }

  function h(tag, attrs, kids) {
    var node = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        if (k === 'text') node.textContent = attrs[k];
        else if (k === 'class') node.className = attrs[k];
        else if (attrs[k] !== null && attrs[k] !== undefined) node.setAttribute(k, attrs[k]);
      });
    }
    (kids || []).forEach(function (kid) {
      if (kid === null || kid === undefined) return;
      node.appendChild(typeof kid === 'string' ? document.createTextNode(kid) : kid);
    });
    return node;
  }

  function svg(tag, attrs, kids) {
    var node = document.createElementNS('http://www.w3.org/2000/svg', tag);
    Object.keys(attrs || {}).forEach(function (k) { node.setAttribute(k, attrs[k]); });
    (kids || []).forEach(function (kid) { node.appendChild(kid); });
    return node;
  }

  function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }

  function fmt(n, decimals) {
    return Number(n).toLocaleString('en-US', { minimumFractionDigits: decimals || 0, maximumFractionDigits: decimals || 0 });
  }

  function mean(rows, i) {
    var sum = 0;
    rows.forEach(function (r) { sum += r[i]; });
    return rows.length ? sum / rows.length : 0;
  }

  function distinct(rows, i) {
    var seen = {};
    var out = [];
    rows.forEach(function (r) { if (!seen[r[i]]) { seen[r[i]] = 1; out.push(r[i]); } });
    return out;
  }

  /* [label, count] pairs, most frequent first; blanks are ignored. Ties keep their first-seen order. */
  function countBy(rows, i) {
    var counts = {};
    var order = [];
    rows.forEach(function (r) {
      var v = r[i];
      if (v === '' || v === null) return;
      if (counts[v] === undefined) { counts[v] = 0; order.push(v); }
      counts[v] += 1;
    });
    return order.map(function (k) { return [k, counts[k]]; }).sort(function (a, b) { return b[1] - a[1]; });
  }

  /* [label, mean] pairs, highest first. Ties are sorted by name. */
  function meanBy(rows, gi, vi) {
    var sums = {};
    var ns = {};
    rows.forEach(function (r) {
      var g = r[gi];
      sums[g] = (sums[g] || 0) + r[vi];
      ns[g] = (ns[g] || 0) + 1;
    });
    return Object.keys(sums).map(function (k) { return [k, sums[k] / ns[k]]; }).sort(function (a, b) {
      return b[1] - a[1] || (a[0] < b[0] ? -1 : 1);
    });
  }

  function mode(rows, i) {
    var pairs = countBy(rows, i);
    if (!pairs.length) return '';
    var top = pairs[0][1];
    var tied = pairs.filter(function (p) { return p[1] === top; }).map(function (p) { return p[0]; }).sort();
    return tied[0];
  }

  /* ---------------------------------------------------------------- filtering */

  function inYears() {
    if (!state.years.length) return DATA;
    var set = {};
    state.years.forEach(function (y) { set[y] = true; });
    return DATA.filter(function (r) { return set[r[C.year]]; });
  }

  function byMakerAndLine(rows) {
    var out = rows;
    if (state.makers.length) {
      var set = {};
      state.makers.forEach(function (m) { set[m] = true; });
      out = out.filter(function (r) { return set[r[C.maker]]; });
    }
    var q = state.line.trim().toLowerCase();
    if (q) out = out.filter(function (r) { return r[C.line].toLowerCase().indexOf(q) !== -1; });
    return out;
  }

  /* ---------------------------------------------------------------- chart pieces */

  function heading(text, note, level) {
    var nodes = [h(level === 3 ? 'h3' : 'h2', { class: level === 3 ? 'h3' : 'h2', text: text })];
    if (note) nodes.push(h('p', { class: 'note', text: note }));
    return nodes;
  }

  function add(parent, nodes) { nodes.forEach(function (n) { parent.appendChild(n); }); }

  function notice(text) { return h('p', { class: 'notice', text: text }); }

  /* Horizontal bars, largest first. The leader is red, the rest are gray. Values sit at the bar ends. */
  function ranking(pairs, unit, opts) {
    opts = opts || {};
    var suffix = opts.suffix || '';
    var decimals = opts.decimals || 0;
    var top = 0;
    pairs.forEach(function (p) { if (p[1] > top) top = p[1]; });
    var list = h('ol', { class: 'rank' });
    pairs.forEach(function (p, n) {
      var text = fmt(p[1], decimals) + suffix;
      var share = top > 0 ? p[1] / top : 0;
      var bar = h('span', { class: 'bar' });
      bar.style.width = 'calc((100% - 4rem) * ' + share.toFixed(4) + ')';
      var li = h('li', { class: n === 0 ? 'lead' : null, title: p[0] + ': ' + text + ' ' + unit }, [
        h('span', { class: 'label', text: p[0] }),
        h('span', { class: 'track' }, [bar, h('span', { class: 'val', text: text })])
      ]);
      list.appendChild(li);
    });
    return list;
  }

  /* Vertical bars for an ordered scale. One colour, red on the peak. */
  function columns(labels, values, unit) {
    var peak = 0;
    values.forEach(function (v, i) { if (v > values[peak]) peak = i; });
    var max = Math.max.apply(null, values.concat([1]));
    var wrap = h('div', { role: 'img', 'aria-label': labels.map(function (l, i) { return l + ': ' + fmt(values[i]) + ' ' + unit; }).join('; ') });
    var cols = h('div', { class: 'cols' });
    values.forEach(function (v, i) {
      var bar = h('div', { class: 'b' });
      bar.style.height = 'calc((100% - 28px) * ' + (v / max).toFixed(4) + ')';
      cols.appendChild(h('div', { class: 'col' + (i === peak ? ' peak' : ''), title: labels[i] + ': ' + fmt(v) + ' ' + unit }, [
        h('div', { class: 'v', text: fmt(v) }), bar
      ]));
    });
    var names = h('div', { class: 'col-labels', 'aria-hidden': 'true' });
    labels.forEach(function (l) { names.appendChild(h('span', { text: l })); });
    add(wrap, [cols, names]);
    return wrap;
  }

  function niceStep(max, count) {
    var raw = max / count;
    var pow = Math.pow(10, Math.floor(Math.log10(raw)));
    var f = raw / pow;
    var m = f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10;
    return m * pow;
  }

  /* One red line, one marker per model year. Drawn at the container's real width so type stays readable. */
  function trend(container, years, counts, unit) {
    var width = Math.max(container.clientWidth || 0, 280);
    var height = 300;
    var maxCount = Math.max.apply(null, counts.concat([1]));
    var step = niceStep(maxCount, 4);
    var yMax = Math.ceil(maxCount / step) * step;
    var labelW = String(fmt(yMax)).length * 8 + 14;
    var m = { l: labelW, r: 20, t: 16, b: 34 };
    var iw = width - m.l - m.r;
    var ih = height - m.t - m.b;
    function px(i) { return years.length > 1 ? m.l + (i / (years.length - 1)) * iw : m.l + iw / 2; }
    function py(v) { return m.t + (1 - v / yMax) * ih; }

    var root = svg('svg', {
      width: width, height: height, viewBox: '0 0 ' + width + ' ' + height, role: 'img',
      'aria-label': 'Models per model year: ' + years.map(function (y, i) { return y + ', ' + fmt(counts[i]); }).join('; ')
    });
    for (var t = 0; t <= yMax + 0.0001; t += step) {
      root.appendChild(svg('line', { x1: m.l, x2: width - m.r, y1: py(t), y2: py(t), stroke: LINE, 'stroke-width': 1 }));
      var tick = svg('text', { x: m.l - 8, y: py(t) + 4, 'text-anchor': 'end', 'font-size': 13, fill: MUTED });
      tick.textContent = fmt(t);
      root.appendChild(tick);
    }
    root.appendChild(svg('line', { x1: m.l, x2: width - m.r, y1: m.t + ih, y2: m.t + ih, stroke: INK, 'stroke-width': 1.5 }));
    var points = years.map(function (y, i) { return px(i) + ',' + py(counts[i]); }).join(' ');
    root.appendChild(svg('polyline', { points: points, fill: 'none', stroke: RED, 'stroke-width': 3, 'stroke-linejoin': 'round' }));
    years.forEach(function (y, i) {
      var label = svg('text', { x: px(i), y: height - 10, 'text-anchor': 'middle', 'font-size': 14, fill: INK });
      label.textContent = y;
      root.appendChild(label);
      var tip = svg('title', {});
      tip.textContent = y + ': ' + fmt(counts[i]) + ' ' + unit;
      root.appendChild(svg('circle', { cx: px(i), cy: py(counts[i]), r: 5, fill: RED, stroke: '#fff', 'stroke-width': 2 }, [tip]));
      var hit = svg('circle', { cx: px(i), cy: py(counts[i]), r: 14, fill: 'transparent' });
      var tip2 = svg('title', {});
      tip2.textContent = y + ': ' + fmt(counts[i]) + ' ' + unit;
      hit.appendChild(tip2);
      root.appendChild(hit);
    });
    clear(container);
    container.appendChild(root);
  }

  function legend(items) {
    var box = h('div', { class: 'legend' });
    items.forEach(function (it) {
      var swatch = h('i');
      swatch.style.background = it[1];
      box.appendChild(h('span', {}, [swatch, it[0]]));
    });
    return box;
  }

  /* One 100% bar: where the average vehicle's parts content comes from. */
  function composition(segments) {
    var bar = h('div', { class: 'comp', role: 'img',
      'aria-label': segments.map(function (s) { return s.name + ': ' + s.value.toFixed(1) + '%'; }).join('; ') });
    segments.forEach(function (s) {
      var seg = h('div', { class: 'seg', title: s.name + ': ' + s.value.toFixed(1) + '% of parts content', text: s.value >= 4 ? Math.round(s.value) + '%' : '' });
      seg.style.width = s.value + '%';
      seg.style.background = s.fill;
      seg.style.color = s.text;
      bar.appendChild(seg);
    });
    var axis = h('div', { class: 'comp-axis', 'aria-hidden': 'true' });
    [0, 25, 50, 75, 100].forEach(function (p) {
      var tick = h('span', { text: p + '%' });
      tick.style.left = p + '%';
      axis.appendChild(tick);
    });
    return h('div', {}, [bar, axis]);
  }

  /* ---------------------------------------------------------------- tabs */

  function renderOverview(panel) {
    var rows = view.rows;
    add(panel, heading('Overview', 'Models in the current selection, by manufacturer and over time.'));
    add(panel, heading('Models by manufacturer', 'The 15 manufacturers with the most models in this selection.', 3));
    panel.appendChild(ranking(countBy(rows, C.maker).slice(0, 15), 'models'));

    add(panel, heading('Models reported per model year',
      'Covers all model years, whatever year is selected above. Reflects the manufacturer and car line filters.', 3));
    var holder = h('div', { class: 'trend' });
    panel.appendChild(holder);
    var perYear = {};
    view.trendRows.forEach(function (r) { perYear[r[C.year]] = (perYear[r[C.year]] || 0) + 1; });
    var years = Object.keys(perYear).map(Number).sort(function (a, b) { return a - b; });
    trend(holder, years, years.map(function (y) { return perYear[y]; }), 'models');
  }

  function renderAssembly(panel) {
    var rows = view.rows;
    add(panel, heading('Assembly', 'Where the final vehicle is put together.'));
    var known = rows.filter(function (r) { return r[C.asm] !== ''; }).length;
    if (known < rows.length) {
      panel.appendChild(notice('Assembly country is reported for ' + fmt(known) + ' of ' + fmt(rows.length) +
        ' vehicles in this selection. The rest are left out of this chart.'));
    }
    add(panel, heading('Vehicles by assembly country', 'Top 20 countries.', 3));
    panel.appendChild(ranking(countBy(rows, C.asm).slice(0, 20), 'vehicles'));
  }

  function renderComponents(panel) {
    var rows = view.rows;
    add(panel, heading('Engines and transmissions', 'The country each major component comes from.'));
    var pair = h('div', { class: 'pair' });
    var left = h('div');
    add(left, heading('Engine source', 'Top 10 countries.', 3));
    left.appendChild(ranking(countBy(rows, C.eng).slice(0, 10), 'vehicles'));
    var right = h('div');
    add(right, heading('Transmission source', 'Top 10 countries.', 3));
    right.appendChild(ranking(countBy(rows, C.trans).slice(0, 10), 'vehicles'));
    add(pair, [left, right]);
    panel.appendChild(pair);
  }

  function bandCounts(rows) {
    var counts = [0, 0, 0, 0, 0];
    rows.forEach(function (r) {
      var v = r[C.us];
      for (var b = 0; b < 5; b++) {
        var lo = BANDS[b], hi = BANDS[b + 1];
        if ((b === 0 ? v >= lo : v > lo) && v <= hi) { counts[b] += 1; break; }
      }
    });
    return counts;
  }

  function renderContent(panel) {
    var rows = view.rows;
    add(panel, heading('Parts content',
      'The label lists the share of parts from the US and Canada, plus up to two other countries that supply the most.'));

    var top = h('div', { class: 'pair' });
    var a = h('div');
    add(a, heading('US and Canada content', 'How many vehicles fall in each band.', 3));
    a.appendChild(columns(BAND_LABELS, bandCounts(rows), 'vehicles'));
    var b = h('div');
    add(b, heading('Highest US and Canada content', 'Average by manufacturer, top 15.', 3));
    b.appendChild(ranking(meanBy(rows, C.maker, C.us).slice(0, 15), 'average', { suffix: '%' }));
    add(top, [a, b]);
    panel.appendChild(top);

    var primary = rows.filter(function (r) { return r[C.pc] !== ''; });
    var mid = h('div', { class: 'pair' });
    var c = h('div');
    add(c, heading('Largest foreign source', 'Vehicles by the country supplying the most non-US parts, top 15.', 3));
    c.appendChild(ranking(countBy(primary, C.pc).slice(0, 15), 'vehicles'));
    var d = h('div');
    add(d, heading('Share from that country', 'Average percent of parts content, top 15.', 3));
    d.appendChild(ranking(meanBy(primary, C.pc, C.pp).slice(0, 15), 'average', { suffix: '%' }));
    add(mid, [c, d]);
    panel.appendChild(mid);

    add(panel, heading('Content breakdown for one manufacturer', null, 3));
    var makers = distinct(rows, C.maker).sort();
    var largest = countBy(rows, C.maker)[0][0];
    if (makers.indexOf(state.breakdown) === -1) state.breakdown = largest;

    var select = h('select', { id: 'breakdown', class: 'control' });
    makers.forEach(function (m) {
      var opt = h('option', { value: m, text: m });
      if (m === state.breakdown) opt.selected = true;
      select.appendChild(opt);
    });
    panel.appendChild(h('div', { class: 'picker' }, [h('label', { for: 'breakdown', text: 'Manufacturer' }), select]));
    var out = h('div', { id: 'breakdown-out' });
    panel.appendChild(out);

    function draw() {
      var own = rows.filter(function (r) { return r[C.maker] === state.breakdown; });
      var us = mean(own, C.us), main = mean(own, C.pp), second = mean(own, C.sp);
      var other = Math.max(0, 100 - us - main - second);
      var country = mode(own.filter(function (r) { return r[C.pc] !== ''; }), C.pc) || 'not itemized';
      var segments = [
        { name: 'US and Canada', value: us, fill: RED, text: '#FFFFFF' },
        { name: 'Largest foreign source (' + country + ')', value: main, fill: BLUE, text: '#FFFFFF' },
        { name: 'Second foreign source', value: second, fill: GRAY_MID, text: INK },
        { name: 'Other or not itemized', value: other, fill: GRAY_LIGHT, text: INK }
      ];
      clear(out);
      out.appendChild(legend(segments.map(function (s) { return [s.name, s.fill]; })));
      out.appendChild(composition(segments));
    }
    select.addEventListener('change', function () { state.breakdown = select.value; draw(); });
    draw();
  }

  function cellText(r, col) {
    var v = r[col.i];
    if (col.kind === 'share') return r[col.country] === '' ? '' : v + '%';
    if (col.kind === 'pct') return v + '%';
    return v === null ? '' : String(v);
  }

  function sortedRows() {
    var rows = view.rows.slice();
    if (state.sortCol < 0) return rows;
    var col = TABLE_COLS[state.sortCol];
    var dir = state.sortDir;
    return rows.sort(function (x, y) {
      var a = x[col.i], b = y[col.i];
      if (col.kind === 'share') { a = x[col.country] === '' ? -1 : a; b = y[col.country] === '' ? -1 : b; }
      if (typeof a === 'number' && typeof b === 'number') return (a - b) * dir;
      return String(a).localeCompare(String(b), 'en', { numeric: true, sensitivity: 'base' }) * dir;
    });
  }

  function csvCell(v) {
    var s = v === null || v === undefined ? '' : String(v);
    return /[",\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  }

  function downloadCsv() {
    var lines = [COLUMNS.map(csvCell).join(',')];
    view.rows.forEach(function (r) { lines.push(r.map(csvCell).join(',')); });
    var blob = new Blob([lines.join('\n') + '\n'], { type: 'text/csv;charset=utf-8' });
    var url = URL.createObjectURL(blob);
    var link = h('a', { href: url, download: 'nhtsa_filtered_data.csv' });
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  }

  function renderData(panel) {
    add(panel, heading('Data', fmt(view.rows.length) + ' vehicles match the filters above.'));
    var wrap = h('div', { class: 'table-wrap', tabindex: '0', role: 'region', 'aria-label': 'Vehicle data table, scrollable' });
    var table = h('table', { class: 'data' });
    var head = h('tr');
    TABLE_COLS.forEach(function (col, n) {
      var th = h('th', { scope: 'col', 'aria-sort': state.sortCol === n ? (state.sortDir === 1 ? 'ascending' : 'descending') : 'none' });
      var btn = h('button', { type: 'button', text: col.label });
      btn.addEventListener('click', function () {
        if (state.sortCol === n) state.sortDir = -state.sortDir; else { state.sortCol = n; state.sortDir = 1; }
        state.shown = PAGE;
        renderTab('data');
      });
      th.appendChild(btn);
      head.appendChild(th);
    });
    table.appendChild(h('thead', {}, [head]));
    var body = h('tbody');
    var rows = sortedRows();
    rows.slice(0, state.shown).forEach(function (r) {
      var tr = h('tr');
      TABLE_COLS.forEach(function (col) {
        var td = h('td');
        var text = cellText(r, col);
        if (col.kind === 'pct') {
          var pill = h('span', { class: 'pbar', text: text });
          pill.style.setProperty('--p', r[col.i] + '%');
          td.appendChild(pill);
          td.className = 'num-cell';
        } else {
          td.textContent = text;
          if (col.kind === 'share' || col.i === C.year) td.className = 'num-cell';
        }
        tr.appendChild(td);
      });
      body.appendChild(tr);
    });
    table.appendChild(body);
    wrap.appendChild(table);
    panel.appendChild(wrap);

    var actions = h('div', { class: 'actions' });
    if (rows.length > state.shown) {
      var more = h('button', { type: 'button', class: 'btn ghost', text: 'Show ' + Math.min(PAGE, rows.length - state.shown) + ' more' });
      more.addEventListener('click', function () { state.shown += PAGE; renderTab('data'); });
      actions.appendChild(more);
    }
    var dl = h('button', { type: 'button', class: 'btn', text: 'Download filtered data (CSV)' });
    dl.addEventListener('click', downloadCsv);
    actions.appendChild(dl);
    actions.appendChild(h('span', { class: 'note', style: 'margin:0', text: 'Showing ' + fmt(Math.min(state.shown, rows.length)) + ' of ' + fmt(rows.length) + '.' }));
    panel.appendChild(actions);
  }

  var RENDER = { overview: renderOverview, assembly: renderAssembly, components: renderComponents, content: renderContent, data: renderData };

  function renderTab(name) {
    var panel = $('panel-' + name);
    var scroller = panel.querySelector('.table-wrap');
    var top = scroller ? scroller.scrollTop : 0;
    clear(panel);
    RENDER[name](panel);
    var again = panel.querySelector('.table-wrap');
    if (again && top) again.scrollTop = top;
  }

  function showTab(name, focus) {
    state.tab = name;
    TABS.forEach(function (t) {
      var on = t === name;
      var tab = $('tab-' + t);
      tab.setAttribute('aria-selected', on ? 'true' : 'false');
      tab.tabIndex = on ? 0 : -1;
      $('panel-' + t).hidden = !on;
    });
    if (focus) $('tab-' + name).focus();
    if (view.rows.length) renderTab(name);
  }

  /* ---------------------------------------------------------------- board and filters */

  function renderBoard(rows) {
    var cells = [
      [fmt(rows.length), 'Vehicle models in this selection', true],
      [String(distinct(rows, C.maker).length), 'Manufacturers', false],
      [String(distinct(rows, C.year).length), 'Model years', false],
      [mean(rows, C.us).toFixed(0) + '%', 'Average US and Canada parts content', false]
    ];
    var board = $('board');
    clear(board);
    cells.forEach(function (c) {
      board.appendChild(h('div', { class: 'cell' }, [
        h('div', { class: 'num' + (c[2] ? ' signal' : ''), text: c[0] }),
        h('div', { class: 'cell-label', text: c[1] })
      ]));
    });
  }

  function renderYearChips() {
    var box = $('year-chips');
    clear(box);
    var all = h('button', { type: 'button', class: 'chip', 'aria-pressed': state.years.length ? 'false' : 'true', text: 'All years' });
    all.addEventListener('click', function () { state.years = []; yearsChanged(); });
    box.appendChild(all);
    YEARS.forEach(function (y) {
      var on = state.years.indexOf(y) !== -1;
      var chip = h('button', { type: 'button', class: 'chip', 'aria-pressed': on ? 'true' : 'false', text: String(y) });
      chip.addEventListener('click', function () {
        var at = state.years.indexOf(y);
        if (at === -1) state.years.push(y); else state.years.splice(at, 1);
        state.years.sort(function (p, q) { return p - q; });
        yearsChanged();
      });
      box.appendChild(chip);
    });
  }

  function makerSummary() {
    var n = state.makers.length;
    $('make-summary').textContent = n === 0 ? 'All manufacturers' : n <= 2 ? state.makers.join(', ') : n + ' manufacturers';
  }

  function renderMakerList() {
    var list = $('make-list');
    clear(list);
    var q = $('make-search').value.trim().toLowerCase();
    var pairs = countBy(inYears(), C.maker).sort(function (a, b) { return a[0] < b[0] ? -1 : 1; });
    var shown = 0;
    pairs.forEach(function (p) {
      if (q && p[0].toLowerCase().indexOf(q) === -1) return;
      shown += 1;
      var box = h('input', { type: 'checkbox', value: p[0] });
      box.checked = state.makers.indexOf(p[0]) !== -1;
      box.addEventListener('change', function () {
        var at = state.makers.indexOf(p[0]);
        if (box.checked && at === -1) state.makers.push(p[0]);
        if (!box.checked && at !== -1) state.makers.splice(at, 1);
        state.makers.sort();
        makerSummary();
        update(false);
      });
      list.appendChild(h('li', {}, [h('label', {}, [box, h('span', { text: p[0] }), h('span', { class: 'n', text: fmt(p[1]) })])]));
    });
    if (!shown) list.appendChild(h('li', { class: 'menu-empty', text: 'No manufacturers match.' }));
  }

  function setMenu(open) {
    $('make-panel').hidden = !open;
    $('make-button').setAttribute('aria-expanded', open ? 'true' : 'false');
    if (open) { renderMakerList(); $('make-search').focus(); }
  }

  function yearsChanged() {
    var options = {};
    countBy(inYears(), C.maker).forEach(function (p) { options[p[0]] = true; });
    state.makers = state.makers.filter(function (m) { return options[m]; });
    renderYearChips();
    makerSummary();
    if (!$('make-panel').hidden) renderMakerList();
    update(false);
  }

  /* Recompute the filtered rows, then redraw the board and the open tab. */
  function update() {
    var base = inYears();
    var rows = byMakerAndLine(base);
    view.rows = rows;
    view.trendRows = byMakerAndLine(DATA);
    var empty = rows.length === 0;
    $('empty').hidden = !empty;
    $('results').hidden = empty;
    if (empty) return;
    state.shown = PAGE;
    renderBoard(rows);
    renderTab(state.tab);
  }

  function setUpEvents() {
    $('make-button').addEventListener('click', function () { setMenu($('make-panel').hidden); });
    $('make-search').addEventListener('input', renderMakerList);
    $('make-clear').addEventListener('click', function () {
      state.makers = [];
      makerSummary();
      renderMakerList();
      update();
    });
    document.addEventListener('click', function (e) {
      if (!$('make-panel').hidden && !$('make-menu').contains(e.target)) setMenu(false);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !$('make-panel').hidden) { setMenu(false); $('make-button').focus(); }
    });
    $('car-line').addEventListener('input', function () { state.line = $('car-line').value; update(); });

    TABS.forEach(function (t, n) {
      var tab = $('tab-' + t);
      tab.addEventListener('click', function () {
        showTab(t, false);
        if (history.replaceState) history.replaceState(null, '', '#' + t);
      });
      tab.addEventListener('keydown', function (e) {
        var to = null;
        if (e.key === 'ArrowRight') to = (n + 1) % TABS.length;
        else if (e.key === 'ArrowLeft') to = (n + TABS.length - 1) % TABS.length;
        else if (e.key === 'Home') to = 0;
        else if (e.key === 'End') to = TABS.length - 1;
        if (to === null) return;
        e.preventDefault();
        showTab(TABS[to], true);
        if (history.replaceState) history.replaceState(null, '', '#' + TABS[to]);
      });
    });

    var timer = null;
    window.addEventListener('resize', function () {
      clearTimeout(timer);
      timer = setTimeout(function () { if (state.tab === 'overview' && !$('results').hidden) renderTab('overview'); }, 150);
    });
  }

  function start(payload) {
    COLUMNS = payload.columns;
    DATA = payload.rows;
    if (EXPECTED.join('|') !== COLUMNS.join('|')) throw new Error('Unexpected columns in vehicles.json');
    YEARS = distinct(DATA, C.year).sort(function (a, b) { return a - b; });
    state.years = [YEARS[YEARS.length - 1]];
    var hash = (location.hash || '').replace('#', '');
    if (TABS.indexOf(hash) !== -1) state.tab = hash;
    $('source').textContent = 'Source: NHTSA AALA reports, model years ' + YEARS[0] + '–' + YEARS[YEARS.length - 1];
    renderYearChips();
    makerSummary();
    setUpEvents();
    showTab(state.tab, false);
    update();
  }

  fetch('data/vehicles.json')
    .then(function (res) { if (!res.ok) throw new Error('HTTP ' + res.status); return res.json(); })
    .then(start)
    .catch(function () {
      $('results').hidden = true;
      var box = $('empty');
      box.textContent = 'The data could not be loaded. Try reloading the page.';
      box.hidden = false;
    });
})();
