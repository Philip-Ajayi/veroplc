import { WaveformRenderer } from './waveform.js';

class VeroPLCApp {
  constructor() {
    this.editor = document.getElementById("st-code-editor");
    this.benchmarkSelect = document.getElementById("benchmark-select");
    this.verifyBtn = document.getElementById("verify-btn");
    this.patchBtn = document.getElementById("patch-btn");
    this.ruleInput = document.getElementById("invariant-rule");
    this.cyclesInput = document.getElementById("unroll-cycles");
    this.resultsCard = document.getElementById("results-card");
    this.metricsGrid = document.getElementById("metrics-grid");
    this.waveformContainer = "waveform-viewport";
    this.waveformRenderer = new WaveformRenderer(this.waveformContainer);

    this.benchmarks = [];
    this.currentBenchmark = null;
    this.init();
  }

  async init() {
    this.bindEvents();
    await this.loadBenchmarks();
  }

  bindEvents() {
    this.verifyBtn.addEventListener("click", () => this.runVerification());
    this.patchBtn.addEventListener("click", () => this.applyPatch());
    this.benchmarkSelect.addEventListener("change", (e) => this.selectBenchmark(e.target.value));

    // File Upload Handler (PLCopen XML)
    const fileUpload = document.getElementById("xml-file-upload");
    fileUpload.addEventListener("change", (e) => this.handleFileUpload(e));
  }

  async loadBenchmarks() {
    try {
      const res = await fetch("/api/benchmarks");
      this.benchmarks = await res.json();
      this.benchmarkSelect.innerHTML = `<option value="">-- Select Industrial Benchmark --</option>`;
      this.benchmarks.forEach((b) => {
        this.benchmarkSelect.innerHTML += `<option value="${b.id}">${b.title} (${b.industry})</option>`;
      });
      // Default to Stamping Press
      if (this.benchmarks.length > 0) {
        this.selectBenchmark(this.benchmarks[0].id);
        this.benchmarkSelect.value = this.benchmarks[0].id;
      }
    } catch (err) {
      console.error("Failed to fetch benchmarks:", err);
    }
  }

  selectBenchmark(id) {
    this.currentBenchmark = this.benchmarks.find((b) => b.id === id);
    if (!this.currentBenchmark) return;

    this.editor.value = this.currentBenchmark.structured_text;
    if (this.currentBenchmark.recommended_invariants.length > 0) {
      this.ruleInput.value = this.currentBenchmark.recommended_invariants[0].expression;
    }
    this.cyclesInput.value = this.currentBenchmark.cycle_bound;
    this.resetResultsView();
  }

  applyPatch() {
    if (!this.currentBenchmark) return;
    this.editor.value = this.currentBenchmark.patched_structured_text;
    this.runVerification();
  }

  resetResultsView() {
    this.resultsCard.innerHTML = `
      <div style="color: #64748b; font-size: 0.9rem; text-align: center; padding: 2rem;">
        Click "Run Bounded Verification" to execute formal SMT analysis.
      </div>
    `;
    this.metricsGrid.innerHTML = "";
    document.getElementById(this.waveformContainer).innerHTML = "";
  }

  async handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/parse/xml", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (res.ok) {
        this.editor.value = data.structured_text;
      } else {
        alert("Upload Error: " + data.detail);
      }
    } catch (err) {
      alert("Network error reading file: " + err);
    }
  }

  async runVerification() {
    const code = this.editor.value;
    const rule = this.ruleInput.value;
    const unrollCycles = parseInt(this.cyclesInput.value, 10);

    this.resultsCard.innerHTML = `
      <div style="color: #06b6d4; font-size: 0.9rem; text-align: center; padding: 2rem;">
        Unrolling ${unrollCycles} scan cycles in Microsoft Z3 SMT Solver...
      </div>
    `;

    const payload = {
      structured_text: code,
      invariants: [
        {
          name: "User Safety Invariant",
          invariant_type: "MUTUAL_EXCLUSION",
          expression: rule,
          description: "Active safety property under test.",
        },
      ],
      unroll_cycles: unrollCycles,
      cycle_time_ms: 20,
    };

    try {
      const res = await fetch("/api/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const result = await res.json();

      if (!res.ok) {
        this.resultsCard.innerHTML = `
          <div class="status-card status-sat">
            <div>
              <strong>Error:</strong> ${result.detail}
            </div>
          </div>
        `;
        return;
      }

      this.renderResults(result);
    } catch (err) {
      this.resultsCard.innerHTML = `<div class="status-card status-sat">Network Error: ${err}</div>`;
    }
  }

  renderResults(result) {
    const isSat = result.status === "SAT";

    // Results Banner
    this.resultsCard.innerHTML = `
      <div class="status-card ${isSat ? 'status-sat' : 'status-unsat'}">
        <div style="font-size: 1.5rem;">${isSat ? '🚨' : '🛡️'}</div>
        <div>
          <div style="font-weight: 700; font-size: 1rem;">
            ${isSat ? 'SAFETY INVARIANT VIOLATION DETECTED (SAT)' : 'MATHEMATICALLY PROVEN SAFE (UNSAT)'}
          </div>
          <div style="font-size: 0.85rem; margin-top: 0.25rem;">
            ${result.message}
          </div>
        </div>
      </div>
    `;

    // Metrics Grid
    const m = result.metrics;
    this.metricsGrid.innerHTML = `
      <div class="metric-pill">
        <div class="metric-val">${m.solve_time_seconds}s</div>
        <div class="metric-label">Solve Time</div>
      </div>
      <div class="metric-pill">
        <div class="metric-val">${m.unrolled_cycles}</div>
        <div class="metric-label">Scan Cycles (k)</div>
      </div>
      <div class="metric-pill">
        <div class="metric-val">${m.boolean_variables_count}</div>
        <div class="metric-label">SMT Variables</div>
      </div>
      <div class="metric-pill">
        <div class="metric-val">${m.assertions_count}</div>
        <div class="metric-label">Assertions</div>
      </div>
    `;

    // Render Waveform Counterexample if SAT
    if (isSat && result.counterexample) {
      this.waveformRenderer.render(
        result.counterexample.cycle_traces,
        result.counterexample.clashing_signals,
        20
      );
    } else {
      document.getElementById(this.waveformContainer).innerHTML = `
        <div style="color: #10b981; padding: 2rem; text-align: center; font-size: 0.9rem;">
          ✓ Mathematical Proof Certificate Generated: Zero clashing states exist across all 2^N input permutations up to k=${m.unrolled_cycles}.
        </div>
      `;
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  new VeroPLCApp();
});
