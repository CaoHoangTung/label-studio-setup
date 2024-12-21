function confirmBeforeNavigation(link, message) {
    if (window.confirm(message)) {
        window.location = link;
    }
}