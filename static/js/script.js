// =====================================================
// MOBILE MENU
// =====================================================
const bar = document.getElementById("bar");
const closeBtn = document.getElementById("close");
const nav = document.getElementById("navbar");

if (bar && nav && closeBtn) {
    bar.addEventListener("click", () => {
        nav.classList.add("active");
        closeBtn.classList.add("active");
    });

    closeBtn.addEventListener("click", () => {
        nav.classList.remove("active");
        closeBtn.classList.remove("active");
    });
}

// =====================================================
// PRODUCT SEARCH
// =====================================================
const productContainer = document.getElementById("product1");
const searchInput = document.getElementById("search");

if (productContainer && searchInput) {
    const products = productContainer.querySelectorAll(".pro");

    searchInput.addEventListener("keyup", function (e) {
        const value = e.target.value.toUpperCase();

        products.forEach(product => {
            const name = product.querySelector("h6").innerText.toUpperCase();
            product.style.display = name.includes(value) ? "block" : "none";
        });
    });
}

// =====================================================
// CART SIDEBAR
// =====================================================
function openCart() {
    document.getElementById("cartSidebar").classList.add("open");
}

function closeCart() {
    document.getElementById("cartSidebar").classList.remove("open");
}
// ================= POPUP MESSAGE =================
function showMessage(message) {
    const msg = document.createElement("div");
    msg.className = "cart-popup";
    msg.innerText = message;
    document.body.appendChild(msg);
    setTimeout(() => msg.remove(), 2000);
}


// =====================================================
// CSRF TOKEN (Django Required)
// =====================================================
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
const csrftoken = getCookie('csrftoken');

// =====================================================
// ADD TO CART (Django Backend)
// =====================================================
function addToCart(productId, qty = 1) {
    fetch(`/add-to-cart/${productId}/`, {
        method: "POST",
        headers: {
            "X-CSRFToken": csrftoken,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ qty: qty })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            showMessage("Product added to cart!");
            loadCart();
            openCart();
        } else {
            showMessage(data.message || "Failed to add product");
        }
    });
}
// =====================================================
// LOAD CART FROM DJANGO
// =====================================================
function loadCart() {
    fetch("/get-cart/")
        .then(res => res.json())
        .then(data => {
            const cartItemsDiv = document.getElementById("cartItems");
            const totalAmount = document.getElementById("totalAmount");
            if (!cartItemsDiv || !totalAmount) return;

            cartItemsDiv.innerHTML = "";
            let totalQty = 0;

            data.items.forEach(item => {
                totalQty += item.qty;

                cartItemsDiv.innerHTML += `
                    <div class="cart-item">
                        <img src="${item.image}" width="60">
                        <div class="cart-info">
                            <p>${item.name}</p>
                            <p>₹${item.price}</p>
                            <div class="qty-controls">
                                <button onclick="updateCart(${item.id}, -1)">-</button>
                                <span id="qty-${item.id}">${item.qty}</span>
                                <button onclick="updateCart(${item.id}, 1)">+</button>
                            </div>
                        </div>
                        <button onclick="removeCart(${item.id})" class="remove-btn">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </div>
                `;
            });

            totalAmount.innerText = data.total.toFixed(2);

            // Update cart badges
            document.querySelectorAll(".cart-badge").forEach(b => b.innerText = totalQty);
        });
}
function loadCartCount() {

    fetch("/get-cart/")
        .then(response => response.json())
        .then(data => {

            const countElement = document.getElementById("cart-count");

            if (countElement) {
                countElement.innerText = data.total_qty;
            }
        });
}
function updateCart(cartId, change) {
    fetch("/update-cart/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken
        },
        body: JSON.stringify({ cart_id: cartId, change: change })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "error") {
            showMessage(data.message);
            return;
        }
        // Update sidebar dynamically
        loadCart();
    });
}
function removeCart(cartId) {
    fetch("/remove-cart/", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": csrftoken
        },
        body: `cart_id=${cartId}`
    })
    .then(res => res.json())
    .then(data => {
        loadCart();
    });
}

function toggleAddressForm() {
    let form = document.getElementById("addressForm");

    if (form.style.display === "none") {
        form.style.display = "block";
    } else {
        form.style.display = "none";
    }
}
// =====================================================
// CONTACT FORM VALIDATION
// =====================================================
function setError(inputId, message) {
    const input = document.getElementById(inputId);
    const error = document.getElementById(inputId + "Error");

    if (!input || !error) return;

    error.innerText = message;
    input.classList.add("errorborder");
    input.classList.remove("successborder");
}

function setSuccess(inputId) {
    const input = document.getElementById(inputId);
    const error = document.getElementById(inputId + "Error");

    if (!input || !error) return;

    error.innerText = "";
    input.classList.remove("errorborder");
    input.classList.add("successborder");
}

const contactForm = document.getElementById("contactForm");

if (contactForm) {
    contactForm.addEventListener("submit", function (e) {
        e.preventDefault();

        const name = document.getElementById("username").value.trim();
        const email = document.getElementById("useremail").value.trim();
        const subject = document.getElementById("subject").value.trim();
        const message = document.getElementById("message").value.trim();

        let isValid = true;

        // Name
        if (name === "") {
            setError("username", "Name is required");
            isValid = false;
        } else {
            setSuccess("username");
        }

        // Email
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailPattern.test(email)) {
            setError("useremail", "Enter a valid email");
            isValid = false;
        } else {
            setSuccess("useremail");
        }

        // Subject
        if (subject === "") {
            setError("subject", "Subject is required");
            isValid = false;
        } else {
            setSuccess("subject");
        }

        // Message
        if (message.length < 10) {
            setError("message", "Message must be at least 10 characters");
            isValid = false;
        } else {
            setSuccess("message");
        }

        if (!isValid) return;

        alert("Message sent successfully!");
        contactForm.reset();

        document.querySelectorAll("input, textarea").forEach(el => {
            el.classList.remove("successborder");
        });
    });
}

// =====================================================
// LOAD CART ON PAGE LOAD
// =====================================================
document.addEventListener("DOMContentLoaded", function () {
    const checkoutBtn = document.getElementById("checkoutBtn");
    if (checkoutBtn) {
        checkoutBtn.addEventListener("click", function () {
            fetch("/get-cart/")
                .then(res => res.json())
                .then(data => {
                    if (data.items.length === 0) {
                        showMessage("Your cart is empty!");
                        return;
                    }
                    window.location.href = "/checkout/";
                });
        });
    }

    // Load cart sidebar initially
    loadCart();
});

// ================= CHECKOUT =================
function goToCheckout() {
    window.location.href = "/checkout/";
}

document.addEventListener("DOMContentLoaded", function () {

    const checkoutBtn = document.getElementById("checkoutBtn");

    if (checkoutBtn) {
        checkoutBtn.addEventListener("click", function () {
            fetch("/get-cart/")
                .then(res => res.json())
                .then(data => {
                    if (data.items.length === 0) {
                        alert("Your cart is empty");
                        return;
                    }
                    window.location.href = "/checkout/";
                });
        });
    }

});
//if cart is empty prevent checkout
function goToCheckout() {
    fetch("/get-cart/")
        .then(res => res.json())
        .then(data => {
            if (data.items.length === 0) {
                alert("Your cart is empty");
                return;
            }
            window.location.href = "/checkout/";
        });
}


function setPayment(method) {
    document.getElementById("paymentMethod").value = method;
}

document.addEventListener("DOMContentLoaded", function () {
    loadCartCount();
});