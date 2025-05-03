document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".code-card").forEach(card => {
        if (!card.classList.contains("used")) {
            card.addEventListener("click", () => {
                const code = card.dataset.code;
                const app_name = window.location.pathname.split("/")[1];

                // Copy to clipboard
                navigator.clipboard.writeText(code).then(() => {
                    alert("Copied: " + code);
                }).catch(() => {
                    alert("Failed to copy");
                });

                // Mark as used in backend
                fetch("/mark_used", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ app_name, code })
                }).then(res => res.json()).then(data => {
                    if (data.success) card.classList.add("used");
                });
            });
        }
    });
});