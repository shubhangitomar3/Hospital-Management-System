// Toggle Mobile Menu
const menuBars = document.getElementById("menu-bars");
const navbar = document.querySelector(".navbar");

menuBars.addEventListener("click", () => {
    navbar.classList.toggle("active");
});

// Smooth Scroll for Internal Links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();

        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});

// Scroll Animation with Intersection Observer
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            observer.unobserve(entry.target);
        }
    });
});

document.querySelectorAll('.animate-on-scroll').forEach((el) => {
    observer.observe(el);
});

// Modal for Doctor Images
const modal = document.getElementById("imageModal");
const modalImg = document.getElementById("modalImg");
const closeModal = document.getElementsByClassName("close")[0];

document.querySelectorAll('.doc-poster img').forEach(img => {
    img.addEventListener('click', () => {
        modal.style.display = "block";
        modalImg.src = img.src;
    });
});

closeModal.onclick = function() {
    modal.style.display = "none";
};

// Feedback Form Submission (Optional)
const form = document.querySelector('form');
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(form);

    try {
        const response = await fetch('/submit', {
            method: 'POST',
            body: formData,
        });
        if (response.ok) {
            alert('Form submitted successfully!');
            form.reset();
        } else {
            alert('There was an error submitting the form.');
        }
    } catch (error) {
        console.error('Error:', error);
    }
});
