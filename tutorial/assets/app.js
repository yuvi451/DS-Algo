// Renders the lessons in content.js: a tiny Markdown dialect, a C++/bash
// highlighter, the sidebar, progress tracking and hash routing.
(function () {
  "use strict";

  const LESSONS = window.LESSONS || [];
  const STORE = "microredis-tutorial-done";
  const done = new Set(JSON.parse(localStorage.getItem(STORE) || "[]"));

  const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  // ---------- syntax highlighting ----------

  const CPP_KW = new Set(("alignas auto bool break case catch class const constexpr continue default delete do " +
    "else enum explicit false for if inline namespace noexcept nullptr operator private protected public " +
    "return sizeof static static_cast reinterpret_cast const_cast struct switch template this throw true try " +
    "typename using virtual void while new").split(" "));
  const CPP_TY = new Set(("int char short long unsigned signed float double size_t ssize_t uint8_t uint16_t " +
    "uint32_t uint64_t int32_t int64_t nfds_t socklen_t pollfd sockaddr sockaddr_in std string vector optional " +
    "string_view unique_ptr unordered_map map thread chrono").split(" "));
  const CPP_RE = /(\/\/.*|\/\*[\s\S]*?\*\/)|("(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*')|(^[ \t]*#[ \t]*\w+(?:[ \t]*<[^>\n]*>)?)|(\b(?:0x[\da-fA-F]+|\d+(?:\.\d+)?)(?:ULL|UL|LL|U|L|f)?\b)|([A-Za-z_]\w*)/gm;

  function span(cls, text) { return `<span class="tok-${cls}">${esc(text)}</span>`; }

  function highlightCpp(code) {
    let out = "", last = 0, m;
    CPP_RE.lastIndex = 0;
    while ((m = CPP_RE.exec(code))) {
      out += esc(code.slice(last, m.index));
      last = CPP_RE.lastIndex;
      const [t, com, str, pp, num, id] = m;
      if (com) out += span("com", t);
      else if (str) out += span("str", t);
      else if (pp) out += span("pp", t);
      else if (num) out += span("num", t);
      else if (id) {
        const next = code.slice(last).match(/^\s*(.)/);
        if (CPP_KW.has(id)) out += span("kw", id);
        else if (CPP_TY.has(id) || /^[A-Z][a-z]\w*$/.test(id)) out += span("ty", id);
        else if (/^[A-Z][A-Z0-9_]+$/.test(id) || /^k[A-Z]/.test(id)) out += span("num", id);
        else if (next && next[1] === "(") out += span("fn", id);
        else out += esc(id);
      }
    }
    return out + esc(code.slice(last));
  }

  function highlightShell(code) {
    return code.split("\n").map((line) => {
      const prompt = line.match(/^(\$ )(.*)$/);
      if (!prompt) return esc(line);  // command output: leave plain
      let rest = prompt[2], out = "", m;
      const re = /(\s#.*$|^#.*$)|("(?:\\.|[^"\\])*"|'[^']*')|(\$\{?[\w?!#@]+\}?)/g;
      let last = 0;
      while ((m = re.exec(rest))) {
        out += esc(rest.slice(last, m.index));
        last = re.lastIndex;
        out += m[1] ? span("com", m[0]) : m[2] ? span("str", m[0]) : span("var", m[0]);
      }
      return span("prompt", "$ ") + out + esc(rest.slice(last));
    }).join("\n");
  }

  function highlightPlainShell(code) {  // whole scripts (no "$ " prompts)
    return code.split("\n").map((line) => {
      const c = line.match(/^(\s*)(#.*)$/);
      if (c) return esc(c[1]) + span("com", c[2]);
      return esc(line).replace(/(\$\{?[\w?!#@]+\}?)/g, '<span class="tok-var">$1</span>');
    }).join("\n");
  }

  function highlightMake(code) {
    return code.split("\n").map((line) => {
      if (/^\s*#/.test(line)) return span("com", line);
      let h = esc(line).replace(/(\$[@<^]|\$\([\w]+\))/g, '<span class="tok-var">$1</span>');
      return h.replace(/^([\w./$()%-][^:=\s]*)(:)(?!=)/, '<span class="tok-fn">$1</span>$2');
    }).join("\n");
  }

  function highlight(lang, code) {
    if (lang === "cpp") return highlightCpp(code);
    if (lang === "bash" || lang === "sh") {
      return /^\$ /m.test(code) ? highlightShell(code) : highlightPlainShell(code);
    }
    if (lang === "make") return highlightMake(code);
    return esc(code);
  }

  // ---------- markdown ----------

  function inline(s) {
    const codes = [];
    s = s.replace(/`([^`]+)`/g, (_, c) => { codes.push(c); return `\u0000${codes.length - 1}\u0000`; });
    s = esc(s);
    s = s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    s = s.replace(/(^|[^*\w])\*([^*\s][^*]*?)\*(?![\w*])/g, "$1<em>$2</em>");
    s = s.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (_, text, url) =>
      `<a href="${url}"${url.startsWith("#") ? "" : ' target="_blank" rel="noopener"'}>${text}</a>`);
    return s.replace(/\u0000(\d+)\u0000/g, (_, n) => `<code>${esc(codes[n])}</code>`);
  }

  // [icon, default title]
  const BOXES = {
    goal: ["🎯", "Goal of this lesson"],
    analogy: ["💡", "Analogy"],
    why: ["🤔", "Why?"],
    cpp: ["🧩", "C++ syntax"],
    net: ["🌐", "Networking concept"],
    warn: ["⚠️", "Watch out"],
    recap: ["✅", "Recap"],
    task: ["", ""],
  };
  const REVEALS = { hint: "💡 Hint", solution: "🔓 Show solution (try it yourself first!)", quiz: "❓ " };

  function codeBlock(info, code) {
    const lang = (info.match(/^(\w+)/) || [, "text"])[1];
    const title = (info.match(/title=(.+)$/) || [, ""])[1];
    let cls = "code", label = lang;
    if (lang === "output") { cls += " output"; label = "expected output"; }
    if (lang === "text") { cls += " diagram"; label = ""; }
    const head = `<div class="code-head"><span class="lang">${esc(label)}</span>` +
      (title ? `<span class="file">${esc(title)}</span>` : "") +
      `<button class="copy" type="button">Copy</button></div>`;
    return `<div class="${cls}" data-lang="${lang}">${head}<pre><code>${highlight(lang, code)}</code></pre></div>`;
  }

  const isBlockStart = (l) => /^(```|:::|#{1,4} |\||\s*([-*]|\d+\.) |---+\s*$)/.test(l);

  function render(md) {
    const lines = md.split("\n");
    const out = [];
    let i = 0;
    while (i < lines.length) {
      const line = lines[i];
      let m;
      if ((m = line.match(/^```(.*)$/))) {
        const body = [];
        for (i++; i < lines.length && !/^```\s*$/.test(lines[i]); i++) body.push(lines[i]);
        i++;
        out.push(codeBlock(m[1].trim(), body.join("\n")));
      } else if ((m = line.match(/^:::(\w+)\s*(.*)$/))) {
        // Collect until the matching ":::", skipping nested blocks and code fences.
        const body = [];
        let depth = 0, fence = false;
        for (i++; i < lines.length; i++) {
          const l = lines[i];
          if (/^```/.test(l)) fence = !fence;
          else if (!fence && /^:::\w/.test(l)) depth++;
          else if (!fence && /^:::\s*$/.test(l)) { if (depth === 0) break; depth--; }
          body.push(l);
        }
        i++;
        out.push(box(m[1], m[2], body.join("\n")));
      } else if ((m = line.match(/^(#{1,4}) (.*)$/))) {
        const n = m[1].length + 1;  // the lesson title is the only <h1>
        out.push(`<h${n}>${inline(m[2])}</h${n}>`);
        i++;
      } else if (/^\|/.test(line)) {
        const rows = [];
        for (; i < lines.length && /^\|/.test(lines[i]); i++) rows.push(lines[i]);
        out.push(table(rows));
      } else if (/^\s*([-*]|\d+\.) /.test(line)) {
        // Items sit at this list's indent; deeper lines belong to the current item
        // (nested lists, wrapped text) and are rendered recursively.
        const ordered = /^\s*\d+\./.test(line);
        const indent = (s) => s.match(/^ */)[0].length;
        const base = indent(line);
        const itemRe = /^ *([-*]|\d+\.) /;
        const isItem = (l) => itemRe.test(l) && indent(l) <= base + 1 && ordered === /^ *\d+\./.test(l);
        const isMore = (l) => l.trim() !== "" && indent(l) > base;
        const items = [];
        for (; i < lines.length; i++) {
          const l = lines[i];
          if (isItem(l)) items.push([l.replace(itemRe, "")]);
          else if (isMore(l) && items.length) items[items.length - 1].push(l.slice(Math.min(indent(l), base + 3)));
          else if (l.trim() === "" && items.length && (isItem(lines[i + 1] || "") || isMore(lines[i + 1] || ""))) {
            items[items.length - 1].push("");  // a blank line inside the list
          } else break;
        }
        const start = ordered ? parseInt(line, 10) : 1;  // lists split by a code block keep counting
        const tag = ordered ? "ol" : "ul";
        out.push(`<${tag}${start > 1 ? ` start="${start}"` : ""}>` + items.map((it) => `<li>${renderTight(it.join("\n"))}</li>`).join("") + `</${tag}>`);
      } else if (/^---+\s*$/.test(line)) {
        out.push("<hr>");
        i++;
      } else if (line.trim() === "") {
        i++;
      } else {
        const para = [];
        for (; i < lines.length && lines[i].trim() !== "" && (para.length === 0 || !isBlockStart(lines[i])); i++) {
          para.push(lines[i]);
        }
        out.push(`<p>${inline(para.join(" "))}</p>`);
      }
    }
    return out.join("\n");
  }

  function renderTight(text) {  // list items: no <p> around a single paragraph
    const html = render(text);
    return html.replace(/^<p>([\s\S]*?)<\/p>/, "$1");
  }

  function table(rows) {
    const cells = (r) => r.replace(/^\||\|\s*$/g, "").split(/(?<!\\)\|/).map((c) => inline(c.trim().replace(/\\\|/g, "|")));
    const [head, , ...body] = rows;
    return "<table><thead><tr>" + cells(head).map((c) => `<th>${c}</th>`).join("") + "</tr></thead><tbody>" +
      body.map((r) => "<tr>" + cells(r).map((c) => `<td>${c}</td>`).join("") + "</tr>").join("") + "</tbody></table>";
  }

  function box(type, title, body) {
    if (type in REVEALS) {
      const label = type === "quiz" ? REVEALS.quiz + inline(title) : inline(title) || REVEALS[type];
      return `<details class="reveal ${type}"><summary>${label}</summary><div class="reveal-body">${render(body)}</div></details>`;
    }
    const [icon, fallback] = BOXES[type] || ["", ""];
    const text = title ? inline(title) : esc(fallback);
    const heading = text && icon ? `${icon} ${text}` : text;
    return `<div class="box ${type}">${heading ? `<div class="box-title">${heading}</div>` : ""}${render(body)}</div>`;
  }

  // ---------- navigation ----------

  const modules = [];
  LESSONS.forEach((l, idx) => {
    let mod = modules[modules.length - 1];
    if (!mod || mod.name !== l.module) modules.push((mod = { name: l.module, lessons: [] }));
    l.index = idx;
    l.modNum = modules.length - 1;
    l.num = `${l.modNum}.${mod.lessons.length + 1}`;
    mod.lessons.push(l);
  });

  const $ = (id) => document.getElementById(id);

  function save() {
    localStorage.setItem(STORE, JSON.stringify([...done]));
    updateProgress();
  }

  function updateProgress() {
    const pct = LESSONS.length ? Math.round((done.size / LESSONS.length) * 100) : 0;
    $("progress-fill").style.width = pct + "%";
    $("progress-text").textContent = `${done.size}/${LESSONS.length} done`;
  }

  function buildToc(filter) {
    const q = (filter || "").toLowerCase();
    const current = currentLesson();
    $("toc").innerHTML = modules.map((mod, mi) => {
      const shown = mod.lessons.filter((l) => !q || (l.title + " " + l.body).toLowerCase().includes(q));
      if (!shown.length) return "";
      const finished = mod.lessons.filter((l) => done.has(l.id)).length;
      return `<div class="module"><div class="module-title"><span>${mi}. ${esc(mod.name)}</span>` +
        `<span class="count">${finished}/${mod.lessons.length}</span></div>` +
        shown.map((l) => `<a class="toc-link${done.has(l.id) ? " done" : ""}${l === current ? " active" : ""}" href="#${l.id}">` +
          `<span class="tick">✓</span><span class="num">${l.num}</span><span>${esc(l.title)}</span></a>`).join("") +
        "</div>";
    }).join("") || `<p style="color:var(--muted);padding:8px">No lessons match.</p>`;
  }

  function currentLesson() {
    const id = location.hash.slice(1);
    return LESSONS.find((l) => l.id === id) || LESSONS[0];
  }

  function show() {
    const l = currentLesson();
    if (!l) return;
    document.title = `${l.title} · Build MicroRedis`;
    $("lesson").innerHTML =
      `<div class="lesson-meta"><span class="pill module">Part ${l.modNum} · ${esc(l.module)}</span>` +
      `<span>Lesson ${l.num}</span>${l.time ? `<span class="pill">⏱ ${esc(l.time)}</span>` : ""}</div>` +
      `<h1>${inline(l.title)}</h1>` + render(l.body) +
      `<div class="complete-row"><button class="complete-btn" id="complete"></button></div>`;
    const prev = LESSONS[l.index - 1], next = LESSONS[l.index + 1];
    $("pager").innerHTML =
      (prev ? `<a class="prev" href="#${prev.id}"><small>← Previous</small>${esc(prev.title)}</a>` : `<span class="spacer"></span>`) +
      (next ? `<a class="next" href="#${next.id}"><small>Next →</small>${esc(next.title)}</a>` : `<span class="spacer"></span>`);
    syncComplete(l);
    buildToc($("search").value);
    document.body.classList.remove("nav-open");
    window.scrollTo(0, 0);
    const active = document.querySelector(".toc-link.active");
    if (active) active.scrollIntoView({ block: "nearest" });
  }

  function syncComplete(l) {
    const btn = $("complete");
    const isDone = done.has(l.id);
    btn.className = "complete-btn" + (isDone ? " done" : "");
    btn.textContent = isDone ? "✓ Completed (click to undo)" : "Mark lesson as complete";
    btn.onclick = () => {
      if (done.has(l.id)) done.delete(l.id);
      else done.add(l.id);
      save();
      syncComplete(l);
      buildToc($("search").value);
      const next = LESSONS[l.index + 1];
      if (done.has(l.id) && next) location.hash = next.id;
    };
  }

  // Copy buttons: for shell snippets, copy only the commands (drop "$ " and output lines).
  document.addEventListener("click", (e) => {
    const btn = e.target.closest(".copy");
    if (!btn) return;
    const block = btn.closest(".code");
    let text = block.querySelector("pre").innerText;
    if (block.dataset.lang === "bash" && /^\$ /m.test(text)) {
      text = text.split("\n").filter((l) => l.startsWith("$ ")).map((l) => l.slice(2)).join("\n");
    }
    navigator.clipboard.writeText(text).then(() => {
      btn.textContent = "Copied!";
      setTimeout(() => (btn.textContent = "Copy"), 1200);
    });
  });

  document.addEventListener("keydown", (e) => {
    if (/INPUT|TEXTAREA/.test(document.activeElement.tagName) || e.metaKey || e.ctrlKey || e.altKey) return;
    const l = currentLesson();
    if (e.key === "ArrowRight" && LESSONS[l.index + 1]) location.hash = LESSONS[l.index + 1].id;
    if (e.key === "ArrowLeft" && LESSONS[l.index - 1]) location.hash = LESSONS[l.index - 1].id;
  });

  $("menu").onclick = () => document.body.classList.toggle("nav-open");
  $("search").oninput = (e) => buildToc(e.target.value);
  $("reset").onclick = () => {
    if (confirm("Clear all lesson progress?")) { done.clear(); save(); show(); }
  };
  window.addEventListener("hashchange", show);

  updateProgress();
  show();
})();
