import {getCookie} from "./get_cookie.js";
import {playlistFetch} from "./playlist_controler.js";
import {favoriteAddRemove} from "./favorite_controler.js"

const favoriteButtons = document.getElementsByClassName('song-actions')
const playlists = document.getElementsByClassName('playlists')
const newPlaylists = document.getElementsByClassName('newPlaylist')


for (let i = 0; i < favoriteButtons.length; i++) {
    favoriteButtons[i].addEventListener('click', async (e) => {
        favoriteAddRemove(e.currentTarget.id.replace('favorite-', ''), getCookie('csrftoken'), favoriteButtons[i], undefined, 'red')
    })
}

const getTrackSlug = (element) => {
    return element.closest('.d-flex').getElementsByClassName('song-actions')[0].id.replace('favorite-', '')
}

for (let i = 0; i < playlists.length; i++) {
    playlists[i].addEventListener('click', (e) => {
        playlistFetch(getTrackSlug(e.currentTarget), getCookie('csrftoken'), e.currentTarget.id.replace('playlist-', ''))
    })
}
for (let i = 0; i < newPlaylists.length; i++) {
    newPlaylists[i].addEventListener('click', async (e) => {
        playlistFetch(getTrackSlug(e.currentTarget), getCookie('csrftoken'))
    })
}