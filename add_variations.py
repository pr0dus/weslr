#!/usr/bin/env python3
"""Add variations section to the dashboard HTML f-string in sim.py"""

with open('sim.py', 'r') as f:
    lines = f.readlines()

# Find the line with "</table>" followed by "</section>" and then "id='packs'"
variations_html = '''
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
'''

# Find the insertion point - look for pattern in lines
found = False
for i in range(len(lines) - 3):
    # Check for pattern: </table> on line i, </section> on i+1, empty on i+2, id="packs" on i+3
    if '</table>' in lines[i] and '</section>' in lines[i+1] and 'id="packs"' in lines[i+3]:
        # Insert variations section after </section> line (at i+2)
        lines.insert(i+2, variations_html)
        found = True
        print(f'Found insertion point at line {i+1}, inserted at {i+2}')
        break

if not found:
    print('Could not find insertion point')

# Write back
with open('sim.py', 'w') as f:
    f.writelines(lines)

print('Done')
