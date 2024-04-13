const avatarPreview = document.getElementById('avatarPreview')
const avatar = document.getElementById('avatar');
let lastAvatar = null;

avatar.addEventListener('change', previewFile)
avatarPreview.addEventListener('click', (e) => {
    avatar.click()
})

function previewFile(e) {
    const preview = document.getElementById('avatarPreview');
    const file = document.getElementById('avatar').files[0];
    const reader = new FileReader();
    lastAvatar = preview.src

    reader.onloadend = () => {
        preview.src = reader.result;
    }

    if (file) {
        reader.readAsDataURL(file);
    } else {
        preview.src = lastAvatar;
    }
}