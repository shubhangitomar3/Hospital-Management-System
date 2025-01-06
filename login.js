document.getElementById('loginForm').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent the default form submission

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    // Replace these with your actual credentials
    const correctUsername = 'admin';
    const correctPassword = '123456';

    // Check if the entered credentials are correct
    if (username === correctUsername && password === correctPassword) {
        alert('Login successful!');
        
        // Redirect or perform login actions here
        window.location.href = 'index.html'; // Example redirection
    } else {
        alert('Incorrect username or password. Please try again.');
    }
});
