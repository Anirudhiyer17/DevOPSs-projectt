// ==========================================================================
// Enterprise SOC Incident Command Console JavaScript
// Telemetry, Interactive Navigation, Charts & Utilities
// ==========================================================================

document.addEventListener('DOMContentLoaded', function () {
  'use strict';

  // -------------------------------------------------------------------------
  // 1. COLLAPSIBLE SIDEBAR & RESPONSIVE DRAWER
  // -------------------------------------------------------------------------
  const body = document.body;
  const sidebarToggle = document.getElementById('sidebarToggle');
  const mobileSidebarToggle = document.getElementById('mobileSidebarToggle');
  const sidebarBackdrop = document.getElementById('sidebarBackdrop');

  // Restore saved desktop collapse preference
  const savedSidebarState = localStorage.getItem('soc_sidebar_collapsed');
  if (savedSidebarState === 'true' && window.innerWidth >= 992) {
    body.classList.add('sidebar-collapsed');
  }

  // Desktop sidebar toggle
  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', function (e) {
      e.preventDefault();
      body.classList.toggle('sidebar-collapsed');
      const isCollapsed = body.classList.contains('sidebar-collapsed');
      localStorage.setItem('soc_sidebar_collapsed', isCollapsed ? 'true' : 'false');
    });
  }

  // Mobile sidebar drawer toggle
  if (mobileSidebarToggle) {
    mobileSidebarToggle.addEventListener('click', function (e) {
      e.preventDefault();
      body.classList.toggle('sidebar-mobile-open');
    });
  }

  // Close mobile sidebar on backdrop click
  if (sidebarBackdrop) {
    sidebarBackdrop.addEventListener('click', function () {
      body.classList.remove('sidebar-mobile-open');
    });
  }

  // Close mobile sidebar on Escape key
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && body.classList.contains('sidebar-mobile-open')) {
      body.classList.remove('sidebar-mobile-open');
    }
  });

  // -------------------------------------------------------------------------
  // 2. LIVE UTC TACTICAL CLOCK
  // -------------------------------------------------------------------------
  const clockEl = document.getElementById('socClock');
  if (clockEl) {
    const updateClock = () => {
      const now = new Date();
      const pad = (n) => String(n).padStart(2, '0');
      const y = now.getUTCFullYear();
      const m = pad(now.getUTCMonth() + 1);
      const d = pad(now.getUTCDate());
      const hh = pad(now.getUTCHours());
      const mm = pad(now.getUTCMinutes());
      const ss = pad(now.getUTCSeconds());
      clockEl.textContent = `${y}-${m}-${d} ${hh}:${mm}:${ss} UTC`;
    };
    updateClock();
    setInterval(updateClock, 1000);
  }

  // -------------------------------------------------------------------------
  // 3. COPY TO CLIPBOARD UTILITY
  // -------------------------------------------------------------------------
  document.querySelectorAll('[data-copy]').forEach((btn) => {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      const text = this.getAttribute('data-copy');
      if (text) {
        navigator.clipboard.writeText(text).then(() => {
          const originalHTML = this.innerHTML;
          this.innerHTML = '<i class="bi bi-check2 text-success"></i>';
          this.classList.add('text-success');
          setTimeout(() => {
            this.innerHTML = originalHTML;
            this.classList.remove('text-success');
          }, 1800);
        }).catch(err => {
          console.warn('Clipboard write failed:', err);
        });
      }
    });
  });

  // -------------------------------------------------------------------------
  // 4. NOTIFICATIONS DROPDOWN INTERACTION
  // -------------------------------------------------------------------------
  const markAllReadBtn = document.getElementById('markAllNotificationsRead');
  const notificationBadge = document.getElementById('notificationBadge');
  if (markAllReadBtn && notificationBadge) {
    markAllReadBtn.addEventListener('click', function (e) {
      e.preventDefault();
      document.querySelectorAll('.notification-item.unread').forEach(item => {
        item.classList.remove('unread');
      });
      notificationBadge.style.display = 'none';
    });
  }

  // -------------------------------------------------------------------------
  // 5. CHART.JS TELEMETRY VISUALIZATIONS
  // -------------------------------------------------------------------------
  const severityCanvas = document.getElementById('severityChart');
  const categoryCanvas = document.getElementById('categoryChart');
  const activityCanvas = document.getElementById('activityChart');
  if (severityCanvas || categoryCanvas || activityCanvas) {

    fetch('/api/stats')
      .then((response) => {
        if (!response.ok) throw new Error('Telemetry API error: ' + response.statusText);
        return response.json();
      })
      .then((data) => {
        // Chart 1: Severity Doughnut
        if (severityCanvas) {
          const sevCtx = severityCanvas.getContext('2d');
          const sevLabels = ['Critical', 'High', 'Medium', 'Low'];
          const sevValues = [
            data.severity.Critical || 0,
            data.severity.High || 0,
            data.severity.Medium || 0,
            data.severity.Low || 0
          ];

          new Chart(sevCtx, {
            type: 'doughnut',
            data: {
              labels: sevLabels,
              datasets: [{
                data: sevValues,
                backgroundColor: [
                  '#ef4444', // Critical Red
                  '#f97316', // High Orange
                  '#eab308', // Medium Yellow
                  '#38bdf8'  // Low Cyan/Blue
                ],
                borderColor: '#0d1629',
                borderWidth: 3,
                hoverBorderColor: '#00f2fe',
                hoverBorderWidth: 2,
                hoverOffset: 6
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              cutout: '72%',
              plugins: {
                legend: {
                  position: 'bottom',
                  labels: {
                    color: '#94a3b8',
                    font: {
                      family: "'Inter', sans-serif",
                      size: 12,
                      weight: 500
                    },
                    padding: 18,
                    usePointStyle: true,
                    pointStyle: 'circle'
                  }
                },
                tooltip: {
                  backgroundColor: '#0a1120',
                  borderColor: '#1a2c4e',
                  borderWidth: 1,
                  titleColor: '#f8fafc',
                  titleFont: { weight: 600 },
                  bodyColor: '#94a3b8',
                  padding: 12,
                  boxPadding: 6,
                  usePointStyle: true,
                  callbacks: {
                    label: function (context) {
                      const label = context.label || '';
                      const value = context.parsed || 0;
                      const total = context.dataset.data.reduce((a, b) => a + b, 0);
                      const pct = total > 0 ? Math.round((value / total) * 100) : 0;
                      return ` ${label}: ${value} incident${value === 1 ? '' : 's'} (${pct}%)`;
                    }
                  }
                }
              }
            }
          });
        }

        // Chart 2: Threat Categories Horizontal Bar
        if (categoryCanvas) {
          const catCtx = categoryCanvas.getContext('2d');
          const catLabels = Object.keys(data.categories || {});
          const catValues = Object.values(data.categories || {});

          // Create gradient for bars
          const gradient = catCtx.createLinearGradient(0, 0, 400, 0);
          gradient.addColorStop(0, 'rgba(2, 132, 199, 0.4)');
          gradient.addColorStop(1, 'rgba(0, 242, 254, 0.85)');

          new Chart(catCtx, {
            type: 'bar',
            data: {
              labels: catLabels.length > 0 ? catLabels : ['No Data'],
              datasets: [{
                label: 'Cases',
                data: catValues.length > 0 ? catValues : [0],
                backgroundColor: gradient,
                borderColor: '#00f2fe',
                borderWidth: 1.5,
                borderRadius: 6,
                hoverBackgroundColor: '#00f2fe'
              }]
            },
            options: {
              indexAxis: 'y',
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: { display: false },
                tooltip: {
                  backgroundColor: '#0a1120',
                  borderColor: '#1a2c4e',
                  borderWidth: 1,
                  titleColor: '#f8fafc',
                  bodyColor: '#94a3b8',
                  padding: 10,
                  callbacks: {
                    label: function (ctx) {
                      return ` Recorded Cases: ${ctx.parsed.x}`;
                    }
                  }
                }
              },
              scales: {
                x: {
                  beginAtZero: true,
                  ticks: {
                    stepSize: 1,
                    color: '#64748b',
                    font: { family: "'JetBrains Mono', monospace", size: 11 }
                  },
                  grid: {
                    color: 'rgba(26, 44, 78, 0.4)',
                    drawBorder: false
                  }
                },
                y: {
                  ticks: {
                    color: '#94a3b8',
                    font: { family: "'Inter', sans-serif", size: 12, weight: 500 }
                  },
                  grid: {
                    display: false
                  }
                }
              }
            }
          });
        }
       // Chart 3: 24-Hour Incident Activity
        if (activityCanvas) {
          const activityCtx = activityCanvas.getContext('2d');

          new Chart(activityCtx, {
            type: 'line',
            data: {
              labels: data.hourly.labels,
              datasets: [{
                label: 'Incidents',
                data: data.hourly.counts,
                borderColor: '#00f2fe',
                backgroundColor: 'rgba(0, 242, 254, 0.12)',
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointBackgroundColor: '#00f2fe'
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: {
                  display: false
                }
              },
              scales: {
                x: {
                  ticks: {
                    color: '#94a3b8',
                    maxTicksLimit: 8
                  },
                  grid: {
                    display: false
                  }
                },
                y: {
                  beginAtZero: true,
                  ticks: {
                    color: '#94a3b8',
                    precision: 0
                  },
                  grid: {
                    color: 'rgba(26, 44, 78, 0.4)'
                  }
                }
              }
            }
          });
        }
      })

      
      .catch((error) => {
        console.error('Failed to load telemetry statistics:', error);
      });
  }
});
