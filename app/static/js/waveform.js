/**
 * High-Performance Multi-Channel SVG Digital Waveform Timing Diagram Visualizer.
 * Renders discrete cycle transitions, clashing signals, and millisecond time points.
 */

export class WaveformRenderer {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
  }

  render(traces, clashingSignals = [], cycleTimeMs = 20) {
    if (!traces || traces.length === 0) {
      this.container.innerHTML = `<div style="color: #6b7280; padding: 1rem; text-align: center;">No simulation traces available</div>`;
      return;
    }

    const cyclesCount = traces.length;
    // Gather all variable keys
    const allSignals = new Set();
    traces.forEach(t => {
      Object.keys(t.inputs).forEach(k => allSignals.add(k));
      Object.keys(t.outputs).forEach(k => allSignals.add(k));
      Object.keys(t.states).forEach(k => allSignals.add(k));
    });

    const signalList = Array.from(allSignals);
    const labelWidth = 180;
    const cycleWidth = 60;
    const rowHeight = 36;
    const headerHeight = 30;
    const totalWidth = labelWidth + (cyclesCount * cycleWidth) + 40;
    const totalHeight = headerHeight + (signalList.length * rowHeight) + 20;

    let svg = `<svg class="waveform-svg" viewBox="0 0 ${totalWidth} ${totalHeight}" height="${totalHeight}">`;

    // Background Grid & Cycle Headers
    for (let c = 0; c < cyclesCount; c++) {
      const x = labelWidth + (c * cycleWidth);
      const timeMs = (c + 1) * cycleTimeMs;
      svg += `
        <line x1="${x}" y1="${headerHeight}" x2="${x}" y2="${totalHeight}" class="timeline-tick" />
        <text x="${x + (cycleWidth / 2)}" y="${headerHeight - 8}" font-size="11" fill="#64748b" text-anchor="middle" font-family="monospace">
          k=${c + 1} (${timeMs}ms)
        </text>
      `;
    }
    const endX = labelWidth + (cyclesCount * cycleWidth);
    svg += `<line x1="${endX}" y1="${headerHeight}" x2="${endX}" y2="${totalHeight}" class="timeline-tick" />`;

    // Render Each Signal Trace
    signalList.forEach((sig, idx) => {
      const y = headerHeight + (idx * rowHeight);
      const isClash = clashingSignals.includes(sig);
      const strokeColor = isClash ? '#ef4444' : '#06b6d4';

      // Signal Label
      svg += `
        <text x="10" y="${y + 22}" class="signal-label" fill="${isClash ? '#f87171' : '#94a3b8'}" font-weight="${isClash ? 'bold' : 'normal'}">
          ${sig} ${isClash ? '⚠️' : ''}
        </text>
        <line x1="${labelWidth}" y1="${y + rowHeight}" x2="${endX}" y2="${y + rowHeight}" stroke="#1e293b" stroke-width="1" />
      `;

      // Digital Line Trace (High / Low)
      let pathD = "";
      for (let c = 0; c < cyclesCount; c++) {
        const trace = traces[c];
        const val = trace.outputs[sig] ?? trace.inputs[sig] ?? trace.states[sig] ?? false;
        const isHigh = Boolean(val);

        const xStart = labelWidth + (c * cycleWidth);
        const xEnd = xStart + cycleWidth;
        const yHigh = y + 8;
        const yLow = y + 26;
        const currentY = isHigh ? yHigh : yLow;

        if (c === 0) {
          pathD += `M ${xStart} ${currentY} L ${xEnd} ${currentY} `;
        } else {
          // Transition vertical edge
          pathD += `V ${currentY} L ${xEnd} ${currentY} `;
        }
      }

      svg += `<path d="${pathD}" fill="none" stroke="${strokeColor}" stroke-width="2.5" />`;
    });

    svg += `</svg>`;
    this.container.innerHTML = svg;
  }
}
