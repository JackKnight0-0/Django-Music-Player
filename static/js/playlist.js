import {getCookie} from "./get_cookie.js";

const dropdownItems = document.getElementsByClassName('dropdown-item')


for (let i = 0; i < dropdownItems.length; i++) {
    dropdownItems[i].addEventListener('click', async (e) => {
        if (e.currentTarget.id.match('remove')) {
            const playlistPK = e.currentTarget.id.replace('remove-', '')
            const playlist = e.currentTarget.closest('.playlist-item')

            const response = await fetch(`http://${window.location.host}/player/api/v1/playlist/delete/${playlistPK}`, {
                'method': 'DELETE',
                mode: "cors",
                cache: "no-cache",
                credentials: "same-origin",
                headers: {
                    "Content-type": "application/json",
                    "X-CSRFToken": getCookie('csrftoken'),
                },
            })
            if (response.ok) {
                playlist.remove()
            }
        }
    })

}