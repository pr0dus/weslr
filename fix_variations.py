#!/usr/bin/env python3
"""Clean up sim.py and properly add variations section"""

# Restore from git first
import subprocess
subprocess.run(['git', 'checkout', 'sim.py'], check=True, cwd='/data/data/com.termux/files/home/.openclaw/workspace/CircleForge')

# Now add properly
with open('/data/data/com.termux/files/home/.openclaw/workspace/CircleForge/sim.py', 'r') as f:
    content = f.read()

# Find where to add the variations section in the HTML f-string
# The HTML f-string contains a template with sections for themes, artifacts, etc.
# We need to add the variations section in the correct place within this template

# First, add the payload tracker data
old_payload = '"release_ledger": release_ledger,'
new_payload = '"release_ledger": release_ledger,\n        "revisit_tracker": load_revisit_tracker_for_dashboard(),'

if old_payload in content:
    content = content.replace(old_payload, new_payload)
    print('Added revisit_tracker to payload')
else:
    print('Could not find payload insertion point')

# Add the variations HTML section - find the themes section and add before packs
# Look for: </table>\n    </section>\n\n    <div class="grid" style="margin-top:16px;" id="packs">

old_html = '      </table>\n    </section>\n\n    <div class="grid" style="margin-top:16px;" id="packs">'
new_html = '''      </table>
    </section>

    <section class="card" style="margin-top:16px;" id="variations">
      <h2>Variation Generation</h2>
      <div id="variations-container"><p class="muted">Loading variation data...</p></div>
      <script>
      (function() {
        const el = document.getElementById('variations-container');
        try {
          const tracker = payload_json ? JSON.parse(payload_json).revisit_tracker : null;
          if (!tracker || !tracker.revisits_by_theme || Object.keys(tracker.revisits_by_theme).length === 0) {
            el.innerHTML = '<p class="muted">No variations generated yet.</p>';
            return;
          }
          let html = '<div class="grid">';
          for (const [theme, data] of Object.entries(tracker.revisits_by_theme)) {
            const rejections = tracker.rejections_by_theme?.[theme]?.count || 0;
            const revisits = data.times_revisited || 0;
            const variations = data.generated_variations || [];
            const math_scores = data.math_scores || {};
            
            html += "<section class='card'><h3>" + esc(theme) + "</h3>";
            html += "<p class='muted'>Rejections: " + rejections + " · Revisits: " + revisits + "</p>";
            
            if (variations.length > 0) {
              html += "<p><strong>Generated Variations:</strong></p><ul>";
              for (const v of variations.slice(-5)) {
                html += "<li>" + esc(v) + "</li>";
              }
              html += "</ul>";
            }
            
            if (Object.keys(math_scores).length > 0) {
              html += "<p><strong>Math Scores:</strong></p><ul>";
              for (const [method, score] of Object.entries(math_scores)) {
                const width = Math.min(score * 100, 100);
                html += "<li><span style='color:#8dd3ff'>" + esc(method) + "</span> · <div class='bar'><span style='width:" + width + "%'></span></div> · <span>" + score.toFixed(3) + "</span></li>";
              }
              html += "</ul>";
            }
            html += "</section>";
          }
          html += '</div>';
          el.innerHTML = html;
        } catch (e) {
          el.innerHTML = '<p class="muted">Could not load variation data.</p>';
        }
      })();
      </script>
    </section>

    <div class="grid" style="margin-top:16px;" id="packs">'''

if old_html in content:
    content = content.replace(old_html, new_html)
    print('Added variations HTML section')
else:
    print('Could not find HTML insertion point')

# Write back
with open('/data/data/com.termux/files/home/.openclaw/workspace/CircleForge/sim.py', 'w') as f:
    f.write(content)

print('Done')
