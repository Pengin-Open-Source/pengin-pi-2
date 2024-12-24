/* Google Gemini's suggestion for clearing all the check boxes -  button needed
since the user cannot seem to manually deselect ALL participants once some are selected  */


function clearParticipants() {
    $('#id_participants').val([]).change();
}

/* Similar function for clearing roles  */
function clearRoles() {
    $('#id_roles').val([]).change();
}



