const searchTrack = document.getElementById('search-track')
const searchResult = document.getElementById('search-results')
const url = `http://${window.location.host}/player/api/v1/search/track/`


searchTrack.addEventListener('input', async (e) => {

    q = e.target.value
    const response = await fetch(url + `?q=${q}`)

    const data = await response.json()
    if (data.data.length === 0 || !q) {
        searchResult.innerHTML = ''
    } else {
        insertSuggestions(data.data)
    }
})


function insertSuggestions(data) {
    searchResult.innerHTML = ''
    for (let i = 0; i < data.length; i++) {
        const newElement = document.createElement('div')
        newElement.insertAdjacentHTML('afterbegin', `<a href="${data[i].url}" style="text-decoration: none; color: lime">${data[i].name}</a>`)
        searchResult.appendChild(newElement)
    }

}

document.addEventListener('click', (event) => {
    if (!searchTrack.contains(event.target) && !searchResult.contains(event.target)) {
        searchResult.setAttribute('hidden', 'hidden')
    } else {
        searchResult.removeAttribute('hidden')
    }
});