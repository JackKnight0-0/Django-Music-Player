import {getCookie} from "./get_cookie.js";

const modal = document.getElementById("myModal");
const modalOpen = document.getElementById("modalOpen");
let lastCover = null;
const currentCover = document.getElementById('coverPreview').src;
const coverPreview = document.getElementById('coverPreview')
const spanClose = document.getElementsByClassName("close")[0];
const playlistCover = document.getElementById('playlistCover');
const formUpdate = document.getElementById('coverUpdate');
const mainCover = document.getElementById('playlistMainCover');
const playlistName = document.getElementById('playlist-name');
const removeSongButtons = document.getElementsByClassName('remove-song');

playlistCover.addEventListener('change', previewFile)
coverPreview.addEventListener('click', (e) => {
    playlistCover.click()
})

modalOpen.addEventListener('click', (e) => {
    modal.style.display = "block";
})
spanClose.addEventListener('click', (e) => {
    modal.style.display = "none";
    coverPreview.src = currentCover
})

window.addEventListener('click', (e) => {
    if (e.target === modal) {
        modal.style.display = "none";
        coverPreview.src = currentCover
    }
})

for (let i = 0; i < removeSongButtons.length; i++) {
    removeSongButtons[i].addEventListener('click', async (e) => {
        const songElement = e.currentTarget.closest('.song')
        const songSlug = songElement.getAttribute('id')
        const removeURL = `http://${window.location.host}/player/api/v1/playlist/remove/${songSlug}/${getPlayList()}/`
        const response = await fetch(removeURL, {
            method: 'DELETE',
            mode: "cors",
            cache: "no-cache",
            credentials: "same-origin",
            headers: {
                "X-CSRFToken": getCookie('csrftoken'),
            }
        })
        if (response.ok) {
            songElement.remove()
        }
    })
}

function previewFile(e) {
    const preview = document.getElementById('coverPreview');
    const file = document.getElementById('playlistCover').files[0];
    const reader = new FileReader();
    lastCover = preview.src

    reader.onloadend = () => {
        preview.src = reader.result;
    }

    if (file) {
        reader.readAsDataURL(file);
    } else {
        preview.src = lastCover;
    }
}

function getPlayList() {
    const pathname = window.location.pathname.slice(0, -1)
    return pathname.slice(pathname.lastIndexOf('/')).replace('/', '')
}


formUpdate.addEventListener('submit', async (e) => {
    e.preventDefault()
    const url = `http://${window.location.host}/player/api/v1/playlist/update/${getPlayList()}/`
    const csrftoken = getCookie('csrftoken')
    const formElement = e.target
    const data = new FormData()
    const cover = formElement.playlistCover.files[0]
    const name = formElement.playlistName.value
    if (cover) {
        data.append('cover', cover)
    }
    data.append('name', name)
    const response = await fetch(url, {
        method: 'PUT',
        mode: "cors",
        cache: "no-cache",
        credentials: "same-origin",
        headers: {
            "X-CSRFToken": csrftoken,
        },
        body: data
    })
    if (response.ok) {
        modal.style.display = "none";
        if (cover) {
            mainCover.src = coverPreview.src
        }
        if (name) {
            playlistName.innerText = name
        }
    }
})


let audio = null;
let isPlaying = false;
let randomSong = false;
let isRepeat = false;
let isInputRange = false;

let audioTitle = document.getElementById('audio-title');

const playPauseButton = document.getElementById('playPauseButton');
const mainPlayPauseButton = document.getElementById('main-play-pause-button');
const progressBarFill = document.getElementById('progressBarFill');
const currentTimeSpan = document.getElementById('currentTime');
const totalTimeSpan = document.getElementById('totalTime');
const songList = document.getElementById('song-list');
const volumeControl = document.getElementById('volumeControl');
const audioControlPanel = document.getElementById('audio-control');
const randomButton = document.getElementById('shuffleButton');
const repeatButton = document.getElementById('repeatButton');
const audioAuthors = document.getElementById('audio-authors');
const audioCover = document.getElementById('audio-cover');
const nextButton = document.getElementById('nextButton');
const prevButton = document.getElementById('prevButton');
const progressRange = document.getElementById('progressRange');


