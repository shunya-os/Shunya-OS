/**
 * SHUNYA OS — Dashboard UI helpers
 */

// Active nav highlighting
document.querySelectorAll('.menu-toggle a[href]').forEach(a => {
  const path = a.getAttribute('href')
  if (path === location.pathname) {
    a.classList.add('current')
  }
})

// Auto-dismiss flash messages after 5s
document.querySelectorAll('.flash').forEach(el => {
  setTimeout(() => {
    el.style.transition = 'opacity .3s'
    el.style.opacity = '0'
    setTimeout(() => el.remove(), 300)
  }, 5000)
})

// Confirm dialogs for delete buttons
document.querySelectorAll('form[onsubmit]').forEach(form => {
  const orig = form.onsubmit
  if (orig && orig.toString().includes('confirm(')) {
    // Already has inline confirm, leave it
  }
})