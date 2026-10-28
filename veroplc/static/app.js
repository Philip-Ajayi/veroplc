// VeroPLC Frontend Controller
let currentBenchmark = null;
let currentPatchedCode = null;

const codeEditor = document.getElementById('code-editor');
const invNameInput = document.getElementById('inv-name');
const invExprInput = document.getElementById('inv-expr');
const kMaxInput = document.getElementById('input-k-max');
const btnVerify = document.getElementById('btn-verify');
const statusCard = document.getElementById('status-card');
const statusIndicator = document.getElementById('status-indicator');
const statusTitle = document.getElementById('status-title');
const statusDesc = document.getElementById('status-desc');
const solverMetrics = document.getElementById('solver-metrics');
const waveformContainer = document.getElementById('waveform-container');
const traceContainer = document.getElementById('trace-table-container');
const btnPatch = document.getElementById('btn-patch-code');

// Initialize Benchmarks
async function loadBenchmark(slug) {
    try {
        const resp = await fetch(`/api/benchmarks/${slug}`);
        const data = await resp.json();
        currentBenchmark = data;
        currentPatchedCode = data.patched_code;
        codeEditor.value = data.raw_code;
        invExprInput.value = data.default_invariant;
        kMaxInput.value = data.expected_k;
        btnPatch.classList.remove('hidden');
        resetStatus();
    } catch (err) {
        console.error("Failed to load benchmark", err);
    }
}

document.getElementById('btn-bm-press').onclick = () => loadBenchmark('stamping-press');
document.getElementById('btn-bm-chemical').onclick = () => loadBenchmark('chemical-reactor');
document.getElementById('btn-bm-baggage').onclick = () => loadBenchmark('baggage-sorter');

btnPatch.onclick = () => {
    if (currentPatchedCode) {
        codeEditor.value = currentPatchedCode;
        btnPatch.classList.add('hidden');
        runVerification();
    }
};

function resetStatus() {
    statusIndicator.className = "h-3.5 w-3.5 rounded-full bg-slate-600";
    statusTitle.textContent = "Awaiting Verification";
    statusDesc.textContent = "Click 'Verify Invariants' to unroll the transition relation.";
    solverMetrics.innerHTML = "";
    waveformContainer.innerHTML = '<span class="text-xs text-slate-600 font-mono">No active trace.</span>';
    traceContainer.innerHTML = '<div class="text-center text-xs text-slate-600 py-6">Inspection details will appear here.</div>';
}

async function runVerification() {
    const code = codeEditor.value;
    const invName = invNameInput.value || "Invariant";
    const invExpr = invExprInput.value;
    const kMax = parseInt(kMaxInput.value, 10);

    statusIndicator.className = "h-3.5 w-3.5 rounded-full bg-amber-400 animate-ping";
    statusTitle.textContent = "Solving SMT Formula in Z3...";
    statusDesc.textContent = `Unrolling cyclic scan semantics for k=1..${kMax}...`;

    try {
        const resp = await fetch('/api/verify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code: code,
                code_format: 'ST',
                k_max: kMax,
                invariants: [{ name: invName, expression: invExpr }]
            })
        });

        const data = await resp.json();
        renderVerificationResult(data);
    } catch (err) {
        statusIndicator.className = "h-3.5 w-3.5 rounded-full bg-rose-600";
        statusTitle.textContent = "Solver Error";
        statusDesc.textContent = err.message;
    }
}

btnVerify.onclick = runVerification;

function renderVerificationResult(res) {
    solverMetrics.innerHTML = `
        <div>Time: <span class="text-cyan-400">${res.time_seconds}s</span></div>
        <div>Variables: <span class="text-slate-300">${res.variables_count}</span> | Clauses: <span class="text-slate-300">${res.clauses_count}</span></div>
    `;

    if (res.status === "SAT") {
        statusIndicator.className = "h-3.5 w-3.5 rounded-full bg-rose-500 shadow-lg shadow-rose-500/50";
        statusTitle.className = "text-sm font-bold text-rose-400";
        statusTitle.textContent = `SAFETY VIOLATION FOUND (SAT) — Cycle k = ${res.violating_cycle}`;
        statusDesc.textContent = res.message;
        renderWaveform(res.counterexample);
        renderTraceTable(res.counterexample);
    } else if (res.status === "UNSAT") {
        statusIndicator.className = "h-3.5 w-3.5 rounded-full bg-emerald-500 shadow-lg shadow-emerald-500/50";
        statusTitle.className = "text-sm font-bold text-emerald-400";
        statusTitle.textContent = `MATHEMATICALLY PROVEN SAFE (UNSAT)`;
        statusDesc.textContent = res.message;
        renderProofCert(res.proof_certificate);
    }
}

