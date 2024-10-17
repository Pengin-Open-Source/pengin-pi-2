
const checkedValues = [];
const uncheckedValues = [];
const formData = new FormData(document.getElementById('memberForm'));
const companyMemberEditLink = document.getElementById('company-member-edit-link')
const editLinkString = companyMemberEditLink.value;
const checkboxes = document.querySelectorAll('input[name="member-checkbox"]');



checkboxes.forEach(checkbox => {
  checkbox.addEventListener('change', () => {
    if (checkbox.checked) {
      checkedValues.push(checkbox.value);
      if (uncheckedValues.indexOf(checkbox.value) > -1) {
        uncheckedValues.splice(uncheckedValues.indexOf(checkbox.value), 1);
      }
    } else {
      if (checkedValues.indexOf(checkbox.value) > -1) {
        checkedValues.splice(checkedValues.indexOf(checkbox.value), 1);
      }
      uncheckedValues.push(checkbox.value);
    }
  });
});


function checkReferringPage() {
  const referrer = document.referrer;

  // Check if the referrer is empty or something other than a page in this editable list of members
  if (!referrer || !referrer.includes(editLinkString)) {
    // if we came from anything but another page in this list,  trigger a wipe out of 
    // The users prior selections
    const this_page = document.getElementsByName("page-number");

    fetch(editLinkString + '?wipe_out=True', {
      method: 'GET'
    }).then(data => {
      window.location.href = `?page=${this_page}`
    })
  }
}

window.addEventListener("load", checkReferringPage);


function saveSelectedMembers(company_id) {
  const selectedUsers = JSON.stringify(checkedValues);
  const deselectedUsers = JSON.stringify(uncheckedValues);
  fetch(editLinkString + '?selected_users=' + encodeURIComponent(selectedUsers) + '&unselected_users=' + encodeURIComponent(deselectedUsers), {
    method: 'POST'
  }).then(data => {
    window.location.href = `company/${company_id}/members/`
  })
}

function navigateToPage(page_number) {
  const selectedUsers = JSON.stringify(checkedValues);
  const deselectedUsers = JSON.stringify(uncheckedValues);
  fetch(editLinkString + '?page=' + page_number + '&selected_users=' + encodeURIComponent(selectedUsers) + '&unselected_users=' + encodeURIComponent(deselectedUsers), {
    method: 'GET'
  }).then(data => {
    window.location.href = `?page=${page_number}`
  })
}