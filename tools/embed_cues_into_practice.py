"""Embed cues.json into content/mock17/practice.html so 字幕 show without fetch."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOCK_DIR = ROOT / "content" / "mock17"
CUES_PATH = MOCK_DIR / "cues.json"
HTML_PATH = MOCK_DIR / "practice.html"

def main():
    cues = json.loads(CUES_PATH.read_text(encoding="utf-8"))
    # Minify and escape for use inside script tag (avoid </script> in text)
    raw = json.dumps(cues, ensure_ascii=False)
    raw = raw.replace("</", "<\\/")
    html = HTML_PATH.read_text(encoding="utf-8")
    # Replace fetch block with: embed first, then renderCues
    old_fetch = r"""  fetch\(\(BASE \|\| "\."\) \+ "cues\.json"\)
    \.then\(function\(r\) \{ return r\.json\(\); \}\)
    \.then\(function\(data\) \{
      cues = Array\.isArray\(data\) \? data : \[\];
      cuesContainer\.innerHTML = "";
      cues\.forEach\(function\(cue, index\) \{
        var row = document\.createElement\("div"\);
        row\.className = "cue-row";
        row\.setAttribute\("data-index", String\(index\)\);
        var timeSpan = document\.createElement\("span"\);
        timeSpan\.className = "time";
        timeSpan\.textContent = formatTime\(cue\.start\) \+ "\u2013" \+ formatTime\(cue\.end\);
        var lines = document\.createElement\("div"\);
        lines\.className = "lines";
        var textEl = document\.createElement\("div"\);
        textEl\.className = "text";
        textEl\.textContent = cue\.text \|\| "";
        lines\.appendChild\(textEl\);
        row\.appendChild\(timeSpan\);
        row\.appendChild\(lines\);
        cuesContainer\.appendChild\(row\);
      \}\);
    \}\)
    \.catch\(function\(err\) \{
      console\.error\(err\);
      cuesContainer\.innerHTML = "<p style='color: var\(--muted\);'>加载字幕失败，请确保 cues\.json 存在。</p>";
    \}\);"""
    render_def = """
  function renderCues() {
    cuesContainer.innerHTML = "";
    cues.forEach(function(cue, index) {
      var row = document.createElement("div");
      row.className = "cue-row";
      row.setAttribute("data-index", String(index));
      var timeSpan = document.createElement("span");
      timeSpan.className = "time";
      timeSpan.textContent = formatTime(cue.start) + "\u2013" + formatTime(cue.end);
      var lines = document.createElement("div");
      lines.className = "lines";
      var textEl = document.createElement("div");
      textEl.className = "text";
      textEl.textContent = cue.text || "";
      lines.appendChild(textEl);
      row.appendChild(timeSpan);
      row.appendChild(lines);
      cuesContainer.appendChild(row);
    });
  }
  var embedEl = document.getElementById("cues-embed");
  if (embedEl) try { cues = JSON.parse(embedEl.textContent); } catch(e) {}
  if (Array.isArray(cues) && cues.length > 0) {
    renderCues();
  } else {
    cuesContainer.innerHTML = "<p style='color: var(--muted);'>无字幕数据。</p>";
  }"""
    html = re.sub(old_fetch, render_def, html, count=1)
    # Insert embedded JSON script before the main <script>
    embed_tag = '\n<script type="application/json" id="cues-embed">\n' + raw + '\n</script>\n'
    html = html.replace('  <div id="cues" class="cues"></div>\n</div>\n\n<script>', '  <div id="cues" class="cues"></div>\n</div>\n' + embed_tag + '\n<script>')
    HTML_PATH.write_text(html, encoding="utf-8")
    print("Embedded", len(cues), "cues into", HTML_PATH)

if __name__ == "__main__":
    main()