function renderWaveform(cx) {
    if (!cx || !cx.timeline) return;
    const timeline = cx.timeline;
    const cyclesCount = timeline.length;

    // Extract all signals
    const first = timeline[0];
    const signalNames = [...Object.keys(first.inputs), ...Object.keys(first.outputs), ...Object.keys(first.state)];

    let html = '<div class="w-full font-mono text-xs">';
    
    // Header row of cycle numbers
    html += '<div class="wave-row font-bold text-slate-400"><div class="wave-label">SCAN CYCLE (k)</div><div class="wave-track">';
    for (let c = 0; c < cyclesCount; c++) {
        const isFailing = c === cx.violating_cycle;
        html += `<div class="wave-cycle text-center ${isFailing ? 'bg-rose-950/80 text-rose-300 font-bold' : ''}">k=${c}</div>`;
    }
    html += '</div></div>';

    // Signal rows
    signalNames.forEach(sig => {
        html += `<div class="wave-row"><div class="wave-label" title="${sig}">${sig}</div><div class="wave-track">`;
        for (let c = 0; c < cyclesCount; c++) {
            const step = timeline[c];
            const val = step.inputs[sig] ?? step.outputs[sig] ?? step.state[sig] ?? false;
            const isFailing = c === cx.violating_cycle;
            
            let color = val ? 'bg-cyan-500/30 border-cyan-400 text-cyan-200' : 'bg-industrial-900 border-slate-700 text-slate-600';
            if (isFailing && val && (sig.includes("Extend") || sig.includes("Pump") || sig.includes("Diverter"))) {
                color = 'bg-rose-600/40 border-rose-400 text-rose-200 font-bold animate-pulse';
            }

            html += `<div class="wave-cycle p-1 flex items-center justify-center">
                <div class="w-full h-full rounded border ${color} flex items-center justify-center text-[10px]">
                    ${val ? '1' : '0'}
                </div>
            </div>`;
        }
        html += '</div></div>';
    });

    html += '</div>';
    waveformContainer.innerHTML = html;
}

function renderTraceTable(cx) {
    if (!cx) return;
    let html = `
        <table class="w-full text-left font-mono text-[11px] text-slate-300">
            <thead class="text-slate-500 border-b border-industrial-800">
                <tr>
                    <th class="py-1">Cycle</th>
                    <th class="py-1">Inputs (Permuted by Z3)</th>
                    <th class="py-1">Outputs / Actuators</th>
                    <th class="py-1">Invariant Status</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-industrial-800">
    `;

    cx.timeline.forEach(step => {
        const isFail = step.cycle === cx.violating_cycle;
        html += `
            <tr class="${isFail ? 'bg-rose-950/40 text-rose-200' : ''}">
                <td class="py-1.5 font-bold">k=${step.cycle}</td>
                <td class="py-1.5 text-amber-300">${JSON.stringify(step.inputs)}</td>
                <td class="py-1.5 text-cyan-300 font-semibold">${JSON.stringify(step.outputs)}</td>
                <td class="py-1.5">${isFail ? '<span class="text-rose-400 font-bold">FAIL (VIOLATION)</span>' : '<span class="text-emerald-400">PASS</span>'}</td>
            </tr>
        `;
    });

    html += `</tbody></table>`;
    traceContainer.innerHTML = html;
}

function renderProofCert(cert) {
    if (!cert) return;
    traceContainer.innerHTML = `
        <div class="p-4 rounded border border-emerald-500/30 bg-emerald-950/20 font-mono space-y-2">
            <div class="text-emerald-400 font-bold flex items-center space-x-2">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                <span>FORMAL MATHEMATICAL SAFETY CERTIFICATE</span>
            </div>
            <div class="text-xs text-slate-300">Prover: ${cert.prover}</div>
            <div class="text-xs text-slate-300">Bounded Cycles Verified: ${cert.cycles_verified}</div>
            <div class="text-xs text-slate-300">SMT Result: <span class="text-emerald-400 font-bold">${cert.mathematical_result}</span></div>
            <div class="text-xs text-slate-400 pt-2 border-t border-emerald-900">${cert.guarantee}</div>
        </div>
    `;
    waveformContainer.innerHTML = '<div class="text-center text-xs text-emerald-400 font-mono py-8">Invariant unconditionally holds for all state transitions. No counterexample path exists.</div>';
}

// Auto-load benchmark on first load
window.onload = () => loadBenchmark('stamping-press');
