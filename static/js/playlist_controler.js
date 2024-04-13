export async function playlistFetch(trackSlug, csrftoken, playlistID = null) {
    if (playlistID !== null) {
        const response = await fetch(`http://${window.location.host}/player/api/v1/playlist/add/${trackSlug}/${playlistID}/`, {
            'method': 'POST',
            mode: "cors",
            cache: "no-cache",
            credentials: "same-origin",
            headers: {
                "Content-type": "application/json",
                "X-CSRFToken": csrftoken,
            }
        })
    } else {
        const response = await fetch(`http://${window.location.host}/player/api/v1/playlist/create/${trackSlug}/`,
            {
                method: 'POST',
                mode: "cors",
                cache: "no-cache",
                credentials: 'same-origin',
                headers: {
                    "Content-type": "application/json",
                    "X-CSRFToken": csrftoken,
                }
            }
        )
    }
}
