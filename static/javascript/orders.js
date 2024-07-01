// Add a new line of product with quantity in the order form
document.getElementById('add-more-products').addEventListener('click', function() {
    const formsetDiv = document.getElementById('order-products');
    const totalForms = document.getElementById('id_orderproduct_set-TOTAL_FORMS');
    const currentFormCount = parseInt(totalForms.value);
    const newForm = formsetDiv.lastElementChild.cloneNode(true);  // Clone the first form row
    // Update form indexes
    const formRegex = new RegExp(`orderproduct_set-\\d+`, 'g');
    newForm.innerHTML = newForm.innerHTML.replace(formRegex, `orderproduct_set-${currentFormCount}`);

    // Clear input values
    const inputs = newForm.querySelectorAll('input');
    inputs.forEach(input => {
        if (input.type !== 'hidden') {
            input.value = '';
        }
    });

    // Append the new form before the button
    formsetDiv.insertBefore(newForm, formsetDiv.lastElementChild.nextSibling);

    // Increment the total forms count
    totalForms.value = currentFormCount + 1;
});