function togglePlayPause() {
    if (isPlaying) {
        audio.pause();
        playPauseButton.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="lime"
                         class="bi bi-play-circle-fill" viewBox="0 0 16 16">
                        <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0M6.79 5.093A.5.5 0 0 0 6 5.5v5a.5.5 0 0 0 .79.407l3.5-2.5a.5.5 0 0 0 0-.814z"></path>
                    </svg>`;
        mainPlayPauseButton.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="55" height="55" fill="lime"
                         class="bi bi-play-circle-fill" viewBox="0 0 16 16">
                        <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0M6.79 5.093A.5.5 0 0 0 6 5.5v5a.5.5 0 0 0 .79.407l3.5-2.5a.5.5 0 0 0 0-.814z"></path>
                    </svg>`
    } else {
        audio.play();
        playPauseButton.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="lime" class="bi bi-pause-circle-fill" viewBox="0 0 16 16">
  <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0M6.25 5C5.56 5 5 5.56 5 6.25v3.5a1.25 1.25 0 1 0 2.5 0v-3.5C7.5 5.56 6.94 5 6.25 5m3.5 0c-.69 0-1.25.56-1.25 1.25v3.5a1.25 1.25 0 1 0 2.5 0v-3.5C11 5.56 10.44 5 9.75 5"/>
</svg>`;
        mainPlayPauseButton.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="55" height="55" fill="lime" class="bi bi-pause-circle-fill" viewBox="0 0 16 16">
  <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0M6.25 5C5.56 5 5 5.56 5 6.25v3.5a1.25 1.25 0 1 0 2.5 0v-3.5C7.5 5.56 6.94 5 6.25 5m3.5 0c-.69 0-1.25.56-1.25 1.25v3.5a1.25 1.25 0 1 0 2.5 0v-3.5C11 5.56 10.44 5 9.75 5"/>
</svg>`
    }
    isPlaying = !isPlaying;
}

function updateProgress() {
    if (audio.currentTime !== audio.duration) {
        if (!isInputRange) {
            progressRange.value = audio.currentTime
            const progress = (audio.currentTime / audio.duration) * 100;
            progressBarFill.style.width = `${progress}%`;

            currentTimeSpan.textContent = formatTime(audio.currentTime)
        }
    } else {
        changeSongFetch({
            'last_track': audioTitle.textContent,
            'next': true,
            'random': randomSong
        })
    }
}

function randomToggle() {
    if (randomSong) {
        randomButton.firstElementChild.setAttribute('fill', 'lime')
    } else {
        randomButton.firstElementChild.setAttribute('fill', 'white')
    }
    randomSong = !randomSong
}

function repeatToggle() {
    if (isRepeat) {
        repeatButton.firstElementChild.setAttribute('fill', 'lime')
    } else {
        repeatButton.firstElementChild.setAttribute('fill', 'white')
    }
    isRepeat = !isRepeat
}


function formatTime(time) {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
}

function updateTotalTime() {
    totalTimeSpan.textContent = formatTime(audio.duration)
    audio.removeEventListener('loadedmetadata', updateTotalTime)
    progressRangeUpdate()
}

function updateMetadata(metadata) {
    audioCover.src = metadata['cover']
    audioTitle.textContent = metadata['name']
    audioTitle = document.getElementById('audio-title')
    audioAuthors.textContent = metadata['author'][0]
}

function progressRangeUpdate() {
    progressRange.setAttribute('max', audio.duration)
    progressRange.value = 0
}

