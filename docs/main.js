/* ===== PRP-AI Assistant — Shared JavaScript ===== */

(function () {
  'use strict';

  /* ----- Mobile Menu ----- */
  const mobileToggle = document.getElementById('mobile-toggle');
  const mobileMenu = document.getElementById('mobile-menu');
  if (mobileToggle && mobileMenu) {
    mobileToggle.addEventListener('click', () => {
      mobileMenu.classList.toggle('open');
      const icon = mobileToggle.querySelector('svg');
      if (mobileMenu.classList.contains('open')) {
        icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>';
      } else {
        icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>';
      }
    });
    mobileMenu.querySelectorAll('a').forEach(a => {
      a.addEventListener('click', () => {
        mobileMenu.classList.remove('open');
        const icon = mobileToggle.querySelector('svg');
        icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>';
      });
    });
  }

  /* ----- Scroll Reveal ----- */
  function initReveal() {
    const els = document.querySelectorAll('.reveal');
    if (!els.length) return;
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
    els.forEach(el => observer.observe(el));
  }

  /* ----- Counter Animation ----- */
  function animateCounters() {
    const counters = document.querySelectorAll('[data-count]');
    if (!counters.length) return;
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting && !entry.target.dataset.counted) {
          entry.target.dataset.counted = 'true';
          const target = parseInt(entry.target.dataset.count, 10);
          const suffix = entry.target.dataset.suffix || '';
          const prefix = entry.target.dataset.prefix || '';
          const duration = 1500;
          const start = performance.now();
          function update(now) {
            const progress = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = Math.round(target * eased);
            entry.target.textContent = prefix + current.toLocaleString() + suffix;
            if (progress < 1) requestAnimationFrame(update);
          }
          requestAnimationFrame(update);
        }
      });
    }, { threshold: 0.5 });
    counters.forEach(el => observer.observe(el));
  }

  /* ----- FAQ Accordion ----- */
  function initFAQ() {
    document.querySelectorAll('.faq-question').forEach(btn => {
      btn.addEventListener('click', () => {
        const item = btn.closest('.faq-item');
        const wasOpen = item.classList.contains('open');
        // Close all siblings (optional: remove this for independent toggle)
        item.parentElement.querySelectorAll('.faq-item').forEach(i => i.classList.remove('open'));
        if (!wasOpen) item.classList.add('open');
      });
    });
  }

  /* ----- Pricing Toggle ----- */
  function initPricingToggle() {
    const toggle = document.getElementById('pricing-toggle');
    const monthlyLabel = document.getElementById('pricing-monthly-label');
    const annualLabel = document.getElementById('pricing-annual-label');
    if (!toggle) return;

    function updatePrices(annual) {
      document.querySelectorAll('[data-monthly]').forEach(el => {
        if (annual) {
          el.textContent = el.dataset.annual;
        } else {
          el.textContent = el.dataset.monthly;
        }
      });
      document.querySelectorAll('[data-annual-detail]').forEach(el => {
        el.style.opacity = annual ? '1' : '0';
        el.textContent = annual ? el.dataset.annualDetail : '';
      });
      if (monthlyLabel) monthlyLabel.classList.toggle('active', !annual);
      if (annualLabel) annualLabel.classList.toggle('active', annual);
      toggle.classList.toggle('annual', annual);
    }

    toggle.addEventListener('click', () => {
      const isAnnual = !toggle.classList.contains('annual');
      updatePrices(isAnnual);
    });

    if (monthlyLabel) monthlyLabel.addEventListener('click', () => updatePrices(false));
    if (annualLabel) annualLabel.addEventListener('click', () => updatePrices(true));
  }

  /* ----- Clipboard Copy ----- */
  function initClipboard() {
    document.querySelectorAll('[data-copy]').forEach(btn => {
      btn.addEventListener('click', () => {
        const text = btn.dataset.copy;
        navigator.clipboard.writeText(text).then(() => {
          const original = btn.innerHTML;
          btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg> Copied';
          setTimeout(() => { btn.innerHTML = original; }, 2000);
        });
      });
    });
  }

  /* ----- Smooth Scroll ----- */
  function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(a => {
      a.addEventListener('click', e => {
        const id = a.getAttribute('href');
        if (id === '#') return;
        const target = document.querySelector(id);
        if (target) {
          e.preventDefault();
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      });
    });
  }

  /* ----- Nav Active State ----- */
  function initNavActive() {
    const path = window.location.pathname;
    document.querySelectorAll('.nav-links a, .mobile-menu a').forEach(a => {
      const href = a.getAttribute('href');
      if (href && !href.startsWith('#')) {
        const page = href.split('/').pop();
        const current = path.split('/').pop() || 'index.html';
        if (page === current) {
          a.classList.add('active');
        }
      }
    });
  }

  /* ----- Dashboard Simulation ----- */
  function initDashboardSim() {
    const taskCount = document.getElementById('dash-task-count');
    const successRate = document.getElementById('dash-success-rate');
    const logPanel = document.getElementById('dash-log');
    if (!taskCount && !logPanel) return;

    const agents = ['CodeAgent', 'TestAgent', 'SecurityAgent', 'DeployAgent', 'AnalysisAgent', 'DocsAgent'];
    const actions = [
      'Processing task', 'Completed analysis', 'Generated output',
      'Running checks', 'Optimizing result', 'Finalizing'
    ];
    const colors = {
      CodeAgent: '#3B82F6', TestAgent: '#22C55E', SecurityAgent: '#EF4444',
      DeployAgent: '#F97316', AnalysisAgent: '#8B5CF6', DocsAgent: '#06B6D4'
    };

    let count = 847;
    function addLog() {
      if (!logPanel) return;
      const agent = agents[Math.floor(Math.random() * agents.length)];
      const action = actions[Math.floor(Math.random() * actions.length)];
      const time = new Date().toLocaleTimeString('en-US', { hour12: false });
      const line = document.createElement('div');
      line.style.marginBottom = '4px';
      line.innerHTML = '<span style="color:#475569">' + time + '</span> <span style="color:' + colors[agent] + '">[' + agent + ']</span> ' + action;
      logPanel.prepend(line);
      if (logPanel.children.length > 50) logPanel.removeChild(logPanel.lastChild);
    }

    function updateMetrics() {
      count += Math.floor(Math.random() * 3);
      if (taskCount) taskCount.textContent = count.toLocaleString();
      if (successRate) {
        const rate = (95 + Math.random() * 4.5).toFixed(1);
        successRate.textContent = rate + '%';
      }
    }

    setInterval(addLog, 3000);
    setInterval(updateMetrics, 5000);
    // Initial entries
    for (let i = 0; i < 5; i++) addLog();
  }

  /* ----- Pipeline Demo (landing page) ----- */
  function initPipelinePreview() {
    const nodes = document.querySelectorAll('.pipeline-node');
    const progress = document.querySelector('.pipeline-progress');
    if (!nodes.length || !progress) return;

    let current = 0;
    const total = nodes.length;

    function step() {
      nodes.forEach((n, i) => {
        const dot = n.querySelector('.pipeline-dot');
        dot.classList.remove('active', 'complete', 'processing');
        n.querySelector('.pipeline-label').classList.remove('active');
        if (i < current) {
          dot.classList.add('complete');
        } else if (i === current) {
          dot.classList.add('active', 'processing');
          n.querySelector('.pipeline-label').classList.add('active');
        }
      });
      progress.style.width = (current / (total - 1)) * 100 + '%';
      current++;
      if (current > total) {
        current = 0;
        setTimeout(step, 2000);
      } else {
        setTimeout(step, 1200);
      }
    }
    step();
  }

  /* ----- Demo Page: Full Animation Sequence ----- */
  function initDemoAnimation() {
    const container = document.getElementById('demo-animation');
    if (!container) return;

    const steps = container.querySelectorAll('.demo-step');
    const progressBars = container.querySelectorAll('.demo-progress-fill');
    const testResults = container.querySelectorAll('.demo-test-result');
    const codeBlocks = container.querySelectorAll('.demo-code-output');
    const replayBtn = document.getElementById('demo-replay');

    function resetAll() {
      steps.forEach(s => { s.classList.remove('active', 'complete'); s.classList.add('demo-step'); });
      progressBars.forEach(p => { p.style.width = '0%'; });
      testResults.forEach(t => t.classList.remove('visible'));
      codeBlocks.forEach(c => { c.style.opacity = '0'; });
      const scoreBig = container.querySelector('.demo-security-score');
      if (scoreBig) { scoreBig.style.opacity = '0'; scoreBig.textContent = ''; }
      const liveBadge = container.querySelector('.demo-live-badge');
      if (liveBadge) { liveBadge.style.opacity = '0'; }
      const dashUpdate = container.querySelector('.demo-dash-update');
      if (dashUpdate) { dashUpdate.style.opacity = '0'; }
    }

    function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

    async function playSequence() {
      resetAll();
      await delay(500);

      // Step 0: User submits task
      if (steps[0]) { steps[0].classList.add('active'); await delay(1500); steps[0].classList.remove('active'); steps[0].classList.add('complete'); }

      // Step 1: Task enters pipeline
      if (steps[1]) { steps[1].classList.add('active'); await delay(1000); steps[1].classList.remove('active'); steps[1].classList.add('complete'); }

      // Step 2: AnalysisAgent
      if (steps[2]) {
        steps[2].classList.add('active');
        const bar = steps[2].querySelector('.demo-progress-fill');
        if (bar) { await delay(300); bar.style.width = '100%'; }
        await delay(2000);
        steps[2].classList.remove('active'); steps[2].classList.add('complete');
      }

      // Step 3: CodeAgent
      if (steps[3]) {
        steps[3].classList.add('active');
        const code = steps[3].querySelector('.demo-code-output');
        if (code) { await delay(500); code.style.opacity = '1'; }
        await delay(2500);
        steps[3].classList.remove('active'); steps[3].classList.add('complete');
      }

      // Step 4: TestAgent
      if (steps[4]) {
        steps[4].classList.add('active');
        const tests = steps[4].querySelectorAll('.demo-test-result');
        for (let i = 0; i < tests.length; i++) {
          await delay(300);
          tests[i].classList.add('visible');
        }
        await delay(1000);
        steps[4].classList.remove('active'); steps[4].classList.add('complete');
      }

      // Step 5: SecurityAgent
      if (steps[5]) {
        steps[5].classList.add('active');
        const bar = steps[5].querySelector('.demo-progress-fill');
        if (bar) { await delay(300); bar.style.width = '100%'; }
        await delay(1500);
        const score = steps[5].querySelector('.demo-security-score');
        if (score) { score.style.opacity = '1'; score.textContent = 'A+'; }
        await delay(1500);
        steps[5].classList.remove('active'); steps[5].classList.add('complete');
      }

      // Step 6: DocsAgent
      if (steps[6]) {
        steps[6].classList.add('active');
        const code = steps[6].querySelector('.demo-code-output');
        if (code) { await delay(500); code.style.opacity = '1'; }
        await delay(2000);
        steps[6].classList.remove('active'); steps[6].classList.add('complete');
      }

      // Step 7: DeployAgent
      if (steps[7]) {
        steps[7].classList.add('active');
        const bar = steps[7].querySelector('.demo-progress-fill');
        if (bar) { await delay(300); bar.style.width = '100%'; }
        await delay(2000);
        const badge = steps[7].querySelector('.demo-live-badge');
        if (badge) { badge.style.opacity = '1'; }
        await delay(1500);
        steps[7].classList.remove('active'); steps[7].classList.add('complete');
      }

      // Step 8: Dashboard update
      if (steps[8]) {
        steps[8].classList.add('active');
        const dashUpdate = steps[8].querySelector('.demo-dash-update');
        if (dashUpdate) { await delay(500); dashUpdate.style.opacity = '1'; }
        await delay(2000);
        steps[8].classList.remove('active'); steps[8].classList.add('complete');
      }
    }

    // Auto-play
    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) {
        playSequence();
        observer.disconnect();
      }
    }, { threshold: 0.2 });
    observer.observe(container);

    // Replay
    if (replayBtn) {
      replayBtn.addEventListener('click', () => playSequence());
    }
  }

  /* ----- Task Progress Animation (features page) ----- */
  function initTaskProgress() {
    document.querySelectorAll('.task-progress-bar').forEach(bar => {
      const fill = bar.querySelector('.task-progress-fill');
      if (!fill) return;
      const observer = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting) {
          const target = fill.dataset.progress || '75';
          fill.style.width = target + '%';
          observer.disconnect();
        }
      }, { threshold: 0.5 });
      observer.observe(bar);
    });
  }

  /* ----- Init All ----- */
  document.addEventListener('DOMContentLoaded', () => {
    initReveal();
    animateCounters();
    initFAQ();
    initPricingToggle();
    initClipboard();
    initSmoothScroll();
    initNavActive();
    initDashboardSim();
    initPipelinePreview();
    initDemoAnimation();
    initTaskProgress();
  });
})();
