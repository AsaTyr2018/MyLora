document.addEventListener('DOMContentLoaded', () => {
  const modalEl = document.getElementById('previewModal');
  if (!modalEl) return;
  const modal = new bootstrap.Modal(modalEl);
  const modalImg = document.getElementById('modalImage');
  const images = Array.from(document.querySelectorAll('.preview-grid img'));
  let current = 0;

  function show(index) {
    if (index < 0 || index >= images.length) return;
    current = index;
    modalImg.src = images[current].src;
    modal.show();
  }

  images.forEach((img, idx) => {
    img.style.cursor = 'pointer';
    img.addEventListener('click', () => show(idx));
  });

  document.getElementById('prevBtn').addEventListener('click', () => {
    show((current - 1 + images.length) % images.length);
  });

  document.getElementById('nextBtn').addEventListener('click', () => {
    show((current + 1) % images.length);
  });

  document.addEventListener('keydown', (e) => {
    if (!modalEl.classList.contains('show')) return;
    if (e.key === 'ArrowLeft') {
      show((current - 1 + images.length) % images.length);
    } else if (e.key === 'ArrowRight') {
      show((current + 1) % images.length);
    } else if (e.key === 'Escape') {
      modal.hide();
    }
  });
});