function changeProgressBarRange() {
    if (!isInputRange) {
        isInputRange = true;
    }
    const progress = (progressRange.value / audio.duration) * 100;
    progressBarFill.style.width = `${progress}%`;

    currentTimeSpan.textContent = formatTime(progressRange.value)
}

function changeAudioTimeRange() {
    isInputRange = false;
    audio.currentTime = progressRange.value
}

function changeVolume() {
    audio.volume = (volumeControl.value / 100)
}


function updateAudio(urlBlob) {
    if (audio === null) {
        audio = new Audio(urlBlob)
    } else {
        audio.src = urlBlob
    }
    isPlaying = true
    audio.load()
    audio.play()
    mainPlayPauseButton.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="55" height="55" fill="lime" class="bi bi-pause-circle-fill" viewBox="0 0 16 16">
  <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0M6.25 5C5.56 5 5 5.56 5 6.25v3.5a1.25 1.25 0 1 0 2.5 0v-3.5C7.5 5.56 6.94 5 6.25 5m3.5 0c-.69 0-1.25.56-1.25 1.25v3.5a1.25 1.25 0 1 0 2.5 0v-3.5C11 5.56 10.44 5 9.75 5"/>
</svg>`
    audio.addEventListener('loadedmetadata', updateTotalTime)
    audio.addEventListener('timeupdate', updateProgress)
}


async function firstPlay() {
    const url = `http://${window.location.host}/player/api/v1/playlist/track/${getPlayList()}/`
    const csrftoken = getCookie('csrftoken')
    const responseMetadata = await fetch(url, {
        method: 'POST',
        mode: "cors",
        cache: "no-cache",
        credentials: "same-origin",
        headers: {
            'Content-Type': 'application/json',
            "X-CSRFToken": csrftoken,
        },
    })
    const metadata = await responseMetadata.json()
    const audioUrl = `http://${window.location.host}/player/api/v1/track/${metadata['data']['slug']}/`
    const responseAudio = await fetch(audioUrl)
    updateAudio(window.URL.createObjectURL(await responseAudio.blob()))
    updateMetadata(metadata['data'])
    volumeControl.value = 100
    mainPlayPauseButton.removeEventListener('click', firstPlay)
    mainPlayPauseButton.addEventListener('click', togglePlayPause)
    audioControlPanel.style.visibility = 'visible'

}

async function changeSongFetch(data) {
    if (!isRepeat) {
        const url = `http://${window.location.host}/player/api/v1/playlist/track/${getPlayList()}/`
        const csrftoken = getCookie('csrftoken')
        const responseMetadata = await fetch(url, {
            method: 'POST',
            mode: "cors",
            cache: "no-cache",
            credentials: "same-origin",
            headers: {
                'Content-Type': 'application/json',
                "X-CSRFToken": csrftoken,
            },
            body: JSON.stringify(data)
        })
        const metadata = await responseMetadata.json()
        const audioUrl = `http://${window.location.host}/player/api/v1/track/${metadata['data']['slug']}/`
        const responseAudio = await fetch(audioUrl)
        updateAudio(window.URL.createObjectURL(await responseAudio.blob()))
        updateMetadata(metadata['data'])
    } else {
        audio.currentTime = 0
        audio.play()
    }
}

nextButton.addEventListener('click', () => {
    changeSongFetch({
        'last_track': audioTitle.textContent,
        'next': true,
        'random': randomSong
    })
});

prevButton.addEventListener('click', () => {
    changeSongFetch({
        'last_track': audioTitle.textContent,
        'previous': true,
        'random': randomSong
    })
});

randomButton.addEventListener('click', randomToggle);

repeatButton.addEventListener('click', repeatToggle);

playPauseButton.addEventListener('click', togglePlayPause);

progressRange.addEventListener('input', changeProgressBarRange);

progressRange.addEventListener('change', changeAudioTimeRange);

volumeControl.addEventListener('input', changeVolume);

mainPlayPauseButton.addEventListener('click', firstPlay)
