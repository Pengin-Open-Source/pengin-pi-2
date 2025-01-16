/* Google Gemini's suggestion for clearing all the check boxes -  button needed
since the user cannot seem to manually deselect ALL participants once some are selected  */


function clearParticipants() {
    $('#id_participants').val([]).change();
}

/* Similar function for clearing roles  */
function clearRoles() {
    $('#id_roles').val([]).change();
}


/* Functions to Keep Track of User's TimeZone */

// Tweaked Gemini's idea on sending a value to the backend.
// using this to set the TimeZone from the home view
function sendLocalTimeZoneToServer(userZone) {
    fetch(`/home/?user_zone=${encodeURIComponent(userZone)}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();

        })
        .then(data => {
            console.log('Received from server:', data);
            // Handle the response from the server here
        })
        .catch(error => {
            console.error('There has been a problem with your fetch operation:', error);
        });
}

//Gemini code to extract a value out of the cookie
// Using this to get the time zone
function getCookieValue(cookieName) {
    const name = cookieName + "=";
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        let c = cookies[i].trim();
        if (c.indexOf(name) === 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}

function extractLocalTimeZone() {

    const timeZoneCookieValue = getCookieValue("time_zone");
    sendLocalTimeZoneToServer(timeZoneCookieValue)

}

window.addEventListener("load", extractLocalTimeZone);

