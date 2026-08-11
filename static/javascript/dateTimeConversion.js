// Code to manage UTC-to-local timezone conversion.  Worked with Google Gemini on this
function convertUTCToLocal(utcTime) {
    const utcMillis = new Date(utcTime).getTime();
    const localDate = new Date(utcMillis);
    return localDate.toLocaleString('en-US', {
        month: 'long',
        day: 'numeric',
        year: 'numeric',
        hour: 'numeric',
        minute: 'numeric',
        hour12: true
    });

}