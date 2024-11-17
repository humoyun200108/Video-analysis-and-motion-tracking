document.addEventListener("DOMContentLoaded", function() {
    const fileInput = document.getElementById('file-upload');
    const customBtn = document.querySelector('.custom-file-upload');
    const submitBtn = document.querySelector('button[type="submit"]');

    customBtn.addEventListener('click', function() {
        fileInput.click();
    });

    fileInput.addEventListener('change', function() {
        if (fileInput.value) {
            customBtn.textContent = 'Tanlandi: ' + fileInput.files[0].name;
            submitBtn.style.display = 'inline-block';
        } else {
            customBtn.textContent = 'Faylni tanlang';
            submitBtn.style.display = 'none';
        }
    });
});
